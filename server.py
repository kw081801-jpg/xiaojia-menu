#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小家菜单 · 后端（零依赖，只用 Python 标准库）

    python server.py                # 默认 0.0.0.0:8080
    python server.py --port 9000

第一次打开 http://localhost:8080/admin.html
默认管理密码：xiaojia   （用环境变量 XJ_ADMIN_PASSWORD 覆盖，上线一定要改）

数据落在一个 SQLite 文件 data.db 里，删掉它等于恢复出厂设置。
"""

import base64
import hashlib
import hmac
import json
import mimetypes
import os
import re
import secrets
import sqlite3
import sys
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ROOT, "data.db")
UPLOAD_DIR = os.path.join(ROOT, "images", "uploads")
PASSWORD = os.environ.get("XJ_ADMIN_PASSWORD", "xiaojia")
SESSIONS = {}          # token -> expire_ts
SESSION_TTL = 7 * 24 * 3600

mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("application/javascript", ".js")

# ---------------------------------------------------------------- db

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS items (
            id TEXT PRIMARY KEY, sort INTEGER, data TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK (id = 1), data TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created TEXT NOT NULL, who TEXT, note TEXT, items TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'new'
        );
        """
    )
    conn.commit()
    conn.close()


def get_settings():
    conn = db()
    row = conn.execute("SELECT data FROM settings WHERE id = 1").fetchone()
    conn.close()
    return json.loads(row["data"]) if row else {}


def put_settings(data):
    conn = db()
    conn.execute(
        "INSERT INTO settings (id, data) VALUES (1, ?) "
        "ON CONFLICT(id) DO UPDATE SET data = excluded.data",
        (json.dumps(data, ensure_ascii=False),),
    )
    conn.commit()
    conn.close()


def list_items():
    conn = db()
    rows = conn.execute("SELECT data FROM items ORDER BY sort, rowid").fetchall()
    conn.close()
    return [json.loads(r["data"]) for r in rows]


