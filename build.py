"""Builds the Glowfin Games website into docs/.

    python3 build.py

Python 3 standard library only. Reads site.json and games/<id>/game.json,
copies assets/ and each game's media/, and writes plain HTML pages with
relative links, so the result works on GitHub Pages, any static host, a
sub-path, or straight from disk. See README.md and AGENTS.md.
"""
import html
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "docs")  # GitHub Pages serves main /docs
GAMES = os.path.join(HERE, "games")

REQUIRED = ["id", "order", "title", "tagline", "summary", "description", "icon",
            "banner", "screenshots", "stores", "credits"]
STORES = {
    "google_play": {"name": "Google Play", "verb": "Get it on", "icon": "play"},
    "app_store": {"name": "the App Store", "verb": "Download on", "icon": "apple"},
    "steam": {"name": "Steam", "verb": "Wishlist on", "icon": "steam"},
    "itch": {"name": "itch.io", "verb": "Play on", "icon": "itch"},
    "web": {"name": "your browser", "verb": "Play in", "icon": "web"},
}
ICONS = {
    "play": '<path d="M5 3.5v17a1 1 0 0 0 1.5.9l14-8.5a1 1 0 0 0 0-1.8l-14-8.5A1 1 0 0 0 5 3.5z"/>',
    "apple": '<path d="M16.4 12.6c0-2.4 2-3.5 2-3.6-1.1-1.6-2.8-1.8-3.4-1.8-1.4-.1-2.8.9-3.5.9s-1.8-.9-3-.8C7 7.3 5.6 8.2 4.8 9.6c-1.7 2.9-.4 7.2 1.2 9.6.8 1.2 1.8 2.5 3 2.4 1.2 0 1.7-.8 3.1-.8s1.9.8 3.1.8c1.3 0 2.1-1.2 2.9-2.4.9-1.3 1.3-2.6 1.3-2.7 0 0-2.5-1-2.5-3.9zM14.1 5.5c.6-.8 1.1-1.9 1-3-1 0-2.1.7-2.8 1.4-.6.7-1.1 1.8-1 2.9 1.1.1 2.2-.6 2.8-1.3z"/>',
    "steam": '<circle cx="12" cy="12" r="9"/>',
    "itch": '<rect x="4" y="5" width="16" height="14" rx="3"/>',
    "web": '<circle cx="12" cy="12" r="9"/>',
}


def esc(text):
    return html.escape(str(text), quote=True)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_games():
    games = []
    for gid in sorted(os.listdir(GAMES)):
        path = os.path.join(GAMES, gid, "game.json")
        if not os.path.isfile(path):
            continue
        game = load_json(path)
        missing = [k for k in REQUIRED if k not in game]
        if missing:
            sys.exit(f"{path}: missing {', '.join(missing)}")
        if game["id"] != gid:
            sys.exit(f"{path}: id '{game['id']}' must match its folder name '{gid}'")
        for rel in [game["icon"], game["banner"], game.get("hero", game["banner"])] + [s["src"] for s in game["screenshots"]]:
            if not os.path.isfile(os.path.join(GAMES, gid, rel)):
                sys.exit(f"{path}: file not found: {rel}")
        for store in game["stores"]:
            if store["store"] not in STORES:
                sys.exit(f"{path}: unknown store '{store['store']}' (known: {', '.join(STORES)})")
        if game.get("privacy") and not os.path.isfile(os.path.join(GAMES, gid, game["privacy"])):
            sys.exit(f"{path}: privacy file not found: {game['privacy']}")
        games.append(game)
    games.sort(key=lambda g: (g["order"], g["title"]))
    return games


def svg(name, cls="ico"):
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true">{ICONS[name]}</svg>'


def store_buttons(game, root):
    out = []
    for s in game["stores"]:
        info = STORES[s["store"]]
        inner = f'{svg(info["icon"])}<span><small>{esc(info["verb"])}</small>{esc(info["name"])}</span>'
        if s.get("live") and s.get("url"):
            out.append(f'<a class="store" href="{esc(s["url"])}" rel="noopener">{inner}</a>')
        else:
            label = s.get("soon_label", "Coming soon")
            out.append(f'<span class="store soon" title="{esc(label)}">{inner}<em>{esc(label)}</em></span>')
    return "\n".join(out)


