# AngryVPN-Telegram-Bot

A modular, production-ready Telegram bot for managing VPN subscriptions, users, payments, and admin functions. Supports English and Persian localization, multiple admin roles, and integrates with payment gateways.

---

## 🚀 Features

- **User Management**: Register, purchase, and manage VPN accounts
- **Admin & Org Admin Panels**: Manage users, organizations, servers, and announcements
- **Payment Integration**: Supports Zarinpal, crypto (TRON), Stripe, and manual payments
- **Localization**: English and Persian, with easy translation updates
- **Ticketing**: Users can submit support tickets to admins
- **Stats & Monitoring**: Usage, wallet, and server status reporting
- **Modular Architecture**: Clean, maintainable codebase with helpers split by domain
- **GitHub Automation**: Automated issue management and project tools

## 👥 Roles

- **User**: Register, purchase, recharge, view usage, submit tickets
- **Admin**: Manage all users, servers, payments, send announcements
- **Org Admin**: Manage users and servers within their organization

---

## 📁 Project Structure

```
AngryVPN-Telegram-Bot/
├── bot.py                          # Main entry point
├── helpers/                        # Modular business logic
│   ├── client/                     # Client-side functions
│   │   ├── charge.py              # Account charging logic
│   │   ├── crypto.py              # Cryptocurrency payments
│   │   └── purchase/              # Payment processing
│   │       ├── __init__.py        # Payment orchestration
│   │       ├── rial.py            # Rial payment methods
│   │       ├── crypto.py          # Crypto payment methods
│   │       └── stripe.py          # Stripe integration (planned)
│   ├── org_admin/                  # Organization admin functions
│   │   ├── __init__.py            # Package initialization
│   │   ├── members.py             # Member management
│   │   ├── servers.py             # Server management
│   │   ├── announcements.py       # Announcement system
│   │   ├── charging.py            # Admin charging functions
│   │   └── utils.py               # Admin utilities
│   ├── bot_functions.py           # Core bot functionality
│   ├── commands.py                # Command handlers
│   ├── main_admin.py              # Main admin functions
│   ├── states.py                  # Conversation states
│   ├── xuiAPI.py                  # X-UI panel integration
│   └── utils.py                   # Utility functions
├── payment/                        # Payment integration
├── locales/                        # Translation files
├── scripts/                        # Automation scripts
│   └── github/                     # GitHub automation tools
│       ├── create_all_issues.py   # Master issue creation
│       ├── create_*_issues.py     # Category-specific scripts
│       ├── create_missing_labels.py # Label management
│       └── summary.py             # Issue summary tool
├── Dockerfile                      # Container configuration
├── docker-compose.yml             # Docker orchestration
├── req.txt                        # Python dependencies
└── LICENSE                        # Polyform Noncommercial License
```

---

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/rasoulbsd/AngryVPN-Telegram-Bot.git
cd AngryVPN-Telegram-Bot
```

### 2. Install dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r req.txt
```

---

## ⚙️ Configuration

### 1. Environment Variables (.env file)
```bash
# Create .env file in project root
BOT_TOKEN=your_telegram_bot_token
DBConString=mongodb://localhost:27017
DBName=angryvpn
secret_file=secrets.json
```

### 2. Secrets Configuration (secrets.json)
```json
{
  "DBConString": "mongodb://localhost:27017",
  "DBName": "angryvpn",
  "BOT_USERNAME": "YourBotUsername",
  "ZARINPAL_MERCHANT_ID": "your_zarinpal_merchant_id",
  "STRIPE_SECRET_KEY": "your_stripe_secret_key",
  "ticket_topic_id": 123456,
  "payments_topic_id": 123456,
  "test_topic_id": 123456
}
```

---

## 🚀 Running the Bot

### Local Development
```bash
python bot.py
```

### Docker Deployment
```bash
docker-compose up --build
```

---

## 🧪 Testing & Quality

### Run Tests
```bash
pytest
```

### Code Quality
```bash
# Install Ruff for linting and formatting
pip install ruff

# Run linting and auto-fix
ruff check --fix .

# Format code
ruff format .
```

---

## 🌐 Localization

- Translation files are in `helpers/locales/`
- Supports English (`en`) and Persian (`fa`)
- To update translations:
  1. Edit `.po` files in `helpers/locales/{lang}/LC_MESSAGES/`
  2. Compile with: `msgfmt file.po -o file.mo`
  3. Or use tools like Poedit

---

## 🤖 GitHub Automation

The project includes automated GitHub tools for issue management:

### Available Scripts
- `scripts/github/create_all_issues.py` - Create all project issues
- `scripts/github/create_*_issues.py` - Category-specific issue creation
- `scripts/github/create_missing_labels.py` - Label management
- `scripts/github/summary.py` - Issue summary and reporting

### Usage
```bash
# Create all issues with deduplication
python scripts/github/create_all_issues.py

# View issue summary
python scripts/github/summary.py

# Create missing labels
python scripts/github/create_missing_labels.py
```

---

## 📋 Recent Improvements

### v1.1.0 - Code Modularization & GitHub Tools
- **Modular Architecture**: Split monolithic files into domain-specific modules
- **Payment Modularization**: Organized payment methods by type (rial, crypto, stripe)
- **Admin Modularization**: Separated org admin functions into focused modules
- **GitHub Automation**: Added comprehensive issue management tools
- **Deduplication**: Smart issue creation that prevents duplicates
- **Enhanced Documentation**: Updated structure and configuration guides

### Planned Features
- **Stripe Integration**: International payment processing
- **E-Transfer Support**: Email-based payment method
- **Alternative Infrastructure**: Web dashboard for restricted users
- **Enhanced Monitoring**: Real-time bot performance tracking
- **Advanced Security**: Rate limiting and DDoS protection

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Follow the modular architecture patterns
4. Add tests for new functionality
5. Update documentation as needed
6. Submit a pull request

### Development Guidelines
- Keep code modular and focused on single responsibilities
- Add proper error handling and logging
- Follow the existing naming conventions
- Update issue tracking for new features
- Test thoroughly before submitting

---

## 📄 License

This project is licensed under the **Polyform Noncommercial License 1.0.0**.

### License Terms
- **Commercial use is prohibited** unless licensed by AngryDevs Technologies Inc.
- For licensing inquiries, contact: info@angrydevs.ca
- See [LICENSE](LICENSE) file for full terms

### What This Means
- ✅ **Personal use**: You can use this for personal projects
- ✅ **Educational use**: You can study and learn from the code
- ✅ **Non-commercial projects**: Open source, research, etc.
- ❌ **Commercial use**: Requires separate licensing from AngryDevs Technologies Inc.

---

## 📞 Support

- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Documentation**: Check the code comments and this README
- **Commercial Licensing**: Contact info@angrydevs.ca

---

## 🙏 Acknowledgments

- Built with [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- Payment integrations with Zarinpal, TRON, and Stripe
- Modular architecture inspired by clean code principles
- GitHub automation tools for efficient project management