#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重建字体子集。

页面只内置了两个字体的拉丁/中文子集，其余全部走系统字体：
  fonts/cormorant-var.woff2         拉丁衬线（Cormorant Garamond，可变字重）
  fonts/cormorant-var-italic.woff2  同上斜体
  fonts/zcool-subset.woff2          「角落」主题的圆体（只含页面用到的字）

改了 menu-data.js 里的菜名 / 分类名，并且用到了子集里没有的字时，
跑一遍这个脚本重新生成 zcool-subset.woff2（需要联网访问 fonts.googleapis.com）。

python scripts/subset-fonts.py
"""
import io, os, re, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
PUNCT = "，。、；：？！“”‘’（）《》〈〉…—·～％＋－"
EXTRA = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz .,:;!?()[]{}'\"-+&/×"


def collect():
    text = ""
    for name in ("index.html", "menu-data.js"):
        text += io.open(os.path.join(ROOT, name), encoding="utf-8").read()
    cjk = {c for c in text if "\u4e00" <= c <= "\u9fff"}
    return "".join(sorted(cjk)) + PUNCT + EXTRA


def fetch(css_url, dest):
    css = urllib.request.urlopen(
        urllib.request.Request(css_url, headers={"User-Agent": UA}), timeout=60
    ).read().decode()
    m = re.search(r"url\((https://fonts\.gstatic\.com/[^)]+)\)", css)
    if not m:
        raise SystemExit("没有拿到字体地址，可能是网络或接口变更")
    data = urllib.request.urlopen(
        urllib.request.Request(m.group(1), headers={"User-Agent": UA}), timeout=60
    ).read()
    io.open(dest, "wb").write(data)
    print("wrote %s (%.1f KB)" % (dest, len(data) / 1024))


def main():
    chars = collect()
    print("chars:", len(chars))
    fetch(
        "https://fonts.googleapis.com/css2?family=ZCOOL+KuaiLe&text="
        + urllib.parse.quote(chars),
        os.path.join(ROOT, "fonts", "zcool-subset.woff2"),
    )


if __name__ == "__main__":
    main()
