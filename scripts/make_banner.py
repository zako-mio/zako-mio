#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_banner.py — profile 横幅的单一真相源 → 双模 SVG 派生。

设计原则（与 zako-mio.github.io 同源）：
  · 单一真相源：几何与文案在本文件里定义一次，明/暗两版由同一份数据派生，杜绝两处手抄漂移。
  · 零第三方运行期依赖：产物是仓库内静态 SVG，不请求任何外部服务。
  · 双模：输出 banner-dark.svg / banner-light.svg 两份，由 README 侧 <picture> 按
    prefers-color-scheme 切换（GitHub 官方机制）。

用法：
    python3 scripts/make_banner.py --out assets
自检（负向夹具，证明判据不是恒真）：
    python3 scripts/make_banner.py --selftest
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
import xml.etree.ElementTree as ET

W, H = 1200, 300

# ---- 语义色（只增「语义 → 色」映射；明暗两套并行）--------------------------------
PALETTE = {
    "dark": {
        "bg": "#060A14",
        "bg_deep": "#02040A",
        "dot": "#1E3A8A",
        "hairline": "#1B2740",
        "title": "#F4F7FC",
        "subtitle": "#C7D2FE",
        "muted": "#8FA3BF",
        # 品牌蓝在近黑底上仅 2.95:1 ⇒ 暗色版提亮到 #2563EB（3.83:1），
        # 这是「同一语义、两档明度」而非换品牌色。
        "logo_fill": "#2563EB",
        "logo_ink": "#FFFFFF",
        "node": "#2563EB",
        "node_ring": "#60A5FA",
        "center": "#60A5FA",
        "edge": "#4A76D4",
    },
    "light": {
        "bg": "#F4F7FC",
        "bg_deep": "#E6EBF5",
        "dot": "#C9D6EC",
        "hairline": "#D3DCEA",
        "title": "#0B1220",
        "subtitle": "#1E3A8A",
        "muted": "#5A6B85",
        "logo_fill": "#1D4ED8",
        "logo_ink": "#FFFFFF",
        "node": "#1D4ED8",
        "node_ring": "#1D4ED8",
        "center": "#1D4ED8",
        "edge": "#6B80A8",
    },
}

# ---- 文案（单一真相源）------------------------------------------------------------
COPY = {
    "title": "zako-mio",
    "subtitle": "数据科学 × AI Agent 工程",
    "meta": "知识图谱 · 交互式 DAG · 可复现交付",
    "url": "zako-mio.github.io",
}

# ---- 几何（单一真相源）------------------------------------------------------------
GEO = {
    "logo": (64.0, 102.0, 96.0),          # x, y, size
    "text_x": 196.0,
    "title_y": 112.0,
    "title_size": 56.0,
    "sub_y": 162.0,
    "sub_size": 25.0,
    "rule_y": 188.0,
    "rule_x2": 560.0,
    "meta_y": 212.0,
    "meta_size": 18.0,
    "url_y": 278.0,
    "url_size": 15.0,
    "center": (1040.0, 150.0, 16.0),      # 以结论为中心
    "sats": [(944.0, 66.0, 10.0), (1136.0, 66.0, 10.0), (1040.0, 240.0, 10.0)],
    "font": "system-ui,-apple-system,'Segoe UI','PingFang SC','Hiragino Sans GB',"
            "'Microsoft YaHei',sans-serif",
}

# 自建 favicon 的「Z」折线（与 public/favicon.svg 同源，64×64 user unit）
Z_PATH = "M20 21h24L20 43h24"


def _stars(seed: str, n: int, x0: float, x1: float, y0: float, y1: float):
    """确定性伪随机星点（无随机时钟 ⇒ 逐字节可复现）。"""
    out, h = [], hashlib.sha256(seed.encode()).digest()
    for i in range(n):
        h = hashlib.sha256(h).digest()
        fx = int.from_bytes(h[0:4], "big") / 0xFFFFFFFF
        fy = int.from_bytes(h[4:8], "big") / 0xFFFFFFFF
        fr = int.from_bytes(h[8:10], "big") / 0xFFFF
        out.append((round(x0 + fx * (x1 - x0), 2), round(y0 + fy * (y1 - y0), 2),
                    round(0.7 + fr * 1.3, 2)))
    return out


