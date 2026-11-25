#!/usr/bin/env python3
"""Build the Prof Romandie static site (FR / EN / ES / IT).

    python3 build.py            production build into site/  (clean URLs, for GitHub Pages)
    python3 build.py --preview  preview build into preview/   (relative .html links, works anywhere)

Content lives in content/<lang>/*.md (YAML front matter + Markdown) and
content/<lang>/home.yml. Change CHECKED when you re-verify the sources,
The public address comes from PR_BASE_URL (default https://profromandie.ch).
Before the domain exists, the workflow sets it to the GitHub Pages address.

The contact address is never stored in the repository. Without PR_CONTACT_EMAIL,
pages point readers to the address published on pablocorreaprieto.ch (decision of
15 November 2026). To show a direct address instead, set it when you build:
    PR_CONTACT_EMAIL="contact@example.ch" python3 build.py
"""
import html
import json
import os
import re
import shutil
from urllib.parse import urlparse
import sys
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).resolve().parent
BASE_URL = (os.environ.get("PR_BASE_URL") or "https://profromandie.ch").rstrip("/")
PATH_PREFIX = urlparse(BASE_URL).path.rstrip("/")  # "" on the own domain, "/prof-romandie" on GitHub Pages
CHECKED = "2026-11-15"                # date the official sources were last checked
LANGS = [l for l in ["fr", "en", "es", "it"] if (ROOT / "content" / l / "home.yml").exists()]
PREVIEW = "--preview" in sys.argv
OUT = ROOT / ("preview" if PREVIEW else "site")
CONTACT = os.environ.get("PR_CONTACT_EMAIL", "").strip()

# Same person as on pablocorreaprieto.ch: "id" is the @id of the Person in that site's JSON-LD,
# so search engines can tie the guide and the personal site to one author.
AUTHOR = {"name": "Pablo Correa Prieto", "url": "https://pablocorreaprieto.ch/",
          "id": "https://pablocorreaprieto.ch/#person"}
# IndexNow key (Bing, Yandex, Seznam, Naver). Published as /<key>.txt by the build and
# used by .github/scripts/indexnow.py after each deploy. Do not change it once deployed.
INDEXNOW_KEY = "0944e1cb191643742ca2fc7f3bd07e84"

