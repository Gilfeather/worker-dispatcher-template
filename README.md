# Worker Dispatcher Template

A comprehensive FastAPI template implementing Domain-Driven Design (DDD) and Clean Architecture principles with a Worker-Dispatcher pattern for asynchronous task processing.

## 🏗️ Architecture Overview

This template follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│           Presentation Layer            │
│  (FastAPI routes, controllers, logic)   │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│            Domain Layer                 │
│   (Entities, Services, Business Logic)  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Infrastructure Layer            │
│  (Database, External APIs, Adapters)    │
└─────────────────────────────────────────┘
```

### Core Principles

- **Dependency Inversion**: Domain layer defines interfaces, infrastructure implements them
- **Single Responsibility**: Each module has a clear, focused purpose
- **Open/Closed**: Easy to extend without modifying existing code
- **Interface Segregation**: Small, focused interfaces rather than large ones

## 🚀 Features

- **Worker-Dispatcher Pattern**: Scalable asynchronous task processing
- **Clean Architecture**: Proper separation of concerns and dependency inversion
- **FastAPI Integration**: Modern async web framework with automatic API documentation
- **Pydantic Models**: Type-safe data validation and serialization
- **Database Integration**: SQLAlchemy with PostgreSQL support
- **External Service Adapters**: AWS S3, Slack, Google Cloud Platform, Amazon Marketing Cloud
- **Docker Support**: Multi-stage builds and docker-compose setup
- **Comprehensive Testing**: Unit tests, integration tests, and test utilities
- **Database Migrations**: Alembic for database schema management
- **Monitoring & Health Checks**: Built-in health checks and monitoring endpoints

## 📁 Project Structure

```
worker-dispatcher-template/
├── app/
│   ├── domain/                 # Domain layer
│   │   ├── entities.py         # Core business entities
│   │   ├── enums.py           # Domain enumerations
│   │   └── services/          # Domain services and interfaces
│   ├── infrastructure/        # Infrastructure layer
│   │   ├── db/               # Database models and repositories
│   │   ├── aws/              # AWS service adapters
│   │   ├── slack/            # Slack integration
│   │   ├── gcp/              # Google Cloud Platform adapters
│   │   ├── amc/              # Amazon Marketing Cloud adapter
│   │   └── exceptions/       # Custom exceptions
│   └── presentation/         # Presentation layer
│       ├── interface.py      # FastAPI application setup
│       └── logic/           # API routes and schemas
├── worker/                   # Worker implementation
├── tests/                    # Test suite
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── e2e/                 # End-to-end tests
├── alembic/                 # Database migrations
├── docker-compose.yml       # Docker services
├── Dockerfile              # Application container
├── Dockerfile.worker       # Worker container
├── pyproject.toml          # Poetry configuration
└── README.md              # This file
```

## 🏃 Quick Start

### Prerequisites

- Python 3.9+
- Poetry (for dependency management)
- Docker & Docker Compose
- PostgreSQL (or use Docker)

### Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd worker-dispatcher-template
```

2. **Install dependencies**:
```bash
poetry install
```

3. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Start services with Docker Compose**:
```bash
docker-compose up -d
```

5. **Run database migrations**:
```bash
poetry run alembic upgrade head
```

6. **Access the application**:
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Dispatch Endpoints: http://localhost:8000/dispatch/
- Work Endpoints: http://localhost:8000/work/

### Manual Setup (without Docker)

1. **Start PostgreSQL**:
```bash
# Using Docker
docker run -d --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15

# Or install locally
```

2. **Set environment variables**:
```bash
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/worker_dispatcher"
export REDIS_URL="redis://localhost:6379"
```

3. **Run the application**:
```bash
poetry run uvicorn app.presentation.interface:app --reload
```

4. **Test the dispatch/work workflow**:
```bash
poetry run python example_usage.py
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:password@localhost:5432/worker_dispatcher` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `AWS_ACCESS_KEY_ID` | AWS access key | - |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | - |
| `AWS_DEFAULT_REGION` | AWS region | `us-east-1` |
| `SLACK_BOT_TOKEN` | Slack bot token | - |
| `SLACK_WEBHOOK_URL` | Slack webhook URL | - |
| `GCP_PROJECT_ID` | Google Cloud Project ID | - |
| `WORKER_NAME` | Worker instance name | `worker-1` |
| `WORKER_CAPABILITIES` | Worker capabilities (comma-separated) | `general` |

### Database Configuration

The application uses Alembic for database migrations. To create a new migration:

```bash
poetry run alembic revision --autogenerate -m "Description of changes"
poetry run alembic upgrade head
```

## 📊 API Endpoints

### Dispatch Endpoints (Task Distribution)

