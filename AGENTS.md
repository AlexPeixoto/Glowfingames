# Website: notes for agents

Read README.md first. Rules:

- Content lives in JSON (`site.json`, `i18n/<lang>.json`, `games/<id>/game.json` and `games/<id>/i18n/<lang>.json`). Do not hand-edit `docs/`: change the source and run `python3 build.py`. Commit the source **and** the rebuilt `docs/` together.
- Python standard library only in `build.py`. No npm, no framework, no CDN, no analytics, no cookies, nothing fetched from other servers except Cloudflare Turnstile on the home page when the contact form is on (the Legal page says exactly this). Any new font or third-party file goes in the "This website" table in `build_legal()`.
- Keep images light: WebP, screenshots about 540x960 (portrait) or 1280x720 (landscape), under ~100 KB each.
- After any change, check the pages at phone width (390 px) and desktop (1440 px): no sideways scroll, nothing clipped. Post screenshots to Alex.

## Add a game

1. Make `games/<id>/` where `<id>` is lowercase letters, digits and dashes (it becomes the URL `games/<id>/`).
2. Put images in `games/<id>/media/`. From the game's store kit, for example with Pillow:
   ```python
   from PIL import Image
   im = Image.open(src).convert("RGB"); im.thumbnail((540, 960)); im.save(dst, "WEBP", quality=82, method=6)
   ```
   - `icon`: square, 256x256 (the store icon).
   - `banner`: 1024x500 (the Play feature graphic). Used on the home page card.
   - `hero` (optional): artwork with no text in it, for the right side of the game page header. Falls back to `banner`.
   - `screenshots`: as many as you like, shown in order.
3. Write `games/<id>/game.json` (copy `games/starkeel/game.json`). Fields:

   | Field | Required | Meaning |
   |---|---|---|
   | `id` | yes | Same as the folder name |
   | `order` | yes | Sort order on the home page (1 first) |
   | `title`, `tagline`, `summary` | yes | Name, one-line hook, 1-2 sentence pitch (home card + page description) |
   | `description` | yes | List of paragraphs for the game page |
   | `status` | no | Small badge, e.g. "Coming soon to Google Play", "Out now". Leave out to hide |
   | `accent` | no | Hex colour for this game's highlights (default cyan) |
   | `features` | no | List of `{title, text}` cards |
   | `facts` | no | List of `{label, value}` rows (genre, platform, price, languages...) |
   | `icon`, `banner`, `hero`, `screenshots` | see 2 | Paths relative to the game folder; screenshots are `{src, alt}` (alt text is required for accessibility) |
   | `trailer_youtube_id` | no | YouTube trailer, click to play: nothing loads from YouTube until the visitor presses play, then the privacy-enhanced youtube-nocookie.com player; empty hides it |
| `trailer_poster` | with trailer | 1280x720 WebP shown before play (the video's YouTube thumbnail) |
| `trailer_play_x` | no | Play button position, % from the left (default 50); move it off the thumbnail's text |
   | `stores` | yes | List of `{store, url, live}`. `store` is one of `google_play`, `app_store`, `steam`, `itch`, `web` (add more in `STORES` in build.py). `live: false` shows a greyed "Coming soon" button; set `live: true` when the store page is public |
   | `privacy` | no | File name of the privacy policy fragment (e.g. `privacy.html`); makes `games/<id>/privacy/` |
   | `privacy_updated` | with `privacy` | Date shown on the policy |
   | `credits` | yes | List of `{what, who, licence}` rows for the Legal page. Must match the game's own credits (for STARKEEL: docs/CREDITS.md and data/credits.json in AndroidProto) |
4. Translate it for every other language in `site.json` (see Languages below): `games/<id>/i18n/<code>.json`.
5. `python3 build.py`. It stops with a clear message if a field, file or translation is missing.
6. Check the home page, the game page, its privacy page and the Legal page in each language; commit; push.

## Common edits

- **A store page goes live**: set that store's `live` to `true` (check the `url`), update `status`, rebuild.
- **Contact email chosen**: set `contact.email` in `site.json` (the GitHub link is only the fallback).
- **Contact form**: off until `contact.form` in `site.json` is filled in; setup steps in worker/contact/README.md.
- **STARKEEL privacy policy changes**: it also exists in the AndroidProto repo at `publishing/privacy/index.html` (hosted at alexpeixoto.github.io/starkeel-privacy, the URL in Play Console). Keep all three in sync, with the same date, and update the translation `games/starkeel/privacy.pt-br.html` (and its `privacy_updated` in `games/starkeel/i18n/pt-br.json`).

## Languages

The site is English (default, at the root: `/`, `/games/<id>/`) and Brazilian Portuguese (under `/pt-br/`). A globe menu at the top right switches language on every page. Never mix languages on one page: the build refuses a language with missing text.

| File | What |
|---|---|
| `site.json` `languages` | Language list. First = default (site root). Each: `code` (URL folder, lowercase), `name` (shown in the menu, in its own language), `short` (menu button, e.g. `PT`), `hreflang`, and for auto-detect `countries` (ISO codes from Cloudflare, e.g. `BR`) and `accept` (browser language prefixes, e.g. `pt`) |
| `i18n/en.json` | All interface text (buttons, headings, form messages, legal and privacy text). Keys ending `_html` may hold HTML |
| `i18n/<code>.json` | `ui`: the same keys as en.json with the same `{placeholders}`. `site`: slogan, intro, about, contact.text, contact.fallback_label |
| `games/<id>/i18n/<code>.json` | Required: tagline, summary, description, features, facts, credits, screenshots (same count as game.json, each `{src, alt}`; `src` may point at localised images), plus status / privacy (a translated policy file, e.g. `privacy.pt-br.html`) / privacy_updated when the game has them. Optional: banner, hero, icon, trailer_* |
| `games/<id>/media/<code>/` | Localised images (store screenshots and feature graphic from the game's store kit, e.g. AndroidProto `publishing/pt-BR/`) |
| `functions/_middleware.js` | Cloudflare Pages Function that picks the language (below). build.py rewrites its `LANGS` line from site.json; edit the rest by hand |
| `docs/_routes.json` | Written by build.py: the Function runs only for pages, not images, fonts or CSS |

**How a visitor gets a language** (functions/_middleware.js):
1. Picking a language in the menu (a link ending `?lang=<code>`) saves it in a `lang` cookie (1 year) and always wins, on every page.
2. Without a saved choice, someone arriving from outside on an English page goes to their language by country (`CF-IPCountry`, so Brazil gets `/pt-br/`), then by browser language (`Accept-Language`, so any `pt` browser too). Everyone else stays on English.
3. Clicks inside the site and links straight to `/pt-br/...` are never redirected without a saved choice, so shared links open as sent and search engines see every page.

The Legal page says the site's only cookie is that language choice; keep it true. To test the Function without Cloudflare: import `onRequest` in Node with mock `Request`s (see the commit that added it), or `npx wrangler pages dev docs`.

**Add a language**: add it to `site.json` `languages`; copy `i18n/en.json` to `i18n/<code>.json` and translate `ui`, add a `site` block (copy pt-br.json's shape); add `games/<id>/i18n/<code>.json` for every game (use the game's own translations: STARKEEL's are in AndroidProto `locale/strings.csv`, `tools/store/i18n/<lang>.json` and `publishing/<locale>/`); put localised screenshots in `games/<id>/media/<code>/`; translate the privacy policy (start it with a note that the English version prevails, linking to it with `?lang=en`); build; check 390 px and 1440 px. Alex is a native Brazilian Portuguese speaker: send him Portuguese changes to spot-check. New interface text needs a key in every `i18n/*.json`.