def page(site, root, title, description, body, active="", head=""):
    def nav(href, label, key):
        cur = ' aria-current="page"' if key == active else ""
        return f'<a href="{root}{href}"{cur}>{label}</a>'

    full_title = site["name"] if title == site["name"] else f"{title} · {site['name']}"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(description)}">
<meta name="theme-color" content="#030817">
<link rel="icon" type="image/png" href="{root}assets/brand/favicon.png">
<link rel="apple-touch-icon" href="{root}assets/brand/apple-touch-icon.png">
<link rel="stylesheet" href="{root}assets/site.css">
{head}</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="wrap top-in">
    <a class="brand" href="{root}index.html"><img src="{root}assets/brand/glowfin-fish.png" alt="" width="54" height="26"><span>Glowfin<b>Games</b></span></a>
    <nav>{nav("index.html#games", "Games", "games")}{nav("index.html#about", "About", "about")}{nav("index.html#contact", "Contact", "contact")}{nav("legal/index.html", "Legal", "legal")}</nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="foot">
  <div class="wrap foot-in">
    <img src="{root}assets/brand/glowfin-fish.png" alt="" width="64" height="31">
    <p>© {esc(site["copyright"])}. {esc(site["slogan"])}.</p>
    <p><a href="{root}legal/index.html">Licences, credits &amp; privacy</a></p>
  </div>
</footer>
<script src="{root}assets/site.js" defer></script>
</body>
</html>
"""


def form_on(site):
    f = site["contact"].get("form", {})
    return bool(f.get("endpoint") and f.get("turnstile_sitekey"))


def contact_block(site):
    c = site["contact"]
    if c.get("email"):
        action = f'<a class="btn" href="mailto:{esc(c["email"])}">{esc(c["email"])}</a>'
    else:
        action = f'<a class="btn" href="{esc(c["fallback_url"])}" rel="noopener">{esc(c["fallback_label"])}</a>'
    if form_on(site):
        f = c["form"]
        alt = f'<p class="form-alt">Or email <a href="mailto:{esc(c["email"])}">{esc(c["email"])}</a></p>' if c.get("email") else ""
        action = f"""<form class="contact-form" action="{esc(f['endpoint'])}" method="post" data-contact>
  <div class="two">
    <label>Name<input name="name" autocomplete="name" maxlength="100"></label>
    <label>Email<input name="email" type="email" autocomplete="email" maxlength="200" required></label>
  </div>
  <label>Subject<input name="subject" maxlength="150"></label>
  <label>Message<textarea name="message" rows="5" maxlength="5000" required></textarea></label>
  <label class="hp" aria-hidden="true">Website<input name="website" tabindex="-1" autocomplete="off"></label>
  <div class="cf-turnstile" data-sitekey="{esc(f['turnstile_sitekey'])}" data-theme="dark"></div>
  <div class="row"><button class="btn" type="submit">Send message</button><p class="form-status" role="status" aria-live="polite"></p></div>
  {alt}
</form>"""
    return f"""<section id="contact" class="section contact">
  <div class="wrap contact-in{' has-form' if form_on(site) else ''}">
    <div>
      <p class="kicker">Contact</p>
      <h2>Say hello</h2>
      <p>{esc(c["text"])}</p>
    </div>
    <div class="contact-card">{action}</div>
  </div>
</section>"""


def game_card(game, root):
    href = f'{root}games/{game["id"]}/index.html'
    status = f'<span class="badge">{esc(game["status"])}</span>' if game.get("status") else ""
    accent = esc(game.get("accent", "#4fd6ff"))
    return f"""<article class="game-card" style="--accent:{accent}">
  <a class="game-card-img" href="{href}"><img src="{root}games/{game['id']}/{esc(game['banner'])}" alt="{esc(game['title'])} artwork" loading="lazy" width="1024" height="500"></a>
  <div class="game-card-body">
    <div class="game-card-head">
      <img class="game-icon" src="{root}games/{game['id']}/{esc(game['icon'])}" alt="" width="64" height="64">
      <div><h3><a href="{href}">{esc(game['title'])}</a></h3><p class="tag">{esc(game['tagline'])}</p></div>
    </div>
    <p>{esc(game['summary'])}</p>
    <div class="row">{status}<a class="btn small" href="{href}">See the game</a></div>
  </div>
