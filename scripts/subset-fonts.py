#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重建字体子集（本地子集化，不依赖 Google Fonts 的 text 接口）。

页面只内置了两个字体的拉丁/中文子集，其余全部走系统字体：
  fonts/cormorant-var.woff2         拉丁衬线（Cormorant Garamond，可变字重）
  fonts/cormorant-var-italic.woff2  同上斜体
  fonts/zcool-subset.woff2          「角落」主题的圆体（只含页面用到的字）

改了 menu-data.js 里的菜名 / 分类名，或者在服务器管理台新增菜品后，
把新字补进 font-extra.txt，然后跑：

    python scripts/subset-fonts.py

字库来源：scripts/.cache/ZCOOLKuaiLe-Regular.ttf
（缺失时会自动从 GitHub 镜像下载一次；也可以设 ZCOOL_TTF 指向自己的文件）

注意：Google Fonts 的 css2?text= 接口对超长 text 会静默截断
（1000 字以上只会返回几十个字），所以这里走 fontTools 本地裁剪。
"""
import io
import os
import urllib.request

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "scripts", ".cache")
TTF = os.path.join(CACHE, "ZCOOLKuaiLe-Regular.ttf")
OUT = os.path.join(ROOT, "fonts", "zcool-subset.woff2")

MIRRORS = [
    "https://ghproxy.net/https://raw.githubusercontent.com/google/fonts/main/ofl/zcoolkuaile/ZCOOLKuaiLe-Regular.ttf",
    "https://gh-proxy.com/https://raw.githubusercontent.com/google/fonts/main/ofl/zcoolkuaile/ZCOOLKuaiLe-Regular.ttf",
    "https://raw.githubusercontent.com/google/fonts/main/ofl/zcoolkuaile/ZCOOLKuaiLe-Regular.ttf",
]

PUNCT = "，。、；：？！“”‘’（）《》〈〉…—·～％＋－"
EXTRA = (
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz "
    ".,:;!?()[]{}'\"-+&/×→▼"
)


def ensure_font():
    """拿到完整字库；本地有就不联网。"""
    custom = os.environ.get("ZCOOL_TTF")
    if custom and os.path.exists(custom):
        return custom
    if os.path.exists(TTF) and os.path.getsize(TTF) > 500_000:
        return TTF
    os.makedirs(CACHE, exist_ok=True)
    last = None
    for url in MIRRORS:
        try:
            print("downloading", url)
            data = urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}),
                timeout=120,
            ).read()
            if len(data) < 500_000:
                last = "too small: %d bytes" % len(data)
                continue
            io.open(TTF, "wb").write(data)
            print("cached %s (%.2f MB)" % (TTF, len(data) / 1048576))
            return TTF
        except Exception as exc:  # noqa: BLE001
            last = str(exc)
    raise SystemExit("字库下载失败：%s\n请手动放置 scripts/.cache/ZCOOLKuaiLe-Regular.ttf" % last)


def collect():
    text = ""
    for name in ("index.html", "menu-data.js", "font-extra.txt"):
        path = os.path.join(ROOT, name)
        if os.path.exists(path):
            text += io.open(path, encoding="utf-8").read()
    cjk = {c for c in text if "\u4e00" <= c <= "\u9fff"}
    return "".join(sorted(cjk)) + PUNCT + EXTRA


def main():
    chars = collect()
    ttf = ensure_font()

    source = TTFont(ttf)
    have = set()
    for table in source["cmap"].tables:
        have.update(table.cmap.keys())
    missing = [c for c in chars if ord(c) not in have]
    print("chars: %d   source glyphs: %d   missing in source: %d" % (len(chars), len(have), len(missing)))
    if missing:
        print("MISSING:", "".join(missing))

    options = subset.Options()
    options.flavor = "woff2"
    options.desubroutinize = True
    options.layout_features = ["*"]
    options.notdef_outline = True
    options.recalc_bounds = True

    font = subset.load_font(ttf, options)
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(text=chars)
    subsetter.subset(font)
    subset.save_font(font, OUT, options)

    covered = set()
    check = TTFont(OUT)
    for table in check["cmap"].tables:
        covered.update(table.cmap.keys())
    print("wrote %s  %.1f KB  glyphs in subset: %d" % (OUT, os.path.getsize(OUT) / 1024, len(covered)))
    still = [c for c in chars if ord(c) not in covered]
    print("not covered after subset:", "".join(still) if still else "none")


if __name__ == "__main__":
    main()