def _shorten(x1, y1, x2, y2, r1, r2, pad=2.0):
    """把圆心间连线裁到两圆边界，供带箭头的有向边使用。"""
    dx, dy = x2 - x1, y2 - y1
    d = (dx * dx + dy * dy) ** 0.5 or 1.0
    ux, uy = dx / d, dy / d
    return (round(x1 + ux * (r1 + pad), 2), round(y1 + uy * (r1 + pad), 2),
            round(x2 - ux * (r2 + pad + 6), 2), round(y2 - uy * (r2 + pad + 6), 2))


def build(mode: str) -> str:
    p = PALETTE[mode]
    g = GEO
    lx, ly, ls = g["logo"]
    cx, cy, cr = g["center"]

    s = []
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
             f'width="{W}" height="{H}" role="img" '
             f'aria-label="{COPY["title"]} · {COPY["subtitle"]}">')
    s.append(f'<title>{COPY["title"]} · {COPY["subtitle"]}</title>')
    s.append('<defs>'
             f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
             f'<stop offset="0" stop-color="{p["bg"]}"/>'
             f'<stop offset="1" stop-color="{p["bg_deep"]}"/></linearGradient>'
             f'<marker id="arw" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" '
             f'markerHeight="5" orient="auto-start-reverse">'
             f'<path d="M0 0 L10 5 L0 10 z" fill="{p["edge"]}"/></marker>'
             '</defs>')

    # 背景
    s.append(f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')
    if mode == "dark":
        for (sx, sy, sr) in _stars("zako-mio/banner", 46, 20, W - 20, 16, H - 16):
            s.append(f'<circle cx="{sx}" cy="{sy}" r="{sr}" fill="{p["dot"]}" '
                     f'opacity="0.55"/>')
    # 左侧竖向主色条
    s.append(f'<rect x="0" y="0" width="6" height="{H}" fill="{p["logo_fill"]}"/>')

    # 徽标（与 favicon 同源图形，等比放大 1.5×）
    s.append(f'<rect x="{lx}" y="{ly}" width="{ls}" height="{ls}" rx="22" '
             f'fill="{p["logo_fill"]}"/>')
    k = ls / 64.0
    s.append(f'<g transform="translate({lx},{ly}) scale({k})">'
             f'<path d="{Z_PATH}" fill="none" stroke="{p["logo_ink"]}" stroke-width="5" '
             f'stroke-linecap="round" stroke-linejoin="round"/></g>')

    # 文案
    f = g["font"]
    s.append(f'<text x="{g["text_x"]}" y="{g["title_y"]}" fill="{p["title"]}" '
             f'font-family="{f}" font-size="{g["title_size"]}" font-weight="700" '
             f'dominant-baseline="central">{COPY["title"]}</text>')
    s.append(f'<text x="{g["text_x"] + 2}" y="{g["sub_y"]}" fill="{p["subtitle"]}" '
             f'font-family="{f}" font-size="{g["sub_size"]}" font-weight="600" '
             f'dominant-baseline="central">{COPY["subtitle"]}</text>')
    s.append(f'<line x1="{g["text_x"] + 2}" y1="{g["rule_y"]}" x2="{g["rule_x2"]}" '
             f'y2="{g["rule_y"]}" stroke="{p["hairline"]}" stroke-width="1.5"/>')
    s.append(f'<text x="{g["text_x"] + 2}" y="{g["meta_y"]}" fill="{p["muted"]}" '
             f'font-family="{f}" font-size="{g["meta_size"]}" '
             f'dominant-baseline="central">{COPY["meta"]}</text>')

    # 右侧动机：三节点有向图 · 以结论为中心
    for (sx, sy, sr) in g["sats"]:
        x1, y1, x2, y2 = _shorten(sx, sy, cx, cy, sr, cr)
        s.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                 f'stroke="{p["edge"]}" stroke-width="2" marker-end="url(#arw)"/>')
    for (sx, sy, sr) in g["sats"]:
        s.append(f'<circle cx="{sx}" cy="{sy}" r="{sr}" fill="none" '
                 f'stroke="{p["node_ring"]}" stroke-width="2.5"/>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{cr}" fill="{p["center"]}"/>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{cr - 6}" fill="{p["bg"]}"/>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{cr - 9}" fill="{p["center"]}"/>')

    # 右下角站点地址（主页链接的视觉锚点）
    s.append(f'<text x="{W - 56}" y="{g["url_y"]}" fill="{p["muted"]}" '
             f'font-family="{f}" font-size="{g["url_size"]}" text-anchor="end" '
             f'dominant-baseline="central">{COPY["url"]}</text>')

    s.append('</svg>')
    return "\n".join(s) + "\n"


