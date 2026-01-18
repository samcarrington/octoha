# Octoha Implementation Plan

## 1. Title

Octoha - Home Assistant Octopus Energy Integration Implementation

## 2. Short description

Implement a Home Assistant custom integration that provides accurate gas and electricity consumption data from Octopus Energy's APIs, replacing the broken Bright/SMETS integration. Delivers automation-ready entities, Intelligent Go dispatch support, and HA Energy Dashboard compatibility.

## 3. Current status

```yaml
owner: Sam Carrington <octopus@gwawr.co.uk>
state: proposed
last_updated: 2026-01-18
blockers: []
```

## 4. Objectives

1. Deliver accurate smart meter data within Home Assistant, with gas readings matching the Smart Meter IHD exactly
2. Expose electricity and gas consumption as HA entities compatible with the Energy Dashboard
3. Support Intelligent Octopus Go dispatch schedules for EV charging automation
4. Provide a seamless config flow UI for API key entry, validation, and reconfiguration
5. Follow Home Assistant official integration patterns for maintainability and potential future core submission
6. Release as open-source on GitHub with comprehensive documentation

## 5. Success criteria

| Name                  | Metric                                                | Target       | Verification                                    |
| --------------------- | ----------------------------------------------------- | ------------ | ----------------------------------------------- |
| Gas Accuracy          | Daily gas readings vs IHD display                     | 100% match   | Manual comparison over 7 days                   |
| Electricity Freshness | Time lag between consumption and entity update        | < 1 hour     | Compare entity `last_updated` vs API timestamps |
| Entity Availability   | Time from config completion to all entities available | < 30 minutes | Automated integration test                      |
| Integration Stability | Unhandled exceptions in continuous operation          | 0 in 7 days  | Monitor HA logs during beta                     |
| Setup Experience      | Time from integration add to working dashboard        | < 5 minutes  | Manual timing during testing                    |
| Test Coverage         | Unit test coverage for API client and coordinators    | > 80%        | pytest-cov report                               |

## 6. Scope

```yaml
in:
  - API client for Octopus Energy GraphQL and REST APIs (extracted/adapted from open-octopus patterns)
  - Config flow UI for API key entry, meter discovery, and validation
  - Options flow for reconfiguration without reinstall
  - Electricity consumption entities (current period, daily total, historical)
  - Gas consumption entities (current period, daily total, historical)
  - Electricity tariff rate entity with off-peak detection
  - Gas tariff rate entity
  - Intelligent Go dispatch entities (active dispatch, next dispatch, schedule)
  - Binary sensors for off-peak status and dispatch active state
  - Automation events for rate changes and dispatch start/end
  - HA Energy Dashboard compatibility
  - Unit and integration tests with pytest
  - GitHub Actions CI/CD pipeline (linting, testing)
  - Documentation (README, setup guide, troubleshooting)
  - GitHub release (manual install)

out:
  - Cost calculation entities (deferred to post-MVP)
  - Live power from Home Mini (no device available; SMETS2 data via API only)
  - HACS publication (GitHub-only release for MVP)
  - Natural language query support via HA Assist (P2 feature)
  - Push notifications for rate changes (P2 feature)
  - Saving Sessions integration (P2 feature)
  - Carbon intensity data (P2 feature)
  - Multi-property/multi-account support (future roadmap)
  - Export functionality (P2 feature)
```

## 7. Stakeholders & Roles

| Name                     | Role                      | Responsibility                                           | Contact                  |
| ------------------------ | ------------------------- | -------------------------------------------------------- | ------------------------ |
| Sam Carrington           | Product Owner / Developer | Overall delivery, architecture decisions, implementation | octopus@gwawr.co.uk      |
| Home Assistant Community | End Users                 | Feedback, bug reports, feature requests                  | GitHub Issues            |

## 8. High-level timeline & milestones

