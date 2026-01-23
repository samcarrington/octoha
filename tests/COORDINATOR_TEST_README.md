# Octoha Data Coordinator Test Suite

## Overview

This document describes the comprehensive test suite for Home Assistant data coordinators in the Octoha integration. The coordinators have been implemented and tests serve as verification of the coordinator functionality.

**Test File:** `tests/test_coordinator.py`

## Test Organization

The test suite is organized into 9 main test classes covering different aspects of the coordinator architecture:

### 1. **TestOctohaBaseCoordinator**

Tests the foundation that all coordinators build upon.

**Scenarios:**

- Base coordinator class extends Home Assistant's `DataUpdateCoordinator`
- Proper initialization with required parameters
- Abstract interface for subclasses

### 2. **TestElectricityCoordinator**

Tests the coordinator that fetches electricity consumption data.

**Key Scenarios:**

- Successful fetch of `Consumption` objects
- 5-minute update interval (`UPDATE_INTERVAL_ELECTRICITY`)
- Data storage in `coordinator.data`
- Error handling for API failures and auth errors

### 3. **TestGasCoordinator**

Tests the coordinator that fetches gas consumption data.

**Key Scenarios:**

- Successful fetch of `GasConsumption` objects with kWh and m³
- 5-minute update interval (`UPDATE_INTERVAL_GAS`)
- Handling of missing meter configuration
- Error handling

### 4. **TestTariffCoordinator**

Tests the coordinator that fetches electricity and gas tariff rates.

**Key Scenarios:**

- Fetches both `Tariff` and `GasTariff` data
- 30-minute update interval (`UPDATE_INTERVAL_TARIFF`)
- Stores both tariff types
- Handles missing tariff data gracefully

### 5. **TestDispatchCoordinator**

Tests the coordinator that fetches Intelligent Octopus dispatch schedules.

**Key Scenarios:**

- Returns `DispatchStatus` with current/upcoming/completed dispatches
- 5-minute update interval (`UPDATE_INTERVAL_DISPATCH`)
- Handles absence of dispatches
- Proper error handling

### 6. **TestCoordinatorIntegration**

Tests how coordinators work together in the system.

**Key Scenarios:**

- Multiple coordinators can run concurrently
- Coordinators notify listeners on data updates
- Failure recovery and retry logic
- Manual refresh via `request_refresh()`

### 7. **TestCoordinatorErrorHandling**

Tests error handling across all coordinators.

**Error Scenarios:**

- `OctopusError` wrapped in `UpdateFailed`
- `AuthenticationError` wrapped in `UpdateFailed`
- Network timeouts
- Rate limiting
- Empty responses

### 8. **TestCoordinatorEdgeCases**

Tests boundary conditions and edge cases.

**Edge Cases:**

- Large datasets (hundreds of records)
- Data gaps/missing points
- Zero consumption values
- Very high consumption values
- Timezone transitions

### 9. **TestCoordinatorConfiguration**

Tests that coordinators are properly configured.

**Configuration Tests:**

- Electricity: 5-minute interval
- Gas: 5-minute interval
- Tariff: 30-minute interval
- Dispatch: 5-minute interval
- Descriptive coordinator names

## Test Count Summary

**Total Test Methods:** 43 tests

- Base Coordinator: 2 tests
- Electricity Coordinator: 6 tests
- Gas Coordinator: 6 tests
- Tariff Coordinator: 6 tests
- Dispatch Coordinator: 6 tests
- Integration: 4 tests
- Error Handling: 5 tests
- Edge Cases: 5 tests
- Configuration: 5 tests

## Implementation Requirements

### 1. Module Structure

```python
# Location: src/custom_components/octoha/coordinator.py

class OctohaBaseCoordinator(DataUpdateCoordinator):
    """Base coordinator for all Octoha coordinators."""

class ElectricityCoordinator(OctohaBaseCoordinator):
    """Fetches electricity consumption every 5 minutes."""

class GasCoordinator(OctohaBaseCoordinator):
    """Fetches gas consumption every 5 minutes."""

class TariffCoordinator(OctohaBaseCoordinator):
    """Fetches tariff data every 30 minutes."""

class DispatchCoordinator(OctohaBaseCoordinator):
    """Fetches dispatch schedules every 5 minutes."""
```

### 2. Error Handling

All coordinators MUST:

- Catch `OctopusError` and `AuthenticationError` from API client
- Wrap errors in `UpdateFailed` exception
- Log errors appropriately
- Allow Home Assistant to manage retry strategy

### 3. Data Storage

Each coordinator MUST:

- Store fetched data in `self.data` attribute
- Initialize with sensible defaults
- Use appropriate types (lists, objects, dicts)

### 4. Update Intervals

| Coordinator | Interval | Constant                      |
| ----------- | -------- | ----------------------------- |
| Electricity | 5 min    | `UPDATE_INTERVAL_ELECTRICITY` |
| Gas         | 5 min    | `UPDATE_INTERVAL_GAS`         |
| Tariff      | 30 min   | `UPDATE_INTERVAL_TARIFF`      |
| Dispatch    | 5 min    | `UPDATE_INTERVAL_DISPATCH`    |

### 5. API Client Integration

```python
# ElectricityCoordinator
await self.client.get_electricity_consumption(periods=48)

# GasCoordinator
await self.client.get_gas_consumption(periods=48)

# TariffCoordinator
await self.client.get_electricity_tariff()
await self.client.get_gas_tariff()
await self.client.get_current_rate()

# DispatchCoordinator
await self.client.get_dispatches()
```

## Test Execution

### Running All Tests

```bash
pytest tests/test_coordinator.py -v
```

### Running Specific Class

```bash
pytest tests/test_coordinator.py::TestElectricityCoordinator -v
```

### Running Specific Test

```bash
pytest tests/test_coordinator.py::TestElectricityCoordinator::test_electricity_coordinator_successful_fetch -v
```

## Implementation Status

The coordinator module has been implemented at `src/custom_components/octoha/coordinator.py`.

Key features implemented:

- Base coordinator with graceful degradation support
- Data staleness tracking
- Failure count and timestamp tracking
- Custom update intervals via options flow

## Test Fixtures

The test suite provides:

- `mock_api_client`: Mocked OctohaApiClient
- `hass_fixture`: Home Assistant test instance
- Sample data fixtures for each model type

## Implementation Notes

- Use `@pytest.mark.asyncio` for async tests
- Import `UpdateFailed` from `homeassistant.helpers.update_coordinator`
- Accept `hass` and `api_client` in constructor
- Use `_LOGGER = logging.getLogger(__name__)` for logging
- Consider `asyncio.gather()` for concurrent API calls

## Related Files

- API Client: `src/custom_components/octoha/api/client.py`
- Data Models: `src/custom_components/octoha/models/`
- Constants: `src/custom_components/octoha/const.py`
- Integration: `src/custom_components/octoha/__init__.py`

---

**Status:** Implemented
**Module:** `src/custom_components/octoha/coordinator.py`