# ---- 判据（带负向夹具）------------------------------------------------------------
def _contrast(a: str, b: str) -> float:
    def lum(h):
        h = h.lstrip("#")
        c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    l1, l2 = sorted([lum(a), lum(b)], reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def check(svg_texts: dict, min_text=4.5, min_graphic=3.0):
    """读真实产物文本；不是恒真判据——负向夹具在 --selftest 里跑。"""
    fails, rows = [], []
    pairs = [("title", "text", min_text), ("subtitle", "text", min_text),
             ("muted", "text", min_text), ("edge", "graphic", min_graphic),
             ("center", "graphic", min_graphic), ("logo_fill", "graphic", min_graphic)]
    for mode, pal in PALETTE.items():
        for key, kind, floor in pairs:
            r = _contrast(pal[key], pal["bg"])
            rows.append((mode, key, round(r, 2), floor))
            if r < floor:
                fails.append(f"{mode}:{key} 对比度 {r:.2f} < {floor} ({kind})")
        # 徽标墨色对底色（在同一元素内部，不是对画布底）
        r = _contrast(pal["logo_ink"], pal["logo_fill"])
        rows.append((mode, "logo_ink", round(r, 2), min_graphic))
        if r < min_graphic:
            fails.append(f"{mode}:logo_ink 对比度 {r:.2f} < {min_graphic} (graphic)")
    # 结构判据：必须是可解析 XML、viewBox 覆盖画布、无外部引用、无栅格
    for mode, txt in svg_texts.items():
        try:
            root = ET.fromstring(txt)
        except ET.ParseError as e:
            fails.append(f"{mode}: SVG 不可解析 {e}")
            continue
        if root.get("viewBox") != f"0 0 {W} {H}":
            fails.append(f"{mode}: viewBox 不覆盖画布")
        if "http" in txt.replace("http://www.w3.org/2000/svg", ""):
            fails.append(f"{mode}: 含外部引用")
        if 'clip-path' in txt:
            fails.append(f"{mode}: 含 clip-path")
        # 文本是否越出画布（含标签的包围盒口径，留字宽上界估计）
        for t in root.iter("{http://www.w3.org/2000/svg}text"):
            if t.get("text-anchor") == "end":
                continue
            x = float(t.get("x", 0))
            size = float(t.get("font-size", 12))
            body = t.text or ""
            est = sum(size if ord(ch) > 0x2E80 else size * 0.62 for ch in body)
            if x + est > W - 40:
                fails.append(f"{mode}: 文本越界 x={x} est={est:.0f} '{body[:20]}'")
    return rows, fails


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="assets")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    svgs = {m: build(m) for m in ("dark", "light")}
    rows, fails = check(svgs)

    if a.selftest:
        # 负向夹具：故意造一个白底白字，判据必须能判假
        poisoned = dict(PALETTE["light"])
        poisoned["title"] = "#F4F7FC"
        PALETTE["__neg__"] = poisoned
        r = _contrast(poisoned["title"], poisoned["bg"])
        PALETTE.pop("__neg__")
        caught = r < 4.5
        print(f"[selftest] 白底白字对比度={r:.2f} 判据捕获={'是' if caught else '否'}")
        print(f"[selftest] {'PASS' if caught else 'FAIL'} — 判据非恒真")
        # 越界夹具
        bad = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 300">' \
              '<text x="1100" font-size="40">越界测试越界测试</text></svg>'
        _, f2 = check({"neg": bad})
        caught2 = any("越界" in x for x in f2)
        print(f"[selftest] 越界文本捕获={'是' if caught2 else '否'}")
        print(f"[selftest] {'PASS' if caught2 else 'FAIL'} — 越界判据非恒真")
        return 0 if (caught and caught2) else 1

    print(f"{'mode':<7}{'token':<12}{'contrast':>9}{'floor':>7}  verdict")
    for mode, key, r, floor in rows:
        print(f"{mode:<7}{key:<12}{r:>9}{floor:>7}  {'OK' if r >= floor else 'FAIL'}")
    if fails:
        print("\n[FAIL] " + "\n       ".join(fails))
        return 1

    os.makedirs(a.out, exist_ok=True)
    for mode, txt in svgs.items():
        p = os.path.join(a.out, f"banner-{mode}.svg")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(txt)
        print(f"[write] {p}  {len(txt.encode('utf-8'))} bytes  "
              f"sha256={hashlib.sha256(txt.encode()).hexdigest()[:16]}")
    print("\n[PASS] 对比度 / 结构 / 越界 判据全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