| ID  | Title                  | Description                                                                       | Owner          |
| --- | ---------------------- | --------------------------------------------------------------------------------- | -------------- |
| M1  | Project Setup Complete | Repository structure, CI/CD, development environment ready                        | Sam Carrington |
| M2  | API Client Functional  | Octopus API client with authentication, consumption, and tariff retrieval working | Sam Carrington |
| M3  | Core HA Integration    | Config flow, coordinators, and electricity entities functional in HA              | Sam Carrington |
| M4  | Gas & Tariffs Complete | Gas consumption entities and tariff rate entities working                         | Sam Carrington |
| M5  | Intelligent Go Support | Dispatch coordinators and entities for Intelligent Go customers                   | Sam Carrington |
| M6  | Automation Ready       | Events, binary sensors, and automation triggers implemented                       | Sam Carrington |
| M7  | Documentation Complete | README, setup guide, troubleshooting guide published                              | Sam Carrington |
| M8  | MVP Release            | v0.1.0 released on GitHub with all MVP features                                   | Sam Carrington |

## 9. Task list

### Phase 1: Project Setup & Foundation

| ID    | Title                                                     | Owner | Complexity | Dependencies | Done  |
| ----- | --------------------------------------------------------- | ----- | ---------- | ------------ | ----- |
| T-001 | Create `src/` directory structure for HA custom component | Sam Carrington | XS         | []           | false |
| T-002 | Create `manifest.json` with integration metadata          | Sam Carrington | XS         | [T-001]      | false |
| T-003 | Create `const.py` with constants and configuration keys   | Sam Carrington | XS         | [T-001]      | false |
| T-004 | Set up pytest configuration and test directory structure  | Sam Carrington | S          | [T-001]      | false |
| T-005 | Create GitHub Actions workflow for linting (ruff/pylint)  | Sam Carrington | S          | [T-001]      | false |
| T-006 | Create GitHub Actions workflow for testing (pytest)       | Sam Carrington | S          | [T-004]      | false |
| T-007 | Create `pyproject.toml` for development dependencies      | Sam Carrington | XS         | [T-001]      | false |

### Phase 2: API Client Layer

| ID    | Title                                                              | Owner | Complexity | Dependencies          | Done  |
| ----- | ------------------------------------------------------------------ | ----- | ---------- | --------------------- | ----- |
| T-008 | Create `api/exceptions.py` with custom exception classes           | Sam Carrington | XS         | [T-001]               | false |
| T-009 | Create `api/auth.py` with token management (GraphQL auth)          | Sam Carrington | M          | [T-008]               | false |
| T-010 | Create `api/graphql.py` with query definitions                     | Sam Carrington | M          | [T-008]               | false |
| T-011 | Create `api/rest.py` with consumption/tariff endpoint methods      | Sam Carrington | M          | [T-008]               | false |
| T-012 | Create `api/client.py` main OctohaApiClient facade                 | Sam Carrington | L          | [T-009, T-010, T-011] | false |
| T-013 | Create `models/account.py` with Account and MeterPoint dataclasses | Sam Carrington | S          | [T-001]               | false |
| T-014 | Create `models/consumption.py` with Consumption dataclasses        | Sam Carrington | S          | [T-001]               | false |
| T-015 | Create `models/tariff.py` with Tariff and Rate dataclasses         | Sam Carrington | S          | [T-001]               | false |
| T-016 | Create `models/dispatch.py` with Dispatch dataclasses              | Sam Carrington | S          | [T-001]               | false |
| T-017 | Write unit tests for API client authentication flow                | Sam Carrington | M          | [T-012]               | false |
| T-018 | Write unit tests for consumption data retrieval                    | Sam Carrington | M          | [T-012, T-014]        | false |
| T-019 | Write unit tests for tariff data retrieval                         | Sam Carrington | M          | [T-012, T-015]        | false |
| T-020 | Add API response fixtures (JSON samples) for tests                 | Sam Carrington | S          | [T-004]               | false |

### Phase 3: Config Flow & Integration Setup

