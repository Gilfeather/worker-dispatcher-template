# Contributing to Worker Dispatcher Template

Thank you for your interest in contributing to the Worker Dispatcher Template! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues

1. **Check existing issues** first to avoid duplicates
2. **Use the issue template** when creating new issues
3. **Provide detailed information** including:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Relevant logs or error messages

### Submitting Pull Requests

1. **Fork the repository** and create a feature branch
2. **Follow the coding standards** (see below)
3. **Write tests** for new functionality
4. **Update documentation** as needed
5. **Ensure all tests pass**
6. **Submit a pull request** with a clear description

## 🏗️ Development Setup

### Prerequisites

- Python 3.9+
- Poetry
- Docker & Docker Compose
- Git

### Setup Steps

1. **Clone your fork**:
```bash
git clone https://github.com/YOUR_USERNAME/worker-dispatcher-template.git
cd worker-dispatcher-template
```

2. **Install dependencies**:
```bash
make dev-install
# or
poetry install --with dev
poetry run pre-commit install
```

3. **Start development environment**:
```bash
make dev
# or
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

4. **Run tests**:
```bash
make test
# or
poetry run pytest
```

## 📝 Coding Standards

### Code Style

We use the following tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pre-commit**: Git hooks

### Running Code Quality Checks

```bash
# Format code
make format

# Run all checks
make lint

# Fix issues automatically
poetry run black .
poetry run isort .
```

### Code Guidelines

1. **Follow PEP 8** style guidelines
2. **Use type hints** for all function parameters and return values
3. **Write docstrings** for all public functions and classes
4. **Keep functions small** and focused on a single responsibility
5. **Use meaningful variable and function names**
6. **Follow the existing project structure**

### Example Code Style

```python
from typing import Optional, List, Dict, Any
from datetime import datetime

async def process_task(
    task_id: str, 
    worker_id: str, 
    payload: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Process a task with the given parameters.
    
    Args:
        task_id: Unique identifier for the task
        worker_id: Identifier of the worker processing the task
        payload: Task data and configuration
        
    Returns:
        Processing result or None if failed
        
    Raises:
        TaskProcessingException: If task processing fails
    """
    # Implementation here
    pass
```

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for component interactions
├── e2e/           # End-to-end tests for complete workflows
└── conftest.py    # Shared test fixtures and configuration
```

### Writing Tests

1. **Write tests for all new functionality**
2. **Use descriptive test names** that explain what is being tested
3. **Follow the AAA pattern**: Arrange, Act, Assert
4. **Use fixtures** for common test setup
5. **Mock external dependencies** in unit tests
6. **Test both success and failure scenarios**

### Example Test

```python
import pytest
from app.domain.entities import Task, TaskId
from app.domain.enums import TaskStatus, TaskPriority

class TestTask:
    def test_task_creation_with_valid_data(self):
        # Arrange
        task_name = "Test Task"
        priority = TaskPriority.HIGH
        
        # Act
        task = Task(name=task_name, priority=priority)
        
        # Assert
        assert task.name == task_name
        assert task.priority == priority
        assert task.status == TaskStatus.PENDING
    
    def test_task_validation_with_empty_name(self):
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="Task name cannot be empty"):
            Task(name="   ")
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test file
poetry run pytest tests/unit/domain/test_entities.py

# Run tests in watch mode
make test-watch
```

## 📚 Documentation

### Code Documentation

1. **Write docstrings** for all public APIs
2. **Include type information** in docstrings
3. **Provide usage examples** for complex functions
4. **Document exceptions** that may be raised

### Project Documentation

1. **Update README.md** for new features
2. **Add usage examples** to USAGE_EXAMPLES.md
3. **Update API documentation** for new endpoints
4. **Include migration guides** for breaking changes

## 🏷️ Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Format

```
<type>(<scope>): <description>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or modifying tests
- `chore`: Maintenance tasks

### Examples

```
feat(dispatch): add bulk task dispatch endpoint

Add new endpoint /dispatch/task/bulk for dispatching multiple tasks
in a single request. Includes validation and error handling.

Closes #123

fix(worker): resolve heartbeat timeout issue

Workers were not properly updating heartbeat timestamps,
causing them to be marked as offline prematurely.

test(entities): add comprehensive task entity tests

Add tests for task creation, validation, and business logic
methods to improve coverage.
```

## 🔄 Release Process

### Version Management

We use [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Steps

1. **Update version** in `pyproject.toml`
2. **Update CHANGELOG.md** with release notes
3. **Create release branch**: `release/v1.2.3`
4. **Run full test suite**
5. **Create pull request** to main branch
6. **Tag release** after merge: `git tag v1.2.3`
7. **Create GitHub release** with release notes

## 🐛 Debugging

### Local Development

1. **Use debugger**: Set breakpoints in your IDE
2. **Enable debug logging**: Set `LOG_LEVEL=DEBUG`
3. **Use Docker logs**: `docker-compose logs -f app`
4. **Check health endpoints**: `/health`, `/api/v1/monitoring/health`

### Common Issues

1. **Database connection errors**: Check PostgreSQL is running
2. **Import errors**: Ensure virtual environment is activated
3. **Test failures**: Check test database is clean
4. **Docker build issues**: Clear Docker cache with `make docker-clean`

## 📋 Pull Request Checklist

Before submitting a pull request, ensure:

- [ ] Code follows project style guidelines
- [ ] All tests pass locally
- [ ] New functionality includes tests
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] No sensitive information is committed
- [ ] Breaking changes are documented
- [ ] Performance impact is considered

## 🎯 Areas for Contribution

We welcome contributions in these areas:

### High Priority
- Bug fixes and stability improvements
- Performance optimizations
- Test coverage improvements
- Documentation enhancements

### Medium Priority
- New adapter implementations (Redis, RabbitMQ, etc.)
- Monitoring and observability features
- Security enhancements
- API improvements

### Low Priority
- UI dashboard development
- Additional deployment options
- Integration examples
- Performance benchmarks

## 💬 Getting Help

If you need help:

1. **Check the documentation** first
2. **Search existing issues** for similar problems
3. **Ask in discussions** for general questions
4. **Create an issue** for bugs or feature requests
5. **Join our community** discussions

## 🏆 Recognition

Contributors will be recognized in:

- **CONTRIBUTORS.md** file
- **Release notes** for significant contributions
- **GitHub contributors** section

Thank you for contributing to the Worker Dispatcher Template! 🎉