# Testing Guide for Octoha Home Assistant Integration

This document outlines the testing processes, infrastructure, and best practices for the Octoha Home Assistant custom integration.

## Table of Contents

1. [Overview](#overview)
2. [Testing Stack](#testing-stack)
3. [Project Structure](#project-structure)
4. [Running Tests](#running-tests)
5. [Test Categories](#test-categories)
6. [Fixtures and Mocking](#fixtures-and-mocking)
7. [Home Assistant Testing Patterns](#home-assistant-testing-patterns)
8. [CI/CD Pipeline](#cicd-pipeline)
9. [Coverage Requirements](#coverage-requirements)
10. [Adding New Tests](#adding-new-tests)
11. [Snapshot Testing](#snapshot-testing)
12. [Troubleshooting](#troubleshooting)

---

## Overview

The Octoha integration uses a comprehensive testing strategy that includes:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **Config Flow Tests**: Test the Home Assistant setup UI
- **Coordinator Tests**: Test data update coordinators
- **API Client Tests**: Test external API communication
- **Sensor/Entity Tests**: Test Home Assistant entity behavior

### Testing Philosophy

We follow Test-Driven Development (TDD) principles:
1. **Red**: Write failing tests that define expected behavior
2. **Green**: Implement code to make tests pass
3. **Refactor**: Improve code while maintaining test coverage

---

## Testing Stack

### Core Dependencies

| Package | Purpose | Version |
|---------|---------|---------|
| `pytest` | Test framework | >= 7.0.0 |
| `pytest-asyncio` | Async test support | >= 0.21.0 |
| `pytest-cov` | Coverage reporting | >= 4.0.0 |
| `pytest-homeassistant-custom-component` | HA testing utilities | >= 0.13.0 |
| `aioresponses` | HTTP mocking for aiohttp | >= 0.7.0 |
| `homeassistant` | HA core for testing | >= 2024.1.0 |

### Installation

```bash
# Create virtual environment (recommended)
python3.11 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or: venv\Scripts\activate  # On Windows

# Install development dependencies
pip install -e ".[dev]"
```

### Alternative: Using uv (faster)

```bash
# Install uv if not available
pip install uv

# Install dependencies
uv pip install -e ".[dev]"
```

---

## Project Structure

```plaintext
octopus-ha/
├── src/
│   └── custom_components/
│       └── octoha/              # Integration source code
│           ├── api/             # API client layer
│           ├── models/          # Data models
│           ├── __init__.py      # Entry point
│           ├── config_flow.py   # Setup UI
│           ├── coordinator.py   # Data coordinators
│           ├── sensor.py        # Sensor entities
│           └── binary_sensor.py # Binary sensor entities
│
├── tests/                       # Test suite
│   ├── fixtures/                # JSON response fixtures
│   │   ├── account_response.json
│   │   ├── auth_token_response.json
│   │   ├── electricity_consumption_response.json
│   │   ├── gas_consumption_response.json
│   │   ├── electricity_rates_response.json
│   │   └── ...
│   ├── conftest.py              # Shared pytest fixtures
│   ├── test_api_client.py       # API client tests
│   ├── test_auth.py             # Authentication tests
│   ├── test_config_flow.py      # Config flow tests
│   ├── test_coordinator.py      # Coordinator tests
│   ├── test_sensors.py          # Sensor entity tests
│   ├── test_binary_sensors.py   # Binary sensor tests
│   ├── test_consumption.py      # Consumption model tests
│   ├── test_tariff.py           # Tariff model tests
│   └── TEST_SUMMARY.md          # Test documentation
│
└── pyproject.toml               # Project configuration
```

---

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_api_client.py

# Run specific test class
pytest tests/test_sensors.py::TestElectricityConsumptionSensor

# Run specific test method
pytest tests/test_sensors.py::TestElectricityConsumptionSensor::test_native_value_returns_latest_consumption

# Run tests matching a pattern
pytest -k "electricity"
```

### With Coverage

```bash
# Run with coverage report
pytest --cov=src/custom_components/octoha --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=src/custom_components/octoha --cov-report=html
# Open htmlcov/index.html in browser

# Generate XML coverage report (for CI)
pytest --cov=src/custom_components/octoha --cov-report=xml
```

### Debugging Tests

```bash
# Stop at first failure
pytest -x

# Show print statements
pytest -s

# Enter debugger on failure
pytest --pdb

# Run last failed tests
pytest --lf

# Show slowest 10 tests
pytest --duration=10
```

---

## Test Categories

### 1. API Client Tests (`test_api_client.py`)

Tests for the Octopus Energy API client:

```python
class TestOctohaApiClient:
    """Tests for OctohaApiClient class."""

    @pytest.mark.asyncio
    async def test_validate_credentials_success(self, client, mock_response_factory):
        """Test validate_credentials returns True for valid key."""
        mock_response = mock_response_factory(status=200, json_data=auth_response)
        client._session.post.return_value = mock_response
        
        result = await client.validate_credentials()
        
        assert result is True
```

**Test coverage includes:**
- Credential validation (success/failure)
- Account data retrieval
- Electricity/gas consumption fetching
- Tariff and rate data
- Dispatch schedule retrieval
- Error handling (auth errors, network errors, rate limiting)
- Response caching

### 2. Config Flow Tests (`test_config_flow.py`)

Tests for the Home Assistant setup UI:

```python
@pytest.mark.asyncio
async def test_user_step_success_single_meter(self, hass, mock_api_client):
    """Test successful user step with single meter account."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: api_key}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
```

**Test coverage includes:**
- Form display and validation
- API key validation
- Meter discovery
- Multi-meter selection flow
- Duplicate account detection
- Error handling (invalid key, connection errors)

### 3. Coordinator Tests (`test_coordinator.py`)

Tests for data update coordinators:

```python
class TestElectricityCoordinator:
    """Tests for ElectricityCoordinator."""

    @pytest.mark.asyncio
    async def test_successful_data_fetch(self, hass, mock_api_client):
        """Test successful electricity consumption data fetch."""
        mock_api_client.get_electricity_consumption.return_value = sample_data
        
        coordinator = ElectricityCoordinator(hass, mock_api_client)
        await coordinator.async_config_entry_first_refresh()
        
        assert coordinator.data.consumption == sample_data
```

**Test coverage includes:**
- Data fetching (electricity, gas, tariff, dispatch)
- Update intervals (5 min for consumption, 30 min for tariff)
- Error handling and `UpdateFailed` wrapping
- Listener notifications
- Recovery from failures

### 4. Sensor Tests (`test_sensors.py`)

Tests for Home Assistant sensor entities:

```python
class TestElectricityConsumptionSensor:
    """Tests for ElectricityConsumptionSensor."""

    def test_native_value_returns_latest_consumption(self, coordinator, entry):
        """Test native_value returns the most recent consumption reading."""
        sensor = ElectricityConsumptionSensor(
            coordinator=coordinator,
            entry=entry,
            mpan="1234567890123",
        )
        assert sensor.native_value == 0.75  # Latest reading
```

**Test coverage includes:**
- `native_value` calculation
- Unit of measurement
- Device class and state class
- Extra state attributes
- Availability based on coordinator state
- Device info grouping

### 5. Model Tests (`test_consumption.py`, `test_tariff.py`)

Tests for data models:

```python
class TestConsumption:
    """Tests for Consumption model."""

    def test_consumption_from_api_response(self):
        """Test creating Consumption from API response."""
        data = {"consumption": 1.5, "interval_start": "2026-01-18T00:00:00Z"}
        consumption = Consumption.from_api_response(data)
        
        assert consumption.consumption == 1.5
```

---

## Fixtures and Mocking

### Shared Fixtures (`conftest.py`)

```python
@pytest.fixture
def api_key() -> str:
    """Return a test API key."""
    return "sk_test_abc123def456"

@pytest.fixture
def account_number() -> str:
    """Return a test account number."""
    return "A-FB05ED6C"

@pytest.fixture
def load_fixture(fixtures_path: Path):
    """Load a JSON fixture file."""
    def _load(filename: str) -> dict:
        filepath = fixtures_path / filename
        with open(filepath) as f:
            return json.load(f)
    return _load

@pytest.fixture
def mock_response_factory():
    """Factory for creating mock aiohttp responses."""
    def _create(status: int = 200, json_data: dict = None):
        response = MagicMock()
        response.status = status
        response.json = AsyncMock(return_value=json_data or {})
        response.__aenter__ = AsyncMock(return_value=response)
        response.__aexit__ = AsyncMock(return_value=None)
        return response
    return _create
```

### Using pytest-homeassistant-custom-component

The `pytest-homeassistant-custom-component` package provides fixtures from Home Assistant core:

```python
# Available fixtures:
# - hass: HomeAssistant instance
# - enable_custom_integrations: Required for custom component testing

@pytest.mark.asyncio
async def test_with_hass(hass: HomeAssistant):
    """Test using the hass fixture."""
    # hass is a fully functional Home Assistant instance
    assert hass is not None
```

### Mocking HTTP Requests

For API client tests, use `aioresponses` or manual mocking:

```python
from aioresponses import aioresponses

@pytest.mark.asyncio
async def test_api_call():
    """Test with aioresponses."""
    with aioresponses() as m:
        m.get("https://api.octopus.energy/...", payload={"data": "value"})
        
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.octopus.energy/...") as resp:
                data = await resp.json()
                assert data == {"data": "value"}
```

---

## Home Assistant Testing Patterns

### 1. Config Entry Testing

```python
from pytest_homeassistant_custom_component.common import MockConfigEntry

@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "api_key": "test_key",
            "account": "A-12345",
        },
        entry_id="test_entry_id",
    )

async def test_setup_entry(hass, mock_config_entry):
    """Test setting up the integration."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
```

### 2. Entity State Testing

```python
async def test_sensor_state(hass, mock_config_entry):
    """Test sensor entity state."""
    # Setup integration
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    
    # Get entity state via the state machine
    state = hass.states.get("sensor.electricity_consumption")
    assert state is not None
    assert state.state == "1.5"
    assert state.attributes["unit_of_measurement"] == "kWh"
```

### 3. Service Call Testing

```python
async def test_service_call(hass):
    """Test calling a service."""
    await hass.services.async_call(
        "homeassistant",
        "update_entity",
        {"entity_id": "sensor.electricity_consumption"},
        blocking=True,
    )
```

### 4. Device Registry Testing

```python
from homeassistant.helpers import device_registry as dr

async def test_device_registered(hass, mock_config_entry):
    """Test device is registered correctly."""
    device_registry = dr.async_get(hass)
    device = device_registry.async_get_device(
        identifiers={(DOMAIN, "account_id")}
    )
    assert device is not None
    assert device.manufacturer == "Octopus Energy"
```

---

## CI/CD Pipeline

### GitHub Actions Workflows

#### Test Workflow (`.github/workflows/test.yml`)

```yaml
name: Test

on:
  push:
    branches: [main, feat/*, fix/*]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: pip install -e ".[dev]"
      
      - name: Run tests with coverage
        run: pytest --cov=src/custom_components/octoha --cov-report=xml
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        if: matrix.python-version == '3.11'
```

#### Lint Workflow (`.github/workflows/lint.yml`)

```yaml
name: Lint

on: [push, pull_request]

jobs:
  ruff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Ruff
        run: |
          pip install ruff
          ruff check src tests
          ruff format --check src tests

  mypy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run mypy
        run: |
          pip install -e ".[dev]"
          mypy src/custom_components/octoha
```

### Pre-commit Hooks (Optional)

Add `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest tests/ -x -q
        language: system
        pass_filenames: false
        always_run: true
```

---

## Coverage Requirements

### Minimum Coverage Targets

| Component | Target | Current |
|-----------|--------|---------|
| API Client | 90% | - |
| Config Flow | 85% | - |
| Coordinators | 90% | - |
| Sensors | 85% | - |
| Binary Sensors | 85% | - |
| Models | 95% | - |
| **Overall** | **85%** | - |

### Coverage Configuration (`pyproject.toml`)

```toml
[tool.coverage.run]
source = ["src/custom_components/octoha"]
omit = ["*/tests/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
]
```

---

## Adding New Tests

### Test File Template

```python
"""Tests for [component name].

Description of what this test module covers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.octoha.const import DOMAIN


class TestComponentName:
    """Tests for ComponentName."""

    @pytest.fixture
    def mock_dependency(self) -> MagicMock:
        """Create a mock dependency."""
        return MagicMock()

    def test_happy_path(self, mock_dependency):
        """Test the happy path scenario."""
        # Arrange
        expected_value = "expected"
        
        # Act
        result = component_function(mock_dependency)
        
        # Assert
        assert result == expected_value

    def test_error_handling(self, mock_dependency):
        """Test error handling."""
        mock_dependency.method.side_effect = Exception("Error")
        
        with pytest.raises(Exception):
            component_function(mock_dependency)

    @pytest.mark.asyncio
    async def test_async_operation(self, hass: HomeAssistant):
        """Test async operation."""
        result = await async_function(hass)
        assert result is not None
```

### Test Naming Conventions

```python
# Pattern: test_[unit]_[scenario]_[expected_result]

def test_sensor_native_value_returns_consumption():
    """Test that sensor native_value returns consumption value."""
    pass

def test_coordinator_api_failure_raises_update_failed():
    """Test that API failure raises UpdateFailed."""
    pass

def test_config_flow_invalid_key_shows_error():
    """Test that invalid API key shows error message."""
    pass
```

---

## Snapshot Testing

### Snapshot Overview

Snapshot testing compares output against stored reference values. Useful for:

- Entity state validation
- Registry entry verification
- Diagnostic output testing

### Setup

Add to `conftest.py`:

```python
from pytest_homeassistant_custom_component.syrupy import HomeAssistantSnapshotExtension
from syrupy.assertion import SnapshotAssertion

@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture with Home Assistant extension."""
    return snapshot.use_extension(HomeAssistantSnapshotExtension)
```

### Usage

```python
async def test_sensor_state_snapshot(hass, snapshot):
    """Test sensor state matches snapshot."""
    state = hass.states.get("sensor.electricity_consumption")
    assert state == snapshot
```

### Updating Snapshots

```bash
# Update all snapshots
pytest --snapshot-update

# Update specific test snapshots
pytest tests/test_sensors.py --snapshot-update
```

---

## Troubleshooting

### Common Issues

#### 1. Import Errors

```bash
ModuleNotFoundError: No module named 'custom_components.octoha'
```

**Solution**: Ensure `pythonpath = ["src"]` is in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
pythonpath = ["src"]
```

#### 2. Async Test Issues

```bash
RuntimeWarning: coroutine was never awaited
```

**Solution**: Ensure `asyncio_mode = "auto"` in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

#### 3. Missing `hass` Fixture

```bash
fixture 'hass' not found
```

**Solution**: Ensure `pytest-homeassistant-custom-component` is installed:

```bash
pip install pytest-homeassistant-custom-component>=0.13.0
```

#### 4. Custom Component Not Loading

**Solution**: Add `enable_custom_integrations` fixture:

```python
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield
```

#### 5. Timezone Issues

```python
# Always use timezone-aware datetimes
from datetime import datetime, timezone

now = datetime.now(timezone.utc)  # Good
now = datetime.now()  # Bad - naive datetime
```

### Debug Tips

1. **Use `-s` flag** to see print output:
   ```bash
   pytest -s tests/test_sensors.py
   ```

2. **Use `--pdb`** to drop into debugger on failure:
   ```bash
   pytest --pdb tests/test_sensors.py
   ```

3. **Add breakpoints** in code:
   ```python
   import pdb; pdb.set_trace()
   ```

4. **Check fixture values** with pytest debug:
   ```bash
   pytest --fixtures
   ```

---

## References

- [Home Assistant Developer Docs - Testing](https://developers.home-assistant.io/docs/development_testing)
- [pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component)
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [Home Assistant Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/)

---

## Appendix: Test Checklist for New Features

When adding a new feature, ensure you have tests for:

- [ ] Happy path / success case
- [ ] Error handling (API errors, validation errors)
- [ ] Edge cases (empty data, null values, extreme values)
- [ ] Boundary conditions (rate limits, timeouts)
- [ ] State transitions (available/unavailable)
- [ ] Entity attributes
- [ ] Device info
- [ ] Config flow changes (if applicable)
- [ ] Coordinator updates (if applicable)

---

*Last updated: January 2026*
