# FastAPI Large Application Template 🚀

A production-ready template for building scalable FastAPI applications with modular architecture and essential integrations.

## Project Structure 🌳

<!-- TREE_START -->
```
.
├── app
│   ├── health
│   │   └── health_router.py
│   ├── user
│   │   ├── user_auth.py
│   │   ├── user_crud.py
│   │   ├── user_model.py
│   │   ├── user_router.py
│   │   ├── user_schema.py
│   │   └── user_service.py
│   ├── utils
│   │   └── helper.py
│   ├── database.py
│   └── settings.py
├── CONTRIBUTORS.txt
├── Dockerfile
├── README.md
├── gunicorn_conf.py
├── main.py
├── requirements.txt
├── run.sh
├── set_env.sh
└── tree.txt

5 directories, 19 files
```
<!-- TREE_END -->


## Features

- JWT-based authentication system
- Modular architecture with separation of concerns
- PostgreSQL database integration
- Health check endpoint
- Docker containerization support
- Environment configuration management
- Production-ready server configuration

## Technologies

- Python 3.9+
- FastAPI
- SQLAlchemy (ORM)
- PostgreSQL
- Docker
- Gunicorn + Uvicorn

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL database
- Docker (optional)

## API Documentation

Interactive documentation is available at `/docs` endpoint after starting the server:
- Swagger UI: `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`
- OpenAPI schema: `http://localhost:8000/openapi.json`

## Contributing

See [CONTRIBUTORS.txt](CONTRIBUTORS.txt) for contribution guidelines and code of conduct.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.
