// Fragment TJ — main JS

(function () {
  "use strict";

  // Auto-dismiss flash messages after 5s
  setTimeout(() => {
    document.querySelectorAll(".flash-message").forEach((el) => {
      el.style.opacity = "0";
      el.style.transform = "translateY(-10px)";
      setTimeout(() => el.remove(), 400);
    });
  }, 5000);

  // Live TON rate update (every 5 minutes)
  async function updateRates() {
    try {
      const r = await fetch("/api/rates");
      if (!r.ok) return;
      const data = await r.json();
      document.querySelectorAll("[data-ton-tjs]").forEach((el) => {
        el.textContent = Number(data.ton_tjs).toFixed(2);
      });
      document.querySelectorAll("[data-ton-usd]").forEach((el) => {
        el.textContent = Number(data.ton_usd).toFixed(2);
      });
      document.querySelectorAll("[data-usd-tjs]").forEach((el) => {
        el.textContent = Number(data.usd_tjs).toFixed(2);
      });
    } catch (e) {
      console.warn("Rate update failed:", e);
    }
  }
  setInterval(updateRates, 5 * 60 * 1000);

  // Image fallback
  document.querySelectorAll("img").forEach((img) => {
    img.addEventListener("error", () => {
      const wrap = img.parentElement;
      if (wrap && !wrap.dataset.fallback) {
        wrap.dataset.fallback = "1";
        wrap.innerHTML =
          '<div class="w-full h-full flex items-center justify-center text-6xl opacity-20">🎁</div>';
      }
    });
  });
})();