| ID    | Title                                                              | Owner | Complexity | Dependencies | Done  |
| ----- | ------------------------------------------------------------------ | ----- | ---------- | ------------ | ----- |
| T-021 | Create `config_flow.py` with user step (API key input)             | Sam Carrington | M          | [T-012]      | false |
| T-022 | Implement meter discovery step in config flow                      | Sam Carrington | M          | [T-021]      | false |
| T-023 | Implement config flow validation and error handling                | Sam Carrington | S          | [T-022]      | false |
| T-024 | Create `strings.json` and `translations/en.json` for UI strings    | Sam Carrington | S          | [T-021]      | false |
| T-025 | Implement options flow for reconfiguration                         | Sam Carrington | M          | [T-023]      | false |
| T-026 | Create `__init__.py` with async_setup_entry and async_unload_entry | Sam Carrington | M          | [T-023]      | false |
| T-027 | Write integration tests for config flow                            | Sam Carrington | M          | [T-026]      | false |

### Phase 4: Data Coordinators

| ID    | Title                                                          | Owner | Complexity | Dependencies                 | Done  |
| ----- | -------------------------------------------------------------- | ----- | ---------- | ---------------------------- | ----- |
| T-028 | Create `coordinator.py` with OctohaBaseCoordinator             | Sam Carrington | M          | [T-026]                      | false |
| T-029 | Implement ElectricityCoordinator with 5-minute update interval | Sam Carrington | M          | [T-028]                      | false |
| T-030 | Implement GasCoordinator with 5-minute update interval         | Sam Carrington | M          | [T-028]                      | false |
| T-031 | Implement TariffCoordinator with 30-minute update interval     | Sam Carrington | M          | [T-028]                      | false |
| T-032 | Implement DispatchCoordinator for Intelligent Go               | Sam Carrington | M          | [T-028]                      | false |
| T-033 | Implement coordinator error handling and retry logic           | Sam Carrington | S          | [T-029, T-030, T-031, T-032] | false |
| T-034 | Write unit tests for coordinator update logic                  | Sam Carrington | M          | [T-033]                      | false |

### Phase 5: Entity Platforms

| ID    | Title                                                               | Owner | Complexity | Dependencies                               | Done  |
| ----- | ------------------------------------------------------------------- | ----- | ---------- | ------------------------------------------ | ----- |
| T-035 | Create `sensor.py` with base OctohaSensorEntity class               | Sam Carrington | S          | [T-029]                                    | false |
| T-036 | Implement electricity consumption sensors (current, daily)          | Sam Carrington | M          | [T-035]                                    | false |
| T-037 | Implement gas consumption sensors (current, daily)                  | Sam Carrington | M          | [T-035, T-030]                             | false |
| T-038 | Implement electricity rate sensor with off-peak detection           | Sam Carrington | M          | [T-035, T-031]                             | false |
| T-039 | Implement gas rate sensor                                           | Sam Carrington | S          | [T-035, T-031]                             | false |
| T-040 | Implement dispatch sensors (next dispatch, active dispatch)         | Sam Carrington | M          | [T-035, T-032]                             | false |
| T-041 | Create `binary_sensor.py` with off-peak and dispatch active sensors | Sam Carrington | M          | [T-031, T-032]                             | false |
| T-042 | Implement entity attributes (metadata, timestamps, MPAN/MPRN)       | Sam Carrington | S          | [T-036, T-037, T-038, T-039, T-040, T-041] | false |
| T-043 | Ensure Energy Dashboard compatibility (state_class, device_class)   | Sam Carrington | S          | [T-036, T-037]                             | false |
| T-044 | Write unit tests for sensor state calculations                      | Sam Carrington | M          | [T-043]                                    | false |

### Phase 6: Automation Support

| ID    | Title                                          | Owner | Complexity | Dependencies   | Done  |
| ----- | ---------------------------------------------- | ----- | ---------- | -------------- | ----- |
| T-045 | Implement octoha_off_peak_start/end events     | Sam Carrington | M          | [T-038]        | false |
| T-046 | Implement octoha_dispatch_start/end events     | Sam Carrington | M          | [T-040]        | false |
| T-047 | Document automation trigger examples in README | Sam Carrington | S          | [T-045, T-046] | false |
| T-048 | Write integration tests for event firing       | Sam Carrington | S          | [T-046]        | false |

