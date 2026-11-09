// Cloudflare Pages Function: sends each visitor to the website in their language.
// Runs before every page (docs/_routes.json keeps it off images, fonts and CSS).
//
// 1. A language picked in the menu (link with ?lang=<code>) is saved in a "lang" cookie and always wins.
// 2. With no saved choice, a visitor arriving from outside on a default-language (English) page is
//    sent to their language: by country first (CF-IPCountry), then by the browser's languages.
// 3. Links between pages and links to a language's own pages (e.g. /pt-br/...) are never redirected
//    without a saved choice, so shared links open as sent.
// The LANGS line is written by build.py from site.json "languages"; edit it there.

const LANGS = [{"code": "en", "prefix": "", "countries": [], "accept": []}, {"code": "pt-br", "prefix": "/pt-br", "countries": ["BR"], "accept": ["pt"]}]; // written by build.py from site.json
const COOKIE = "lang";
const YEAR = 60 * 60 * 24 * 365;

const byCode = (code) => LANGS.find((l) => l.code === code);
const DEFAULT = LANGS[0];

function langOfPath(path) {
  for (const l of LANGS) {
    if (l.prefix && (path === l.prefix || path.startsWith(l.prefix + "/"))) return l;
  }
  return DEFAULT;
}

function swapPath(path, from, to) {
  const rest = from.prefix ? path.slice(from.prefix.length) || "/" : path;
  return (to.prefix + rest).replace(/\/index\.html$/, "/") || "/";
}

function readCookie(request) {
  const m = (request.headers.get("Cookie") || "").match(/(?:^|;\s*)lang=([a-z0-9-]+)/);
  return m ? byCode(m[1]) : null;
}

function fromCountry(request) {
  const country = (request.cf && request.cf.country) || request.headers.get("CF-IPCountry") || "";
  return LANGS.find((l) => l.countries.includes(country.toUpperCase())) || null;
}

function fromBrowser(request) {
  // "pt-BR,pt;q=0.9,en;q=0.8" -> tags by preference; the first one we have wins.
  const tags = (request.headers.get("Accept-Language") || "")
    .split(",")
    .map((part, i) => {
      const [tag, ...params] = part.trim().toLowerCase().split(";");
      const q = params.map((p) => p.trim()).find((p) => p.startsWith("q="));
      return { tag, q: q ? parseFloat(q.slice(2)) || 0 : 1, i };
    })
    .filter((t) => t.tag && t.tag !== "*" && t.q > 0)
    .sort((a, b) => b.q - a.q || a.i - b.i);
  for (const { tag } of tags) {
    for (const l of LANGS) {
      const prefixes = l.accept.length ? l.accept : [l.code.split("-")[0]];
      if (prefixes.some((p) => tag === p || tag.startsWith(p + "-"))) return l;
    }
  }
  return null;
}

function cameFromThisSite(request, url) {
  try {
    return new URL(request.headers.get("Referer") || "").host === url.host;
  } catch {
    return false;
  }
}

function redirect(location, cookie) {
  const headers = { Location: location, "Cache-Control": "private, no-store", Vary: "Cookie, Accept-Language" };
  if (cookie) headers["Set-Cookie"] = `${COOKIE}=${cookie}; Path=/; Max-Age=${YEAR}; SameSite=Lax; Secure`;
  return new Response(null, { status: 302, headers });
}

export async function onRequest({ request, next }) {
  if (request.method !== "GET" && request.method !== "HEAD") return next();
  const url = new URL(request.url);
  const here = langOfPath(url.pathname);

  // 1. Picked in the menu: remember it and show that language's page (without the ?lang).
  const picked = byCode(url.searchParams.get("lang") || "");
  if (picked) {
    url.searchParams.delete("lang");
    const path = swapPath(url.pathname, here, picked);
    return redirect(path + url.search + url.hash, picked.code);
  }

  const saved = readCookie(request);
  if (saved) {
    if (saved === here) return next();
    return redirect(swapPath(url.pathname, here, saved) + url.search);
  }

  // 2. First arrival on an English page: guess from country, then browser.
  if (here !== DEFAULT || cameFromThisSite(request, url)) return next();
  const guess = fromCountry(request) || fromBrowser(request) || DEFAULT;
  if (guess === here) return next();
  return redirect(swapPath(url.pathname, here, guess) + url.search);
}