</article>"""


def build_home(site, games):
    root = ""
    cards = "\n".join(game_card(g, root) for g in games)
    about = "\n".join(f"<p>{esc(p)}</p>" for p in site["about"])
    body = f"""<section class="hero">
  <div class="glow" aria-hidden="true"></div>
  <div class="wrap hero-in">
    <img class="hero-logo" src="assets/brand/glowfin-logo.png" alt="Glowfin Games" width="625" height="515">
    <p class="slogan">{esc(site["slogan"])}</p>
    <p class="lead">{esc(site["intro"])}</p>
    <div class="row center"><a class="btn" href="#games">Our games</a><a class="btn ghost" href="#contact">Get in touch</a></div>
  </div>
  <div class="bubbles" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></div>
</section>
<section id="games" class="section">
  <div class="wrap">
    <p class="kicker">Games</p>
    <h2>What we make</h2>
    <div class="game-grid">
{cards}
    </div>
  </div>
</section>
<section id="about" class="section alt">
  <div class="wrap about-in">
    <div><p class="kicker">About</p><h2>Small games, big glow</h2></div>
    <div class="prose">{about}</div>
  </div>
</section>
{contact_block(site)}"""
    head = ('<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>\n'
            if form_on(site) else "")
    write("index.html", page(site, root, site["name"], site["intro"], body, head=head))


def build_game(site, game):
    gid = game["id"]
    root = "../../"
    desc = "\n".join(f"<p>{esc(p)}</p>" for p in game["description"])
    feats = "\n".join(
        f'<li><h3>{esc(f["title"])}</h3><p>{esc(f["text"])}</p></li>' for f in game.get("features", []))
    facts = "\n".join(
        f'<div><dt>{esc(f["label"])}</dt><dd>{esc(f["value"])}</dd></div>' for f in game.get("facts", []))
    shots = "\n".join(
        f'<li><a href="{esc(s["src"])}" data-lightbox><img src="{esc(s["src"])}" alt="{esc(s["alt"])}" loading="lazy" width="540" height="960"></a></li>'
        for s in game["screenshots"])
    trailer = ""
    if game.get("trailer_youtube_id"):
        yid = esc(game["trailer_youtube_id"])
        trailer = f"""<section class="section"><div class="wrap"><p class="kicker">Trailer</p><h2>See it move</h2>
<div class="video"><iframe src="https://www.youtube-nocookie.com/embed/{yid}" title="{esc(game['title'])} trailer" loading="lazy" allowfullscreen></iframe></div></div></section>"""
    privacy = ""
    if game.get("privacy"):
        privacy = f'<p class="small-links"><a href="privacy/index.html">Privacy policy</a> · <a href="{root}legal/index.html#{gid}">Credits</a></p>'
    accent = esc(game.get("accent", "#4fd6ff"))
    # The store buttons already say "Coming soon", so the page header only shows the badge when no store is listed.
    status = (f'<span class="badge">{esc(game["status"])}</span>'
              if game.get("status") and not game["stores"] else "")
    body = f"""<div style="--accent:{accent}">
<section class="game-hero">
  <img class="game-hero-bg" src="{esc(game.get('hero', game['banner']))}" alt="">
  <div class="wrap game-hero-in">
    <img class="game-icon big" src="{esc(game['icon'])}" alt="" width="128" height="128">
    <div>
      {status}
      <h1>{esc(game['title'])}</h1>
      <p class="tag">{esc(game['tagline'])}</p>
      <div class="row">{store_buttons(game, root)}</div>
      {privacy}
    </div>
  </div>
</section>
<section class="section">
  <div class="wrap about-in">
    <div class="prose">{desc}</div>
    <dl class="facts">{facts}</dl>
  </div>
</section>
<section class="section alt">
  <div class="wrap">
    <p class="kicker">Screenshots</p>
    <h2>A look inside</h2>
    <ul class="shots">{shots}</ul>
  </div>
</section>
{trailer}
<section class="section">
  <div class="wrap">
    <p class="kicker">Features</p>
    <h2>Why you'll keep playing</h2>
    <ul class="features">{feats}</ul>
  </div>
</section>
</div>"""
    write(f"games/{gid}/index.html", page(site, root, game["title"], game["summary"], body, "games"))
    if game.get("privacy"):
        with open(os.path.join(GAMES, gid, game["privacy"]), encoding="utf-8") as f:
            policy = f.read()
        updated = f'<p class="meta">{esc(site["name"])} · Last updated {esc(game.get("privacy_updated", ""))}</p>'
        body = f"""<section class="section"><div class="wrap narrow prose legal">