def upsert_item(item):
    data = dict(item)
    if not data.get("id"):
        base = slugify(data.get("name") or "dish")
        data["id"] = base + "-" + secrets.token_hex(3)
    conn = db()
    nxt = conn.execute("SELECT COALESCE(MAX(sort), 0) + 1 FROM items").fetchone()[0]
    conn.execute(
        "INSERT INTO items (id, sort, data) VALUES (?, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET data = excluded.data",
        (data["id"], data.get("sort") or nxt, json.dumps(data, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()
    return data


def delete_item(item_id):
    conn = db()
    cur = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return cur.rowcount > 0


def replace_all(settings, items):
    conn = db()
    conn.execute("DELETE FROM items")
    for i, it in enumerate(items):
        data = dict(it)
        if not data.get("id"):
            data["id"] = slugify(data.get("name") or "dish") + "-" + secrets.token_hex(3)
        conn.execute(
            "INSERT INTO items (id, sort, data) VALUES (?, ?, ?)",
            (data["id"], i + 1, json.dumps(data, ensure_ascii=False)),
        )
    conn.commit()
    conn.close()
    if settings is not None:
        put_settings(settings)


def slugify(text):
    text = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", str(text)).strip("-")
    return text or "dish"


# ---------------------------------------------------------------- http

class Handler(BaseHTTPRequestHandler):
    server_version = "XiaojiaMenu/1.0"

    # ---- helpers
    def _json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if not n:
            return {}
        raw = self.rfile.read(n)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def _cookie_token(self):
        raw = self.headers.get("Cookie") or ""
        for part in raw.split(";"):
            k, _, v = part.strip().partition("=")
            if k == "xj_admin":
                return v
        return None

    def _is_admin(self):
        tok = self._cookie_token()
        exp = SESSIONS.get(tok) if tok else None
        if not exp:
            return False
        if exp < time.time():
            SESSIONS.pop(tok, None)
            return False
        return True

    def _require_admin(self):
        if self._is_admin():
            return True
        self._json({"error": "需要登录"}, 401)
        return False

    # ---- routing
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path.startswith("/api/"):
            return self.api_get(path)
        return self.static(path)

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        data = self._body()
        if path == "/api/login":
            if hmac.compare_digest(str(data.get("password", "")), PASSWORD):
                tok = secrets.token_urlsafe(24)
                SESSIONS[tok] = time.time() + SESSION_TTL
                body = json.dumps({"ok": True}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_header(
                    "Set-Cookie",
                    "xj_admin=%s; Path=/; HttpOnly; SameSite=Lax; Max-Age=%d" % (tok, SESSION_TTL),
                )
                self.end_headers()
                self.wfile.write(body)
                return
            return self._json({"error": "密码不对"}, 401)
        if path == "/api/logout":
            tok = self._cookie_token()
            if tok:
                SESSIONS.pop(tok, None)
            return self._json({"ok": True})
        if path == "/api/orders":
            items = data.get("items") or []
            if not isinstance(items, list) or not items:
                return self._json({"error": "没选菜"}, 400)
            known = {i.get("id"): i.get("name") for i in list_items()}
            resolved = [{"id": i, "name": known.get(i, i)} for i in items if i in known]
            if not resolved:
                return self._json({"error": "菜不在菜单里"}, 400)
            conn = db()
            conn.execute(
                "INSERT INTO orders (created, who, note, items, status) VALUES (?, ?, ?, ?, 'new')",
                (
                    time.strftime("%Y-%m-%d %H:%M"),
                    str(data.get("who", ""))[:40],
                    str(data.get("note", ""))[:200],
                    json.dumps(resolved, ensure_ascii=False),
                ),
            )
            conn.commit()
            oid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.close()
            return self._json({"ok": True, "id": oid})
        if path == "/api/items":
            if not self._require_admin():
                return
            item = data.get("item") or {}
            if not (item.get("name") or "").strip():
                return self._json({"error": "菜名不能空"}, 400)
            return self._json({"ok": True, "item": upsert_item(item)})
        if path == "/api/settings":
            if not self._require_admin():
                return
            put_settings(data.get("settings") or {})
            return self._json({"ok": True})
        if path == "/api/seed":
            if not self._require_admin():
                return
            replace_all(data.get("settings"), data.get("items") or [])
            return self._json({"ok": True, "count": len(data.get("items") or [])})
        if path == "/api/upload":
            if not self._require_admin():
                return
            blob = str(data.get("data") or "")
            m = re.match(r"data:image/(png|jpeg|jpg|webp);base64,(.+)", blob)
            if not m:
                return self._json({"error": "只收 png/jpg/webp"}, 400)
            ext = "jpg" if m.group(1) in ("jpeg", "jpg") else m.group(1)
            raw = base64.b64decode(m.group(2))
            if len(raw) > 6 * 1024 * 1024:
                return self._json({"error": "图太大（上限 6MB）"}, 400)
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            name = slugify(data.get("name") or "img")[:40] + "-" + secrets.token_hex(4) + "." + ext
            with open(os.path.join(UPLOAD_DIR, name), "wb") as f:
                f.write(raw)
            return self._json({"ok": True, "path": "images/uploads/" + name})
        return self._json({"error": "not found"}, 404)

    def do_DELETE(self):
        path = urllib.parse.urlparse(self.path).path
        if path.startswith("/api/items/"):
            if not self._require_admin():
                return
            return self._json({"ok": delete_item(path.rsplit("/", 1)[-1])})
        if path.startswith("/api/orders/"):
            if not self._require_admin():
                return
            oid = path.rsplit("/", 1)[-1]
            conn = db()
            conn.execute("DELETE FROM orders WHERE id = ?", (oid,))
            conn.commit()
            conn.close()
            return self._json({"ok": True})
        return self._json({"error": "not found"}, 404)

    def do_PATCH(self):
        path = urllib.parse.urlparse(self.path).path
        if path.startswith("/api/orders/"):
            if not self._require_admin():
                return
            oid = path.rsplit("/", 1)[-1]
            status = (self._body().get("status") or "new")[:10]
            conn = db()
            conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, oid))
            conn.commit()
            conn.close()
            return self._json({"ok": True})
        return self._json({"error": "not found"}, 404)

    def api_get(self, path):
        if path == "/api/menu":
            return self._json({"settings": get_settings(), "items": list_items()})
        if path == "/api/session":
            return self._json({"ok": self._is_admin()})
        if path == "/api/orders":
            if not self._require_admin():
                return
            conn = db()
            rows = conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 200").fetchall()
            conn.close()
            out = []
            for r in rows:
                out.append(
                    {
                        "id": r["id"],
                        "created": r["created"],
                        "who": r["who"],
                        "note": r["note"],
                        "items": json.loads(r["items"]),
                        "status": r["status"],
                    }
                )
            return self._json({"orders": out})
        return self._json({"error": "not found"}, 404)

    def static(self, path):
        if path in ("/", ""):
            path = "/index.html"
        rel = urllib.parse.unquote(path.lstrip("/"))
        full = os.path.abspath(os.path.join(ROOT, rel))
        if not full.startswith(ROOT) or not os.path.isfile(full):
            return self._json({"error": "not found"}, 404)
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
            ctype += "; charset=utf-8"
        with open(full, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (time.strftime("%H:%M:%S"), fmt % args))


def main():
    port = 8080
    host = "0.0.0.0"
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--port" and i + 1 < len(args):
            port = int(args[i + 1])
        if a == "--host" and i + 1 < len(args):
            host = args[i + 1]
    init_db()
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    srv = ThreadingHTTPServer((host, port), Handler)
    print("小家菜单后端：http://127.0.0.1:%d/  管理台 /admin.html" % port)
    print("数据文件：%s" % DB_PATH)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    main()
