import base64
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONTS = HERE.parents[1] / "fonts"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
WIDTH = 1000

THEMES = {
    "light": {"bg": "#fafaf9", "ink": "#18181b", "soft": "#71717a", "rule": "#e4e4e7", "card": "#ffffff", "accent": "#0d9488"},
    "dark": {"bg": "#0d1117", "ink": "#f4f4f5", "soft": "#a1a1aa", "rule": "#27272a", "card": "#161b22", "accent": "#2dd4bf"},
}

WEIGHTS = [
    ("Light", 300),
    ("Regular", 400),
    ("Medium", 500),
    ("SemiBold", 600),
    ("Bold", 700),
    ("ExtraBold", 800),
    ("Black", 900),
]

FEATURES = [
    ("ss01", "Single-storey a", "aardvark", "'ss01'"),
    ("ss02", "l without tail", "illegal", "'ss02'"),
    ("ss04", "Disambiguation", "Il1 O0", "'ss04'"),
    ("cv06", "Double-storey g", "gauge", "'cv06'"),
    ("smcp", "Small capitals", "Small Caps", "'smcp'"),
    ("onum", "Old-style figures", "1984 2026", "'onum'"),
    ("frac", "Fractions", "1/2 7/16", "'frac'"),
    ("sups", "Superior letters", ("Mme 1er", "M<span style=\"font-feature-settings:'sups'\">me</span> 1<span style=\"font-feature-settings:'sups'\">er</span>"), "normal"),
    ("calt", "Case-aware punctuation", "(NEW) 10:30", None),
    ("ss03", "Arrows and times", "-> => 2x3", "'ss03'"),
    ("zero", "Slashed zero", "1080 OK", "'zero'"),
    ("cv07", "Flat-top 3", "3 13 33", "'cv07'"),
]

SCRIPTS = [
    ("Czech", "cs", "Příliš žluťoučký kůň úpěl ďábelské ódy"),
    ("Polish", "pl", "Zażółć gęślą jaźń, pchnąć w tę łódź jeża"),
    ("Vietnamese", "vi", "Tiếng Việt có dấu: những chữ cái đẹp"),
    ("Romanian", "ro", "Știință, țară și înțelepciune"),
    ("Greek", "el", "Ξεσκεπάζω την ψυχοφθόρα βδελυγμία"),
    ("Polytonic", "grc", "Ἐν ἀρχῇ ἦν ὁ λόγος, καὶ ὁ λόγος ἦν"),
    ("Russian", "ru", "Съешь же ещё этих мягких булок"),
    ("Bulgarian", "bg", "Ж, д, л, щ и ю по български"),
    ("Kazakh", "kk", "Қазақ тілі: әліпби, өнер, ұлт"),
]


def font_face(name, file):
    data = base64.b64encode((FONTS / file).read_bytes()).decode()
    return (
        "@font-face{font-family:'%s';src:url(data:font/woff2;base64,%s) format('woff2');"
        "font-weight:300 900;font-style:%s}" % ("Plutto", data, name)
    )


def page(theme, body, height, extra=""):
    t = THEMES[theme]
    faces = font_face("normal", "Plutto-Variable.woff2") + font_face("italic", "Plutto-Italic-Variable.woff2")
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{faces}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{WIDTH}px;height:{height}px;overflow:hidden}}
body{{background:{t['bg']};color:{t['ink']};font-family:Plutto;font-kerning:normal;padding:56px 64px}}
.soft{{color:{t['soft']}}}.accent{{color:{t['accent']}}}
.label{{font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:{t['soft']};font-weight:500;font-feature-settings:"cpsp"}}
hr{{border:0;border-top:1px solid {t['rule']}}}
.card{{background:{t['card']};border:1px solid {t['rule']};border-radius:14px}}
{extra}</style></head><body>{body}</body></html>"""


def hero(theme):
    body = """
<div class="label">Plutto · open type family</div>
<div style="font-size:196px;font-weight:800;line-height:1;letter-spacing:-0.02em;margin:22px 0 6px -8px">Plutto</div>
<div style="font-size:30px;font-weight:400;line-height:1.3;max-width:760px">A plain, narrow sans for text, interfaces and small sizes. <i>With a true italic.</i></div>
<hr style="margin:34px 0 22px">
<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:24px;font-size:17px;line-height:1.45">
<div><b style="font-size:30px;font-weight:700">7</b><div class="soft">weights, 300–900</div></div>
<div><b style="font-size:30px;font-weight:700">16</b><div class="soft">font files</div></div>
<div><b style="font-size:30px;font-weight:700">1,741</b><div class="soft">glyphs in each font</div></div>
<div><b style="font-size:30px;font-weight:700">3</b><div class="soft">scripts</div></div>
<div><b style="font-size:30px;font-weight:700">OFL</b><div class="soft">open licence</div></div>
</div>"""
    return page(theme, body, 600)


def weights(theme):
    rows = "".join(
        f"""<div style="display:grid;grid-template-columns:150px 1fr 1fr;align-items:baseline;padding:13px 0;border-top:1px solid var(--rule)">