<p class="kicker"><a href="../index.html">{esc(game['title'])}</a></p>
<h1>{esc(game['title'])} Privacy Policy</h1>
{updated}
{policy}
</div></section>"""
        write(f"games/{gid}/privacy/index.html",
              page(site, "../../../", f"{game['title']} Privacy Policy",
                   f"How {game['title']} handles your data.", body, "legal"))


def build_legal(site, games):
    root = "../"
    sections = []
    for g in games:
        rows = "\n".join(
            f'<tr><td>{esc(c["what"])}</td><td>{esc(c["who"])}</td><td>{esc(c["licence"])}</td></tr>'
            for c in g["credits"])
        pol = (f'<p><a href="../games/{g["id"]}/privacy/index.html">{esc(g["title"])} privacy policy</a></p>'
               if g.get("privacy") else "")
        sections.append(f"""<h2 id="{g['id']}">{esc(g['title'])}</h2>
{pol}
<div class="table"><table><thead><tr><th>What</th><th>By</th><th>Licence</th></tr></thead><tbody>
{rows}
</tbody></table></div>""")
    games_html = "\n".join(sections)
    body = f"""<section class="section"><div class="wrap narrow prose legal">
<p class="kicker">Legal</p>
<h1>Licences, credits &amp; privacy</h1>
<p>Thank you to everyone whose work helps make our games. Each game also shows its full licence texts in its own Credits screen.</p>
<nav class="toc">{" ".join(f'<a href="#{g["id"]}">{esc(g["title"])}</a>' for g in games)}<a href="#website">This website</a></nav>
{games_html}
<h2 id="website">This website</h2>
{site_privacy(site)}
<div class="table"><table><thead><tr><th>What</th><th>By</th><th>Licence</th></tr></thead><tbody>
<tr><td>Font: Inter</td><td>Rasmus Andersson, The Inter Project</td><td>SIL Open Font License 1.1</td></tr>
<tr><td>Font: Silkscreen</td><td>Jason Kottke</td><td>SIL Open Font License 1.1</td></tr>
<tr><td>Logo, text and game images</td><td>{esc(site["name"])}</td><td>All rights reserved</td></tr>
</tbody></table></div>
<p>Game names, logos and screenshots are the property of {esc(site["name"])}. Google Play and the Google Play logo are trademarks of Google LLC.</p>
</div></section>"""
    write("legal/index.html", page(site, root, "Licences, credits & privacy",
                                   f"Licences, credits and privacy policies for {site['name']} games.", body, "legal"))


def site_privacy(site):
    text = ("<p><strong>Privacy.</strong> This site sets no cookies and runs no analytics or ads. "
            "Fonts and images are served from this site. Links to stores and other sites follow those sites' own policies.</p>")
    if form_on(site):
        text += ("<p><strong>Contact form.</strong> When you send the form, your name, email address and message are emailed "
                 "to us so we can reply, and are kept only in our inbox. Nothing is stored on the website. The form uses "
                 "Cloudflare Turnstile to stop spam, which loads a script from Cloudflare and checks your browser "
                 "(<a href=\"https://www.cloudflare.com/privacypolicy/\">Cloudflare privacy policy</a>). "
                 "Ask us any time to delete your messages.</p>")
    else:
        text += "<p>Nothing is loaded from other servers.</p>"
    return text


def build_404(site):
    # GitHub Pages serves this file for a missing URL at any depth, so its links need the
    # site's full address (site.json "site_url"); "/" works when the site is at a domain root.
    root = (site.get("site_url") or "").rstrip("/") + "/"
    body = f"""<section class="section"><div class="wrap narrow center-text">
<p class="kicker">404</p><h1>Lost at sea</h1><p>This page swam away.</p>
<p><a class="btn" href="{root}index.html">Back to the start</a></p></div></section>"""
    write("404.html", page(site, root, "Page not found", "Page not found", body))


def write(rel, text):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    site = load_json(os.path.join(HERE, "site.json"))
    games = load_games()
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(os.path.join(HERE, "assets"), os.path.join(OUT, "assets"))
    for g in games:
        shutil.copytree(os.path.join(GAMES, g["id"], "media"), os.path.join(OUT, "games", g["id"], "media"))
        build_game(site, g)
    build_home(site, games)
    build_legal(site, games)
    build_404(site)
    write(".nojekyll", "")
    if site.get("cname"):
        write("CNAME", site["cname"] + "\n")
    print(f"Built {len(games)} game(s) into {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main()