UI = {
    "fr": {
        "locale": "fr_CH", "lang_name": "Français", "brand_tag": "enseigner en Suisse romande",
        "home": "Accueil", "skip": "Aller au contenu", "step": "Étape {n} sur 5",
        "steps_aria": "Les cinq étapes", "verified": "Sources vérifiées le 15 novembre 2026",
        "read": "Lecture {n} min", "bref": "En bref", "exp": "Mon expérience", "warn": "Attention",
        "next": "Étape suivante", "back_home": "Revenir au parcours complet",
        "sources": "Sources officielles", "sources_note": "Liens consultés le 15 novembre 2026.",
        "about": "Qui écrit", "legal": "Mentions légales", "langs_aria": "Langue",
        "check_note": "Cette liste est la mienne, pas une liste officielle. Les cases cochées restent enregistrées dans votre navigateur.",
        "foot_note": "Ce guide donne une information générale. Pour votre cas précis, la décision de l'autorité compétente fait foi.",
        "ai_note": "Texte rédigé avec l'aide d'une IA, relu et validé par l'auteur.",
        "nf_title": "Page introuvable", "photo_alt": "Pablo Correa Prieto",
        "no_contact": "l’adresse publiée sur {link}",
        "contact_url": "https://pablocorreaprieto.ch/#contact",
    },
    "en": {
        "locale": "en_GB", "lang_name": "English", "brand_tag": "teaching in French-speaking Switzerland",
        "home": "Home", "skip": "Skip to content", "step": "Step {n} of 5",
        "steps_aria": "The five steps", "verified": "Sources checked on 15 November 2026",
        "read": "{n} min read", "bref": "In short", "exp": "My experience", "warn": "Watch out",
        "next": "Next step", "back_home": "Back to all the steps",
        "sources": "Official sources", "sources_note": "Links checked on 15 November 2026.",
        "about": "Who writes this", "legal": "Legal notice", "langs_aria": "Language",
        "check_note": "This is my list, not an official one. The boxes you tick stay saved in your browser.",
        "foot_note": "This guide gives general information. For your own case, the decision of the competent authority prevails.",
        "ai_note": "Text written with the help of AI, reviewed and approved by the author.",
        "nf_title": "Page not found", "photo_alt": "Pablo Correa Prieto",
        "no_contact": "the address published on {link}",
        "contact_url": "https://pablocorreaprieto.ch/en/#contact",
    },
    "es": {
        "locale": "es_ES", "lang_name": "Español", "brand_tag": "dar clase en la Suiza francófona",
        "home": "Inicio", "skip": "Saltar al contenido", "step": "Paso {n} de 5",
        "steps_aria": "Los cinco pasos", "verified": "Fuentes comprobadas el 15 de noviembre de 2026",
        "read": "Lectura de {n} min", "bref": "En breve", "exp": "Mi experiencia", "warn": "Atención",
        "next": "Siguiente paso", "back_home": "Volver al recorrido completo",
        "sources": "Fuentes oficiales", "sources_note": "Enlaces consultados el 15 de noviembre de 2026.",
        "about": "Quién escribe", "legal": "Aviso legal", "langs_aria": "Idioma",
        "check_note": "Es mi lista, no una lista oficial. Las casillas marcadas se guardan en tu navegador.",
        "foot_note": "Esta guía da información general. Para tu caso concreto, manda la decisión de la autoridad competente.",
        "ai_note": "Texto redactado con ayuda de una IA, revisado y validado por el autor.",
        "nf_title": "Página no encontrada", "photo_alt": "Pablo Correa Prieto",
        "no_contact": "la dirección publicada en {link}",
        "contact_url": "https://pablocorreaprieto.ch/es/#contact",
    },
    "it": {
        "locale": "it_IT", "lang_name": "Italiano", "brand_tag": "insegnare nella Svizzera romanda",
        "home": "Pagina iniziale", "skip": "Vai al contenuto", "step": "Tappa {n} di 5",
        "steps_aria": "Le cinque tappe", "verified": "Fonti verificate il 15 novembre 2026",
        "read": "Lettura {n} min", "bref": "In breve", "exp": "La mia esperienza", "warn": "Attenzione",
        "next": "Tappa successiva", "back_home": "Torna al percorso completo",
        "sources": "Fonti ufficiali", "sources_note": "Link consultati il 15 novembre 2026.",
        "about": "Chi scrive", "legal": "Note legali", "langs_aria": "Lingua",
        "check_note": "È la mia lista, non una lista ufficiale. Le caselle spuntate restano salvate nel tuo browser.",
        "foot_note": "Questa guida dà informazioni generali. Per il tuo caso concreto fa fede la decisione dell'autorità competente.",
        "ai_note": "Testo redatto con l'aiuto di un'IA, riletto e approvato dall'autore.",
        "nf_title": "Pagina non trovata", "photo_alt": "Pablo Correa Prieto",
        "no_contact": "l’indirizzo pubblicato su {link}",
        "contact_url": "https://pablocorreaprieto.ch/#contact",
    },
}

ORDER = ["cdip", "francais", "poste", "salaire", "permis"]


# --------------------------------------------------------------------------- content

def load_lang(lang):
    pages = {}
    for f in sorted((ROOT / "content" / lang).glob("*.md")):
        raw = f.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
        if not m:
            raise SystemExit(f"missing front matter in {f}")
        meta = yaml.safe_load(m.group(1))
        meta["body"] = m.group(2)
        meta["lang"] = lang
        pages[meta["id"]] = meta
    home = yaml.safe_load((ROOT / "content" / lang / "home.yml").read_text(encoding="utf-8"))
    home["id"] = "home"
    home["lang"] = lang
    pages["home"] = home
    return pages


SITE = {lang: load_lang(lang) for lang in LANGS}


def file_of(lang, pid):
    prefix = "" if lang == "fr" else f"{lang}/"
    if pid == "home":
        return f"{prefix}index.html"
    return f"{prefix}{SITE[lang][pid]['slug']}.html"


def url_of(lang, pid):
    """Absolute production URL path (clean URLs)."""
    prefix = "/" if lang == "fr" else f"/{lang}/"
    if pid == "home":
        return prefix
    return f"{prefix}{SITE[lang][pid]['slug']}"


def href(cur_file, lang, pid):
    if PREVIEW:
        return os.path.relpath(file_of(lang, pid), start=os.path.dirname(cur_file) or ".")
    return PATH_PREFIX + url_of(lang, pid)


def asset(cur_file, path):
    if PREVIEW:
        return os.path.relpath(f"assets/{path}", start=os.path.dirname(cur_file) or ".")
    return f"{PATH_PREFIX}/assets/{path}"


def esc(s):
    return html.escape(str(s), quote=True)


