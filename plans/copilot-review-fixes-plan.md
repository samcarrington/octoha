# Copilot Review Fixes Implementation Plan

This plan addresses all 12 issues identified by GitHub Copilot during the PR review of the Octoha Home Assistant integration. The issues range from critical runtime bugs to documentation updates.

---

## 1. Title

Fix Copilot-Identified Issues in Octoha Integration PR #1

## 2. Short description

Address 12 code review issues from GitHub Copilot including 2 critical config flow bugs (account discovery and meter selection), 4 coordinator interval configuration issues, and 6 code quality/documentation improvements.

## 3. Current status

```yaml
owner: Sam Carrington <octopus@gwawr.co.uk>
state: complete
last_updated: 2026-01-23
blockers: []
```

## 4. Objectives

1. Enable successful integration setup by fixing the account number discovery bug
2. Make meter selection functional so users can choose which meters to monitor
3. Ensure user-configured update intervals are actually applied to coordinators
4. Achieve Home Assistant compatibility by fixing sensor device class issues
5. Follow Home Assistant best practices for options flow registration
6. Keep documentation current and accurate

## 5. Success criteria

| Name | Metric | Target | Verification |
|------|--------|--------|--------------|
| Config flow success | Setup completion rate | 100% for valid API keys | Manual test and unit tests pass |
| Meter selection works | User selections persisted | Selected meters match stored config | Unit test + integration test |
| Intervals applied | Coordinator update intervals | Match user options | Unit test checking `update_interval` property |
| Sensor compatibility | HA statistics | No errors in logs | Run HA and check energy dashboard |
| Test suite | All tests pass | All existing tests + new account discovery tests pass | `pytest` with no failures |
| Linting | Code quality | Zero ruff/mypy errors | `ruff check src/ tests/` and `mypy src/` pass |
| Performance | Coordinator intervals | No degradation in API call frequency | Log analysis confirms expected intervals |

## 6. Scope

```yaml
in:
  - Fix account number discovery in config flow
  - Fix meter selection persistence in config flow
  - Fix multiple meter point detection logic
  - Apply user-configured intervals to coordinators
  - Fix sensor device class for electricity rate
  - Standardize options flow registration pattern
  - Update entry title format (align with tests)
  - Update stale TDD documentation
out:
  - Adding new features beyond bug fixes
  - Refactoring unrelated code
  - Changing API client architecture
  - Adding new sensors or entities
```

## 7. Stakeholders & Roles

| Name | Role | Responsibility | Contact |
|------|------|----------------|---------|
| Sam Carrington | Developer | Implementation and testing | octopus@gwawr.co.uk |

## 8. High-level timeline & milestones

1. `M1` — Critical bugs fixed (T-001 to T-004) + validation (T-011, T-012, T-015) — TBD — Developer
2. `M2` — Options/coordinator issues fixed (T-005 to T-007) — TBD — Developer
3. `M3` — Code quality & docs fixed (T-008 to T-010) — TBD — Developer
4. `M4` — All tests passing, PR ready (T-013, T-014) — TBD — Developer

**Testing Checkpoints:**
- After M1: Run `pytest tests/test_config_flow.py tests/test_api_client.py` 
- After M2: Run `pytest tests/test_coordinator.py`
- After M3: Run full test suite
- After M4: Manual HA integration test

## 9. Task list

### Critical Priority (Blocking Issues)

| ID | Title | Owner | Complexity | Dependencies | Done |
|----|-------|-------|------------|--------------|------|
| T-001 | Fix GraphQL query and implement account number discovery in API client | Sam Carrington | M | [] | true |
| T-002 | Update config flow to use account discovery | Sam Carrington | S | [T-001] | true |
| T-003 | Fix meter selection to persist user choices | Sam Carrington | M | [] | true |
| T-004 | Fix multiple meter point detection logic | Sam Carrington | S | [T-003] | true |

