# Crypto Assets Management System

A comprehensive Django-based cryptocurrency asset management and notification system that allows users to track their crypto investments and receive real-time price alerts via Telegram.

## 🚀 Features

### 📊 Asset Management
- **Portfolio Tracking**: Monitor your cryptocurrency investments and transactions
- **Multi-Exchange Support**: Integrates with various cryptocurrency exchanges
- **Transaction History**: Keep track of all your buy/sell transactions with detailed analytics

### 🔔 Smart Notifications
- **Price Alerts**: Set custom price thresholds for any cryptocurrency
- **Profit/Loss Notifications**: Get notified when your transactions reach specific profit percentages
- **Telegram Integration**: Receive instant notifications on your Telegram account
- **Real-time Updates**: Price checks every 10 minutes for active notifications

### 💰 Example Use Cases
- **Price Monitoring**: Get notified when Bitcoin reaches $80,000 USD
- **Profit Tracking**: Alert when your 2.5 BNB investment reaches 30% profit
- **Portfolio Management**: Track multiple cryptocurrencies across different exchanges

## 🏗️ Architecture

### Tech Stack
- **Backend**: Django 5.0 with Django REST Framework
- **Database**: PostgreSQL 13.5
- **Cache**: Redis 6.2
- **Task Queue**: Celery with Redis backend
- **Web Server**: Nginx + Gunicorn
- **Containerization**: Docker & Docker Compose

### Core Components
- **Django Apps**:
  - `asset`: Portfolio and asset management
  - `exchange`: Cryptocurrency exchange integrations
  - `notification`: Alert and notification system
  - `user`: User management and Telegram integration

## 🛠️ Installation & Setup

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- PostgreSQL
- Redis

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd crypto_assets
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the services**
   ```bash
   docker-compose up -d
   ```

4. **Run migrations**
   ```bash
   docker-compose exec crypto_assets_api python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   docker-compose exec crypto_assets_api python manage.py createsuperuser
   ```

### Local Development Setup

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up database**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. **Start development server**
   ```bash
   python manage.py runserver
   ```

## 🔧 Configuration

### Environment Variables
Create a `.env` file with the following variables:

```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/crypto_assets
REDIS_URL=redis://localhost:6379/0
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TIME_ZONE=Asia/Tehran
```

### Telegram Bot Setup
1. Create a bot via [@BotFather](https://t.me/botfather)
2. Get your bot token
3. Add the token to your `.env` file
4. Users can start the bot and link their accounts

## 📱 Usage

### Telegram Integration
- **Official Channel**: [@eye_on_crypto](https://t.me/eye_on_crypto)
- **Price Updates**: Automatic price checks every 10 minutes
- **Custom Alerts**: Set personalized notifications for your portfolio

### Admin Panel
- **URL**: [https://crypto.m-gh.com/secret-admin/](https://crypto.m-gh.com/secret-admin/)
- **Features**: Manage users, transactions, notifications, and system settings

## 📊 Monitoring & Logs

### Nginx Logs
```bash
# Access logs
/var/log/nginx/api-crypto_assets_access.log

# Error logs
/var/log/nginx/api-crypto_assets_error.log
```

### Application Logs
```bash
# Located in the logs directory
./logs/
```

## 🧪 Development

### Code Quality
```bash
# Format code
make format-python

# Lint code
make lint-python

# Run tests
make test-python
```

### Available Make Commands
- `make install-dev-tools`: Set up development environment
- `make format`: Format all code
- `make lint`: Run linting checks
- `make test`: Run all tests

## 🐳 Docker Services

The application runs with the following Docker services:

- **crypto_assets_db**: PostgreSQL database
- **crypto_assets_api**: Django application server
- **crypto_assets_celery**: Celery worker for background tasks
- **crypto_assets_beat**: Celery beat scheduler
- **crypto_assets_redis**: Redis cache and message broker

## 📈 API Endpoints

The system provides REST API endpoints for:
- Asset management
- Transaction tracking
- Notification settings
- User management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- **Telegram Channel**: [@eye_on_crypto](https://t.me/eye_on_crypto)
- **Issues**: Create an issue on the repository
- **Documentation**: Check the inline code documentation
