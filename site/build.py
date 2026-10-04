#!/usr/bin/env python3
"""Build the locus comics site into _site/.

One page per comic at /<n>/ (a permalink that never changes), the latest comic
at /, and an archive at /archive/. Standard library only.
"""

import html
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = Path(__file__).resolve().parent
OUT = ROOT / "_site"


def page(*, title, description, depth, body, og_image=None, og_url=None):
    """Wrap a page body. `depth` is how many directories below the site root
    the page lives, so relative links work under any base path."""
    up = "../" * depth
    meta = [
        f'<meta property="og:title" content="{html.escape(title)}">',
        f'<meta property="og:description" content="{html.escape(description)}">',
    ]
    if og_image:
        meta.append(f'<meta property="og:image" content="{html.escape(og_image)}">')
        meta.append('<meta name="twitter:card" content="summary_large_image">')
    if og_url:
        meta.append(f'<meta property="og:url" content="{html.escape(og_url)}">')
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
{chr(10).join(meta)}
<link rel="icon" href="{up}images/logo.png">
<link rel="stylesheet" href="{up}style.css">
</head>
<body>
<header class="masthead">
  <a class="brand" href="{up}">
    <img src="{up}images/logo.png" alt="" width="56" height="56">
    <span class="name">locus</span>
  </a>
  <span class="tagline">How Monarch works</span>
  <nav class="site-nav"><a href="{up}archive/">Archive</a></nav>
</header>
<main>
{body}
</main>
</body>
</html>
"""


def nav(n, count, up):
    """First / prev / random / next / last. Ends are rendered disabled."""

    def link(label, target, cls):
        if target is None:
            return f'<span class="nav-button {cls} disabled" aria-disabled="true">{label}</span>'
        return f'<a class="nav-button {cls}" href="{up}{target}/">{label}</a>'

    first = None if n == 1 else 1
    prev = None if n == 1 else n - 1
    nxt = None if n == count else n + 1
    last = None if n == count else count
    return (
        '<nav class="comic-nav">'
        + link("|&lt;", first, "first")
        + link("&lt; Prev", prev, "prev")
        + f'<a class="nav-button random" href="#" data-random data-count="{count}" data-current="{n}" data-up="{up}">Random</a>'
        + link("Next &gt;", nxt, "next")
        + link("&gt;|", last, "last")
        + "</nav>"
    )


SCRIPT = """<script>
(() => {
  const r = document.querySelector('[data-random]');
  if (r) r.addEventListener('click', (e) => {
    e.preventDefault();
    const count = +r.dataset.count, current = +r.dataset.current;
    if (count < 2) return;
    let n = current;
    while (n === current) n = 1 + Math.floor(Math.random() * count);
    location.href = r.dataset.up + n + '/';
  });
  document.addEventListener('keydown', (e) => {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    const pick = { ArrowLeft: '.comic-nav .prev', ArrowRight: '.comic-nav .next' }[e.key];
    const a = pick && document.querySelector(pick + ':not(.disabled)');
    if (a) location.href = a.href;
  });
  const copy = document.querySelector('[data-copy]');
  if (copy && navigator.clipboard) copy.addEventListener('click', () => {
    navigator.clipboard.writeText(copy.dataset.copy).then(() => {
      copy.textContent = 'Copied';
      setTimeout(() => (copy.textContent = 'Copy'), 1500);
    });
  });
})();
</script>"""


def comic_body(cfg, n, comic, up):
    count = len(cfg["comics"])
    permalink = f'{cfg["base_url"]}{n}/'
    image = f'{up}{comic["image"]}'
    prompt = f'{cfg["repo_url"]}/blob/main/{comic["prompt"]}'
    title = html.escape(comic["title"])
    hover = html.escape(comic.get("hover", ""))
    return f"""<article class="comic">
<h1 class="comic-title"><span class="number">#{n}</span> {title}</h1>
{nav(n, count, up)}
<figure>
  <a href="{image}" title="Open full size"><img src="{image}" alt="{title}" title="{hover}"></a>
</figure>
{nav(n, count, up)}
<dl class="links">
  <dt>Permalink</dt>
  <dd><a href="{permalink}">{permalink}</a> <button type="button" class="copy" data-copy="{permalink}">Copy</button></dd>
  <dt>Prompt</dt>
  <dd><a href="{prompt}">{html.escape(comic["prompt"])}</a></dd>
</dl>
</article>
{SCRIPT}"""


def archive_body(cfg):
    items = "\n".join(
        f'<li><span class="number">#{n}</span> <a href="../{n}/">{html.escape(c["title"])}</a></li>'
        for n, c in reversed(list(enumerate(cfg["comics"], start=1)))
    )
    return f"""<article class="archive">
<h1>Archive</h1>
<ol class="archive-list" reversed>
{items}
</ol>
</article>"""


def build():
    cfg = json.loads((SITE / "comics.json").read_text())
    comics = cfg["comics"]
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "images", OUT / "images")
    shutil.copy(SITE / "style.css", OUT / "style.css")
    (OUT / ".nojekyll").write_text("")

    for n, comic in enumerate(comics, start=1):
        if not (ROOT / comic["image"]).exists():
            raise SystemExit(f"missing image for #{n}: {comic['image']}")
        if not (ROOT / comic["prompt"]).exists():
            raise SystemExit(f"missing prompt for #{n}: {comic['prompt']}")
        common = dict(
            title=f'{comic["title"]} · locus',
            description=comic.get("hover") or cfg["tagline"],
            og_image=cfg["base_url"] + comic["image"],
            og_url=f'{cfg["base_url"]}{n}/',
        )
        (OUT / str(n)).mkdir()
        (OUT / str(n) / "index.html").write_text(
            page(depth=1, body=comic_body(cfg, n, comic, "../"), **common)
        )
        if n == len(comics):
            # The front page is the latest comic; its permalink is still /<n>/.
            (OUT / "index.html").write_text(
                page(depth=0, body=comic_body(cfg, n, comic, ""), **common)
            )

    (OUT / "archive").mkdir()
    (OUT / "archive" / "index.html").write_text(
        page(
            title="Archive · locus",
            description=cfg["tagline"],
            depth=1,
            body=archive_body(cfg),
            og_image=cfg["base_url"] + "images/logo.png",
            og_url=cfg["base_url"] + "archive/",
        )
    )

    not_found = page(
        title="Not found · locus",
        description=cfg["tagline"],
        depth=0,
        body='<article class="archive"><h1>No comic here</h1><p><a href="/locus/">Back to the latest comic</a></p></article>',
    )
    (OUT / "404.html").write_text(not_found)
    print(f"built {len(comics)} comics into {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    build()