def contact_html(lang):
    if CONTACT:
        return f'<a href="mailto:{esc(CONTACT)}">{esc(CONTACT)}</a>'
    link = f'<a href="{esc(UI[lang]["contact_url"])}">pablocorreaprieto.ch</a>'
    return esc(UI[lang]["no_contact"]).replace("{link}", link)


# --------------------------------------------------------------------------- markdown

BLOCK_RE = re.compile(r"^:::(\w+)(?:[ \t]+(\S+))?[ \t]*\n(.*?)\n:::[ \t]*$", re.S | re.M)


def md(text):
    return markdown.markdown(text, extensions=["tables", "sane_lists", "toc"],
                             extension_configs={"toc": {"permalink": False}})


def inline_marks(s):
    return re.sub(r"==(.+?)==", r"<mark>\1</mark>", s)


def render_body(page, cur_file):
    lang = page["lang"]
    ui = UI[lang]
    text = page["body"]
    blocks = []

    def stash(m):
        kind, arg, inner = m.group(1), m.group(2), m.group(3)
        inner = inline_marks(inner)
        if kind == "bref":
            out = f'<aside class="bref" aria-label="{esc(ui["bref"])}"><p class="lbl">{esc(ui["bref"])}</p>{md(inner)}</aside>'
        elif kind == "exp":
            photo = asset(cur_file, "img/pablo-correa-prieto.jpg")
            out = (f'<aside class="exp"><p class="lbl"><img src="{photo}" width="36" height="36" alt="">'
                   f'{esc(ui["exp"])}</p>{md(inner)}</aside>')
        elif kind == "warn":
            out = f'<aside class="warn"><p class="lbl">{esc(ui["warn"])}</p>{md(inner)}</aside>'
        elif kind == "check":
            items = [l[2:].strip() for l in inner.splitlines() if l.startswith("- ")]
            lis = "".join(f'<li><label><input type="checkbox"><span>{it}</span></label></li>' for it in items)
            out = (f'<ul class="checklist" data-key="{esc(arg or "list")}">{lis}</ul>'
                   f'<p class="checklist-note">{esc(ui["check_note"])}</p>')
        else:
            raise SystemExit(f"unknown block {kind}")
        blocks.append(out)
        return f"\n\n<!--BLOCK{len(blocks) - 1}-->\n\n"

    text = BLOCK_RE.sub(stash, text)
    text = inline_marks(text)
    out = md(text)
    for i, b in enumerate(blocks):
        out = out.replace(f"<p><!--BLOCK{i}--></p>", b).replace(f"<!--BLOCK{i}-->", b)

    def internal(m):
        return f'href="{href(cur_file, lang, m.group(1))}"'

    out = re.sub(r'href="@(\w+)"', internal, out)
    out = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" rel="noopener"', out)
    out = out.replace("{{contact}}", contact_html(lang))
    return out


# --------------------------------------------------------------------------- templates

MARK_SVG = ('<svg class="mk" viewBox="0 0 40 14" width="40" height="14" aria-hidden="true">'
            '<line x1="7" y1="7" x2="33" y2="7" stroke="currentColor" stroke-width="4" stroke-linecap="round"/>'
            '<circle cx="7" cy="7" r="5" fill="var(--paper)" stroke="currentColor" stroke-width="3"/>'
            '<circle cx="33" cy="7" r="5" fill="currentColor"/></svg>')