**Complexity Justification:**
- **T-001 (M)**: Requires GraphQL query fix + new method + error handling + multi-account logic
- **T-002 (S)**: Simple integration - just call the new method before get_account()
- **T-003 (M)**: Significant config flow refactoring - new instance variables, schema updates, lookup logic
- **T-004 (S)**: Simple logic change using existing properties

### High Priority (Functional Issues)

| ID | Title | Owner | Complexity | Dependencies | Done |
|----|-------|-------|------------|--------------|------|
| T-005 | Apply user options intervals to coordinators | Sam Carrington | M | [] | true |
| T-006 | Fix electricity rate sensor device class | Sam Carrington | XS | [] | true |

**Complexity Justification:**
- **T-005 (M)**: Affects 4 coordinator classes + __init__.py integration + const imports
- **T-006 (XS)**: Single line removal + optional icon addition

### Medium Priority (Code Quality)

| ID | Title | Owner | Complexity | Dependencies | Done |
|----|-------|-------|------------|--------------|------|
| T-007 | Standardize options flow registration | Sam Carrington | S | [] | true |
| T-008 | Align entry title format with tests | Sam Carrington | XS | [] | true |

**Complexity Justification:**
- **T-007 (S)**: Decorator removal + signature adjustment + verify no regressions (upgraded from XS)
- **T-008 (XS)**: Single line change

### Low Priority (Documentation)

| ID | Title | Owner | Complexity | Dependencies | Done |
|----|-------|-------|------------|--------------|------|
| T-009 | Update COORDINATOR_TEST_README.md | Sam Carrington | XS | [] | true |
| T-010 | Update CONFIG_FLOW_TEST_COVERAGE.md if needed | Sam Carrington | XS | [] | true |

### Testing & Validation Tasks

| ID | Title | Owner | Complexity | Dependencies | Done |
|----|-------|-------|------------|--------------|------|
| T-011 | Add unit tests for account discovery functionality | Sam Carrington | S | [T-001] | true |
| T-012 | Add integration tests for meter selection persistence | Sam Carrington | S | [T-003, T-004] | true |
| T-013 | Run full test suite and fix any failures | Sam Carrington | M | [T-001 to T-012] | true |
| T-014 | Manual integration test in Home Assistant | Sam Carrington | S | [T-013] | true |
| T-015 | Validate GraphQL query syntax with API documentation/testing | Sam Carrington | S | [T-001] | true |

**Complexity Justification:**
- **T-011 (S)**: New test file for account discovery edge cases
- **T-012 (S)**: New integration tests for config flow scenarios
- **T-013 (M)**: May uncover cascading issues requiring fixes (upgraded from S)
- **T-014 (S)**: Manual testing in HA dev environment
- **T-015 (S)**: API validation to ensure query works correctly

## 10. Risks and mitigations

| ID | Description | Probability | Impact | Mitigation | Owner |
|----|-------------|-------------|--------|------------|-------|
| R-001 | GraphQL account discovery query may have incorrect syntax | Medium | High | Validate query syntax before implementation (T-015); test with real API | TBD |
| R-002 | Multi-account users may have unexpected behavior | Medium | Medium | Select first account, log warning if multiple found; document behavior | TBD |
| R-003 | Existing tests may fail after changes | Medium | Medium | Run tests incrementally after each task; fix as needed | TBD |
| R-004 | HA version compatibility for sensor changes | Low | Medium | Test on supported HA versions per manifest.json | TBD |
| R-005 | Config flow breaking changes may affect existing installations | Low | High | No existing installations (pre-release); ensure upgrade path for future | TBD |
| R-006 | Coordinator interval changes may impact HA performance | Low | Medium | Validate intervals stay within documented ranges (60s-3600s) | TBD |
| R-007 | Options flow registration change may break HA integration | Low | High | Test options flow end-to-end after T-007 | TBD |

## 11. Assumptions

