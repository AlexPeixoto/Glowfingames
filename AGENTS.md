# Website: notes for agents

Read README.md first. Rules:

- Content lives in JSON (`site.json`, `games/<id>/game.json`). Do not hand-edit `docs/`: change the source and run `python3 build.py`. Commit the source **and** the rebuilt `docs/` together.
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
| `trailer_poster` | with trailer | 1280x720 WebP shown before play (the video's thumbnail) |
   | `stores` | yes | List of `{store, url, live}`. `store` is one of `google_play`, `app_store`, `steam`, `itch`, `web` (add more in `STORES` in build.py). `live: false` shows a greyed "Coming soon" button; set `live: true` when the store page is public |
   | `privacy` | no | File name of the privacy policy fragment (e.g. `privacy.html`); makes `games/<id>/privacy/` |
   | `privacy_updated` | with `privacy` | Date shown on the policy |
   | `credits` | yes | List of `{what, who, licence}` rows for the Legal page. Must match the game's own credits (for STARKEEL: docs/CREDITS.md and data/credits.json in AndroidProto) |
4. `python3 build.py`. It stops with a clear message if a field or file is missing.
5. Check the home page, the game page, its privacy page and the Legal page; commit; push.

## Common edits

- **A store page goes live**: set that store's `live` to `true` (check the `url`), update `status`, rebuild.
- **Contact email chosen**: set `contact.email` in `site.json` (the GitHub link is only the fallback).
- **Contact form**: off until `contact.form` in `site.json` is filled in; setup steps in worker/contact/README.md.
- **STARKEEL privacy policy changes**: it also exists in the AndroidProto repo at `publishing/privacy/index.html` (hosted at alexpeixoto.github.io/starkeel-privacy, the URL in Play Console). Keep all three in sync, with the same date.