CHECK_SVG = ('<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M3 8.5l3.2 3.2L13 5" '
             'fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def head(page, cur_file, title, description, og_type="article"):
    lang = page["lang"]
    pid = page["id"]
    alts = "".join(
        f'<link rel="alternate" hreflang="{l}" href="{BASE_URL}{url_of(l, pid)}">\n' for l in LANGS)
    alts += f'<link rel="alternate" hreflang="x-default" href="{BASE_URL}{url_of("fr", pid)}">'
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="author" content="{esc(AUTHOR['name'])}">
<link rel="canonical" href="{BASE_URL}{url_of(lang, pid)}">
{alts}
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="Prof Romandie">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{BASE_URL}{url_of(lang, pid)}">
<meta property="og:locale" content="{UI[lang]['locale']}">
<meta property="og:image" content="{BASE_URL}/assets/img/og-{lang}.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc('Prof Romandie, ' + SITE[lang]['home']['h1'])}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#1B2559">
<link rel="icon" href="{asset(cur_file, 'favicon.svg')}" type="image/svg+xml">
<link rel="preload" href="{asset(cur_file, 'fonts/atkinson-hyperlegible-next-latin-wght-normal.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{asset(cur_file, 'site.css')}">
"""


def header(page, cur_file):
    lang = page["lang"]
    ui = UI[lang]
    pid = page["id"]
    links = []
    for l in LANGS:
        cur = ' aria-current="true"' if l == lang else ""
        links.append(f'<a href="{href(cur_file, l, pid)}" hreflang="{l}" lang="{l}"{cur} title="{UI[l]["lang_name"]}">{l.upper()}</a>')
    return f"""<a class="skip" href="#main">{esc(ui['skip'])}</a>
<header class="top wrap">
  <a class="brand" href="{href(cur_file, lang, 'home')}">{MARK_SVG}<span><b>prof</b> romandie</span></a>
  <nav class="langs" aria-label="{esc(ui['langs_aria'])}">{''.join(links)}</nav>
</header>
"""


def footer(page, cur_file):
    lang = page["lang"]
    ui = UI[lang]
    return f"""<footer class="foot">
  <div class="wrap foot-in">
    <p class="foot-brand"><a class="brand" href="{href(cur_file, lang, 'home')}">{MARK_SVG}<span><b>prof</b> romandie</span></a><span class="tag">{esc(ui['brand_tag'])}</span></p>
    <p class="foot-links"><a href="{href(cur_file, lang, 'about')}">{esc(ui['about'])}</a><a href="{href(cur_file, lang, 'legal')}">{esc(ui['legal'])}</a></p>
    <p class="foot-note">{esc(ui['foot_note'])}<span class="ok">{CHECK_SVG}{esc(ui['verified'])}</span></p>
  </div>
</footer>
<script src="{asset(cur_file, 'site.js')}" defer></script>
</body>
</html>
"""


def steps_nav(page, cur_file):
    lang = page["lang"]
    ui = UI[lang]
    cur = page.get("step")
    items = []
    for i, pid in enumerate(ORDER, start=1):
        p = SITE[lang][pid]
        cls = ' class="done"' if cur and i < cur else ""
        aria = ' aria-current="step"' if i == cur else ""
        items.append(f'<li><a{cls} href="{href(cur_file, lang, pid)}"{aria} title="{esc(p["title"])}">{i}</a></li>')
    label = ui["step"].format(n=cur)
    return (f'<nav class="steps" aria-label="{esc(ui["steps_aria"])}"><ol>{"".join(items)}</ol>'
            f'<span class="steps-label">{esc(label)}</span></nav>')


def jsonld_article(page):
    lang = page["lang"]
    data = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": page["title"],
        "description": page["description"],
        "inLanguage": lang,
        "dateModified": CHECKED,
        "mainEntityOfPage": f"{BASE_URL}{url_of(lang, page['id'])}",
        "author": {"@type": "Person", "@id": AUTHOR["id"], "name": AUTHOR["name"], "url": AUTHOR["url"]},
        "publisher": {"@type": "Organization", "name": "Prof Romandie"},
    }
    return f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>\n'


def render_article(page):
    lang = page["lang"]
    ui = UI[lang]
    cur_file = file_of(lang, page["id"])
    body = render_body(page, cur_file)
    step = page.get("step")
    parts = [head(page, cur_file, page["seo_title"], page["description"]),
             jsonld_article(page) if step else "",
             "</head>\n<body>\n", header(page, cur_file),
             '<main id="main" class="article">',
             f'<nav class="crumbs" aria-label="breadcrumb"><a href="{href(cur_file, lang, "home")}">{esc(ui["home"])}</a></nav>']
    if step:
        parts.append(steps_nav(page, cur_file))
    parts.append(f'<h1 class="title">{esc(page["title"])}</h1>')
    if page.get("dek"):
        parts.append(f'<p class="dek">{esc(page["dek"])}</p>')
    if step:
        parts.append(f'<p class="meta"><span class="ok">{CHECK_SVG}{esc(ui["verified"])}</span>'
                     f'<span>{esc(ui["read"].format(n=page["read_min"]))}</span></p>')
    parts.append(f'<div class="prose">{body}</div>')
    if page.get("sources"):
        lis = "".join(f'<li><a href="{esc(s["url"])}" rel="noopener">{esc(s["title"])}</a></li>' for s in page["sources"])
        parts.append(f'<section class="sources" aria-labelledby="src-h"><h2 id="src-h">{esc(ui["sources"])}</h2>'
                     f'<ol>{lis}</ol><p class="src-note">{esc(ui["sources_note"])}</p></section>')
    if step:
        if step < len(ORDER):
            nxt = SITE[lang][ORDER[step]]
            parts.append(f'<a class="next" href="{href(cur_file, lang, nxt["id"])}"><span class="k">{esc(ui["next"])}</span>'
                         f'<span class="t">{esc(nxt["title"])}</span></a>')
        else:
            parts.append(f'<a class="next" href="{href(cur_file, lang, "home")}"><span class="k">{esc(ui["home"])}</span>'
                         f'<span class="t">{esc(ui["back_home"])}</span></a>')
    if page.get("ai_note", True):
        parts.append(f'<p class="ai-note">{esc(ui["ai_note"])}</p>')
    parts.append("</main>\n")
    parts.append(footer(page, cur_file))
    return "".join(parts)


def render_home(page):
    lang = page["lang"]
    ui = UI[lang]
    cur_file = file_of(lang, "home")
    stations = []
    for i, st in enumerate(page["stations"], start=1):
        stations.append(
            f'<li class="station" style="--i:{i}"><a class="st" href="{href(cur_file, lang, st["id"])}">'
            f'<span class="stop" aria-hidden="true">{i}</span>'
            f'<span class="st-title">{esc(st["title"])}</span>'
            f'<span class="st-fig">{esc(st["fig"])}</span>'
            f'<span class="st-note">{esc(st["note"])}</span></a></li>')
    photo = asset(cur_file, "img/pablo-correa-prieto.jpg")
    blocks = "".join(
        f'<section><h2>{esc(b["h"])}</h2>{md(b["text"]).replace("{{contact}}", contact_html(lang))}</section>'
        for b in page["blocks"])
    body = f"""</head>
<body class="home">
{header(page, cur_file)}
<main id="main">
  <section class="hero">
    <div class="wrap">
      <h1 class="display">{esc(page['h1'])}</h1>
      <p class="lede">{esc(page['lede'])}</p>
      <ol class="route" aria-label="{esc(ui['steps_aria'])}">{''.join(stations)}</ol>
    </div>
  </section>
  <div class="wrap home-grid">{blocks}</div>
  <section class="wrap author" aria-labelledby="who-h">
    <img src="{photo}" width="460" height="460" alt="{esc(ui['photo_alt'])}" loading="lazy">
    <div><h2 id="who-h">{esc(ui['about'])}</h2>{md(page['author'])}<p><a href="{href(cur_file, lang, 'about')}">{esc(page['author_link'])}</a></p></div>
  </section>
</main>
"""
    return head(page, cur_file, page["seo_title"], page["description"], og_type="website") + body + footer(page, cur_file)


def render_404():
    items = []
    for l in LANGS:
        root = PATH_PREFIX + ("/" if l == "fr" else f"/{l}/")
        items.append(f'<li lang="{l}"><a href="{root}">{esc(UI[l]["nf_title"])}. {esc(UI[l]["back_home"])}</a></li>')
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>404 | Prof Romandie</title><meta name="robots" content="noindex"><link rel="stylesheet" href="{PATH_PREFIX}/assets/site.css"></head>
<body><main id="main" class="article"><h1 class="title">404</h1><ul class="nf">{''.join(items)}</ul></main></body></html>
"""


def sitemap():
    rows = []
    for lang in LANGS:
        for pid in SITE[lang]:
            alts = "".join(f'<xhtml:link rel="alternate" hreflang="{l}" href="{BASE_URL}{url_of(l, pid)}"/>' for l in LANGS)
            alts += f'<xhtml:link rel="alternate" hreflang="x-default" href="{BASE_URL}{url_of("fr", pid)}"/>'
            rows.append(f"<url><loc>{BASE_URL}{url_of(lang, pid)}</loc><lastmod>{CHECKED}</lastmod>{alts}</url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(rows) + "\n</urlset>\n")


# --------------------------------------------------------------------------- build

def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "assets", OUT / "assets")
    count = 0
    for lang in LANGS:
        for pid, page in SITE[lang].items():
            cur = file_of(lang, pid)
            target = OUT / cur
            target.parent.mkdir(parents=True, exist_ok=True)
            out = render_home(page) if pid == "home" else render_article(page)
            target.write_text(out, encoding="utf-8")
            count += 1
    if not PREVIEW:
        (OUT / "404.html").write_text(render_404(), encoding="utf-8")
        (OUT / "sitemap.xml").write_text(sitemap(), encoding="utf-8")
        (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8")
        (OUT / ".nojekyll").write_text("", encoding="utf-8")
        (OUT / f"{INDEXNOW_KEY}.txt").write_text(INDEXNOW_KEY, encoding="utf-8")
    print(f"built {count} pages into {OUT.relative_to(ROOT)}/"
          + ("" if CONTACT else "  (contact goes through pablocorreaprieto.ch)"))


if __name__ == "__main__":
    main()