- The `ACCOUNT_NUMBER_QUERY` GraphQL query at line 77-89 of `graphql.py` uses the correct Octopus Kraken API schema (to be validated in T-015)
- The Octopus Energy API returns accounts via `viewer.accounts` when authenticated with an API key
- The `viewer` field is populated from the auth token context, not from a query variable
- Users typically have a single Octopus Energy account per API key
- The existing test infrastructure is functional and can be extended
- Home Assistant version compatibility follows manifest.json requirements (2024.4.0+)
- No existing user installations exist (pre-release), so breaking changes are acceptable

## 12. Implementation approach / Technical narrative

### TL;DR
Fix critical config flow bugs by adding account discovery, persist meter selections, apply user-configured intervals to coordinators, and clean up code quality issues. All fixes are isolated to specific files with minimal cross-cutting changes.

### Task T-001: Fix GraphQL Query and Implement Account Number Discovery

**Issue Analysis:**
The `ACCOUNT_NUMBER_QUERY` at lines 77-89 in `graphql.py` has an unused `$apiKey` parameter. The query uses `viewer`, which is populated from the authentication token context (obtained via `obtainKrakenToken`), not from a query variable. The parameter should be removed.

**Step 1: Fix the GraphQL query in `graphql.py`:**

```python
# Current (incorrect):
ACCOUNT_NUMBER_QUERY = """
query getAccountNumber($apiKey: String!) {
  viewer {
    accounts(first: 1) {
      edges {
        node {
          number
        }
      }
    }
  }
}
"""

# Fixed (remove unused parameter):
ACCOUNT_NUMBER_QUERY = """
query getAccountNumber {
  viewer {
    accounts(first: 1) {
      edges {
        node {
          number
        }
      }
    }
  }
}
"""
```

**Step 2: Add the discovery method to `OctohaApiClient`:**

```python
# In src/custom_components/octoha/api/client.py

async def discover_account_number(self) -> str:
    """Discover the account number from the API key.
    
    Uses the viewer.accounts query to find accounts linked to
    the authenticated API key.
    
    Returns:
        The first account number found.
        
    Raises:
        OctopusError: If no accounts found or query fails.
    """
    from .graphql import ACCOUNT_NUMBER_QUERY
    
    data = await self._graphql(ACCOUNT_NUMBER_QUERY)
    
    viewer = data.get("viewer", {})
    accounts = viewer.get("accounts", {})
    edges = accounts.get("edges", [])
    
    if not edges:
        raise OctopusError("No accounts found for this API key")
    
    # Use first account (most users have one)
    account_number = edges[0].get("node", {}).get("number")
    
    if not account_number:
        raise OctopusError("Could not extract account number from API response")
    
    # Cache for later use
    self._account_number = account_number
    
    if len(edges) > 1:
        _LOGGER.warning(
            "Multiple accounts found, using first: %s",
            account_number,
        )
    
    return account_number
```

Note: The `ACCOUNT_NUMBER_QUERY` may need adjustment - it currently takes `$apiKey` as a variable but uses `viewer` which is typically resolved from the auth token. The query should be:

```graphql
query getAccountNumber {
  viewer {
    accounts(first: 1) {
      edges {
        node {
          number
        }
      }
    }
  }
}
```

### Task T-002: Update Config Flow to Use Account Discovery

Modify `async_step_user` in `config_flow.py`:

```python
# After validate_credentials succeeds:
await self._client.validate_credentials()

# Discover account number from API key
account_number = await self._client.discover_account_number()

# Now get_account() will work
self._account = await self._client.get_account()
```

### Task T-003: Fix Meter Selection Persistence

The meter selection step must:
1. Store user selections in instance variables
2. Pass those selections to `_create_entry()`

