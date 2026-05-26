# Fragment TJ

Marketplace барои Telegram Gifts дар Тоҷикистон. Зеҳнӣ ва осон — фақат email лозим аст барои регистратсия.

## ✨ Хусусиятҳо

- 📧 **Email-only authentication** — фақат email + 6-digit code тавассути Gmail SMTP
- 🎁 **Gift catalog** бо search, filter, pagination
- 💰 **TON → TJS converter** аз CoinGecko API + manual override
- 👨‍💼 **Admin panel** — gift management, orders, users, settings
- 🌑 **Dark theme** бо TailwindCSS, glass effect, animations
- 📦 **Order system** (pending → paid → completed)
- 🛡️ Rate-limiting барои code resend, expiration, attempt counter
- 🔒 Password hashing (Werkzeug PBKDF2)
- ✅ CSRF protection

## 🛠 Stack

- **Backend**: Flask 3, SQLAlchemy, Flask-Login, Flask-Mail, Flask-Migrate
- **Frontend**: Jinja2 + TailwindCSS (CDN) + vanilla JS
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Email**: Gmail SMTP бо App Password

## 📂 Сохтори проект

```
fragment-tj/
├── app/
│   ├── __init__.py          # App factory
│   ├── models/
│   │   ├── user.py          # User бо email + password
│   │   ├── verification.py  # 6-digit codes
│   │   ├── gift.py
│   │   ├── order.py
│   │   └── settings.py
│   ├── routes/              # main, auth, admin, api
│   ├── services/
│   │   ├── mail.py          # Flask-Mail integration
│   │   └── ton_price.py     # CoinGecko
│   ├── templates/
│   │   ├── auth/            # login, register, verify
│   │   ├── emails/          # verification_code.html
│   │   ├── admin/
│   │   └── ...
│   └── static/
├── config.py
├── run.py
├── requirements.txt
└── .env.example
```

## 🚀 Кор андохтан (Quick Start)

### 1. Clone ва virtual environment

```bash
git clone https://github.com/safiollohaminov542-commits/fragment-tj.git
cd fragment-tj
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Gmail App Password ҳосил кунед

Барои фиристодани email тавассути Gmail SMTP, App Password лозим:

1. **2-Step Verification фаъол кунед** дар [myaccount.google.com/security](https://myaccount.google.com/security)
2. Ба [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) равед
3. **App name**: `Fragment TJ` → **Create**
4. 16-character password copy кунед (масалан `lwte iydu jnbh exsr`) — фосиларо нест кунед

### 3. `.env` созед

```bash
cp .env.example .env
nano .env
```

Минимум қимматҳои зеринро гузоред:

```ini
SECRET_KEY=ҳосил-кунед-бо-secrets.token_hex(32)
[email protected]
MAIL_PASSWORD=lwteiydujnbhexsr   # бе фосила!
[email protected]
[email protected]   # ҳамин email-и шумо ҳамчун admin
```

> 💡 SECRET_KEY-и random ҳосил кардан:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

### 4. Запуск

```bash
python run.py
```

Сайт дар http://localhost:5000 кушода мешавад.

### 5. Аввалин login ҳамчун admin

1. Ба http://localhost:5000/auth/register равед
2. Email-и худатонро (ҳамон ки дар `ADMIN_EMAILS` гузоштаед) гузоред
3. Email-ро санҷед — code-и 6-рақама аз Gmail хоҳед гирифт
4. Code-ро гузоред → автомат admin мешавед
5. Ба `/admin` равед

## 🔐 Auth Flow

```
Register:
  email + password → 6-digit code → email → verify → ✓ login

Login:
  email + password → 6-digit code → email → verify → ✓ login

Resend:
  cooldown 60s, max 5 attempts per code, 10min lifetime
```

## 🎯 Admin Setup

Ду роҳ admin шудан:

**Роҳи 1**: Email-ро дар `.env` → `ADMIN_EMAILS` гузоред — автомат promotion
```ini
[email protected]
```

**Роҳи 2**: Дар admin panel дастӣ promote кунед — `/admin/users` → "↑ admin"

## 📧 Email Troubleshooting

### Email намерасад / Spam папкаашро тоза кунед
- Spam папкаро санҷед — Gmail баъзан ба он ҷой мегузорад
- Аввалин маротиба эҳтимоли spam зиёд аст. Sender-ро "Not Spam" хабар кунед

### `SMTPAuthenticationError`
- App Password-и нодуруст. Аз нав ҳосил кунед
- Фосиларо нест кунед: `lwte iydu jnbh exsr` → `lwteiydujnbhexsr`

### `[Errno 111] Connection refused`
- Firewall port 465-ро block мекунад
- Альтернатива: TLS port 587-ро санҷед:
  ```ini
  MAIL_PORT=587
  MAIL_USE_TLS=True
  MAIL_USE_SSL=False
  ```

### Email фиристода намешавад дар development
Барои тестинг бе SMTP:
```ini
MAIL_SUPPRESS_SEND=True
```
Code-ҳо дар log нишон дода мешаванд.

## 🌐 Production Deployment

### Gunicorn + Nginx

```bash
gunicorn -w 4 -b 0.0.0.0:8000 'run:app'
```

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

### PostgreSQL

```ini
DATABASE_URL=postgresql://user:password@localhost:5432/fragment_tj
```

```bash
flask db init
flask db migrate -m "init"
flask db upgrade
```

## 🔮 TODO (хусусиятҳои оянда)

- [ ] Forgot password flow
- [ ] User profile editing
- [ ] Telegram Mini App integration
- [ ] Real TON payment integration
- [ ] Multi-language (тоҷикӣ / русӣ / англисӣ)
- [ ] Auction system

## License

MIT