<div class="label">{name} {w}</div>
<div style="font-size:46px;font-weight:{w};line-height:1;white-space:nowrap">Handgloves</div>
<div style="font-size:46px;font-weight:{w};font-style:italic;line-height:1;white-space:nowrap">Handgloves</div></div>"""
        for name, w in WEIGHTS
    )
    body = f"""<div class="label" style="margin-bottom:18px">Seven weights, each with a true italic</div>{rows}"""
    return page(theme, body, 680, f":root{{--rule:{THEMES[theme]['rule']}}}")


def italic(theme):
    pairs = "".join(
        f"""<div style="text-align:center"><div style="font-size:120px;line-height:1.05;font-weight:500">{c}</div>
<div style="font-size:120px;line-height:1.05;font-weight:500;font-style:italic" class="accent">{c}</div></div>"""
        for c in "aefknvy"
    )
    body = f"""<div class="label">Italic forms are drawn, not slanted</div>
<div style="display:flex;justify-content:space-between;margin:26px 20px 18px">{pairs}</div>
<hr style="margin:0 0 22px">
<div style="font-size:26px;line-height:1.4"><i>Single-storey a, a cursive e, an f with a descender, curved k and v, and arches that spring from the stem: the italic keeps Plutto’s weight and reads as its own voice.</i></div>"""
    return page(theme, body, 600)


def scripts(theme):
    rows = "".join(
        f"""<div style="display:grid;grid-template-columns:140px 1fr;align-items:baseline;padding:10px 0;border-top:1px solid var(--rule)">
<div class="label">{name}</div><div lang="{lang}" style="font-size:32px;line-height:1.15">{text}</div></div>"""
        for name, lang, text in SCRIPTS
    )
    body = f"""<div class="label" style="margin-bottom:18px">Latin, Greek and Cyrillic, with local forms</div>{rows}"""
    return page(theme, body, 700, f":root{{--rule:{THEMES[theme]['rule']}}}")


def features(theme):
    cards = []
    for tag, name, text, on in FEATURES:
        plain, marked = text if isinstance(text, tuple) else (text, text)
        off = "'calt' 0" if tag == "calt" else "normal"
        on = "normal" if tag == "calt" else on
        cards.append(
            f"""<div class="card" style="padding:16px 18px 18px">
<div style="display:flex;justify-content:space-between"><span class="label">{name}</span><code class="accent" style="font-family:Plutto;font-size:14px;font-weight:600">{tag}</code></div>
<div style="font-size:30px;line-height:1.2;margin-top:12px;font-feature-settings:{off}" class="soft">{plain}</div>
<div style="font-size:30px;line-height:1.2;margin-top:2px;font-feature-settings:{on}">{marked}</div></div>"""
        )
    body = f"""<div class="label" style="margin-bottom:18px">OpenType features: default, then with the feature on</div>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px">{''.join(cards)}</div>"""
    return page(theme, body, 760)


def text(theme):
    para = (
        "Good type for interfaces is mostly invisible. It sets the menu, the error message and the "
        "fine print at <b>13 to 16 pixels</b>, where every counter and gap is a few pixels wide, and "
        "it should still look <i>calm</i> in a 90-point headline. Plutto keeps its counters open, "
        "its spacing even and its marks clear of the letters, so 1,234.56 lines up and "
        "<span style='font-feature-settings:\"smcp\"'>small caps</span> sit in the line."
    )
    cols = "".join(
        f"""<div><div class="label" style="margin-bottom:10px">{size} px · {w}</div>
<div style="font-size:{size}px;line-height:1.5;font-weight:{wt}">{para}</div></div>"""
        for size, w, wt in [(16, "Regular", 400), (14, "Regular", 400), (13, "Medium", 500)]
    )
    body = f"""<div style="font-size:64px;font-weight:700;line-height:1.05;letter-spacing:-0.01em;margin-bottom:30px">Made for reading<br><span style="font-weight:300">at every size.</span></div>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:34px">{cols}</div>"""
    return page(theme, body, 540)


PAGES = {"hero": (hero, 600), "weights": (weights, 680), "italic": (italic, 600), "scripts": (scripts, 700), "features": (features, 760), "text": (text, 540)}


def main():
    chrome = shutil.which("google-chrome") or CHROME
    only = set(sys.argv[1:])
    with tempfile.TemporaryDirectory() as tmp:
        for name, (build, height) in PAGES.items():
            if only and name not in only:
                continue
            for theme in THEMES:
                html = Path(tmp) / f"{name}-{theme}.html"
                html.write_text(build(theme), encoding="utf-8")
                out = HERE / f"{name}-{theme}.png"
                subprocess.run(
                    [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                     f"--window-size={WIDTH},{height}", "--virtual-time-budget=4000", f"--screenshot={out}", html.as_uri()],
                    check=True, capture_output=True,
                )
                if shutil.which("pngquant"):
                    subprocess.run(["pngquant", "--force", "--skip-if-larger", "--quality=70-95", "--output", str(out), str(out)])
                print(out)


if __name__ == "__main__":
    main()
