#!/usr/bin/env python3
"""Build the locus comics site into _site/.

The front page is a cover: the logo and every comic as a numbered issue. Each
comic has a page at /<n>/, a permalink that never changes. Standard library
only.
"""

import hashlib
import html
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = Path(__file__).resolve().parent
OUT = ROOT / "_site"

e = html.escape


def v(path):
    """`path` with a content hash appended, so a changed file gets a new URL
    and browsers never pair new HTML with a stale cached copy."""
    source = SITE / path if path == "style.css" else ROOT / path
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:10]
    return f"{path}?v={digest}"


def page(*, cfg, title, description, up, body, og_image, og_url):
    """Wrap a page body. `up` is the relative path back to the site root, so
    links work under any base path."""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:image" content="{e(og_image)}">
<meta property="og:url" content="{e(og_url)}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{up}{v("images/logo.png")}">
<link rel="stylesheet" href="{up}{v("style.css")}">
</head>
<body>
{body}
<footer class="site-footer">
  <a href="{up}">locus</a> · How <a href="https://meta-pytorch.org/monarch/">Monarch</a> works · <a href="{e(cfg["repo_url"])}">source</a><br>
  Comics © Shane Fletcher, <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a> · a personal project, not an official Monarch or Meta publication
</footer>
</body>
</html>
"""


def cover_body(cfg):
    issues = "\n".join(
        f"""<li class="issue">
  <a href="{n}/">
    <img src="{e(v(c["image"]))}" alt="" loading="lazy">
    <span class="issue-number">No. {n}</span>
    <span class="issue-title">{e(c["title"])}</span>
    <span class="issue-caption">{e(c.get("caption", ""))}</span>
  </a>
</li>"""
        for n, c in enumerate(cfg["comics"], start=1)
    )
    return f"""<header class="cover">
  <img class="cover-art" src="{v("images/logo.png")}" alt="locus: {e(cfg["tagline"])}" width="420" height="420">
</header>
<section class="intro">
  <p>Hi! <strong>locus</strong> is a small collection of comics about how <a href="https://meta-pytorch.org/monarch/">Monarch</a> works: the snakes, cogs and mailboxes behind the API, one idea per strip.</p>
  <p>Pick any issue, or start at <a href="1/">No. 1</a>.</p>
</section>
<main class="issues-wrap">
<ol class="issues">
{issues}
</ol>
</main>"""


def comic_body(cfg, n, comic):
    comics = cfg["comics"]
    permalink = f'{cfg["base_url"]}{n}/'
    image = f'../{v(comic["image"])}'
    prompt = f'{cfg["repo_url"]}/blob/main/{comic["prompt"]}'
    title = e(comic["title"])

    def neighbour(m, rel, arrow_first):
        if m < 1 or m > len(comics):
            return f'<span class="pager-{rel} empty"></span>'
        label = f'No. {m} · {e(comics[m - 1]["title"])}'
        text = f"← {label}" if arrow_first else f"{label} →"
        return f'<a class="pager-{rel}" rel="{rel}" href="../{m}/">{text}</a>'

    return f"""<header class="bar">
  <a class="brand" href="../"><img src="../{v("images/logo.png")}" alt="" width="40" height="40"><span>locus</span></a>
</header>
<main class="comic">
  <p class="eyebrow">No. {n}
    <button type="button" class="copy" data-copy="{e(permalink)}" title="Copy this comic's permanent link">Copy link</button>
  </p>
  <h1>{title}</h1>
  <figure>
    <a href="{image}" title="Open full size"><img src="{image}" alt="{title}"></a>
    <figcaption>{e(comic.get("caption", ""))}</figcaption>
  </figure>
  <p class="prompt">Drawn from <a href="{e(prompt)}">{e(comic["prompt"])}</a></p>
  <nav class="pager">
    {neighbour(n - 1, "prev", True)}
    <a class="pager-home" href="../">All comics</a>
    {neighbour(n + 1, "next", False)}
  </nav>
</main>
<script>
(() => {{
  document.addEventListener('keydown', (ev) => {{
    if (ev.metaKey || ev.ctrlKey || ev.altKey) return;
    const a = document.querySelector({{ArrowLeft: 'a[rel=prev]', ArrowRight: 'a[rel=next]'}}[ev.key]);
    if (a) location.href = a.href;
  }});
  const copy = document.querySelector('[data-copy]');
  if (copy && navigator.clipboard) copy.addEventListener('click', () => {{
    navigator.clipboard.writeText(copy.dataset.copy).then(() => {{
      copy.textContent = 'Copied';
      setTimeout(() => (copy.textContent = 'Copy link'), 1500);
    }});
  }});
}})();
</script>"""


def build():
    cfg = json.loads((SITE / "comics.json").read_text())
    comics = cfg["comics"]
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "images", OUT / "images")
    shutil.copy(SITE / "style.css", OUT / "style.css")
    (OUT / ".nojekyll").write_text("")

    (OUT / "index.html").write_text(
        page(
            cfg=cfg,
            title=f'locus · {cfg["tagline"]}',
            description=cfg["tagline"],
            up="",
            body=cover_body(cfg),
            og_image=cfg["base_url"] + "images/logo.png",
            og_url=cfg["base_url"],
        )
    )

    for n, comic in enumerate(comics, start=1):
        for key in ("image", "prompt"):
            if not (ROOT / comic[key]).exists():
                raise SystemExit(f"No. {n}: missing {key} {comic[key]}")
        (OUT / str(n)).mkdir()
        (OUT / str(n) / "index.html").write_text(
            page(
                cfg=cfg,
                title=f'No. {n}: {comic["title"]} · locus',
                description=comic.get("caption") or cfg["tagline"],
                up="../",
                body=comic_body(cfg, n, comic),
                og_image=cfg["base_url"] + comic["image"],
                og_url=f'{cfg["base_url"]}{n}/',
            )
        )

    (OUT / "404.html").write_text(
        page(
            cfg=cfg,
            title="Not found · locus",
            description=cfg["tagline"],
            up=cfg["base_url"],
            body='<main class="comic"><h1>No comic here</h1><p><a href="'
            + e(cfg["base_url"])
            + '">Back to the cover</a></p></main>',
            og_image=cfg["base_url"] + "images/logo.png",
            og_url=cfg["base_url"],
        )
    )
    print(f"built {len(comics)} comics into {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    build()
