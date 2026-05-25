// TON Connect integration: authentication + payment

(function () {
  "use strict";

  // === TON Connect UI singleton ===
  let tonConnectUI = null;

  function getOrigin() {
    return window.location.origin;
  }

  function initTonConnect() {
    if (tonConnectUI) return tonConnectUI;
    if (!window.TON_CONNECT_UI) {
      console.warn("@tonconnect/ui library not loaded");
      return null;
    }

    tonConnectUI = new TON_CONNECT_UI.TonConnectUI({
      manifestUrl: getOrigin() + "/static/tonconnect-manifest.json",
      uiPreferences: { theme: "DARK" },
    });

    return tonConnectUI;
  }

  // === TON Login (proof verification) ===
  async function setupTonLogin(buttonSelector) {
    const btn = document.querySelector(buttonSelector);
    if (!btn) return;

    const ui = initTonConnect();
    if (!ui) {
      btn.disabled = true;
      btn.textContent = "TON Connect ҳоло available нест";
      return;
    }

    // Set ton_proof payload пеш аз кушодани wallet
    async function refreshProof() {
      try {
        const r = await fetch("/auth/ton/payload");
        const data = await r.json();
        ui.setConnectRequestParameters({
          state: "ready",
          value: { tonProof: data.payload },
        });
      } catch (e) {
        console.warn("Failed to fetch TON proof payload:", e);
      }
    }

    await refreshProof();

    // Listen ба connect events
    ui.onStatusChange(async (wallet) => {
      if (!wallet) return;
      const proof = wallet.connectItems && wallet.connectItems.tonProof;
      if (!proof || !proof.proof) {
        console.warn("No proof returned by wallet");
        return;
      }

      const payload = {
        address: wallet.account.address,
        public_key: wallet.account.publicKey,
        proof: {
          timestamp: proof.proof.timestamp,
          domain: proof.proof.domain,
          signature: proof.proof.signature,
          payload: proof.proof.payload,
        },
      };

      try {
        const r = await fetch("/auth/ton/verify", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await r.json();
        if (data.ok) {
          window.location.href = data.redirect || "/";
        } else {
          alert("Login fail: " + (data.error || "unknown"));
          await ui.disconnect();
        }
      } catch (e) {
        alert("Network error: " + e.message);
      }
    });

    btn.addEventListener("click", async (e) => {
      e.preventDefault();
      await refreshProof(); // proof-и нав
      await ui.openModal();
    });
  }

  // === TON Payment ===
  async function payOrder(opts) {
    const { merchantWallet, amountTon, comment, orderId } = opts;
    const ui = initTonConnect();
    if (!ui) {
      alert("TON Connect ҳоло available нест");
      return false;
    }

    if (!merchantWallet) {
      alert("Merchant wallet нет конфигуратсия");
      return false;
    }

    if (!ui.connected) {
      await ui.openModal();
      // wait дар connect (max 60s)
      const connected = await new Promise((resolve) => {
        const t = setTimeout(() => resolve(false), 60000);
        const off = ui.onStatusChange((w) => {
          if (w) {
            clearTimeout(t);
            off();
            resolve(true);
          }
        });
      });
      if (!connected) return false;
    }

    // amount → nanoTON
    const amountNano = Math.round(amountTon * 1e9).toString();

    // Build comment payload (text comment в TON message)
    // Тибқи TIP-104: comment encode мешавад ҳамчун
    // op:0x00000000 + UTF-8 text (бо boc base64)
    // tonconnect-ui автомат ин-ро handle мекунад агар payload ҳамчун string бошад
    // Бисёр wallet-ҳо `text` field-ро қабул мекунанд:
    const txParams = {
      validUntil: Math.floor(Date.now() / 1000) + 600,
      messages: [
        {
          address: merchantWallet,
          amount: amountNano,
          payload: textCommentPayload(comment),
        },
      ],
    };

    try {
      await ui.sendTransaction(txParams);
      // Дарҳол TX полchecked мешавад
      startPolling(orderId);
      return true;
    } catch (e) {
      console.error("Payment failed:", e);
      if (e.message && e.message.includes("rejected")) {
        alert("Транзаксия рад карда шуд");
      } else {
        alert("Хатои пардохт: " + (e.message || e));
      }
      return false;
    }
  }

  // Build base64 BOC бо text comment (op=0x00000000 + UTF-8 string)
  // tonweb-ро истифода мекунем агар available бошад, вагарна fallback
  function textCommentPayload(text) {
    if (window.TonWeb) {
      try {
        const cell = new TonWeb.boc.Cell();
        cell.bits.writeUint(0, 32); // op = 0
        cell.bits.writeString(text);
        const boc = cell.toBoc(false);
        // Base64 encode
        let binary = "";
        for (let i = 0; i < boc.length; i++) {
          binary += String.fromCharCode(boc[i]);
        }
        return btoa(binary);
      } catch (e) {
        console.warn("tonweb cell build failed:", e);
      }
    }
    // Fallback: payload-и оддӣ (бисёр wallet-ҳо инро қабул намекунанд!)
    console.warn(
      "tonweb available нест — payload бе comment мефиристам. " +
      "Backend tx-ро бо comment пайдо карда наметавонад."
    );
    return "";
  }

  // === Polling status === 
  let pollTimer = null;
  function startPolling(orderId) {
    if (pollTimer) clearInterval(pollTimer);
    let attempts = 0;
    const maxAttempts = 60; // 5 daqiqa бо 5s интервал

    const statusEl = document.getElementById("payment-status");
    if (statusEl) {
      statusEl.textContent = "⏳ Интизори тасдиқ дар TON blockchain...";
      statusEl.className = "p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-sm";
    }

    pollTimer = setInterval(async () => {
      attempts++;
      try {
        const r = await fetch(`/orders/${orderId}/check-payment`, {
          method: "POST",
        });
        const data = await r.json();
        if (data.status === "paid") {
          clearInterval(pollTimer);
          if (statusEl) {
            statusEl.textContent = `✓ Pardoxt qabul shud! TX: ${data.tx_hash.substring(0, 12)}...`;
            statusEl.className = "p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm";
          }
          setTimeout(() => window.location.reload(), 2000);
          return;
        }
      } catch (e) {
        console.warn("Poll error:", e);
      }
      if (attempts >= maxAttempts) {
        clearInterval(pollTimer);
        if (statusEl) {
          statusEl.textContent = "⚠ Polling-и автомати timeout. Pardoxt-ро баъдтар санҷед.";
          statusEl.className = "p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm";
        }
      }
    }, 5000);
  }

  // === Manual check button ===
  function setupCheckButton(orderId) {
    const btn = document.getElementById("btn-check-payment");
    if (!btn) return;
    btn.addEventListener("click", async () => {
      btn.disabled = true;
      const oldText = btn.textContent;
      btn.textContent = "Санҷида истода...";
      try {
        const r = await fetch(`/orders/${orderId}/check-payment`, {
          method: "POST",
        });
        const data = await r.json();
        if (data.status === "paid") {
          window.location.reload();
        } else {
          btn.textContent = "TX дар blockchain ҳоло нест. Боз кӯшиш кунед.";
          setTimeout(() => {
            btn.textContent = oldText;
            btn.disabled = false;
          }, 3000);
        }
      } catch (e) {
        btn.textContent = "Хато: " + e.message;
        setTimeout(() => {
          btn.textContent = oldText;
          btn.disabled = false;
        }, 3000);
      }
    });
  }

  // === Wallet status display ===
  function setupWalletStatus() {
    const ui = initTonConnect();
    if (!ui) return;
    const display = document.getElementById("wallet-display");
    if (!display) return;

    function update(wallet) {
      if (wallet) {
        const a = wallet.account.address;
        display.textContent = `${a.substring(0, 4)}...${a.substring(a.length - 4)}`;
      } else {
        display.textContent = "Не подключен";
      }
    }
    update(ui.wallet);
    ui.onStatusChange(update);
  }

  // Expose to global
  window.FragmentTJ = window.FragmentTJ || {};
  window.FragmentTJ.setupTonLogin = setupTonLogin;
  window.FragmentTJ.payOrder = payOrder;
  window.FragmentTJ.setupCheckButton = setupCheckButton;
  window.FragmentTJ.setupWalletStatus = setupWalletStatus;
  window.FragmentTJ.initTonConnect = initTonConnect;
})();
