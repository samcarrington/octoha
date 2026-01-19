# Testing Infrastructure Recommendations

This document provides recommendations for improving the testing infrastructure of the Octoha Home Assistant integration.

## Current State Summary

### Existing Test Coverage

| Test File | Lines | Purpose |
|-----------|-------|---------|
| `test_api_client.py` | ~1,571 | API client tests |
| `test_api_client_daily_usage.py` | ~721 | Daily usage aggregation |
| `test_config_flow.py` | ~888 | Config flow tests |
| `test_sensors.py` | ~706 | Sensor entity tests |
| `test_coordinator.py` | ~622 | Coordinator tests |
| `test_binary_sensors.py` | ~389 | Binary sensor tests |
| `test_tariff.py` | ~313 | Tariff model tests |
| `test_consumption.py` | ~282 | Consumption model tests |
| `test_auth.py` | ~214 | Authentication tests |
| **Total** | **~5,700** | |

### Existing CI/CD

- GitHub Actions for testing (Python 3.11 + 3.12)
- GitHub Actions for linting (Ruff + mypy)
- Codecov integration for coverage reporting

---

## Recommended Improvements

### 1. Enhanced Test Fixtures

#### Add `enable_custom_integrations` Fixture

The `pytest-homeassistant-custom-component` package requires this fixture for HA 2021.6.0+:

```python
# tests/conftest.py

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Automatically enable custom integrations for all tests."""
    yield
```

#### Add Mock Config Entry Fixture

```python
# tests/conftest.py

from pytest_homeassistant_custom_component.common import MockConfigEntry

@pytest.fixture
def mock_config_entry(api_key, account_number, mpan, mprn, meter_serial, gas_meter_serial):
    """Create a mock config entry for testing."""
    return MockConfigEntry(
        domain="octoha",
        title=account_number,
        data={
            "api_key": api_key,
            "account": account_number,
            "mpan": mpan,
            "mprn": mprn,
            "meter_serial": meter_serial,
            "gas_meter_serial": gas_meter_serial,
        },
        entry_id="test_entry_id",
        unique_id=account_number,
    )
```

#### Add Snapshot Testing Fixture

```python
# tests/conftest.py

from pytest_homeassistant_custom_component.syrupy import HomeAssistantSnapshotExtension
from syrupy.assertion import SnapshotAssertion

@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture with Home Assistant extension."""
    return snapshot.use_extension(HomeAssistantSnapshotExtension)
```

### 2. Additional Test Categories

#### Integration Tests

Create `tests/test_integration.py` for end-to-end tests:

```python
"""End-to-end integration tests."""

@pytest.mark.asyncio
async def test_full_setup_and_operation(hass, mock_config_entry):
    """Test complete integration lifecycle."""
    # 1. Setup entry
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    
    # 2. Verify entities created
    states = hass.states.async_all()
    entity_ids = [s.entity_id for s in states]
    assert "sensor.octoha_electricity_consumption" in entity_ids
    
    # 3. Trigger update
    await hass.services.async_call(
        "homeassistant", "update_entity",
        {"entity_id": "sensor.octoha_electricity_consumption"},
        blocking=True,
    )
    
    # 4. Unload entry
    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
```

#### Diagnostic Tests

Create `tests/test_diagnostics.py` for diagnostic output:

```python
"""Tests for integration diagnostics."""

from custom_components.octoha.diagnostics import async_get_config_entry_diagnostics

@pytest.mark.asyncio
async def test_diagnostics_redacts_api_key(hass, mock_config_entry):
    """Test that diagnostics redacts sensitive data."""
    diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)
    
    assert "api_key" not in str(diagnostics)
    assert "REDACTED" in str(diagnostics)
```

### 3. Test Organization Improvements

#### Use Test Categories with Markers

```python
# tests/conftest.py

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks integration tests")
    config.addinivalue_line("markers", "api: marks API-related tests")
```

Usage:
```python
@pytest.mark.slow
@pytest.mark.integration
async def test_large_data_handling(hass):
    """Test handling of large datasets."""
    pass
```