### Phase 7: Diagnostics & Error Handling

| ID    | Title                                                         | Owner | Complexity | Dependencies   | Done  |
| ----- | ------------------------------------------------------------- | ----- | ---------- | -------------- | ----- |
| T-049 | Create `diagnostics.py` for debug data export (sanitized)     | Sam Carrington | S          | [T-026]        | false |
| T-050 | Implement graceful degradation on API outages (cached values) | Sam Carrington | M          | [T-033]        | false |
| T-051 | Implement stale data indication in entity states              | Sam Carrington | S          | [T-050]        | false |
| T-052 | Add comprehensive DEBUG-level logging                         | Sam Carrington | S          | [T-012, T-028] | false |

### Phase 8: Documentation

| ID    | Title                                                             | Owner | Complexity | Dependencies | Done  |
| ----- | ----------------------------------------------------------------- | ----- | ---------- | ------------ | ----- |
| T-053 | Write README.md with project overview and features                | Sam Carrington | M          | [T-043]      | false |
| T-054 | Write installation guide (manual GitHub install)                  | Sam Carrington | S          | [T-053]      | false |
| T-055 | Write configuration guide with screenshots                        | Sam Carrington | S          | [T-054]      | false |
| T-056 | Write troubleshooting guide with common issues                    | Sam Carrington | M          | [T-055]      | false |
| T-057 | Add inline code documentation (docstrings, type hints)            | Sam Carrington | M          | [T-044]      | false |
| T-058 | Create CHANGELOG.md                                               | Sam Carrington | XS         | [T-053]      | false |
| T-059 | Create LICENSE file with MIT license and open-octopus attribution | Sam Carrington | XS         | [T-001]      | false |

### Phase 9: Testing & Release

| ID    | Title                                                        | Owner | Complexity | Dependencies   | Done  |
| ----- | ------------------------------------------------------------ | ----- | ---------- | -------------- | ----- |
| T-060 | Run full test suite and achieve >80% coverage                | Sam Carrington | M          | [T-044, T-048] | false |
| T-061 | Manual testing on personal HA instance (7-day stability run) | Sam Carrington | L          | [T-060]        | false |
| T-062 | Validate gas readings against Smart Meter IHD                | Sam Carrington | M          | [T-061]        | false |
| T-063 | Fix bugs identified during testing                           | Sam Carrington | M          | [T-062]        | false |
| T-064 | Create GitHub release v0.1.0 with release notes              | Sam Carrington | S          | [T-063]        | false |

## 10. Risks and mitigations

| ID    | Description                                             | Probability | Impact | Mitigation                                                                                                      | Owner          |
| ----- | ------------------------------------------------------- | ----------- | ------ | --------------------------------------------------------------------------------------------------------------- | -------------- |
| R-001 | Octopus GraphQL API changes or access revoked           | Medium      | High   | Abstract API layer for easier updates; monitor open-octopus repo for changes; implement version detection       | Sam Carrington |
| R-002 | Smart meter data delay exceeds expectations (>24h)      | Medium      | Medium | Document data freshness limitations clearly; show `last_updated` prominently; set appropriate user expectations | Sam Carrington |
| R-003 | Gas data format differs from electricity or unavailable | Medium      | High   | Validate gas endpoints early in Phase 2; implement fallback to electricity-only mode                            | Sam Carrington |
| R-004 | GraphQL API rate limiting impacts functionality         | Low         | Medium | Implement respectful polling (max 1 req/min/endpoint); exponential backoff; configurable intervals              | Sam Carrington |
| R-005 | Token refresh logic fails silently                      | Low         | High   | Comprehensive logging; proactive token refresh 5 min before expiry; clear auth failure states                   | Sam Carrington |
| R-006 | HA integration patterns change in future releases       | Low         | Medium | Target current HA version (2024.1+); follow official documentation; use HA development tools for validation     | Sam Carrington |
| R-007 | Single developer bandwidth constraints                  | Medium      | Medium | Prioritise MVP features strictly; defer P2 features; maintain clear scope boundaries                            | Sam Carrington |

