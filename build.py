"""Builds the Glowfin Games website into docs/.

    python3 build.py

Python 3 standard library only. Reads site.json, i18n/<lang>.json and games/<id>/game.json
(plus games/<id>/i18n/<lang>.json translations), copies assets/ and each game's media/, and
writes plain HTML pages with relative links, so the result works on Cloudflare Pages, any
static host, a sub-path, or straight from disk. The first language in site.json "languages"
is served at the site root, every other one under /<code>/. See README.md and AGENTS.md.
"""
import hashlib
import html
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "docs")  # Cloudflare Pages serves docs/
GAMES = os.path.join(HERE, "games")
I18N = os.path.join(HERE, "i18n")
# Cloudflare Pages Function that picks the visitor's language; build.py keeps its LANGS line in sync.
MIDDLEWARE = os.path.join(HERE, "functions", "_middleware.js")
LANG_COOKIE = "lang"

REQUIRED = ["id", "order", "title", "tagline", "summary", "description", "icon",
            "banner", "screenshots", "stores", "credits"]
# Game text every translation (games/<id>/i18n/<lang>.json) must give, so a page never mixes languages.
GAME_TEXT = ["tagline", "summary", "description", "features", "facts", "screenshots", "credits"]
# Other game fields a translation may replace: localised images, a translated privacy policy.
GAME_OPTIONAL = ["status", "banner", "hero", "icon", "trailer_youtube_id", "trailer_poster",
                 "trailer_play_x", "privacy", "privacy_updated"]
# Studio text every translation's "site" block must give (dotted = nested in site.json).
SITE_TEXT = ["slogan", "intro", "about", "contact.text", "contact.fallback_label"]

# Store button icons. The button words are UI text: store_<id>_verb / store_<id>_name in i18n/*.json.
STORES = {"google_play": "play", "app_store": "apple", "steam": "steam", "itch": "itch", "web": "web"}
ICONS = {
    "play": '<path d="M5 3.5v17a1 1 0 0 0 1.5.9l14-8.5a1 1 0 0 0 0-1.8l-14-8.5A1 1 0 0 0 5 3.5z"/>',
    "apple": '<path d="M16.4 12.6c0-2.4 2-3.5 2-3.6-1.1-1.6-2.8-1.8-3.4-1.8-1.4-.1-2.8.9-3.5.9s-1.8-.9-3-.8C7 7.3 5.6 8.2 4.8 9.6c-1.7 2.9-.4 7.2 1.2 9.6.8 1.2 1.8 2.5 3 2.4 1.2 0 1.7-.8 3.1-.8s1.9.8 3.1.8c1.3 0 2.1-1.2 2.9-2.4.9-1.3 1.3-2.6 1.3-2.7 0 0-2.5-1-2.5-3.9zM14.1 5.5c.6-.8 1.1-1.9 1-3-1 0-2.1.7-2.8 1.4-.6.7-1.1 1.8-1 2.9 1.1.1 2.2-.6 2.8-1.3z"/>',
    "steam": '<circle cx="12" cy="12" r="9"/>',
    "itch": '<rect x="4" y="5" width="16" height="14" rx="3"/>',
    "web": '<circle cx="12" cy="12" r="9"/>',
    "globe": '<circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M3 12h18M12 3c2.6 2.6 3.8 5.6 3.8 9s-1.2 6.4-3.8 9c-2.6-2.6-3.8-5.6-3.8-9S9.4 5.6 12 3z" fill="none" stroke="currentColor" stroke-width="1.8"/>',
}
PLACEHOLDER = re.compile(r"\{(\w+)\}")


