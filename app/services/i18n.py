"""Simple i18n — Tajik (default) + Russian.

Истифода:
    {{ t('site.tagline') }}
    Дар Python: from app.services.i18n import t; t('nav.home')
"""
from flask import session, request

DEFAULT_LANG = "tg"
SUPPORTED_LANGS = ("tg", "ru")

TRANSLATIONS = {
    # === Common ===
    "site.tagline": {
        "tg": "Маркетплейси Telegram Gifts",
        "ru": "Маркетплейс Telegram Gifts",
    },
    "common.search": {"tg": "Ҷустуҷӯ", "ru": "Поиск"},
    "common.save": {"tg": "Захира", "ru": "Сохранить"},
    "common.cancel": {"tg": "Бекор", "ru": "Отмена"},
    "common.delete": {"tg": "Нест кардан", "ru": "Удалить"},
    "common.edit": {"tg": "Тағйир", "ru": "Редактировать"},
    "common.back": {"tg": "Бозгашт", "ru": "Назад"},
    "common.confirm": {"tg": "Тасдиқ", "ru": "Подтвердить"},
    "common.yes": {"tg": "Ҳа", "ru": "Да"},
    "common.no": {"tg": "Не", "ru": "Нет"},
    "common.loading": {"tg": "Боргузорӣ...", "ru": "Загрузка..."},
    "common.optional": {"tg": "ихтиёрӣ", "ru": "необязательно"},
    "common.required": {"tg": "ҳатмӣ", "ru": "обязательно"},

    # === Nav ===
    "nav.home": {"tg": "Асосӣ", "ru": "Главная"},
    "nav.gifts": {"tg": "Gifts", "ru": "Подарки"},
    "nav.about": {"tg": "Дар бораи мо", "ru": "О нас"},
    "nav.profile": {"tg": "Профил", "ru": "Профиль"},
    "nav.wallet": {"tg": "Кошелёк", "ru": "Кошелёк"},
    "nav.inventory": {"tg": "Гифтҳои ман", "ru": "Мои подарки"},
    "nav.orders": {"tg": "Заказҳо", "ru": "Заказы"},
    "nav.admin": {"tg": "Admin Panel", "ru": "Админ"},
    "nav.logout": {"tg": "Баромад", "ru": "Выйти"},
    "nav.login": {"tg": "Login", "ru": "Войти"},
    "nav.register": {"tg": "Сабтнома", "ru": "Регистрация"},

    # === Auth ===
    "auth.login.title": {"tg": "Хуш омадед", "ru": "Добро пожаловать"},
    "auth.login.subtitle": {
        "tg": "Бо ҳисоби худ ворид шавед",
        "ru": "Войдите в свою учётную запись",
    },
    "auth.email": {"tg": "Email", "ru": "Email"},
    "auth.password": {"tg": "Password", "ru": "Пароль"},
    "auth.password_confirm": {"tg": "Тасдиқи Password", "ru": "Подтвердите пароль"},
    "auth.name": {"tg": "Ном", "ru": "Имя"},
    "auth.button.login": {"tg": "Login", "ru": "Войти"},
    "auth.button.register": {"tg": "Ҳисоб эҷод кунед", "ru": "Создать учётную запись"},
    "auth.no_account": {"tg": "Ҳоло ҳисоб надоред?", "ru": "Ещё нет аккаунта?"},
    "auth.have_account": {"tg": "Аллакай ҳисоб доред?", "ru": "Уже есть аккаунт?"},
    "auth.create_account": {"tg": "Ҳисоб созед", "ru": "Создайте"},
    "auth.register.title": {"tg": "Ҳисоб эҷод кунед", "ru": "Создать аккаунт"},
    "auth.register.subtitle": {
        "tg": "Бо email сабт шавед — зуд ва осон",
        "ru": "Регистрация по email — быстро и просто",
    },
    "auth.verify.title": {"tg": "Email-и худро санҷед", "ru": "Проверьте email"},
    "auth.verify.code": {"tg": "Коди тасдиқ", "ru": "Код подтверждения"},
    "auth.verify.button": {"tg": "Тасдиқ кардан", "ru": "Подтвердить"},
    "auth.verify.resend": {"tg": "Кодро аз нав фиристед", "ru": "Отправить код снова"},
    "auth.passwords_match": {"tg": "Password-ҳо мутобиқанд", "ru": "Пароли совпадают"},
    "auth.passwords_differ": {"tg": "Password-ҳо фарқ мекунанд", "ru": "Пароли не совпадают"},

    # === Wallet ===
    "wallet.title": {"tg": "Кошелёк", "ru": "Кошелёк"},
    "wallet.balance": {"tg": "Баланс", "ru": "Баланс"},
    "wallet.total_balance": {"tg": "Баланси умумӣ", "ru": "Общий баланс"},
    "wallet.convert": {"tg": "Convert", "ru": "Конвертация"},
    "wallet.transactions": {"tg": "Транзаксияҳо", "ru": "Транзакции"},
    "wallet.from": {"tg": "Аз", "ru": "Из"},
    "wallet.to": {"tg": "Ба", "ru": "В"},
    "wallet.amount": {"tg": "Маблағ", "ru": "Сумма"},
    "wallet.you_get": {"tg": "Шумо мегиред", "ru": "Вы получите"},
    "wallet.empty": {"tg": "Ҳоло транзаксия нест", "ru": "Пока нет транзакций"},
    "wallet.topup_message": {
        "tg": "Барои зиёд кардани балансатон бо admin тамос гиред",
        "ru": "Для пополнения баланса свяжитесь с администратором",
    },

    # === Gifts ===
    "gifts.title": {"tg": "Тамоми Gifts", "ru": "Все подарки"},
    "gifts.featured": {"tg": "Тавсияшуда", "ru": "Рекомендуемые"},
    "gifts.latest": {"tg": "Нав", "ru": "Новые"},
    "gifts.see_all": {"tg": "Ҳамаро дидан", "ru": "Все"},
    "gifts.buy": {"tg": "Харидан", "ru": "Купить"},
    "gifts.buy_with_balance": {"tg": "Харидан бо balance", "ru": "Купить со счёта"},
    "gifts.sold_out": {"tg": "Дастрас нест", "ru": "Распродано"},
    "gifts.available": {"tg": "Дастрас", "ru": "В наличии"},
    "gifts.empty": {"tg": "Ҳоло gift нест", "ru": "Подарков пока нет"},
    "gifts.search_placeholder": {"tg": "Ҷустуҷӯ...", "ru": "Поиск..."},
    "gifts.collection": {"tg": "Коллексия", "ru": "Коллекция"},
    "gifts.all_collections": {"tg": "Ҳамаи коллексияҳо", "ru": "Все коллекции"},
    "gifts.sort.newest": {"tg": "Аз нав", "ru": "Новые"},
    "gifts.sort.price_asc": {"tg": "Нарх ↑", "ru": "Цена ↑"},
    "gifts.sort.price_desc": {"tg": "Нарх ↓", "ru": "Цена ↓"},
    "gifts.model": {"tg": "Модел", "ru": "Модель"},
    "gifts.backdrop": {"tg": "Замина", "ru": "Фон"},
    "gifts.symbol": {"tg": "Аломат", "ru": "Узор"},
    "gifts.issued": {"tg": "Чопшуда", "ru": "Выпущено"},
    "gifts.owner": {"tg": "Сохиб", "ru": "Владелец"},
    "gifts.no_results": {"tg": "Натиҷа ёфт нашуд", "ru": "Ничего не найдено"},

    # === Inventory ===
    "inventory.title": {"tg": "Гифтҳои ман", "ru": "Мои подарки"},
    "inventory.empty": {"tg": "Шумо ҳоло gift надоред", "ru": "У вас пока нет подарков"},
    "inventory.transfer": {"tg": "Гузарондан", "ru": "Передать"},
    "inventory.acquired": {"tg": "Харида шуд", "ru": "Получен"},
    "inventory.status.owned": {"tg": "Дар ихтиёр", "ru": "В наличии"},
    "inventory.status.transfer_pending": {"tg": "Дар интизор", "ru": "В ожидании"},
    "inventory.status.transferred": {"tg": "Гузаронда шуд", "ru": "Передан"},

    # === Transfer ===
    "transfer.title": {"tg": "Гузарондан ба Telegram", "ru": "Передать в Telegram"},
    "transfer.username": {"tg": "Telegram Username", "ru": "Telegram Username"},
    "transfer.username_help": {
        "tg": "@username-и Telegram-и худатонро ё гирандаро гузоред",
        "ru": "@username получателя в Telegram",
    },
    "transfer.note": {"tg": "Қайд (ихтиёрӣ)", "ru": "Заметка (необязательно)"},
    "transfer.submit": {"tg": "Заявка фиристодан", "ru": "Отправить заявку"},
    "transfer.success": {
        "tg": "Заявка ба admin фиристода шуд. Дар муддати кӯтоҳ gift гузаронда мешавад.",
        "ru": "Заявка отправлена администратору. В скором времени подарок будет передан.",
    },
    "transfer.status.pending": {"tg": "Дар интизор", "ru": "В ожидании"},
    "transfer.status.approved": {"tg": "Қабул шуд", "ru": "Одобрено"},
    "transfer.status.sent": {"tg": "Гузаронда шуд", "ru": "Передан"},
    "transfer.status.rejected": {"tg": "Рад шуд", "ru": "Отклонено"},

    # === Buy / Order ===
    "buy.confirm_title": {"tg": "Тасдиқи харид", "ru": "Подтверждение покупки"},
    "buy.balance_in": {"tg": "Аз balance дар", "ru": "Со счёта в"},
    "buy.insufficient": {
        "tg": "Balance-и кофӣ нест",
        "ru": "Недостаточно средств",
    },
    "buy.success": {
        "tg": "Gift харидорӣ шуд! Дар инвентар ҳозир аст.",
        "ru": "Подарок куплен! Он в вашем инвентаре.",
    },

    # === Profile ===
    "profile.title": {"tg": "Профили ман", "ru": "Мой профиль"},
    "profile.edit": {"tg": "Тағйири профил", "ru": "Редактировать профиль"},
    "profile.telegram_username": {"tg": "Telegram", "ru": "Telegram"},
    "profile.preferred_language": {"tg": "Забон", "ru": "Язык"},
    "profile.preferred_currency": {"tg": "Валюта", "ru": "Валюта"},
}


def get_locale() -> str:
    """Aзии session, query (?lang=...), ё default."""
    lang = request.args.get("lang") if request else None
    if lang in SUPPORTED_LANGS:
        session["lang"] = lang
        return lang
    if "lang" in session and session["lang"] in SUPPORTED_LANGS:
        return session["lang"]
    return DEFAULT_LANG


def t(key: str, lang: str = None) -> str:
    """Translation helper."""
    if lang is None:
        try:
            lang = get_locale()
        except RuntimeError:
            lang = DEFAULT_LANG
    entry = TRANSLATIONS.get(key)
    if entry:
        return entry.get(lang) or entry.get(DEFAULT_LANG) or key
    return key


def install_i18n(app):
    """Регистратсияи `t` дар Jinja templates."""
    @app.context_processor
    def inject_i18n():
        try:
            current_lang = get_locale()
        except Exception:
            current_lang = DEFAULT_LANG
        return {
            "t": t,
            "current_lang": current_lang,
            "supported_langs": SUPPORTED_LANGS,
        }