- `POST /dispatch/task` - Dispatch a new task
- `POST /dispatch/task/bulk` - Dispatch multiple tasks
- `POST /dispatch/assign` - Manually assign task to worker
- `GET /dispatch/queue/status` - Get queue status
- `GET /dispatch/available-workers` - Get available workers
- `POST /dispatch/schedule` - Trigger task processing
- `GET /dispatch/stats` - Get dispatch statistics

### Work Endpoints (Task Processing)

- `POST /work/register` - Register as a worker
- `GET /work/next-task` - Get next task to process
- `POST /work/complete-task` - Mark task as completed
- `POST /work/fail-task` - Mark task as failed
- `POST /work/heartbeat` - Send worker heartbeat
- `GET /work/status/{worker_id}` - Get worker status
- `POST /work/process-tasks` - Start continuous task processing
- `POST /work/stop-processing` - Stop task processing
- `GET /work/my-tasks/{worker_id}` - Get worker's task history
- `GET /work/capabilities` - Get available capabilities

### Traditional REST API (Optional)

- `POST /api/v1/tasks/` - Create a new task
- `GET /api/v1/tasks/` - List tasks with filtering
- `GET /api/v1/tasks/{task_id}` - Get specific task
- `PUT /api/v1/tasks/{task_id}` - Update task
- `DELETE /api/v1/tasks/{task_id}` - Delete task
- `POST /api/v1/workers/` - Register a new worker
- `GET /api/v1/workers/` - List workers with filtering

### Monitoring

- `GET /api/v1/monitoring/health` - System health status
- `GET /api/v1/monitoring/queue/statistics` - Queue statistics
- `GET /api/v1/monitoring/workers/statistics` - Worker statistics
- `GET /api/v1/monitoring/metrics` - Comprehensive metrics
- `GET /api/v1/monitoring/dashboard` - Dashboard data

## 🧪 Testing

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/unit/domain/test_entities.py

# Run integration tests
poetry run pytest tests/integration/
```

### Test Structure

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows

### Test Configuration

The test suite uses:
- `pytest` for test framework
- `pytest-asyncio` for async test support
- `pytest-cov` for coverage reporting
- Mock objects for external dependencies

## 🔌 External Service Integration

### AWS S3

```python
from app.infrastructure.s3.adapter import S3Adapter

s3_adapter = S3Adapter(region_name="us-east-1")
url = await s3_adapter.upload_file("local_file.txt", "bucket-name", "key")
```

### Slack

```python
from app.infrastructure.slack.adapter import SlackAdapter

slack_adapter = SlackAdapter(bot_token="xoxb-your-token")
await slack_adapter.send_message("#general", "Hello from Worker Dispatcher!")
```

### Google Cloud Platform

```python
from app.infrastructure.gcp.adapter import GCPAdapter

gcp_adapter = GCPAdapter(project_id="your-project-id")
await gcp_adapter.storage.upload_blob("bucket", "local_file.txt", "remote_file.txt")
```

## 📈 Monitoring and Observability

### Health Checks

The application provides comprehensive health checks:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/monitoring/health
```

### Metrics

Access detailed metrics at:

```bash
curl http://localhost:8000/api/v1/monitoring/metrics
```

### Logging

The application uses structured logging with correlation IDs for request tracking.

## 🚢 Deployment

### Docker Deployment

1. **Build images**:
```bash
docker-compose build
```

2. **Deploy services**:
```bash
docker-compose up -d
```

3. **Scale workers**:
```bash
docker-compose up -d --scale worker=5
```

### Production Considerations

- Use proper environment variables for production
- Configure database connection pooling
- Set up proper logging aggregation
- Implement monitoring and alerting
- Use a reverse proxy (Nginx) for production
- Configure auto-scaling for workers

## 🔒 Security

### Best Practices Implemented

- No hardcoded secrets or credentials
- Environment variable configuration
- Input validation with Pydantic
- SQL injection prevention with SQLAlchemy
- CORS configuration
- Rate limiting (via Nginx)
- Security headers

### Security Headers

The Nginx configuration includes:
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer-Policy

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Development Setup

```bash
# Install development dependencies
poetry install --with dev

# Install pre-commit hooks
poetry run pre-commit install

# Run linting
poetry run black .
poetry run isort .
poetry run flake8 .
poetry run mypy .
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

1. Check the documentation
2. Review existing issues
3. Create a new issue with detailed information
4. Include logs and error messages

## 🎯 Roadmap

- [ ] Add Redis caching layer
- [ ] Implement circuit breaker pattern
- [ ] Add GraphQL API support
- [ ] Implement task scheduling with cron expressions
- [ ] Add webhook notifications
- [ ] Implement task dependencies
- [ ] Add performance monitoring
- [ ] Create dashboard UI
- [ ] Add multi-tenant support
- [ ] Implement audit logging

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Docker Documentation](https://docs.docker.com/)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)