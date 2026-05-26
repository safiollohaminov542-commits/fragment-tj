# Fragment TJ — Marketplace v2

Маркетплейси Telegram Gifts бо wallet, Fragment auto-import, ва Telegram transfer system.

## ✨ Хусусиятҳо

- 📧 **Email-only auth** — register/login + 6-digit code (Gmail SMTP)
- 💰 **Multi-currency wallet** — TJS / TON / USD бо real-time conversion
- 🎁 **Fragment auto-import** — URL мегузоред, парсер метаdata, animation, нархҳо мегирад
- 🎬 **Lottie animations** — TGS файлҳоро автомат extract ва намоиш медиҳад
- 📈 **Markup %** — admin per-gift % илова мекунад (mas: 3 TON +50% = 4.5 TON)
- 📨 **Telegram transfer** — user заявка медиҳад → admin manually мефиристад
- 🌐 **i18n** — Тоҷикӣ + Русский
- 🌑 **Dark theme** — orange accent (Tailwind CDN)
- 👨‍💼 **Admin panel** — gifts, wallet topup, transfers, settings, users

## 🚀 Кор андохтан

### 1. Install

```bash
git clone https://github.com/safiollohaminov542-commits/fragment-tj.git
cd fragment-tj
git checkout feat/marketplace-v2
python3 -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Playwright (барои Fragment auto-import)

```bash
playwright install chromium
```

⚠️ Агар Playwright install кор накард, парсер автомат ба `requests + BeautifulSoup` fallback мекунад.

### 3. Setup .env

```bash
cp .env.example .env
nano .env
```

Минимум:
```ini
SECRET_KEY=ҳосил кунед бо python -c "import secrets; print(secrets.token_hex(32))"
[email protected]
MAIL_PASSWORD=your-16-char-app-password
[email protected]
[email protected]
```

### 4. Run

```bash
rm -f fragment_tj.db   # агар database-и кӯҳна бошад
python run.py
```

http://localhost:5000

## 🎯 Аввалин қадамҳо

1. **Регистратся**: http://localhost:5000/auth/register
2. Email-и шумо дар `ADMIN_EMAILS` бошад → автомат admin мешавед
3. **Settings**: http://localhost:5000/admin/settings — курсҳои API ё manual
4. **Import gift**: http://localhost:5000/admin/gifts/new → URL-и Fragment гузоред → "Import"
5. **Topup user balance**: http://localhost:5000/admin/users → user → top-up
6. User мехарад → inventory → "Transfer to Telegram" → admin "Approve" → "Sent"

## 🏗 Architecture

```
fragment-tj/
├── app/
│   ├── models/
│   │   ├── user.py             # email auth + 3 wallet balances
│   │   ├── gift.py             # base_price + markup + attributes
│   │   ├── inventory.py        # user-и харидорӣ кардаи gifts
│   │   ├── transfer_request.py # заявка ба Telegram
│   │   ├── balance_transaction.py
│   │   ├── order.py
│   │   ├── verification.py
│   │   └── settings.py
│   ├── routes/
│   │   ├── main.py
│   │   ├── auth.py             # register/login/verify
│   │   ├── admin.py            # gifts/users/wallet/transfers
│   │   ├── wallet.py           # convert
│   │   ├── profile.py          # inventory + edit
│   │   ├── transfer.py         # request to Telegram
│   │   ├── language.py         # tg/ru switcher
│   │   └── api.py              # JSON
│   ├── services/
│   │   ├── currency.py         # TON/TJS/USD rates + cache
│   │   ├── wallet.py           # credit/debit/convert
│   │   ├── fragment_parser.py  # Playwright + BeautifulSoup
│   │   ├── lottie.py           # TGS download + decompress
│   │   ├── mail.py
│   │   └── i18n.py             # tg/ru translations
│   ├── templates/
│   └── static/
├── config.py
└── run.py
```

## 🔧 Курсҳо

Аз CoinGecko: TON→USD, USDT→TJS. Дар admin/settings:
- 🔄 Auto (default) — аз API
- ✋ Manual — admin курси худро мегузорад
- 🔄 Reset → ба API бар мегардад

## 🎨 Themes

- **Dark + orange** (#ff7a18) — асоси UI
- **Glass cards** — backdrop-blur + gradient
- **Lottie animations** — autoplay loop дар gift cards

## License

MIT
