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
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!form.reportValidity()) return;
    button.disabled = true;
    say("Sending…");
    try {
      const res = await fetch(form.action, { method: "POST", body: new FormData(form) });
      const data = await res.json().catch(() => ({}));
      if (res.ok && data.ok) {
        form.reset();
        say("Thanks! Your message is on its way. We'll reply by email.", "ok");
      } else if (data.error === "captcha") {
        say("The spam check didn't pass. Please wait for it to finish and try again.", "err");
      } else if (data.error === "fields") {
        say("Please add a valid email address and a message.", "err");
      } else {
        say("Sorry, that didn't send. Please try again in a moment.", "err");
      }
    } catch {
      say("Sorry, that didn't send. Check your connection and try again.", "err");
    }
    if (window.turnstile) window.turnstile.reset();
    button.disabled = false;
  });
})();