def esc(text):
    return html.escape(str(text), quote=True)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def merged(base, over):
    """base with over's values on top; dicts merge key by key, everything else is replaced."""
    out = dict(base)
    for k, v in over.items():
        if k.startswith("_"):
            continue
        out[k] = merged(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out


def dotted(d, key):
    for part in key.split("."):
        if not isinstance(d, dict) or part not in d:
            return None
        d = d[part]
    return d


# ---------------------------------------------------------------- languages

def load_languages(site):
    langs = site.get("languages")
    if not langs:
        sys.exit("site.json: add \"languages\" (the first one is the default, served at the site root)")
    default_ui = None
    for i, lang in enumerate(langs):
        code = lang.get("code", "")
        if not re.fullmatch(r"[a-z]{2}(-[a-z0-9]+)?", code):
            sys.exit(f"site.json languages: bad code '{code}' (lowercase, like en or pt-br)")
        for k in ("name", "short", "hreflang"):
            if not lang.get(k):
                sys.exit(f"site.json languages '{code}': missing {k}")
        path = os.path.join(I18N, f"{code}.json")
        if not os.path.isfile(path):
            sys.exit(f"{path}: missing (copy i18n/{langs[0]['code']}.json and translate it)")
        data = load_json(path)
        ui = data.get("ui", {})
        if i == 0:
            default_ui = ui
            lang["site"] = site
        else:
            missing = [k for k in default_ui if k not in ui]
            extra = [k for k in ui if k not in default_ui]
            if missing or extra:
                sys.exit(f"{path}: ui keys differ from i18n/{langs[0]['code']}.json. "
                         f"Missing: {', '.join(missing) or '-'}. Unknown: {', '.join(extra) or '-'}")
            for k, text in ui.items():
                if sorted(PLACEHOLDER.findall(text)) != sorted(PLACEHOLDER.findall(default_ui[k])):
                    sys.exit(f"{path}: ui.{k} must use the same {{placeholders}} as the default language")
            over = data.get("site", {})
            missing = [k for k in SITE_TEXT if dotted(over, k) is None]
            if missing:
                sys.exit(f"{path}: \"site\" is missing {', '.join(missing)}")
            lang["site"] = merged(site, over)
        lang["ui"] = ui
        lang["prefix"] = "" if i == 0 else code + "/"
        lang["default"] = i == 0
    return langs


def localise_game(game, lang):
    """The game with this language's text and images (the default language is game.json itself)."""
    if lang["default"]:
        return game
    gid = game["id"]
    path = os.path.join(GAMES, gid, "i18n", f"{lang['code']}.json")
    if not os.path.isfile(path):
        sys.exit(f"{path}: missing. Every game needs a translation for every language in site.json")
    over = load_json(path)
    need = GAME_TEXT + [k for k in ("status", "privacy", "privacy_updated") if game.get(k)]
    missing = [k for k in need if k not in over]
    if missing:
        sys.exit(f"{path}: missing {', '.join(missing)}")
    unknown = [k for k in over if not k.startswith("_") and k not in GAME_TEXT + GAME_OPTIONAL]
    if unknown:
        sys.exit(f"{path}: unknown field(s) {', '.join(unknown)}")
    for k in ("screenshots", "credits"):
        if len(over[k]) != len(game[k]):
            sys.exit(f"{path}: {k} needs {len(game[k])} entries like game.json, has {len(over[k])}")
    shots = [merged(s, o) for s, o in zip(game["screenshots"], over["screenshots"])]
    out = merged(game, {k: v for k, v in over.items() if k != "screenshots"})
    out["screenshots"] = shots
    check_game_files(out, path)
    return out


def check_game_files(game, path):
    gid = game["id"]
    files = [game["icon"], game["banner"], game.get("hero", game["banner"])] + [s["src"] for s in game["screenshots"]]
    if game.get("trailer_poster"):
        files.append(game["trailer_poster"])
    if game.get("privacy"):
        files.append(game["privacy"])
    for rel in files:
        if not os.path.isfile(os.path.join(GAMES, gid, rel)):
            sys.exit(f"{path}: file not found: {rel}")
    for s in game["screenshots"]:
        if not s.get("alt"):
            sys.exit(f"{path}: screenshot {s['src']} needs alt text")


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
        check_game_files(game, path)
        for store in game["stores"]:
            if store["store"] not in STORES:
                sys.exit(f"{path}: unknown store '{store['store']}' (known: {', '.join(STORES)})")
        games.append(game)
    games.sort(key=lambda g: (g["order"], g["title"]))
    return games


class Ctx:
    """One page in one language: its text, and the relative paths it needs.

    rel is the page's path inside a language tree (e.g. "games/starkeel/index.html").
    root leads to this language's home, base to the site root (assets/ and game media/).
    """

    def __init__(self, lang, langs, rel, absolute=""):
        self.lang, self.langs, self.rel = lang, langs, rel
        self.site = lang["site"]
        if absolute:  # the 404 page is served at any depth, so it links with full addresses
            self.base = absolute
            self.root = absolute + lang["prefix"]
            self.menu_rel = "index.html"
        else:
            depth = rel.count("/") + (1 if lang["prefix"] else 0)
            self.base = "../" * depth
            self.root = self.base + lang["prefix"]
            self.menu_rel = rel

    def t(self, key, **values):
        """UI text, HTML-escaped (keys ending in _html are HTML already; their values are escaped)."""
        text = self.lang["ui"][key]
        if key.endswith("_html"):
            return PLACEHOLDER.sub(lambda m: esc(values[m.group(1)]), text)
        return esc(PLACEHOLDER.sub(lambda m: str(values[m.group(1)]), text))

    def media(self, game, path):
        """A game image's URL, with a content hash so a replaced image is never served from an old cache."""
        if "?" not in path:
            with open(os.path.join(GAMES, game["id"], html.unescape(path)), "rb") as fh:
                path += "?v=" + hashlib.sha1(fh.read()).hexdigest()[:8]
        return f'{self.base}games/{game["id"]}/{path}'


def pretty(rel):
    """The URL path Cloudflare Pages serves a page at (no index.html, no .html)."""
    if rel.endswith("index.html"):
        return rel[: -len("index.html")]
    return rel[:-5] if rel.endswith(".html") else rel


# ---------------------------------------------------------------- page frame

def svg(name, cls="ico"):
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true">{ICONS[name]}</svg>'


def lang_menu(ctx):
    if len(ctx.langs) < 2:
        return ""
    items = []
    for L in ctx.langs:
        cur = ' aria-current="true"' if L is ctx.lang else ""
        # ?lang= tells the language Function this is the visitor's choice (it saves it, then drops the query).
        href = f"{ctx.base}{L['prefix']}{ctx.menu_rel}?{LANG_COOKIE}={L['code']}"
        items.append(f'<li><a href="{esc(href)}" hreflang="{esc(L["hreflang"])}" lang="{esc(L["hreflang"])}"'
                     f' data-lang="{esc(L["code"])}"{cur}>{esc(L["name"])}</a></li>')
    label = f'{ctx.t("lang_menu")}: {esc(ctx.lang["name"])}'
    return (f'<details class="lang"><summary aria-label="{label}" title="{ctx.t("lang_menu")}">{svg("globe")}'
            f'<span>{esc(ctx.lang["short"])}</span></summary><ul>{"".join(items)}</ul></details>')


def alternates(ctx):
    url = (ctx.site.get("site_url") or "").rstrip("/")
    if not url or ctx.rel == "404.html" or len(ctx.langs) < 2:
        return ""
    links = [f'<link rel="canonical" href="{esc(url)}/{ctx.lang["prefix"]}{esc(pretty(ctx.rel))}">']
    for L in ctx.langs:
        links.append(f'<link rel="alternate" hreflang="{esc(L["hreflang"])}" href="{esc(url)}/{L["prefix"]}{esc(pretty(ctx.rel))}">')
    links.append(f'<link rel="alternate" hreflang="x-default" href="{esc(url)}/{esc(pretty(ctx.rel))}">')
    return "\n".join(links) + "\n"


def page(ctx, title, description, body, active="", head=""):
    site, root, base = ctx.site, ctx.root, ctx.base

    def nav(href, key, label):
        cur = ' aria-current="page"' if key == active else ""
        return f'<a href="{root}{href}"{cur}>{ctx.t(label)}</a>'

    full_title = site["name"] if title == site["name"] else f"{title} · {site['name']}"
    return f"""<!doctype html>
<html lang="{esc(ctx.lang["hreflang"])}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:locale" content="{esc(ctx.lang["hreflang"].replace("-", "_"))}">
<meta name="theme-color" content="#030817">
{alternates(ctx)}<link rel="icon" type="image/png" href="{base}assets/brand/favicon.png">
<link rel="apple-touch-icon" href="{base}assets/brand/apple-touch-icon.png">
<link rel="stylesheet" href="{base}assets/site.css">
{head}</head>
<body data-lb-close="{ctx.t("lb_close")}" data-lb-prev="{ctx.t("lb_prev")}" data-lb-next="{ctx.t("lb_next")}">
<a class="skip" href="#main">{ctx.t("skip")}</a>
<header class="top">
  <div class="wrap top-in">
    <a class="brand" href="{root}index.html"><img src="{base}assets/brand/glowfin-fish.png" alt="" width="54" height="26"><span>Glowfin<b>Games</b></span></a>
    <div class="top-right">
      <nav>{nav("index.html#games", "games", "nav_games")}{nav("index.html#about", "about", "nav_about")}{nav("index.html#contact", "contact", "nav_contact")}{nav("legal/index.html", "legal", "nav_legal")}</nav>
      {lang_menu(ctx)}
    </div>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="foot">
  <div class="wrap foot-in">
    <img src="{base}assets/brand/glowfin-fish.png" alt="" width="64" height="31">
    <p>© {esc(site["copyright"])}. {esc(site["slogan"])}.</p>
    <p><a href="{root}legal/index.html">{ctx.t("footer_legal")}</a></p>
  </div>
</footer>
<script src="{base}assets/site.js" defer></script>
</body>
</html>
"""


# ---------------------------------------------------------------- pages

def form_on(site):
    f = site["contact"].get("form", {})
    return bool(f.get("endpoint") and f.get("turnstile_sitekey"))


def contact_block(ctx):
    site = ctx.site
    c = site["contact"]
    if c.get("email"):
        action = f'<a class="btn" href="mailto:{esc(c["email"])}">{esc(c["email"])}</a>'
    else:
        action = f'<a class="btn" href="{esc(c["fallback_url"])}" rel="noopener">{esc(c["fallback_label"])}</a>'
    if form_on(site):
        f = c["form"]
        alt = (f'<p class="form-alt">{ctx.t("form_or_email")} <a href="mailto:{esc(c["email"])}">{esc(c["email"])}</a></p>'
               if c.get("email") else "")
        msgs = " ".join(f'data-msg-{k}="{ctx.t("form_" + k.replace("-", "_"))}"'
                        for k in ("sending", "sent", "err-captcha", "err-fields", "err-send", "err-offline"))
        action = f"""<form class="contact-form" action="{esc(f['endpoint'])}" method="post" data-contact {msgs}>
  <div class="two">
    <label>{ctx.t("form_name")}<input name="name" autocomplete="name" maxlength="100"></label>
    <label>{ctx.t("form_email")}<input name="email" type="email" autocomplete="email" maxlength="200" required></label>
  </div>
  <label>{ctx.t("form_subject")}<input name="subject" maxlength="150"></label>
  <label>{ctx.t("form_message")}<textarea name="message" rows="5" maxlength="5000" required></textarea></label>
  <label class="hp" aria-hidden="true">{ctx.t("form_website")}<input name="website" tabindex="-1" autocomplete="off"></label>
  <div class="cf-turnstile" data-sitekey="{esc(f['turnstile_sitekey'])}" data-theme="dark" data-language="{esc(ctx.lang['hreflang'].lower())}"></div>
  <div class="row"><button class="btn" type="submit">{ctx.t("form_send")}</button><p class="form-status" role="status" aria-live="polite"></p></div>
  {alt}
</form>"""
    return f"""<section id="contact" class="section contact">
  <div class="wrap contact-in{' has-form' if form_on(site) else ''}">
    <div>
      <p class="kicker">{ctx.t("contact_kicker")}</p>
      <h2>{ctx.t("contact_title")}</h2>
      <p>{esc(c["text"])}</p>
    </div>
    <div class="contact-card">{action}</div>
  </div>
</section>"""


def store_buttons(ctx, game):
    out = []
    for s in game["stores"]:
        sid = s["store"]
        inner = f'{svg(STORES[sid])}<span><small>{ctx.t(f"store_{sid}_verb")}</small>{ctx.t(f"store_{sid}_name")}</span>'
        if s.get("live") and s.get("url"):
            out.append(f'<a class="store" href="{esc(s["url"])}" rel="noopener">{inner}</a>')
        else:
            label = ctx.t("coming_soon")
            out.append(f'<span class="store soon" title="{label}">{inner}<em>{label}</em></span>')
    return "\n".join(out)


def game_card(ctx, game):
    href = f'{ctx.root}games/{game["id"]}/index.html'
    status = f'<span class="badge">{esc(game["status"])}</span>' if game.get("status") else ""
    accent = esc(game.get("accent", "#4fd6ff"))
    return f"""<article class="game-card" style="--accent:{accent}">
  <a class="game-card-img" href="{href}"><img src="{ctx.media(game, esc(game['banner']))}" alt="{ctx.t('card_artwork_alt', title=game['title'])}" loading="lazy" width="1024" height="500"></a>
  <div class="game-card-body">
    <div class="game-card-head">
      <img class="game-icon" src="{ctx.media(game, esc(game['icon']))}" alt="" width="64" height="64">
      <div><h3><a href="{href}">{esc(game['title'])}</a></h3><p class="tag">{esc(game['tagline'])}</p></div>
    </div>
    <p>{esc(game['summary'])}</p>
    <div class="row">{status}<a class="btn small" href="{href}">{ctx.t("card_see")}</a></div>
  </div>
</article>"""


def build_home(lang, langs, games):
    ctx = Ctx(lang, langs, "index.html")
    site = ctx.site
    cards = "\n".join(game_card(ctx, g) for g in games)
    about = "\n".join(f"<p>{esc(p)}</p>" for p in site["about"])
    bubbles = "<i></i>" * 14
    body = f"""<section class="hero">
  <div class="glow" aria-hidden="true"></div>
  <div class="wrap hero-in">
    <img class="hero-logo" src="{ctx.base}assets/brand/glowfin-logo.png" alt="{esc(site["name"])}" width="625" height="515">
    <p class="slogan">{esc(site["slogan"])}</p>
    <p class="lead">{esc(site["intro"])}</p>
    <div class="row center"><a class="btn" href="#games">{ctx.t("btn_our_games")}</a><a class="btn ghost" href="#contact">{ctx.t("btn_get_in_touch")}</a></div>
  </div>
  <div class="bubbles" aria-hidden="true">{bubbles}</div>
</section>
<section id="games" class="section">
  <div class="wrap">
    <p class="kicker">{ctx.t("games_kicker")}</p>
    <h2>{ctx.t("games_title")}</h2>
    <div class="game-grid">
{cards}
    </div>
  </div>
</section>
<section id="about" class="section alt">
  <div class="wrap about-in">
    <div><p class="kicker">{ctx.t("about_kicker")}</p><h2>{ctx.t("about_title")}</h2></div>
    <div class="prose">{about}</div>
  </div>
</section>
{contact_block(ctx)}"""
    head = ('<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>\n'
            if form_on(site) else "")
    write(lang, "index.html", page(ctx, site["name"], site["intro"], body, head=head))


def build_game(lang, langs, game):
    gid = game["id"]
    ctx = Ctx(lang, langs, f"games/{gid}/index.html")
    desc = "\n".join(f"<p>{esc(p)}</p>" for p in game["description"])
    feats = "\n".join(
        f'<li><h3>{esc(f["title"])}</h3><p>{esc(f["text"])}</p></li>' for f in game.get("features", []))
    facts = "\n".join(
        f'<div><dt>{esc(f["label"])}</dt><dd>{esc(f["value"])}</dd></div>' for f in game.get("facts", []))
    shots = "\n".join(
        f'<li><a href="{ctx.media(game, esc(s["src"]))}" data-lightbox><img src="{ctx.media(game, esc(s["src"]))}" alt="{esc(s["alt"])}" loading="lazy" width="540" height="960"></a></li>'
        for s in game["screenshots"])
    trailer = ""
    if game.get("trailer_youtube_id"):
        # Click to play: the page shows a poster served from this site and only contacts
        # YouTube (privacy-enhanced youtube-nocookie.com) once the visitor presses play.
        yid = esc(game["trailer_youtube_id"])
        title = game["title"]
        poster = game.get("trailer_poster", "")
        # Where the play button sits on the poster (0-100 % from the left), so it can avoid text.
        play_x = float(game.get("trailer_play_x", 50))
        img = ""
        if poster:
            # Content hash in the URL so a replaced poster is never served from an old cache.
            with open(os.path.join(GAMES, gid, poster), "rb") as fh:
                poster += "?v=" + hashlib.sha1(fh.read()).hexdigest()[:8]
            img = f'<img src="{ctx.media(game, esc(poster))}" alt="{ctx.t("trailer_alt", title=title)}" loading="lazy" width="1280" height="720">'
        trailer = f"""<section class="section"><div class="wrap"><p class="kicker">{ctx.t("trailer_kicker")}</p><h2>{ctx.t("trailer_title")}</h2>
<div class="video"><a class="video-facade" style="--play-x:{play_x:g}%" href="https://www.youtube.com/watch?v={yid}" data-youtube="{yid}" data-title="{ctx.t("trailer_alt", title=title)}" aria-label="{ctx.t("trailer_play", title=title)}">{img}<span class="play" aria-hidden="true"></span><span class="video-note">{ctx.t("trailer_note")}</span></a></div></div></section>"""
    privacy = ""
    if game.get("privacy"):
        privacy = (f'<p class="small-links"><a href="privacy/index.html">{ctx.t("privacy_link")}</a> · '
                   f'<a href="{ctx.root}legal/index.html#{gid}">{ctx.t("credits_link")}</a></p>')
    accent = esc(game.get("accent", "#4fd6ff"))
    # The store buttons already say "Coming soon", so the page header only shows the badge when no store is listed.
    status = (f'<span class="badge">{esc(game["status"])}</span>'
              if game.get("status") and not game["stores"] else "")
    body = f"""<div style="--accent:{accent}">
<section class="game-hero">
  <img class="game-hero-bg" src="{ctx.media(game, esc(game.get('hero', game['banner'])))}" alt="">
  <div class="wrap game-hero-in">
    <img class="game-icon big" src="{ctx.media(game, esc(game['icon']))}" alt="" width="128" height="128">
    <div>
      {status}
      <h1>{esc(game['title'])}</h1>
      <p class="tag">{esc(game['tagline'])}</p>
      <div class="row">{store_buttons(ctx, game)}</div>
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
    <p class="kicker">{ctx.t("screenshots_kicker")}</p>
    <h2>{ctx.t("screenshots_title")}</h2>
    <ul class="shots">{shots}</ul>
  </div>
</section>
{trailer}
<section class="section">
  <div class="wrap">
    <p class="kicker">{ctx.t("features_kicker")}</p>
    <h2>{ctx.t("features_title")}</h2>
    <ul class="features">{feats}</ul>
  </div>
</section>
</div>"""
    write(lang, ctx.rel, page(ctx, game["title"], game["summary"], body, "games"))
    if game.get("privacy"):
        ctx = Ctx(lang, langs, f"games/{gid}/privacy/index.html")
        with open(os.path.join(GAMES, gid, game["privacy"]), encoding="utf-8") as f:
            policy = f.read()
        updated = f'<p class="meta">{esc(ctx.site["name"])} · {ctx.t("last_updated", date=game.get("privacy_updated", ""))}</p>'
        title = PLACEHOLDER.sub(game["title"], lang["ui"]["privacy_title"])
        body = f"""<section class="section"><div class="wrap narrow prose legal">
<p class="kicker"><a href="../index.html">{esc(game['title'])}</a></p>
<h1>{esc(title)}</h1>
{updated}
{policy}
</div></section>"""
        desc = PLACEHOLDER.sub(game["title"], lang["ui"]["privacy_desc"])
        write(lang, ctx.rel, page(ctx, title, desc, body, "legal"))


def build_legal(lang, langs, games):
    ctx = Ctx(lang, langs, "legal/index.html")
    site = ctx.site
    head_row = f'<thead><tr><th>{ctx.t("th_what")}</th><th>{ctx.t("th_by")}</th><th>{ctx.t("th_licence")}</th></tr></thead>'
    sections = []
    for g in games:
        rows = "\n".join(
            f'<tr><td>{esc(c["what"])}</td><td>{esc(c["who"])}</td><td>{esc(c["licence"])}</td></tr>'
            for c in g["credits"])
        pol = (f'<p><a href="../games/{g["id"]}/privacy/index.html">{ctx.t("legal_policy_link", title=g["title"])}</a></p>'
               if g.get("privacy") else "")
        sections.append(f"""<h2 id="{g['id']}">{esc(g['title'])}</h2>
{pol}
<div class="table"><table>{head_row}<tbody>
{rows}
</tbody></table></div>""")
    games_html = "\n".join(sections)
    toc = " ".join(f'<a href="#{g["id"]}">{esc(g["title"])}</a>' for g in games)
    body = f"""<section class="section"><div class="wrap narrow prose legal">
<p class="kicker">{ctx.t("legal_kicker")}</p>
<h1>{ctx.t("legal_title")}</h1>
<p>{ctx.t("legal_thanks")}</p>
<nav class="toc">{toc}<a href="#website">{ctx.t("website_heading")}</a></nav>
{games_html}
<h2 id="website">{ctx.t("website_heading")}</h2>
{site_privacy(ctx)}
<div class="table"><table>{head_row}<tbody>
<tr><td>{ctx.t("row_font", name="Inter")}</td><td>Rasmus Andersson, The Inter Project</td><td>SIL Open Font License 1.1</td></tr>
<tr><td>{ctx.t("row_font", name="Silkscreen")}</td><td>Jason Kottke</td><td>SIL Open Font License 1.1</td></tr>
<tr><td>{ctx.t("row_site_art")}</td><td>{esc(site["name"])}</td><td>{ctx.t("all_rights")}</td></tr>
</tbody></table></div>
<p>{ctx.t("legal_trademarks", studio=site["name"])}</p>
</div></section>"""
    write(lang, ctx.rel, page(ctx, lang["ui"]["legal_title"], PLACEHOLDER.sub(site["name"], lang["ui"]["legal_desc"]),
                              body, "legal"))


def site_privacy(ctx):
    text = ctx.t("site_privacy_html")
    text += ctx.t("site_form_html") if form_on(ctx.site) else ctx.t("site_noform_html")
    return text + ctx.t("site_trailers_html")


def build_404(lang, langs):
    # Cloudflare Pages serves the nearest 404.html for a missing URL at any depth, so its links
    # need the site's full address (site.json "site_url"); "/" works when the site is at a domain root.
    ctx = Ctx(lang, langs, "404.html", absolute=(lang["site"].get("site_url") or "").rstrip("/") + "/")
    body = f"""<section class="section"><div class="wrap narrow center-text">
<p class="kicker">404</p><h1>{ctx.t("nf_heading")}</h1><p>{ctx.t("nf_text")}</p>
<p><a class="btn" href="{ctx.root}index.html">{ctx.t("nf_back")}</a></p></div></section>"""
    write(lang, "404.html", page(ctx, lang["ui"]["nf_title"], lang["ui"]["nf_title"], body))


# ---------------------------------------------------------------- language routing

def write_language_routing(langs, games):
    """Keeps the language Function's settings in step with site.json, and limits it to pages."""
    cfg = [{"code": L["code"], "prefix": "/" + L["prefix"].rstrip("/") if L["prefix"] else "",
            "countries": L.get("countries", []), "accept": L.get("accept", [])} for L in langs]
    line = f"const LANGS = {json.dumps(cfg, ensure_ascii=False)}; // written by build.py from site.json"
    with open(MIDDLEWARE, encoding="utf-8") as f:
        js = f.read()
    new = re.sub(r"^const LANGS = .*$", lambda m: line, js, count=1, flags=re.M)
    if new != js:
        with open(MIDDLEWARE, "w", encoding="utf-8") as f:
            f.write(new)
    # Only HTML pages run the Function; files (CSS, fonts, images) are served directly.
    exclude = ["/assets/*", "/api/*"] + [f"/games/{g['id']}/media/*" for g in games]
    routes = {"version": 1, "include": ["/*"], "exclude": exclude}
    with open(os.path.join(OUT, "_routes.json"), "w", encoding="utf-8") as f:
        json.dump(routes, f, indent=2)
        f.write("\n")


def write(lang, rel, text):
    path = os.path.join(OUT, lang["prefix"], rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    site = load_json(os.path.join(HERE, "site.json"))
    langs = load_languages(site)
    games = load_games()
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(os.path.join(HERE, "assets"), os.path.join(OUT, "assets"))
    for g in games:
        shutil.copytree(os.path.join(GAMES, g["id"], "media"), os.path.join(OUT, "games", g["id"], "media"))
    for lang in langs:
        local = [localise_game(g, lang) for g in games]
        for g in local:
            build_game(lang, langs, g)
        build_home(lang, langs, local)
        build_legal(lang, langs, local)
        build_404(lang, langs)
    write_language_routing(langs, games)
    write(langs[0], ".nojekyll", "")
    if site.get("cname"):
        write(langs[0], "CNAME", site["cname"] + "\n")
    print(f"Built {len(games)} game(s) in {len(langs)} language(s) ({', '.join(L['code'] for L in langs)}) "
          f"into {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main()
