#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小家菜单 · 后端（Python 标准库，无第三方依赖）

    python server.py                     # 0.0.0.0:8080
    XJ_ADMIN_PASSWORD=新密码 python server.py

数据就一个 data.json：settings / items / orders。删掉即恢复出厂。
找图功能：Pexels（有 key 时）→ Openverse → Wikimedia Commons，都不需要账号。
"""

import hashlib
import hmac
import json
import mimetypes
import os
import re
import secrets
import sys
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data.json")
UPLOADS = os.path.join(ROOT, "images", "uploads")
PASSWORD = os.environ.get("XJ_ADMIN_PASSWORD", "xiaojia")
PEXELS_KEY = os.environ.get("PEXELS_API_KEY", "")
LLM_KEY = os.environ.get("DEEPSEEK_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")
RECIPES_PATH = os.path.join(ROOT, "recipes.json")
UA = "XiaojiaMenu/1.0 (+personal use)"
UA_BROWSER = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
LOCK = threading.Lock()
SESSIONS = {}          # token -> 过期时间戳
SEARCH_CACHE = {}      # 关键词 -> (时间戳, 结果)
LOGIN_FAILS = {}       # ip -> [失败次数, 解锁时间]
MAX_FAILS = 5
LOCK_SECONDS = 300

mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("font/woff2", ".woff2")

# ---------------------------------------------------------------- 数据

ICON_ALIAS = {"wok": "katsu", "pot": "penguin", "bowl": "bear", "cake": "tapioca", "cup": "lizard"}


def normalize_settings(st):
    """老数据里的线稿图标名（wok/pot/...）映射成角色图名，避免前台裂图。"""
    for c in (st.get("categories") or []):
        if c.get("icon") in ICON_ALIAS:
            c["icon"] = ICON_ALIAS[c["icon"]]
    return st


def load():
    if not os.path.exists(DATA):
        return {"settings": {}, "items": [], "orders": [], "wishes": []}
    with open(DATA, encoding="utf-8") as f:
        d = json.load(f)
    d.setdefault("settings", {})
    d.setdefault("items", [])
    d.setdefault("orders", [])
    d.setdefault("wishes", [])
    return d


def save(d):
    tmp = DATA + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(tmp, DATA)


def _secret():
    with LOCK:
        d = load()
    if not d.get("secret"):
        d["secret"] = secrets.token_hex(32)
        with LOCK:
            cur = load()
            cur["secret"] = d["secret"]
            save(cur)
    return d["secret"]


def make_token(ttl=7 * 86400):
    exp = int(time.time()) + ttl
    sig = hmac.new(_secret().encode(), str(exp).encode(), hashlib.sha256).hexdigest()[:32]
    return "%d.%s" % (exp, sig)


def check_token(tok):
    try:
        exp_s, sig = tok.split(".")
        exp = int(exp_s)
    except Exception:
        return False
    if exp < time.time():
        return False
    good = hmac.new(_secret().encode(), exp_s.encode(), hashlib.sha256).hexdigest()[:32]
    return hmac.compare_digest(sig, good)


def slug(text):
    return re.sub(r"[^\w\u4e00-\u9fff-]+", "-", str(text)).strip("-")[:40] or "dish"


# ---------------------------------------------------------------- 找图

def _get(url, timeout=20, limit=8 * 1024 * 1024, headers=None):
    h = {
        "User-Agent": UA_BROWSER,
        "Accept": "application/json, text/html, image/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.6",
    }
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(limit), r.headers.get("Content-Type", "")


def search_openverse(q):
    u = ("https://api.openverse.org/v1/images/?q=%s&page_size=8&size=large&mature=false"
         % urllib.parse.quote(q))
    data, _ = _get(u, timeout=15)
    out = []
    for it in json.loads(data).get("results", []):
        if it.get("url"):
            out.append({
                "url": it["url"], "thumb": it.get("thumbnail") or it["url"],
                "title": (it.get("title") or "")[:60], "source": "Openverse",
                "license": (it.get("license") or "").upper(),
            })
    return out


def search_wikimedia(q):
    u = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search"
         "&gsrnamespace=6&gsrlimit=8&gsrsearch=%s&prop=imageinfo&iiprop=url&iiurlwidth=1200"
         % urllib.parse.quote("filetype:bitmap " + q))
    data, _ = _get(u, timeout=15)
    pages = (json.loads(data).get("query") or {}).get("pages", {})
    out = []
    for p in pages.values():
        info = (p.get("imageinfo") or [{}])[0]
        if info.get("url"):
            out.append({
                "url": info["url"], "thumb": info.get("thumburl") or info["url"],
                "title": (p.get("title") or "").replace("File:", "")[:60],
                "source": "Wikimedia", "license": "CC",
            })
    return out



def search_baidu(q):
    """百度图片：国内直连、无需 key，中文菜名命中率最高。"""
    u = ("https://image.baidu.com/search/acjson?tn=resultjson_com&ipn=rj&ct=201326592&is=&fp=result"
         "&cl=2&lm=-1&ie=utf-8&oe=utf-8&st=-1&word=%s&pn=0&rn=20" % urllib.parse.quote(q))
    raw, _ = _get(u, timeout=10, headers={
        "Referer": "https://image.baidu.com/search/index?tn=baiduimage&word=x",
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest",
    })
    d = json.loads(raw.decode("utf-8", "ignore"))
    out = []
    for it in d.get("data", []):
        if not isinstance(it, dict):
            continue
        url = it.get("middleURL") or it.get("hoverURL") or it.get("thumbURL")
        if url and url.startswith("http"):
            out.append({
                "url": url, "thumb": it.get("thumbURL") or url,
                "title": (it.get("fromPageTitleEnc") or "")[:60],
                "source": "百度", "license": "",
            })
    return out


def search_bing(q):
    """Bing 中国站图片搜索，不需要 key。"""
    u = "https://cn.bing.com/images/async?q=%s&first=1&count=35&mkt=zh-CN&loadasync=1" % urllib.parse.quote(q)
    raw, _ = _get(u, timeout=10)
    html = raw.decode("utf-8", "ignore").replace("&quot;", '"').replace("&amp;", "&")
    urls = re.findall(r'"murl":"(https?://[^"]+)"', html)
    out = []
    for x in urls:
        out.append({"url": x, "thumb": x, "title": "", "source": "Bing", "license": ""})
    return out


def search_wikipedia(name, lang="zh"):
    """维基条目首图往往就是这道菜本身，命中最准。"""
    if not name:
        return []
    u = "https://%s.wikipedia.org/api/rest_v1/page/summary/%s" % (lang, urllib.parse.quote(name))
    data, _ = _get(u, timeout=12)
    d = json.loads(data)
    img = (d.get("originalimage") or {}).get("source")
    if not img:
        return []
    return [{
        "url": img, "thumb": (d.get("thumbnail") or {}).get("source") or img,
        "title": d.get("title") or name, "source": "Wikipedia", "license": "CC",
    }]


def search_pexels(q):
    u = ("https://api.pexels.com/v1/search?query=%s&per_page=8&orientation=landscape"
         % urllib.parse.quote(q))
    req = urllib.request.Request(u, headers={"Authorization": PEXELS_KEY, "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
    return [{
        "url": p["src"]["large2x"], "thumb": p["src"]["medium"],
        "title": (p.get("alt") or "")[:60], "source": "Pexels", "license": "Pexels",
    } for p in data.get("photos", [])]


def load_recipes():
    try:
        with open(RECIPES_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def autofill(name):
    """先查内置菜谱库；没有但配了大模型 key，就让模型写一份。"""
    name = name.strip()
    if not name:
        return None
    lib = load_recipes()
    if name in lib:
        return lib[name]
    for k, v in lib.items():
        if k in name or name in k:
            return v
    if not LLM_KEY:
        return None
    prompt = (
        "你是家常菜谱助手。为「%s」写一份中文菜谱，只输出 JSON，字段："
        '{"en":"英文名","cat":"home|soup|staple|sweet|drink","flavor":"口味词 · 口味词",'
        '"time":"20 分钟","level":"新手|顺手|慢炖","serve":"2 人份","tag":"招牌|上菜快|空字符串",'
        '"intro":"一句话介绍","ingredients":["食材 用量"],"steps":["步骤"],"tips":"一句提示"}'
        "。共 4-6 条食材、3-5 个步骤，别输出多余文字。" % name
    )
    body = json.dumps({
        "model": "deepseek-chat" if os.environ.get("DEEPSEEK_API_KEY") else "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.3,
    }).encode()
    url = ("https://api.deepseek.com/chat/completions" if os.environ.get("DEEPSEEK_API_KEY")
           else "https://api.openai.com/v1/chat/completions")
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/json", "Authorization": "Bearer " + LLM_KEY})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            data = json.loads(r.read().decode())
        return json.loads(data["choices"][0]["message"]["content"])
    except Exception:
        return None


def find_images(q, name=""):
    key = (q + "|" + name).lower().strip()
    hit = SEARCH_CACHE.get(key)
    if hit and time.time() - hit[0] < 3600:
        return hit[1]
    results = []
    # 国内服务器优先走百度和 Bing 中国站，海外源只在有网时兜底
    plan = []
    if PEXELS_KEY:
        plan.append(search_pexels)
    if q:
        plan.append(search_baidu)
        plan.append(search_bing)
    if name:
        plan.append(lambda _q, n=name: search_wikipedia(n, "zh"))
    plan += [search_openverse, search_wikimedia]
    if q:
        plan.append(lambda _q: search_wikipedia(_q, "en"))
    for fn in plan:
        try:
            results += fn(q)
        except Exception:
            continue
        if len(results) >= 10:
            break
    seen, out = set(), []
    for r in results:
        if r["url"] in seen:
            continue
        seen.add(r["url"])
        out.append(r)
    SEARCH_CACHE[key] = (time.time(), out[:8])
    return out[:8]


def download_image(url, name):
    parts = urllib.parse.urlsplit(url)
    ref = "%s://%s/" % (parts.scheme, parts.netloc)
    if "baidu.com" in url:
        ref = "https://image.baidu.com/"
    elif "bing.com" in url or "bing.net" in url:
        ref = "https://cn.bing.com/"
    req = urllib.request.Request(url, headers={
        "User-Agent": UA_BROWSER,
        "Referer": ref,
        "Accept": "image/avif,image/webp,image/*,*/*;q=0.8",
    })
    def _fetch(u, referer):
        h = {"User-Agent": UA_BROWSER, "Accept": "image/avif,image/webp,image/*,*/*;q=0.8"}
        if referer:
            h["Referer"] = referer
        with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=25) as r:
            return r.headers.get("Content-Type", ""), r.read(8 * 1024 * 1024)

    try:
        ctype, data = _fetch(url, ref)
    except Exception:
        ctype, data = _fetch(url, None)
    if not ctype.startswith("image/"):
        raise ValueError("不是图片：" + ctype)
    ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
           "image/gif": ".gif"}.get(ctype.split(";")[0], ".jpg")
    base = (re.sub(r"[^a-z0-9]+", "-", slug(name).lower()).strip("-")[:28] or "dish") + "-" + secrets.token_hex(3)
    os.makedirs(UPLOADS, exist_ok=True)
    path = os.path.join(UPLOADS, base + ext)
    with open(path, "wb") as f:
        f.write(data)
    try:  # 有 Pillow 就顺手压成 webp，没有就原样留着
        from PIL import Image
        im = Image.open(path)
        im.thumbnail((1400, 1400))
        webp = os.path.join(UPLOADS, base + ".webp")
        im.convert("RGB").save(webp, "WEBP", quality=82, method=5)
        if webp != path:
            os.remove(path)
        return "images/uploads/" + base + ".webp"
    except Exception:
        return "images/uploads/" + os.path.basename(path)


# ---------------------------------------------------------------- HTTP

class H(BaseHTTPRequestHandler):
    server_version = "XiaojiaMenu/2"

    def json(self, obj, code=200, cookie=None):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            return json.loads(self.rfile.read(n).decode()) if n else {}
        except Exception:
            return {}

    def client_ip(self):
        fwd = (self.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
        return fwd or self.client_address[0]

    def token(self):
        for part in (self.headers.get("Cookie") or "").split(";"):
            k, _, v = part.strip().partition("=")
            if k == "xj_admin":
                return v
        return None

    def admin(self):
        t = self.token()
        if not t:
            return False
        if SESSIONS.get(t, 0) > time.time():
            return True
        return check_token(t)

    def need_admin(self):
        if self.admin():
            return True
        self.json({"error": "需要登录"}, 401)
        return False

    # ---------- GET ----------
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(p.query)
        if p.path == "/api/menu":
            with LOCK:
                d = load()
            return self.json({"settings": normalize_settings(d["settings"]), "items": d["items"]})
        if p.path == "/api/session":
            return self.json({"ok": self.admin()})
        if p.path == "/api/autofill":
            if not self.need_admin():
                return
            name = (qs.get("name") or [""])[0].strip()
            item = autofill(name)
            return self.json({"found": bool(item), "item": item or {}})
        if p.path == "/api/wishes":
            if not self.need_admin():
                return
            with LOCK:
                d = load()
            return self.json({"wishes": list(reversed(d["wishes"]))})
        if p.path == "/api/orders":
            if not self.need_admin():
                return
            with LOCK:
                d = load()
            return self.json({"orders": list(reversed(d["orders"]))})
        if p.path == "/api/thumb":
            u = (qs.get("u") or [""])[0]
            if not u.startswith(("http://", "https://")):
                return self.json({"error": "bad"}, 400)
            try:
                ref = "https://image.baidu.com/" if "baidu.com" in u else (
                    "https://cn.bing.com/" if ("bing.com" in u or "bing.net" in u) else "https://commons.wikimedia.org/")
                req = urllib.request.Request(u, headers={"User-Agent": UA_BROWSER, "Referer": ref})
                with urllib.request.urlopen(req, timeout=20) as r:
                    body = r.read(4 * 1024 * 1024)
                    ctype = r.headers.get("Content-Type", "image/jpeg")
            except Exception:
                return self.json({"error": "拿不到图"}, 502)
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            self.wfile.write(body)
            return
        if p.path == "/api/find-image":
            if not self.need_admin():
                return
            q = (qs.get("q") or [""])[0].strip()
            name = (qs.get("name") or [""])[0].strip()
            if not q and not name:
                return self.json({"error": "给个搜索词"}, 400)
            return self.json({"results": find_images(q or name, name)})
        return self.static(p.path)

    # ---------- POST ----------
    def do_POST(self):
        p = urllib.parse.urlparse(self.path).path
        b = self.body()

        if p == "/api/login":
            ip = self.client_ip()
            now = time.time()
            rec = LOGIN_FAILS.get(ip)
            if rec and rec[0] >= MAX_FAILS and now < rec[1]:
                return self.json({"error": "试错太多，等 %d 秒" % int(rec[1] - now)}, 429)
            if not secrets.compare_digest(str(b.get("password", "")), PASSWORD):
                rec = LOGIN_FAILS.setdefault(ip, [0, 0.0])
                rec[0] += 1
                if rec[0] >= MAX_FAILS:
                    rec[1] = now + LOCK_SECONDS
                return self.json({"error": "密码不对"}, 401)
            LOGIN_FAILS.pop(ip, None)
            tok = make_token(7 * 86400)
            SESSIONS[tok] = time.time() + 7 * 86400
            return self.json({"ok": True}, cookie="xj_admin=%s; Path=/; HttpOnly; SameSite=Lax; Max-Age=%d" % (tok, 7 * 86400))
        if p == "/api/logout":
            SESSIONS.pop(self.token(), None)
            return self.json({"ok": True})
        if p == "/api/orders":
            ids = b.get("items") or []
            with LOCK:
                d = load()
                names = {i.get("id"): i.get("name") for i in d["items"]}
                picked = [{"id": i, "name": names.get(i, i)} for i in ids if i in names]
                if not picked:
                    return self.json({"error": "菜不在菜单里"}, 400)
                d["orders"].append({
                    "id": (d["orders"][-1]["id"] + 1) if d["orders"] else 1,
                    "created": time.strftime("%Y-%m-%d %H:%M"),
                    "visit": str(b.get("visit", ""))[:10],
                    "who": str(b.get("who", ""))[:40],
                    "note": str(b.get("note", ""))[:200],
                    "items": picked, "status": "new",
                })
                save(d)
                return self.json({"ok": True, "id": d["orders"][-1]["id"]})
        if p == "/api/wishes":
            dish = str(b.get("dish", "")).strip()[:60]
            if not dish:
                return self.json({"error": "先写个菜名"}, 400)
            with LOCK:
                d = load()
                d["wishes"].append({
                    "id": (d["wishes"][-1]["id"] + 1) if d["wishes"] else 1,
                    "created": time.strftime("%Y-%m-%d %H:%M"),
                    "dish": dish,
                    "note": str(b.get("note", ""))[:300],
                    "who": str(b.get("who", ""))[:40],
                    "status": "new",
                })
                save(d)
            return self.json({"ok": True})
        if p == "/api/items":
            if not self.need_admin():
                return
            it = b.get("item") or {}
            if not str(it.get("name", "")).strip():
                return self.json({"error": "菜名不能空"}, 400)
            with LOCK:
                d = load()
                it["id"] = it.get("id") or slug(it["name"]) + "-" + secrets.token_hex(3)
                for i, old in enumerate(d["items"]):
                    if old.get("id") == it["id"]:
                        d["items"][i] = it
                        break
                else:
                    d["items"].append(it)
                save(d)
            return self.json({"ok": True, "item": it})
        if p == "/api/settings":
            if not self.need_admin():
                return
            with LOCK:
                d = load()
                d["settings"] = b.get("settings") or d["settings"]
                save(d)
            return self.json({"ok": True})
        if p == "/api/seed":
            if not self.need_admin():
                return
            with LOCK:
                d = load()
                d["settings"] = b.get("settings") or d["settings"]
                d["items"] = b.get("items") or []
                save(d)
            return self.json({"ok": True, "count": len(d["items"])})
        if p == "/api/upload":
            if not self.need_admin():
                return
            m = re.match(r"data:image/(png|jpeg|jpg|webp);base64,(.+)", str(b.get("data") or ""))
            if not m:
                return self.json({"error": "只收 png/jpg/webp"}, 400)
            raw = __import__("base64").b64decode(m.group(2))
            if len(raw) > 8 * 1024 * 1024:
                return self.json({"error": "图太大（8MB 以内）"}, 400)
            os.makedirs(UPLOADS, exist_ok=True)
            ext = ".jpg" if m.group(1) in ("jpeg", "jpg") else "." + m.group(1)
            name = (re.sub(r"[^a-z0-9]+", "-", slug(b.get("name") or "img").lower()).strip("-")[:28] or "img") + "-" + secrets.token_hex(3) + ext
            with open(os.path.join(UPLOADS, name), "wb") as f:
                f.write(raw)
            return self.json({"ok": True, "path": "images/uploads/" + name})
        if p == "/api/fetch-image":
            if not self.need_admin():
                return
            url = str(b.get("url") or "")
            if not url.startswith(("http://", "https://")):
                return self.json({"error": "地址不对"}, 400)
            try:
                return self.json({"ok": True, "path": download_image(url, b.get("name") or "dish")})
            except Exception as e:
                return self.json({"error": str(e)}, 400)
        return self.json({"error": "not found"}, 404)

    # ---------- DELETE / PATCH ----------
    def do_DELETE(self):
        p = urllib.parse.urlparse(self.path).path
        if p.startswith("/api/items/"):
            if not self.need_admin():
                return
            iid = p.rsplit("/", 1)[-1]
            with LOCK:
                d = load()
                d["items"] = [i for i in d["items"] if i.get("id") != iid]
                save(d)
            return self.json({"ok": True})
        if p.startswith("/api/wishes/"):
            if not self.need_admin():
                return
            wid = p.rsplit("/", 1)[-1]
            with LOCK:
                d = load()
                d["wishes"] = [w for w in d["wishes"] if str(w.get("id")) != wid]
                save(d)
            return self.json({"ok": True})
        if p.startswith("/api/orders/"):
            if not self.need_admin():
                return
            oid = p.rsplit("/", 1)[-1]
            with LOCK:
                d = load()
                d["orders"] = [o for o in d["orders"] if str(o.get("id")) != oid]
                save(d)
            return self.json({"ok": True})
        return self.json({"error": "not found"}, 404)

    def do_PATCH(self):
        p = urllib.parse.urlparse(self.path).path
        if p.startswith("/api/orders/"):
            if not self.need_admin():
                return
            oid = p.rsplit("/", 1)[-1]
            status = str(self.body().get("status") or "new")[:10]
            with LOCK:
                d = load()
                for o in d["orders"]:
                    if str(o.get("id")) == oid:
                        o["status"] = status
                save(d)
            return self.json({"ok": True})
        return self.json({"error": "not found"}, 404)

    # ---------- 静态 ----------
    def static(self, path):
        if path in ("/", ""):
            path = "/index.html"
        full = os.path.abspath(os.path.join(ROOT, urllib.parse.unquote(path.lstrip("/"))))
        if not full.startswith(ROOT) or not os.path.isfile(full):
            return self.json({"error": "not found"}, 404)
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        if ctype.startswith("text/") or "javascript" in ctype:
            ctype += "; charset=utf-8"
        with open(full, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *a):
        sys.stderr.write("%s %s\n" % (time.strftime("%H:%M:%S"), fmt % a))


def main():
    port, host = 8080, "0.0.0.0"
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if a == "--port":
            port = int(argv[i + 1])
        if a == "--host":
            host = argv[i + 1]
    os.makedirs(UPLOADS, exist_ok=True)
    if PASSWORD == "xiaojia":
        print("!! 正在使用默认密码 xiaojia，公网部署请务必设置 XJ_ADMIN_PASSWORD")
    if host == "0.0.0.0":
        print("!! 监听 0.0.0.0，管理台对所有能连上的人开放；建议 --host 127.0.0.1 并用 Nginx 反代")
    print("小家菜单：http://127.0.0.1:%d/   管理台 /admin.html" % port)
    print("数据：%s" % DATA)
    ThreadingHTTPServer((host, port), H).serve_forever()


if __name__ == "__main__":
    main()
