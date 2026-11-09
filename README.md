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

The site is live on **GitHub Pages** from this repo: Settings > Pages > Deploy from a branch > `main` / `/docs`. Pushing a rebuilt `docs/` to `main` publishes it within a minute. Address: https://alexpeixoto.github.io/Glowfingames/

- **Cloudflare Pages** (free, unlimited bandwidth, DDoS protection, never bills): connect this repo, framework "None", build command empty, output directory `docs`.
- **Own domain**: set `"cname": "glowfingames.com"` (example) and `"site_url": "https://glowfingames.com"` in `site.json`, rebuild, then point the domain's DNS at the host. `site_url` is only used by the 404 page; while on github.io it is `https://alexpeixoto.github.io/Glowfingames`.

## Brand

The logo is Alex's pixel fish (`art/brand/glowfin_splash.png` in the AndroidProto repo, STARKEEL's start splash), cut into `assets/brand/glowfin-logo.png` (fish + wordmark), `glowfin-fish.png` (fish only), `favicon.png` and `apple-touch-icon.png`. Colours: navy `#030817`, blue `#2f7cf6`, cyan `#4fd6ff`. Headings use Silkscreen (pixel) for small labels and Inter for everything else.