```python
# In config_flow.py

def __init__(self) -> None:
    """Initialize the config flow."""
    self._api_key: str | None = None
    self._account: Any = None
    self._client: OctohaApiClient | None = None
    # Add these for meter selection
    self._selected_mpan: str | None = None
    self._selected_mprn: str | None = None
    self._selected_meter_serial: str | None = None
    self._selected_gas_meter_serial: str | None = None

async def async_step_meters(
    self,
    user_input: dict[str, Any] | None = None,
) -> FlowResult:
    """Handle the meter selection step."""
    if user_input is not None:
        # Persist user selections
        self._selected_mpan = user_input.get(CONF_MPAN)
        self._selected_mprn = user_input.get(CONF_MPRN)
        
        # Look up serial numbers for selected meters
        if self._selected_mpan and self._account:
            for mp in self._account.electricity_meter_points:
                if mp.mpan == self._selected_mpan:
                    self._selected_meter_serial = mp.meter_serial
                    break
        
        if self._selected_mprn and self._account:
            for mp in self._account.gas_meter_points:
                if mp.mprn == self._selected_mprn:
                    self._selected_gas_meter_serial = mp.meter_serial
                    break
        
        return self._create_entry()
    
    # Build schema with all available meters as options
    # ... (keep existing schema building code, but enumerate all meters)

def _create_entry(self) -> FlowResult:
    """Create the config entry with collected data."""
    # Use selected meters if available, otherwise fall back to primary
    mpan = self._selected_mpan
    meter_serial = self._selected_meter_serial
    mprn = self._selected_mprn
    gas_meter_serial = self._selected_gas_meter_serial
    
    # Fallback to primary if no selection was made
    if mpan is None and self._account.primary_electricity:
        mpan = self._account.primary_electricity.mpan
        meter_serial = self._account.primary_electricity.meter_serial
    
    if mprn is None and self._account.primary_gas:
        mprn = self._account.primary_gas.mprn
        gas_meter_serial = self._account.primary_gas.meter_serial
    
    # Build data dict...
```

### Task T-004: Fix Multiple Meter Point Detection

Replace the current logic with proper meter counting:

```python
# In async_step_user, after fetching account:

elec_meters = self._account.electricity_meter_points
gas_meters = self._account.gas_meter_points
total_meters = len(elec_meters) + len(gas_meters)

if total_meters == 0:
    errors["base"] = "no_meters"
elif total_meters == 1:
    # Only one meter, no selection needed
    return self._create_entry()
else:
    # Multiple meters, show selection step
    return await self.async_step_meters()
```

### Task T-005: Apply User Options to Coordinators

Modify `async_setup_entry` in `__init__.py`:

```python
from datetime import timedelta

# Read options with defaults
elec_interval = entry.options.get(
    CONF_ELECTRICITY_INTERVAL, 
    DEFAULT_ELECTRICITY_INTERVAL
)
gas_interval = entry.options.get(
    CONF_GAS_INTERVAL,
    DEFAULT_GAS_INTERVAL
)
tariff_interval = entry.options.get(
    CONF_TARIFF_INTERVAL,
    DEFAULT_TARIFF_INTERVAL
)
dispatch_interval = entry.options.get(
    CONF_DISPATCH_INTERVAL,
    DEFAULT_DISPATCH_INTERVAL
)

# Create coordinators with user-configured intervals
if mpan:
    electricity_coordinator = ElectricityCoordinator(
        hass, 
        client,
        update_interval=timedelta(seconds=elec_interval),
    )
# ... similar for other coordinators
```

Update coordinator constructors to accept optional `update_interval`:

```python
class ElectricityCoordinator(OctohaBaseCoordinator[ElectricityData]):
    def __init__(
        self,
        hass: HomeAssistant,
        client: OctohaApiClient,
        update_interval: timedelta | None = None,
    ) -> None:
        super().__init__(
            hass=hass,
            client=client,
            name=f"{DOMAIN}_electricity",
            update_interval=update_interval or UPDATE_INTERVAL_ELECTRICITY,
        )
```