Run by category:
```bash
pytest -m "not slow"  # Skip slow tests
pytest -m "api"       # Run only API tests
```

### 4. Performance Testing

Add performance benchmarks:

```python
# tests/test_performance.py

import time

@pytest.mark.slow
async def test_coordinator_update_performance(hass, mock_api_client):
    """Test coordinator update completes within acceptable time."""
    start = time.time()
    
    coordinator = ElectricityCoordinator(hass, mock_api_client)
    await coordinator.async_config_entry_first_refresh()
    
    elapsed = time.time() - start
    assert elapsed < 1.0, f"Update took {elapsed}s, expected < 1s"
```

### 5. Error Scenario Testing

Expand error scenario coverage:

```python
# tests/test_error_scenarios.py

class TestNetworkErrors:
    """Test network error handling."""

    @pytest.mark.asyncio
    async def test_timeout_handling(self, client):
        """Test handling of request timeouts."""
        client._session.post.side_effect = asyncio.TimeoutError()
        
        with pytest.raises(OctopusError) as exc_info:
            await client.validate_credentials()
        
        assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, client, mock_response_factory):
        """Test handling of rate limiting (429)."""
        mock_response = mock_response_factory(status=429)
        client._session.post.return_value = mock_response
        
        with pytest.raises(OctopusError) as exc_info:
            await client.validate_credentials()
        
        assert "rate limit" in str(exc_info.value).lower()
```

### 6. CI/CD Enhancements

#### Add Test Matrix Enhancements

```yaml
# .github/workflows/test.yml

jobs:
  test:
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
        ha-version: ["2024.1.0", "2024.6.0", "latest"]
    
    steps:
      - name: Install specific HA version
        run: pip install homeassistant==${{ matrix.ha-version }}
        if: matrix.ha-version != 'latest'
```

#### Add Nightly Testing

```yaml
# .github/workflows/nightly.yml

name: Nightly Tests

on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM daily

jobs:
  test-latest-ha:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install latest HA
        run: pip install homeassistant
      - name: Run tests
        run: pytest
```

#### Add PR Coverage Check

```yaml
# .github/workflows/test.yml

- name: Check coverage threshold
  run: |
    pytest --cov=src/custom_components/octoha --cov-fail-under=80
```

### 7. Documentation

#### Add Test Documentation Badge

Add to `README.md`:

```markdown
[![Tests](https://github.com/samcarrington/octoha/actions/workflows/test.yml/badge.svg)](https://github.com/samcarrington/octoha/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/samcarrington/octoha/branch/main/graph/badge.svg)](https://codecov.io/gh/samcarrington/octoha)
```

### 8. Pre-commit Hooks

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
      - id: pytest-check
        name: pytest-check
        entry: pytest tests/ -x -q --tb=short
        language: system
        types: [python]
        pass_filenames: false
        always_run: true
```

Install:
```bash
pip install pre-commit
pre-commit install
```

---

## Implementation Priority

### High Priority (Do First)
1. Add `enable_custom_integrations` fixture
2. Add `mock_config_entry` fixture  
3. Add integration tests for full lifecycle
4. Set up coverage threshold in CI (80%)

### Medium Priority
5. Add diagnostic tests
6. Add error scenario tests
7. Add test markers for categorization
8. Set up pre-commit hooks

### Low Priority (Nice to Have)
9. Add performance benchmarks
10. Add HA version matrix testing
11. Add nightly testing workflow
12. Add snapshot testing for entity states

---

## Quick Start Checklist

- [ ] Update `conftest.py` with recommended fixtures
- [ ] Add `enable_custom_integrations` fixture (autouse)
- [ ] Add `mock_config_entry` fixture
- [ ] Create `tests/test_integration.py`
- [ ] Add coverage threshold to CI (`--cov-fail-under=80`)
- [ ] Add test markers to `pyproject.toml`
- [ ] Set up pre-commit hooks
- [ ] Add badges to README

---

*Last updated: January 2026*
