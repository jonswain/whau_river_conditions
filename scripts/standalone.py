"""Wrap an artifact-style page (no <html>/<head>) into a standalone document for the blog.

The artifact service adds the doctype, <head>, charset and viewport when it publishes; a page
served from GitHub Pages needs them itself. Also adds SEO/share tags, the site's Google
Analytics tag (same snippet as jonswain.github.io/_includes/google-analytics.html, including its
Do Not Track opt-out) and a link back to the blog's Visualisations page.
"""
import html as _html
import re

SITE = "https://jonswain.github.io"
GA_ID = "G-R6CVGR431E"

GA = f"""<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>
  window['ga-disable-{GA_ID}'] = window.doNotTrack === "1" || navigator.doNotTrack === "1" || navigator.doNotTrack === "yes" || navigator.msDoNotTrack === "1";
  window.dataLayer = window.dataLayer || [];
  function gtag(){{window.dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA_ID}');
</script>"""

BACK = """<style>
  body { margin: 0; }
  .vis-back { display: block; padding: 10px 20px; font: 600 13px/1.4 system-ui, -apple-system, "Segoe UI", sans-serif;
              color: var(--muted, #777); background: var(--bg, transparent); text-decoration: none; }
  .vis-back:hover, .vis-back:focus-visible { color: var(--ink, inherit); text-decoration: underline; }
</style>"""


def wrap(page, slug, description, image):
    m = re.search(r"<title>(.*?)</title>\s*", page, flags=re.S)
    title = m.group(1).strip() if m else slug
    body = page[:m.start()] + page[m.end():] if m else page
    url = f"{SITE}/visualisations/{slug}/"
    e = _html.escape
    head = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)} | Jon Swain</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Jon Swain">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}{image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(description)}">
<meta name="twitter:image" content="{SITE}{image}">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/assets/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
{GA}
{BACK}
</head>
<body>
<a class="vis-back" href="/visualisations/">&larr; Jon Swain &middot; Visualisations</a>
"""
    return head + body + "\n</body>\n</html>\n"
