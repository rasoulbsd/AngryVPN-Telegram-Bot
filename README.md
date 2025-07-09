# AngryVPN-Telegram-Bot

A modular, production-ready Telegram bot for managing VPN subscriptions, users, payments, and admin functions. Supports English and Persian localization, multiple admin roles, and integrates with payment gateways.

---

## Features

- **User Management**: Register, purchase, and manage VPN accounts.
- **Admin & Org Admin Panels**: Manage users, organizations, servers, and announcements.
- **Payment Integration**: Supports Zarinpal, crypto (TRON), and manual payments.
- **Localization**: English and Persian, with easy translation updates.
- **Ticketing**: Users can submit support tickets to admins.
- **Stats & Monitoring**: Usage, wallet, and server status reporting.
- **Modular Helpers**: Clean, maintainable codebase with helpers split by domain.

## Roles

- **User**: Register, purchase, recharge, view usage, submit tickets.
- **Admin**: Manage all users, servers, payments, send announcements.
- **Org Admin**: Manage users and servers within their organization.

---

## Project Structure (Key Parts)

- `bot.py` — Main entry point for the Telegram bot.
- `helpers/` — All business logic, modularized:
  - `client/` — Submodules: `server.py`, `user.py`, `ticket.py`, `purchase.py`, `crypto.py`, `charge.py`
  - `bot_functions.py`, `commands.py`, `main_admin.py`, `org_admin.py`, `states.py`, `xuiAPI.py`, `utils.py`
- `payment/` — Payment integration logic.
- `locales/` — Translation files (.po/.mo) for English and Persian.
- `Dockerfile`, `docker-compose.yml` — For containerized deployment.
- `req.txt` — Python dependencies.

---

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/AngryVPN-Telegram-Bot.git
cd AngryVPN-Telegram-Bot
```

### 2. Install dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r req.txt
```

---

## Configuration

### 1. .env file (create in project root)
```
# .env example
BOT_TOKEN=your_telegram_bot_token
DBConString=mongodb://localhost:27017
DBName=angryvpn
secret_file=secrets.json
# Add any other environment variables as needed
```

### 2. secrets.json (create in project root)
```
{
  "DBConString": "mongodb://localhost:27017",
  "DBName": "angryvpn",
  "BOT_USERNAME": "YourBotUsername",
  "ZARINPAL_MERCHANT_ID": "your_zarinpal_merchant_id",
  "ticket_topic_id": 123456,
  "payments_topic_id": 123456,
  "test_topic_id": 123456,
  "other_secret_keys": "..."
}
```

---

## Running the Bot

### Locally
```bash
python bot.py
```

### With Docker
```bash
docker-compose up --build
```

---

## Testing

Run all tests with:
```bash
pytest
```

---

## Localization

- All translation files are in `helpers/locales/`.
- To add or update translations, edit the `.po` files and recompile with `msgfmt` or use a tool like Poedit.
- Supports English (`en`) and Persian (`fa`).

---

## Contributing

Pull requests and issues are welcome! Please keep code modular and add tests for new features.

---

## License

See [LICENSE](LICENSE).