## 11. Assumptions

- User has a valid Octopus Energy account with API access enabled (API key available)
- User's smart meter (SMETS1 or SMETS2) is enrolled and sending data to Octopus
- Octopus Energy continues to provide GraphQL and REST API access (as used by open-octopus)
- Home Assistant instance is version 2024.1 or later
- Python 3.11+ is available (HA requirement)
- User has MPAN (electricity meter point) and/or MPRN (gas meter point) available
- API patterns from open-octopus v0.3.0 remain valid and can be adapted
- The user is on an Intelligent Octopus Go tariff (for dispatch features; graceful degradation for other tariffs)
- Development will use local Python venv (not devcontainer)
- No external testers for beta phase (personal testing only)

## 12. Implementation approach / Technical narrative

### TL;DR

Build a Home Assistant custom integration using a layered architecture: API client (adapted from open-octopus patterns using aiohttp), data coordinators (HA's DataUpdateCoordinator), and entity platforms (sensors, binary sensors). Implement dual API strategy (GraphQL for real-time features, REST for consumption data). Follow HA official patterns for config flow, credential storage, and entity registration.

### Architecture Overview

The integration follows the architecture defined in ADR-001 with three distinct layers:

```
┌─────────────────────────────────────────────────────────────┐
│                    Home Assistant Core                       │
├─────────────────────────────────────────────────────────────┤
│                    Octoha Integration                        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Entity Layer: Sensors, Binary Sensors, Events           ││
│  ├─────────────────────────────────────────────────────────┤│
│  │ Coordinator Layer: Electricity, Gas, Tariff, Dispatch   ││
│  ├─────────────────────────────────────────────────────────┤│
│  │ API Client Layer: GraphQL + REST + Auth                 ││
│  └─────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│              Octopus Energy APIs (GraphQL + REST)            │
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
src/custom_components/octoha/
├── __init__.py           # Integration entry point
├── manifest.json         # HA manifest
├── const.py              # Constants
├── config_flow.py        # Config + options flow
├── coordinator.py        # DataUpdateCoordinator classes
├── diagnostics.py        # Debug export
├── strings.json          # Base UI strings
├── api/
│   ├── __init__.py
│   ├── client.py         # Main API client facade
│   ├── auth.py           # Token management
│   ├── graphql.py        # GraphQL queries
│   ├── rest.py           # REST methods
│   └── exceptions.py     # Custom exceptions
├── models/
│   ├── __init__.py
│   ├── account.py        # Account, MeterPoint
│   ├── consumption.py    # Consumption data
│   ├── tariff.py         # Tariff, Rate
│   └── dispatch.py       # Dispatch, DispatchStatus
├── sensor.py             # Sensor entities
├── binary_sensor.py      # Binary sensor entities
└── translations/
    └── en.json           # English translations
```

### API Client Design

The API client will be adapted from open-octopus patterns but use HA's aiohttp session:

```python
# Key adaptation from httpx to aiohttp
async def _graphql(self, query: str, variables: dict) -> dict:
    """Execute GraphQL query using HA's aiohttp session."""
    session = async_get_clientsession(self.hass)
    headers = {"Authorization": await self._auth.get_token()}

    async with session.post(
        GRAPHQL_URL,
        headers=headers,
        json={"query": query, "variables": variables}
    ) as resp:
        resp.raise_for_status()
        return await resp.json()
```

**Authentication Flow:**

1. User provides API key (sk_live_xxx) in config flow
2. API key used to obtain GraphQL token via `obtainKrakenToken` mutation
3. Token cached for 55 minutes (refresh 5 min before expiry)
4. Token stored in HA's credential storage (encrypted)

**Dual API Strategy:**

- **GraphQL** (`api.octopus.energy/v1/graphql/`): Account info, dispatches, live power, saving sessions
- **REST** (`api.octopus.energy/v1/`): Consumption data, tariff rates, historical data

### Data Coordinator Pattern

Each data domain has a dedicated coordinator with appropriate update intervals:

| Coordinator            | Interval | Data Type              |
| ---------------------- | -------- | ---------------------- |
| ElectricityCoordinator | 5 min    | Consumption (REST)     |
| GasCoordinator         | 5 min    | Consumption (REST)     |
| TariffCoordinator      | 30 min   | Rates (REST + GraphQL) |
| DispatchCoordinator    | 5 min    | Dispatches (GraphQL)   |

Coordinators extend `DataUpdateCoordinator` and handle:

- Automatic caching of last known values
- Error handling with `UpdateFailed` exceptions
- Auth failures triggering `ConfigEntryAuthFailed` for reauth flow
- Exponential backoff on transient failures

### Config Flow Design

```
User adds "Octoha" integration
         │
         ▼
┌─────────────────────┐
│ Step 1: API Key     │ ◄── User enters API key
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ Validate API Key    │ ◄── Call GraphQL obtainKrakenToken
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ Step 2: Meter       │ ◄── Auto-discover MPAN/MPRN
│ Discovery           │     User confirms selection
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ Create Config Entry │ ◄── Store credentials
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ Initialize          │ ◄── Create coordinators
│ Coordinators        │     First data fetch
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ Register Entities   │ ◄── Create sensors
└─────────────────────┘
```

**Options Flow** allows:

- Update API key (triggers reauth)
- Change polling intervals
- Enable/disable meter types

### Entity Design

All entities follow HA naming conventions:

```python
# Example: Electricity Daily Sensor
class OctohaElectricityDailySensor(CoordinatorEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("today_kwh")
```

**Energy Dashboard Compatibility:**

- `SensorStateClass.TOTAL_INCREASING` for cumulative consumption
- Proper `device_class` and `unit_of_measurement`
- `last_reset` attribute for daily sensors

### Event System

Automation events fired on state transitions:

| Event                   | Trigger                      | Data                                           |
| ----------------------- | ---------------------------- | ---------------------------------------------- |
| `octoha_off_peak_start` | Rate transitions to off-peak | `{"rate": 7.5, "ends_at": "..."}`              |
| `octoha_off_peak_end`   | Rate transitions to peak     | `{"rate": 30.0}`                               |
| `octoha_dispatch_start` | Intelligent dispatch begins  | `{"source": "smart-charge", "ends_at": "..."}` |
| `octoha_dispatch_end`   | Intelligent dispatch ends    | `{"source": "smart-charge", "kwh": 15.2}`      |

### Error Handling Strategy

1. **API Unavailable**: Return last cached value; mark entity as potentially stale via attribute
2. **Auth Failure**: Raise `ConfigEntryAuthFailed` to trigger reauth flow
3. **Rate Limiting**: Exponential backoff with jitter; respect 1 req/min limit
4. **Invalid Data**: Log warning; return `None` to mark entity unknown
5. **Gas Unavailable**: Graceful degradation to electricity-only mode

### Attribution

Since we're extracting patterns from open-octopus (MIT licensed):

- Include MIT license attribution in LICENSE file
- Credit open-octopus in README
- Add attribution comment in api/client.py

## 13. Testing & validation plan

### Unit Tests

**Scope:**

- API client methods (mocked HTTP responses)
- Token management and refresh logic
- Coordinator data processing
- Entity state calculations
- Model parsing and validation

**Coverage Target:** >80% for `api/`, `models/`, `coordinator.py`

**Tools:** pytest, pytest-asyncio, pytest-cov, aiohttp test utilities

**Example Test Structure:**

```python
async def test_electricity_consumption_parsing():
    """Test consumption data is correctly parsed."""
    client = OctohaApiClient(...)
    with aioresponses() as mock:
        mock.get(CONSUMPTION_URL, payload=FIXTURE_CONSUMPTION)
        result = await client.get_consumption(periods=48)

    assert len(result) == 48
    assert result[0].kwh == 0.5
```

### Integration Tests

**Scope:**

- Full config flow with mocked API
- Coordinator refresh cycles
- Entity state updates after coordinator refresh
- Options flow changes
- Error recovery scenarios

**Tools:** pytest-homeassistant-custom-component, hass test fixtures

### Fixtures

Sample API responses stored in `tests/fixtures/`:

- `consumption_electricity.json`
- `consumption_gas.json`
- `tariff_rates.json`
- `dispatches.json`
- `account_info.json`

### Manual Validation

1. **7-Day Stability Run:** Integration running on personal HA instance with live Octopus account
2. **IHD Comparison:** Daily comparison of gas readings vs. Smart Meter In-Home Display
3. **Automation Testing:** Verify events fire correctly for off-peak transitions
4. **Energy Dashboard:** Confirm data appears correctly in HA's built-in Energy dashboard

## 14. Deployment plan & roll-back strategy

### Environments

1. **Development:** Local Python venv with pytest
2. **Integration Testing:** Local HA instance (or HA test fixtures)
3. **Beta Testing:** Personal HA instance with live Octopus data
4. **Release:** GitHub repository

### Deployment Steps

1. All unit and integration tests pass (>80% coverage)
2. 7-day stability run on personal HA instance
3. Gas readings validated against IHD
4. Documentation reviewed and complete
5. Create git tag `v0.1.0`
6. Create GitHub release with release notes
7. Attach source archive to release

### Roll-back Strategy

Since this is a custom component installed manually:

1. Users can remove the integration via HA UI
2. Delete `custom_components/octoha/` directory
3. Restart Home Assistant
4. For version rollback: download previous release tag

### Roll-back Criteria

- Any unhandled exception causing HA restart
- Data corruption or incorrect readings
- Security vulnerability discovered

## 15. Monitoring & observability

### Metrics (via HA entity attributes)

| Metric                   | Location              | Target                   |
| ------------------------ | --------------------- | ------------------------ |
| `last_updated`           | All entity attributes | Within expected interval |
| `last_successful_update` | Coordinator attribute | Recent (< 2x interval)   |
| `api_calls_today`        | Diagnostics           | < 300/day                |
| `stale`                  | Entity attribute      | `false`                  |

### Alerts

- Entity becomes `unavailable` for > 30 minutes
- Auth failure requiring reauth (HA notification)

### Dashboards

- HA built-in Energy Dashboard (consumption data)
- Custom Lovelace cards (documented in README)
- Diagnostics export for troubleshooting

### Logging

- DEBUG level: Full API request/response details (sanitized)
- INFO level: Coordinator updates, entity state changes
- WARNING level: Stale data, API errors (transient)
- ERROR level: Auth failures, unrecoverable errors

## 16. Compliance, security & privacy considerations

### Data Classification

| Data Type        | Classification | Handling                                                           |
| ---------------- | -------------- | ------------------------------------------------------------------ |
| API Key          | Secret         | Stored encrypted in HA credential storage; never logged            |
| Account Number   | PII            | Stored in config entry; included in diagnostics (if user consents) |
| MPAN/MPRN        | PII            | Stored in config entry; may be partially redacted in logs          |
| Consumption Data | Personal       | Stored in HA database; retained per HA settings                    |

### Security Controls

- [ ] API keys never logged or exposed in debug output
- [ ] HTTPS-only communication with Octopus API
- [ ] Credentials never transmitted to third parties
- [ ] Diagnostics data sanitized (API keys redacted)
- [ ] No eval() or dynamic code execution
- [ ] Input validation on all API responses

### Compliance

- **GDPR:** User's energy data stays within their HA instance; no external transmission
- **Open Source:** MIT license with proper attribution

### Security Review Checklist

- [ ] API key storage uses HA's secure credential system
- [ ] No hardcoded secrets in source code
- [ ] All HTTP calls use HTTPS
- [ ] Error messages don't leak sensitive data
- [ ] Diagnostics redacts API keys and account numbers

## 17. Communication plan

### Channels

| Event                 | Channel              | Audience        |
| --------------------- | -------------------- | --------------- |
| Development Progress  | Git commits          | Developer       |
| Release Announcement  | GitHub Release Notes | Users           |
| Bug Reports           | GitHub Issues        | Users/Developer |
| Documentation Updates | README/Wiki          | Users           |

### Message Templates

**Release Announcement:**

```markdown
## Octoha v0.1.0 Released

Initial release of Octoha - Home Assistant integration for Octopus Energy.

### Features

- Electricity and gas consumption sensors
- Tariff rate entities with off-peak detection
- Intelligent Go dispatch support
- HA Energy Dashboard compatibility

### Installation

See README for manual installation instructions.
```

## 18. Related documents & links

### Project Documentation

- [PRD: Octoha](../docs/PRDs/prd-octoha.md)
- [ADR-001: Octoha Architecture](../docs/ADRs/adr-001-octoha-architecture.md)
- [Component Architecture](../docs/designs/octoha-component-architecture.md)
- [ERD & Data Models](../docs/designs/octoha-erd-data-models.md)

### External References

- [open-octopus Repository](https://github.com/abracadabra50/open-octopus) - Reference implementation for API patterns
- [Octopus Energy GraphQL Reference](https://docs.octopus.energy/graphql/reference/)
- [Octopus Energy REST API](https://developer.octopus.energy/docs/api/)
- [Home Assistant Developer Docs - Integration](https://developers.home-assistant.io/docs/creating_integration_manifest)
- [Home Assistant Developer Docs - Config Flow](https://developers.home-assistant.io/docs/config_entries_config_flow_handler)
- [Home Assistant Developer Docs - DataUpdateCoordinator](https://developers.home-assistant.io/docs/integration_fetching_data)

## 19. Appendix

### A. Entity Reference

| Entity ID                              | Type   | Description                      | Unit     |
| -------------------------------------- | ------ | -------------------------------- | -------- |
| `sensor.octoha_electricity_current`    | Sensor | Current period consumption       | kWh      |
| `sensor.octoha_electricity_daily`      | Sensor | Today's total consumption        | kWh      |
| `sensor.octoha_electricity_rate`       | Sensor | Current electricity rate         | GBP/kWh  |
| `sensor.octoha_gas_current`            | Sensor | Current period consumption       | kWh      |
| `sensor.octoha_gas_daily`              | Sensor | Today's total consumption        | kWh      |
| `sensor.octoha_gas_rate`               | Sensor | Current gas rate                 | GBP/kWh  |
| `sensor.octoha_next_dispatch`          | Sensor | Next Intelligent dispatch time   | datetime |
| `binary_sensor.octoha_off_peak`        | Binary | Off-peak period active           | -        |
| `binary_sensor.octoha_dispatch_active` | Binary | Intelligent dispatch in progress | -        |

### B. API Endpoints Used

**GraphQL (`api.octopus.energy/v1/graphql/`):**

- `obtainKrakenToken` - Authentication
- `account` - Account details and meter discovery
- `plannedDispatches` - Intelligent Go schedule
- `completedDispatches` - Completed charging sessions

**REST (`api.octopus.energy/v1/`):**

- `GET /electricity-meter-points/{mpan}/meters/{serial}/consumption/`
- `GET /gas-meter-points/{mprn}/meters/{serial}/consumption/`
- `GET /products/{product_code}/electricity-tariffs/{tariff_code}/standard-unit-rates/`
- `GET /products/{product_code}/gas-tariffs/{tariff_code}/standard-unit-rates/`

### C. Configuration Schema

**Config Entry Data (entry.data):**

```python
{
    "api_key": "sk_live_xxx",           # Encrypted
    "account": "A-XXXXXXXX",
    "mpan": "1234567890123",
    "meter_serial": "12A3456789",
    "mprn": "1234567",
    "gas_meter_serial": "G12345678",
    "region": "J"
}
```

**Options (entry.options):**

```python
{
    "electricity_interval": 300,         # seconds
    "gas_interval": 300,
    "tariff_interval": 1800,
    "dispatch_interval": 300
}
```

---

**Checklist before marking plan as ready for review:**

- [x] All minimal required fields are filled
- [x] Dates validated (ISO 8601)
- [x] Complexity assigned to each task (XS/S/M/L/XL)
- [x] At least one test/validation approach is defined
- [x] Security & compliance items are noted
