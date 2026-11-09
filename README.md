# Glowfin Games website

The studio website: home (logo, games, about, contact), one page per game (store buttons, screenshots, features, privacy policy) and a Legal page (licences, credits, privacy). Plain static HTML, no framework, no tracking, nothing loaded from other servers.

```
python3 build.py        # Python 3 standard library only; writes docs/
```

Open `docs/index.html` in a browser to check it. All links are relative, so it works from disk, on a domain root, or under a sub-path.

## Layout

| Path | What |
|---|---|
| `site.json` | Studio text: name, slogan, intro, about, contact email, `site_url`, `cname` |
| `games/<id>/game.json` | One game: text, facts, store links, screenshots, credits. Field guide in [AGENTS.md](AGENTS.md) |
| `games/<id>/media/` | That game's images (icon, banner, hero, screenshots), copied as-is |
| `games/<id>/privacy.html` | That game's privacy policy body (HTML fragment) |
| `assets/` | Shared CSS, JS, fonts (self-hosted Inter + Silkscreen, OFL) and the logo |
| `worker/contact/` | Cloudflare Worker behind the contact form (off until set up; see its README) |
| `build.py` | The generator: page templates live in it as Python functions |
| `docs/` | Build output. Committed, so a static host can serve it directly. Never edit by hand |

## Deploying

Live at **https://glowfingames.com** on **Cloudflare Pages** (free plan): the Pages project `glowfingames` builds from this repo's `main` with no build command and output directory `docs`, so pushing a rebuilt `docs/` to `main` publishes it within a minute or two. The domain is registered on Cloudflare. The contact form's Worker (`worker/contact`) is deployed the same way by Cloudflare Workers Builds (root directory `worker/contact`). The repo can be private; Cloudflare reads it through its GitHub app.

`site_url` in `site.json` is the live address (used by the 404 page). `cname` is only for GitHub Pages and is not used.

## Brand

The logo is Alex's pixel fish (`art/brand/glowfin_splash.png` in the AndroidProto repo, STARKEEL's start splash), cut into `assets/brand/glowfin-logo.png` (fish + wordmark), `glowfin-fish.png` (fish only), `favicon.png` and `apple-touch-icon.png`. Colours: navy `#030817`, blue `#2f7cf6`, cyan `#4fd6ff`. Headings use Silkscreen (pixel) for small labels and Inter for everything else.
