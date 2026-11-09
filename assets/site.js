// Screenshot lightbox: click a screenshot to view it large; arrows/Esc work too.
(function () {
  const links = Array.from(document.querySelectorAll("a[data-lightbox]"));
  if (!links.length) return;
  let box = null, index = 0, opener = null;

  function show(i) {
    index = (i + links.length) % links.length;
    const img = links[index].querySelector("img");
    box.querySelector("img").src = links[index].href;
    box.querySelector("img").alt = img ? img.alt : "";
  }
  function close() {
    box.remove(); box = null;
    document.removeEventListener("keydown", onKey);
    if (opener) opener.focus();
  }
  function onKey(e) {
    if (e.key === "Escape") close();
    else if (e.key === "ArrowRight") show(index + 1);
    else if (e.key === "ArrowLeft") show(index - 1);
  }
  function open(i) {
    opener = links[i];
    box = document.createElement("div");
    box.className = "lightbox";
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-modal", "true");
    box.innerHTML = '<img alt=""><button class="close" aria-label="Close">×</button>' +
      '<button class="nav prev" aria-label="Previous">‹</button><button class="nav next" aria-label="Next">›</button>';
    const d = document.body.dataset;
    box.querySelector(".close").setAttribute("aria-label", d.lbClose || "Close");
    box.querySelector(".prev").setAttribute("aria-label", d.lbPrev || "Previous");
    box.querySelector(".next").setAttribute("aria-label", d.lbNext || "Next");
    box.addEventListener("click", (e) => {
      if (e.target.classList.contains("prev")) show(index - 1);
      else if (e.target.classList.contains("next")) show(index + 1);
      else if (e.target.tagName !== "IMG") close();
    });
    document.body.appendChild(box);
    document.addEventListener("keydown", onKey);
    show(i);
    box.querySelector(".close").focus();
  }
  links.forEach((a, i) => a.addEventListener("click", (e) => { e.preventDefault(); open(i); }));
})();

// Contact form: posts to the contact Worker and shows the result in place.
(function () {
  const form = document.querySelector("form[data-contact]");
  if (!form) return;
  const status = form.querySelector(".form-status");
  const button = form.querySelector("button[type=submit]");
  const say = (text, cls) => { status.textContent = text; status.className = "form-status " + (cls || ""); };
  const msg = form.dataset; // texts in the page's language, from build.py
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!form.reportValidity()) return;
    button.disabled = true;
    say(msg.msgSending);
    try {
      const res = await fetch(form.action, { method: "POST", body: new FormData(form) });
      const data = await res.json().catch(() => ({}));
      if (res.ok && data.ok) {
        form.reset();
        say(msg.msgSent, "ok");
      } else if (data.error === "captcha") {
        say(msg.msgErrCaptcha, "err");
      } else if (data.error === "fields") {
        say(msg.msgErrFields, "err");
      } else {
        say(msg.msgErrSend, "err");
      }
    } catch {
      say(msg.msgErrOffline, "err");
    }
    if (window.turnstile) window.turnstile.reset();
    button.disabled = false;
  });
})();

// Trailer: swap the poster for the YouTube player (privacy-enhanced) only when pressed.
(function () {
  document.querySelectorAll("a[data-youtube]").forEach((a) => {
    a.addEventListener("click", (e) => {
      e.preventDefault();
      const f = document.createElement("iframe");
      f.src = "https://www.youtube-nocookie.com/embed/" + encodeURIComponent(a.dataset.youtube) + "?autoplay=1&rel=0";
      f.title = a.dataset.title || "Trailer";
      f.allow = "autoplay; encrypted-media; picture-in-picture; fullscreen";
      f.allowFullscreen = true;
      a.replaceWith(f);
    });
  });
})();

// Language menu: close it on a click outside or Esc. Picking a language is a plain link
// (?lang=<code>), which the site's language Function remembers.
(function () {
  const menu = document.querySelector("details.lang");
  if (!menu) return;
  document.addEventListener("click", (e) => { if (menu.open && !menu.contains(e.target)) menu.open = false; });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && menu.open) { menu.open = false; menu.querySelector("summary").focus(); }
  });
})();