### Task T-006: Fix Electricity Rate Sensor Device Class

Remove `SensorDeviceClass.MONETARY` since `p/kWh` is not a valid monetary unit:

```python
# In sensor.py, ElectricityRateSensor class

class ElectricityRateSensor(OctohaSensorEntity[TariffCoordinator]):
    """Sensor for current electricity rate."""
    
    # Remove this line:
    # _attr_device_class = SensorDeviceClass.MONETARY
    
    _attr_native_unit_of_measurement = "p/kWh"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2
    _attr_icon = "mdi:currency-gbp"  # Add icon for visual clarity
```

### Task T-007: Standardize Options Flow Registration

Remove the decorator and use standard pattern:

```python
# In config_flow.py

class OctohaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    # ... existing code ...

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OctohaOptionsFlow:
        """Create the options flow handler."""
        return OctohaOptionsFlow(config_entry)

# Remove: @config_entries.HANDLERS.register(DOMAIN)
```

### Task T-008: Align Entry Title Format

Either update code to match tests, or update tests to match code. Recommend updating code:

```python
# In _create_entry():
title = self._account.account_number
```

### Task T-009-010: Update Documentation

Update `tests/COORDINATOR_TEST_README.md` to reflect that:
- Coordinator module now exists
- Tests should pass (not intentionally fail)
- Remove TDD "Red phase" language

## 13. Testing & validation plan

### Unit Tests

| Area | Coverage Target | Key Scenarios | New Tests Needed |
|------|-----------------|---------------|------------------|
| Account discovery | 100% | Success, no accounts, multiple accounts, API error | Yes (T-011) |
| Meter selection | 100% | Single meter, multi-meter, user selection persisted | Yes (T-012) |
| Coordinator intervals | 100% | Default interval, custom interval from options | Extend existing |
| Config flow | 100% | All error paths, success paths, meter detection | Extend existing |

### New Test Cases (T-011, T-012)

**Account Discovery Tests:**
```python
# test_api_client.py - new tests
async def test_discover_account_number_success():
    """Test successful account discovery."""
    
async def test_discover_account_number_no_accounts():
    """Test error when no accounts found."""
    
async def test_discover_account_number_multiple_accounts():
    """Test warning logged for multiple accounts, first used."""
    
async def test_discover_account_number_api_error():
    """Test error handling for API failures."""
```

**Meter Selection Tests:**
```python
# test_config_flow.py - new tests
async def test_meter_selection_persists_user_choice():
    """Test that user-selected meters are stored in config entry."""
    
async def test_single_meter_skips_selection():
    """Test that single meter accounts skip selection step."""
    
async def test_multiple_meters_shows_selection():
    """Test that multi-meter accounts show selection step."""
```

### Integration Tests

- Full config flow with mocked API (existing, verify still passes)
- Coordinator startup with custom intervals (new)
- Options flow change triggers reload (existing, verify still passes)

### Manual Testing Checklist (T-014)

1. [ ] Install integration in HA dev instance
2. [ ] Complete config flow with valid API key
3. [ ] Verify correct account discovered (check logs)
4. [ ] Verify correct meters discovered
5. [ ] For multi-meter accounts, verify selection step appears
6. [ ] Verify selected meters match stored config entry
7. [ ] Change update intervals in options
8. [ ] Verify intervals actually change (check debug logs for update timing)
9. [ ] Verify electricity rate sensor works (no errors in logs)
10. [ ] Verify sensor appears correctly in energy dashboard

## 14. Deployment plan & roll-back strategy

### Deployment Steps

1. Create feature branch from `feat/octoha-implementation`
2. **Milestone 1 (Critical fixes):**
   - Implement T-001 (GraphQL fix + account discovery)
   - Implement T-002 (config flow integration)
   - Implement T-003 (meter selection persistence)
   - Implement T-004 (multiple meter detection)
   - Run T-011, T-012, T-015 tests
   - **Checkpoint:** `pytest tests/test_config_flow.py tests/test_api_client.py`
