# FastAPI Large Application Template 🚀

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)

A production-ready template for building scalable FastAPI applications with modular architecture and essential integrations.

## Features ✨

- **JWT Authentication** with refresh tokens 🔒
- **Custom Rate Limiting** per user/service ⏱️
- **Unified Logging** (UVICORN + GUNICORN) 📝
- **Redis Connection Pooling** with fail-open strategy 🧠
- **PostgreSQL Connection Pooling** with health checks 🐘
- **Standardized API Responses** 📦
- **Production-Ready Error Handling** 🛡️
- **Docker** + **Gunicorn** + **Uvicorn** Stack 🐳⚡

## Tech Stack 🛠️

| Component              | Technology                          |
|------------------------|-------------------------------------|
| Framework              | FastAPI 0.111+                      |
| Database               | PostgreSQL 14+                      |
| Cache                  | Redis 6+                            |
| ORM                    | SQLAlchemy 2.0                      |
| Authentication         | JWT (OAuth2 Password Bearer)        |
| Rate Limiting          | Redis-backed Custom Implementation  |
| Containerization       | Docker + Docker Compose             |

## Project Structure 🌳

<!-- TREE_START -->
```
.
├── app
│   ├── health
│   │   └── health_router.py
│   ├── todo
│   │   ├── todo_crud.py
│   │   ├── todo_model.py
│   │   ├── todo_router.py
│   │   ├── todo_schema.py
│   │   └── todo_service.py
│   ├── user
│   │   ├── user_auth.py
│   │   ├── user_crud.py
│   │   ├── user_model.py
│   │   ├── user_router.py
│   │   ├── user_schema.py
│   │   └── user_service.py
│   ├── utils
│   │   ├── auth_dependency.py
│   │   ├── helper.py
│   │   └── rate_limiter.py
│   ├── database.py
│   └── settings.py
├── docs
│   └── swagger-screenshot.png
├── CONTRIBUTORS.txt
├── Dockerfile
├── LICENSE
├── README.md
├── gunicorn_conf.py
├── main.py
├── requirements.txt
├── run.sh
├── set_env.sh
└── tree.txt

7 directories, 28 files
```
<!-- TREE_END -->


## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL 14+
- Redis 6+
- Docker (optional)

### Installation

```bash
git clone https://github.com/yourrepo/fastapi-template.git
cd fastapi-template
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuration

1. Create `.env` from template:
```bash
cp .env.example .env
```

2. Set environment variables:
```bash
source set_env.sh  # Sets DB, Redis, and JWT settings
```

### Running

**Development:**
```bash
python main.py
```

**Production:**
```bash
./run.sh  # Starts Gunicorn with Uvicorn workers
```

## API Documentation 📚

Access interactive docs after starting server:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

![API Documentation Preview](docs/swagger-screenshot.png)

## Contributing

See [CONTRIBUTORS.txt](CONTRIBUTORS.txt) for contribution guidelines and code of conduct.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.
