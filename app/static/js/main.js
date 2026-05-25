// Fragment TJ — main JS

(function () {
  "use strict";

  // Auto-dismiss flash messages after 5s
  document.querySelectorAll("main > .mb-6 > div").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity 0.4s, transform 0.4s";
      el.style.opacity = "0";
      el.style.transform = "translateY(-10px)";
      setTimeout(() => el.remove(), 400);
    }, 5000);
  });

  // Live TON rate update (every 5 minutes)
  async function updateTonRate() {
    try {
      const r = await fetch("/api/ton-rate");
      if (!r.ok) return;
      const data = await r.json();
      document.querySelectorAll("[data-ton-rate]").forEach((el) => {
        el.textContent = Number(data.rate).toFixed(2);
      });
    } catch (e) {
      console.warn("TON rate update failed:", e);
    }
  }
  setInterval(updateTonRate, 5 * 60 * 1000);

  // Smooth scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach((a) => {
    a.addEventListener("click", (e) => {
      const id = a.getAttribute("href").slice(1);
      const target = document.getElementById(id);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: "smooth" });
      }
    });
  });

  // Image fallback: ҳангоми хатои image, fallback emoji-ро нишон медиҳем
  document.querySelectorAll("img").forEach((img) => {
    img.addEventListener("error", () => {
      const wrap = img.parentElement;
      if (wrap && !wrap.dataset.fallback) {
        wrap.dataset.fallback = "1";
        wrap.innerHTML = '<div class="w-full h-full flex items-center justify-center text-6xl opacity-20">🎁</div>';
      }
    });
  });
})();
