// Glowfin Games contact form: checks Turnstile, then emails the message to Alex
// through Cloudflare Email Routing (send_email binding). No storage, no logs of messages.
import { EmailMessage } from "cloudflare:email";

const LIMITS = { name: 100, email: 200, subject: 150, message: 5000 };

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    const allowed = (env.ALLOWED_ORIGINS || "").split(",").map((s) => s.trim()).filter(Boolean);
    const cors = allowed.includes(origin)
      ? { "Access-Control-Allow-Origin": origin, "Access-Control-Allow-Methods": "POST", "Access-Control-Allow-Headers": "Content-Type", "Vary": "Origin" }
      : {};
    const reply = (status, body) => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", ...cors } });

    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
    if (request.method !== "POST") return reply(405, { ok: false, error: "method" });
    if (origin && !allowed.includes(origin)) return reply(403, { ok: false, error: "origin" });

    let form;
    try {
      form = await request.formData();
    } catch {
      return reply(400, { ok: false, error: "form" });
    }
    const field = (k) => {
      const v = String(form.get(k) || "").trim();
      return (k === "message" ? v : v.replace(/\s+/g, " ")).slice(0, LIMITS[k] || 100);
    };
    const name = field("name"), email = field("email"), subject = field("subject"), message = field("message");
    if (form.get("website")) return reply(200, { ok: true }); // honeypot: bots fill hidden fields
    if (!message || !/^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$/.test(email)) return reply(400, { ok: false, error: "fields" });

    const token = String(form.get("cf-turnstile-response") || "");
    const check = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
      method: "POST",
      body: new URLSearchParams({ secret: env.TURNSTILE_SECRET || "", response: token, remoteip: request.headers.get("CF-Connecting-IP") || "" }),
    }).then((r) => r.json()).catch(() => ({ success: false }));
    if (!check.success) return reply(403, { ok: false, error: "captcha" });

    const raw = buildMime({
      from: `Glowfin website <${env.FROM}>`,
      to: env.TO,
      replyTo: email,
      subject: `[Glowfin contact] ${subject || "Message from " + (name || email)}`,
      text: `From: ${name || "(no name)"} <${email}>\nSubject: ${subject || "(none)"}\nPage: ${request.headers.get("Referer") || "?"}\n\n${message}\n`,
    });
    try {
      await env.MAILER.send(new EmailMessage(env.FROM, env.TO, raw));
    } catch (e) {
      return reply(502, { ok: false, error: "send" });
    }
    return reply(200, { ok: true });
  },
};

function header(value) {
  // Strip line breaks (header injection) and encode non-ASCII as RFC 2047.
  const clean = String(value).replace(/[\r\n]+/g, " ");
  return /^[\x20-\x7e]*$/.test(clean) ? clean : `=?UTF-8?B?${b64(clean)}?=`;
}

function b64(text) {
  const bytes = new TextEncoder().encode(text);
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin);
}

export function buildMime({ from, to, replyTo, subject, text }) {
  const id = `<${crypto.randomUUID()}@${from.split("@").pop().replace(/[>\s]/g, "")}>`;
  const body = b64(text).replace(/.{76}/g, "$&\r\n");
  return [
    `From: ${header(from)}`,
    `To: ${header(to)}`,
    `Reply-To: ${header(replyTo)}`,
    `Subject: ${header(subject)}`,
    `Message-ID: ${id}`,
    `Date: ${new Date().toUTCString()}`,
    "MIME-Version: 1.0",
    "Content-Type: text/plain; charset=utf-8",
    "Content-Transfer-Encoding: base64",
    "",
    body,
  ].join("\r\n");
}
