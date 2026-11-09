# Contact form Worker

Receives the website's contact form, checks Cloudflare Turnstile (spam), and emails the message to Alex with Cloudflare Email Routing. Free on Cloudflare's free plan. Stores nothing.

The form only appears on the site when `contact.form.endpoint` and `contact.form.turnstile_sitekey` are set in `site.json`.

## One-time setup (needs the domain on Cloudflare)

1. **Email Routing**: domain > Email > Email Routing > enable. Add a custom address (e.g. `hello@glowfingames.com`) that forwards to Alex's Gmail, and confirm the Gmail destination from the email Cloudflare sends.
2. **Turnstile**: Dashboard > Turnstile > Add widget. Hostnames: `glowfingames.com`, `www.glowfingames.com`, `glowfingames.pages.dev`. Mode: Managed. Copy the **site key** (public, goes in site.json) and **secret key** (private).
3. **Config**: in `wrangler.toml` set `TO` and `destination_address` to the verified Gmail address, and uncomment `routes` with the real domain.
4. **Deploy** (from this folder; needs a Cloudflare API token with "Edit Cloudflare Workers" or `npx wrangler login`):
   ```
   npx wrangler deploy
   npx wrangler secret put TURNSTILE_SECRET     # paste the secret key
   ```
5. **Site**: set `contact.form.endpoint` to `https://glowfingames.com/api/contact` and `contact.form.turnstile_sitekey` to the site key in `site.json`, run `python3 build.py`, commit, push.
6. Send a test message from the live site and check it arrives (Reply goes to the sender).

## Notes

- Spam protection: Turnstile, a hidden honeypot field, an origin check (`ALLOWED_ORIGINS`) and length limits. The `send_email` binding can only send to the verified address, so the Worker can never be used to email anyone else.
- Turning the form on changes the Legal page's privacy text (it mentions the form and Turnstile); that text is in `site_privacy()` in build.py.
- Local test: `npx wrangler dev` with a `.dev.vars` file containing `TURNSTILE_SECRET=1x0000000000000000000000000000000AA` (Cloudflare's always-pass test secret) and the test site key `1x00000000000000000000AA` in a local build. Never commit `.dev.vars`.
