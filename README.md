# Fragment TJ

Marketplace барои Telegram Gifts дар Тоҷикистон — clone-и сабуки [fragment.com](https://fragment.com) бо Flask.

## Хусусиятҳо

- 🎁 **Gift catalog** бо search, filter, pagination
- 💰 **TON → TJS converter** автоматӣ аз CoinGecko + manual override
- 🔐 **Auth**: Telegram Login Widget + Google OAuth
- 👨‍💼 **Admin panel**: gifts, orders, users, settings
- 🌑 **Dark theme** бо TailwindCSS ва glass effect
- 📦 **Order system** (pending → paid → completed)
- 🛡️ CSRF protection, secure password handling

## Stack

- **Backend**: Flask 3, SQLAlchemy, Flask-Login, Flask-Migrate, Authlib
- **Frontend**: Jinja2 + TailwindCSS (CDN) + vanilla JS
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Auth**: Telegram Login Widget (HMAC-SHA256), Google OAuth 2.0

## Сохтори проект

```
fragment-tj/
├── app/
│   ├── __init__.py          # App factory
│   ├── models/              # User, Gift, Order, Settings
│   ├── routes/              # main, auth, admin, api
│   ├── services/            # ton_price, telegram_auth, google_auth
│   ├── templates/           # Jinja2 templates
│   └── static/              # CSS, JS, uploads
├── config.py
├── run.py
├── requirements.txt
└── .env.example
```

## Кор андохтан (Quick Start)

### 1. Clone ва virtual environment

```bash
git clone https://github.com/safiollohaminov542-commits/fragment-tj.git
cd fragment-tj
python3 -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment

```bash
cp .env.example .env
# .env-ро тағйир диҳед — ҳадди ақал SECRET_KEY ва ADMIN_TELEGRAM_IDS
```

Параметрҳои муҳим дар `.env`:

| Параметр | Тавсиф |
|---|---|
| `SECRET_KEY` | Random string (масалан `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `DATABASE_URL` | SQLite default; барои production PostgreSQL |
| `TELEGRAM_BOT_TOKEN` | Аз [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_BOT_USERNAME` | Username-и bot (бе `@`) |
| `GOOGLE_CLIENT_ID` / `_SECRET` | Аз [Google Cloud Console](https://console.cloud.google.com) |
| `ADMIN_TELEGRAM_IDS` | Бо вергул ҷудо: `123456789,987654321` |

### 3. Кор андохтан

```bash
python run.py
```

Сайт дар http://localhost:5000 кушода мешавад.

### 4. Аввалин login ҳамчун admin

1. `TELEGRAM_BOT_TOKEN` ва `TELEGRAM_BOT_USERNAME`-ро дар `.env` гузоред
2. Telegram ID-и худро дар `ADMIN_TELEGRAM_IDS` илова кунед (барои гирифтан: ба [@userinfobot](https://t.me/userinfobot) Start занед)
3. Дар сайт `Login` тугмаро занед → Login бо Telegram
4. Ба `/admin` гузаред

> ⚠️ Telegram Login Widget-ро ҳамчун bot domain дар [@BotFather](https://t.me/BotFather) сабт кардан лозим аст: `/setdomain` → URL-и сайт.

## Telegram Login Setup

1. Дар Telegram ба [@BotFather](https://t.me/BotFather) равед
2. `/newbot` → ном ва username интихоб кунед
3. Token-ро гиред → ба `TELEGRAM_BOT_TOKEN` дар `.env`
4. `/setdomain` → URL-и сайтро гузоред (барои dev: `localhost`)

## Google OAuth Setup

1. [Google Cloud Console](https://console.cloud.google.com) → новый проект
2. **APIs & Services** → **Credentials** → **Create OAuth Client ID** (Web application)
3. **Authorized redirect URI**: `http://localhost:5000/auth/google/callback`
4. Client ID/Secret-ро ба `.env` гузоред

## TON Курс

Система автомат аз [CoinGecko API](https://www.coingecko.com/en/api) курси TON-ро мегирад ва ба TJS табдил медиҳад. 

Барои **manual override**:
- Ба `/admin/settings` равед
- "Use Manual Rate" фаъол кунед
- Manual rate-ро гузоред

Барои як gift алоҳида:
- Дар admin `Use Manual TJS Price` фаъол кунед
- Manual TJS Price-ро гузоред

## Production Deployment

### Gunicorn + Nginx

```bash
gunicorn -w 4 -b 0.0.0.0:8000 'run:app'
```

Nginx config (мисол):

```nginx
server {
    listen 80;
    server_name your-domain.tj;

    location /static/ {
        alias /var/www/fragment-tj/app/static/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Database migration ба PostgreSQL

```bash
# .env
DATABASE_URL=postgresql://user:password@localhost:5432/fragment_tj

# Initial migration
flask db init
flask db migrate -m "init"
flask db upgrade
```

## Хусусиятҳои оянда (TODO)

- [ ] TON wallet connect (TON Connect)
- [ ] Real payment (TON blockchain)
- [ ] Telegram Mini App
- [ ] Auto-parser аз fragment.com бо BeautifulSoup
- [ ] WebSocket барои real-time price updates
- [ ] Multi-language (тоҷикӣ / русӣ / англисӣ)
- [ ] Telegram bot барои notification
- [ ] Auction system

## License

MIT
