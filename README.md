# InstaBot 🤖

> AI-powered Instagram automation bot built with FastAPI

[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-61%20passed-success.svg)](tests)

InstaBot is an intelligent Instagram automation platform that leverages AI to generate and publish content, respond to messages, and manage your Instagram presence automatically.

## ✨ Features

- 🤖 **AI-Powered Content Generation**: Create engaging posts using OpenRouter's Gemini models
- 💬 **Automated Messaging**: Respond to Instagram DMs with intelligent AI-generated replies
- 📸 **Image Storage**: Integrated MinIO for scalable image storage
- 🔐 **Secure Authentication**: JWT-based authentication with refresh tokens
- 🐳 **Docker-Ready**: Complete containerized setup with Docker Compose
- 📊 **Comprehensive Testing**: 61 tests covering unit, integration, and API scenarios
- 🚀 **Production-Ready**: Built with industry best practices

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenAI/OpenRouter API key
- Instagram Business Account

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/instabot.git
   cd instabot
   ```

2. **Configure environment**
   ```bash
   cp config/.env.example config/.env
   # Edit config/.env with your credentials
   ```

3. **Start the stack**
   ```bash
   docker compose up --build
   ```

4. **Access the application**
   - API Docs: http://localhost:8000/docs
   - MinIO Console: http://localhost:9001
   - Database: localhost:5432

## 📖 Documentation

Detailed documentation is available in the `docs/` directory:

- **[Architecture](docs/ARCHITECTURE.md)** - System architecture and design patterns
- **[API Reference](docs/API.md)** - Complete API documentation
- **[Development Guide](docs/DEVELOPMENT.md)** - Local development setup
- **[Docker Setup](docs/DOCKER_SETUP.md)** - Docker configuration details
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment instructions
- **[Testing Guide](docs/TESTING.md)** - Running and writing tests
- **[Contributing](docs/CONTRIBUTING.md)** - Contribution guidelines

## 🏗️ Project Structure

```
InstaBot/
├── config/              # Configuration files
│   ├── .env.example     # Environment variables template
│   ├── alembic.ini      # Database migrations config
│   └── pytest.ini       # Test configuration
├── docs/                # Documentation
├── scripts/             # Deployment scripts
├── source/              # Application source code
│   ├── alembic/         # Database migrations
│   ├── api/             # FastAPI routes
│   ├── auth/            # Authentication logic
│   ├── core/            # Core utilities
│   ├── db/              # Database configuration
│   ├── dependencies/    # FastAPI dependencies
│   ├── models/          # SQLAlchemy models
│   ├── repositories/    # Data access layer
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── tests/           # Test suite
│   └── utils/           # Helper utilities
├── docker-compose.yml   # Docker services
├── Dockerfile           # Application container
└── README.md            # This file
```

## 🛠️ Technology Stack

- **Framework**: FastAPI 0.115
- **Database**: PostgreSQL 16 with SQLAlchemy 2.0
- **Storage**: MinIO S3-compatible storage
- **AI**: OpenRouter API (Gemini models)
- **Auth**: JWT with bcrypt
- **Testing**: pytest with async support
- **Migrations**: Alembic
- **Monitoring**: Loguru for structured logging

## 🧪 Testing

Run all tests:
```bash
docker compose exec app pytest -c config/pytest.ini
```

Run specific test types:
```bash
# Unit tests
pytest -c config/pytest.ini source/tests/unit/

# API tests
pytest -c config/pytest.ini source/tests/api/

# Integration tests
pytest -c config/pytest.ini source/tests/integration/
```

Current test coverage: **61/61 tests passing** ✅

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the amazing web framework
- [OpenRouter](https://openrouter.ai/) for AI model access
- [Instagram Graph API](https://developers.facebook.com/docs/instagram-api/) for Instagram integration

## 📞 Support

For support, please open an issue on GitHub or contact the maintainers.

---

**Built with ❤️ using Python and FastAPI**