3. **Milestone 2 (Functional fixes):**
   - Implement T-005 (coordinator intervals)
   - Implement T-006 (sensor device class)
   - Implement T-007 (options flow registration)
   - **Checkpoint:** `pytest tests/test_coordinator.py`
4. **Milestone 3 (Code quality):**
   - Implement T-008 (entry title)
   - Implement T-009, T-010 (documentation)
   - **Checkpoint:** Full test suite
5. **Milestone 4 (Validation):**
   - Run T-013 (full test suite)
   - Run T-014 (manual HA testing)
6. Create PR for review
7. Address review feedback
8. Merge after approval

### Roll-back Strategy

- **Granular commits:** Each task is a separate commit for easy revert
- **No database migrations:** All changes are code-only
- **No breaking changes for users:** Pre-release, no existing installations
- **Revert procedure:** `git revert <commit-sha>` for specific task if issues found
- **Full rollback:** Return to `feat/octoha-implementation` branch state

## 15. Monitoring & observability

N/A - This is a bug fix PR, no new monitoring needed.

## 16. Compliance, security & privacy considerations

- No new data collection
- API key handling unchanged
- No new external dependencies
- All changes follow existing security patterns

## 17. Communication plan

- Update PR description with summary of changes
- Reply to each Copilot comment indicating fix status
- Request re-review after fixes complete

## 18. Related documents & links

- PR #1: https://github.com/samcarrington/octoha/pull/1
- Copilot Review: https://github.com/samcarrington/octoha/pull/1#pullrequestreview-3683896413
- GraphQL API Reference: `src/custom_components/octoha/api/graphql.py`
- Config Flow: `src/custom_components/octoha/config_flow.py`
- Coordinators: `src/custom_components/octoha/coordinator.py`

## 19. Appendix

### Copilot Comments Summary

| Comment ID | File | Line | Issue | Task |
|------------|------|------|-------|------|
| 2709748969 | config_flow.py | 104 | get_account() requires account_number | T-001, T-002 |
| 2709748984 | config_flow.py | 123 | Multiple meter point handling | T-004 |
| 2709749001 | config_flow.py | 160 | Meter selection ignored | T-003 |
| 2709749008 | config_flow.py | 210 | Title format mismatch | T-008 |
| 2709749015 | config_flow.py | 220 | Non-standard options registration | T-007 |
| 2709749031 | __init__.py | 114 | Options intervals not applied | T-005 |
| 2709749042 | __init__.py | 120 | Options intervals not applied | T-005 |
| 2709749054 | __init__.py | 125 | Options intervals not applied | T-005 |
| 2709749064 | __init__.py | 133 | Options intervals not applied | T-005 |
| 2709749080 | sensor.py | 304 | MONETARY device class + p/kWh | T-006 |
| 2709749102 | COORDINATOR_TEST_README.md | 5 | Outdated TDD docs | T-009 |
| 2709749112 | COORDINATOR_TEST_README.md | 190 | Outdated TDD docs | T-009 |

### GraphQL Query Fix

The existing `ACCOUNT_NUMBER_QUERY` needs to be corrected:

**Current (incorrect):**
```graphql
query getAccountNumber($apiKey: String!) {
  viewer {
    accounts(first: 1) {
      edges {
        node {
          number
        }
      }
    }
  }
}
```

**Fixed (no variable needed, uses auth token):**
```graphql
query getAccountNumber {
  viewer {
    accounts(first: 1) {
      edges {
        node {
          number
        }
      }
    }
  }
}
```

---

## Checklist before marking plan as ready for review

- [x] All minimal required fields are filled
- [x] Dates validated (ISO 8601)
- [x] Complexity assigned to each task (XS/S/M/L/XL)
- [x] At least one test/validation approach is defined
- [x] Security & compliance items are noted
