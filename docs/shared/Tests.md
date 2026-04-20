# Testing Guidelines

The project uses `pytest` as the primary testing framework. Our testing strategy covers unit tests for core logic, integration tests for decorators and registration, and end-to-end (E2E) tests for the API.

## Core Testing Principles

1.  **Isolation**: Use fixtures to ensure tests are isolated and don't share state.
2.  **Explicit Cleanup**: Always clean global registries (e.g., `Shield` registry, `RouteRegistry`) between tests.
3.  **Dependency Mocking**: Use `fastapi_injectable` or standard mocking to replace external dependencies (DB, external APIs).

---

## Unit Testing

Unit tests focus on individual components like services, resolvers, and core libraries.

### Example: Testing a Shield Resolver
Use mock providers to simulate different authorization states.

```python
import pytest
from core.security.shield import ResolverProvider

class MockProvider(ResolverProvider):
    def __init__(self, allowed: bool):
        self.allowed = allowed
    def resolve(self, **kwargs) -> bool:
        return self.allowed

def test_shield_allows_execution():
    provider = MockProvider(allowed=True)
    # Perform assertion
    ...
```

### Registry Cleanup
The project provides a `clean_registry` fixture pattern to ensure tests start with a fresh state.

```python
@pytest.fixture(autouse=True)
def clean_registry():
    from core.security.shield.registry import permission_registry
    permission_registry.clear()
    yield
    permission_registry.clear()
```

---

## Integration and E2E Testing

### Testing Route Registration
You can verify that custom decorators are correctly injecting metadata and dependencies.

```python
def test_decorator_injects_metadata():
    from src.api.health.controller import HealthController
    # Assert that __route_definition__ is present on the handler
    assert hasattr(HealthController.ping, "__route_definition__")
```

### Mocking with `fastapi_injectable`
One of the most powerful testing features is the ability to resolve dependencies within service logic using the `fastapi_injectable` mocking mechanism. This allows you to test code that uses `Depends()` without needing a live FastAPI server for every test.

### E2E with TestClient
Use FastAPI's `TestClient` for full request/response cycle testing.

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_api_ping():
    response = client.get("/api/v1/health/ping")
    assert response.status_code == 200
```

---

## Running Tests

Run tests using the following command from the root directory:

```bash
pytest
```

To run a specific test file:

```bash
pytest core/tests/test_shield.py
```
