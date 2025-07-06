# Overmind Client Tests

This directory contains the test suite for the Overmind Python client, organized by functionality.

## Test Structure

The tests have been refactored into separate files for better organization and maintainability:

### Core Test Files

- **`test_client_main.py`** - Tests for the main `OvermindClient` class functionality
  - Client initialization
  - Dynamic provider access
  - Provider method chaining
  - API request handling
  - Error handling
  - Invoke method

- **`test_agents.py`** - Tests for the `AgentsClient` subclient
  - Creating agents
  - Listing agents
  - Getting specific agents
  - Deleting agents

- **`test_policies.py`** - Tests for the `PoliciesClient` subclient
  - Creating policies
  - Listing policies
  - Getting specific policies
  - Deleting policies

- **`test_invocations.py`** - Tests for the `InvocationsClient` subclient
  - Listing invocations
  - Getting specific invocations
  - Filtering invocations by agent

- **`test_models.py`** - Tests for Pydantic models
  - `AgentCreateRequest` validation
  - `PolicyCreateRequest` validation
  - Model field validation

- **`test_client.py`** - Integration tests
  - End-to-end workflow testing
  - Component integration verification

### Configuration

- **`conftest.py`** - Shared pytest fixtures and configuration
  - Common client instances
  - Mock response objects
  - Reusable test data

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test files
```bash
# Run only main client tests
pytest test_client_main.py

# Run only agent tests
pytest test_agents.py

# Run only policy tests
pytest test_policies.py

# Run only invocation tests
pytest test_invocations.py

# Run only model tests
pytest test_models.py

# Run only integration tests
pytest test_client.py
```

### Run tests with coverage
```bash
pytest --cov=overmind_client
```

### Run tests with verbose output
```bash
pytest -v
```

## Test Organization Benefits

1. **Separation of Concerns**: Each test file focuses on a specific component
2. **Easier Maintenance**: Changes to one component only affect its specific test file
3. **Better Discoverability**: Easy to find tests for specific functionality
4. **Faster Test Execution**: Can run only relevant tests during development
5. **Shared Fixtures**: Common test setup is centralized in `conftest.py`

## Adding New Tests

When adding new functionality:

1. **For new subclients**: Create a new test file following the naming convention `test_<subclient_name>.py`
2. **For new models**: Add tests to `test_models.py`
3. **For shared fixtures**: Add to `conftest.py`
4. **For integration scenarios**: Add to `test_client.py`

## Mock Strategy

Tests use `unittest.mock` to mock HTTP requests, ensuring:
- Tests don't make actual API calls
- Predictable test behavior
- Fast test execution
- No external dependencies

Each test file includes appropriate mock responses for the specific API endpoints being tested. 