# Octoha Implementation TODO

> **Owner:** Sam Carrington <octopus@gwawr.co.uk>  
> **Status:** In Progress  
> **Last Updated:** 2026-01-18

This file tracks implementation progress for the Octoha Home Assistant integration.
See [octoha-implementation-plan.md](./octoha-implementation-plan.md) for full details.

---

## Progress Summary

| Phase | Description | Tasks | Complete |
|-------|-------------|-------|----------|
| 1 | Project Setup & Foundation | 7 | 7 |
| 2 | API Client Layer | 13 | 13 |
| 2.1 | API Client Review Fixes | 8 | 8 |
| 3 | Config Flow & Integration Setup | 7 | 0 |
| 4 | Data Coordinators | 7 | 0 |
| 5 | Entity Platforms | 10 | 0 |
| 6 | Automation Support | 4 | 0 |
| 7 | Diagnostics & Error Handling | 4 | 0 |
| 8 | Documentation | 7 | 1 |
| 9 | Testing & Release | 5 | 0 |
| **Total** | | **72** | **29** |

---

## Phase 1: Project Setup & Foundation

- [x] **T-001** Create `src/` directory structure for HA custom component `[XS]`
- [x] **T-002** Create `manifest.json` with integration metadata `[XS]` ← T-001
- [x] **T-003** Create `const.py` with constants and configuration keys `[XS]` ← T-001
- [x] **T-004** Set up pytest configuration and test directory structure `[S]` ← T-001
- [x] **T-005** Create GitHub Actions workflow for linting (ruff/pylint) `[S]` ← T-001
- [x] **T-006** Create GitHub Actions workflow for testing (pytest) `[S]` ← T-004
- [x] **T-007** Create `pyproject.toml` for development dependencies `[XS]` ← T-001

## Phase 2: API Client Layer

- [x] **T-008** Create `api/exceptions.py` with custom exception classes `[XS]` ← T-001
- [x] **T-009** Create `api/auth.py` with token management (GraphQL auth) `[M]` ← T-008
- [x] **T-010** Create `api/graphql.py` with query definitions `[M]` ← T-008
- [x] **T-011** Create `api/rest.py` with consumption/tariff endpoint methods `[M]` ← T-008
- [x] **T-012** Create `api/client.py` main OctohaApiClient facade `[L]` ← T-009, T-010, T-011
- [x] **T-013** Create `models/account.py` with Account and MeterPoint dataclasses `[S]` ← T-001
- [x] **T-014** Create `models/consumption.py` with Consumption dataclasses `[S]` ← T-001
- [x] **T-015** Create `models/tariff.py` with Tariff and Rate dataclasses `[S]` ← T-001
- [x] **T-016** Create `models/dispatch.py` with Dispatch dataclasses `[S]` ← T-001
- [x] **T-017** Write unit tests for API client authentication flow `[M]` ← T-012
- [x] **T-018** Write unit tests for consumption data retrieval `[M]` ← T-012, T-014
- [x] **T-019** Write unit tests for tariff data retrieval `[M]` ← T-012, T-015
- [x] **T-020** Add API response fixtures (JSON samples) for tests `[S]` ← T-004

## Phase 2.1: API Client Review Fixes

> Critical and recommended fixes identified during Phase 2 code review.
> See [recommendations.md](../recommendations.md) for full review details.

### Blocking Fixes (Complete)

- [x] **T-020A** Fix logging exposure - remove token expiry from debug logs `[XS]` ← T-009
- [x] **T-020B** Create error message sanitization utility in exceptions.py `[S]` ← T-008
- [x] **T-020C** Apply sanitization to auth.py, client.py, rest.py `[S]` ← T-020B
- [x] **T-020D** Fix daily usage performance with defaultdict + asyncio.gather `[S]` ← T-012
- [x] **T-020E** Add GraphQL client integration tests (35 tests) `[M]` ← T-012
- [x] **T-020F** Add daily usage aggregation tests (14 tests) `[M]` ← T-012

### Recommended Fixes (Complete)

- [x] **T-020G** Add account parsing edge case tests (16 tests) `[S]` ← T-012
- [x] **T-020H** Add input validation for MPAN/MPRN in rest.py `[S]` ← T-011

### Recommended Fixes (Deferred to post-Phase 3)

- [ ] **T-020I** Add tariff building integration tests `[S]` ← T-012
- [ ] **T-020J** Add current rate calculation tests `[S]` ← T-012
- [ ] **T-020K** Add network error simulation tests `[S]` ← T-017
- [ ] **T-020L** Add model edge case tests `[S]` ← T-013, T-014, T-015, T-016
- [ ] **T-020M** Flatten account parsing loops for performance `[S]` ← T-012

## Phase 3: Config Flow & Integration Setup

- [ ] **T-021** Create `config_flow.py` with user step (API key input) `[M]` ← T-012
- [ ] **T-022** Implement meter discovery step in config flow `[M]` ← T-021
- [ ] **T-023** Implement config flow validation and error handling `[S]` ← T-022
- [ ] **T-024** Create `strings.json` and `translations/en.json` for UI strings `[S]` ← T-021
- [ ] **T-025** Implement options flow for reconfiguration `[M]` ← T-023
- [ ] **T-026** Create `__init__.py` with async_setup_entry and async_unload_entry `[M]` ← T-023
- [ ] **T-027** Write integration tests for config flow `[M]` ← T-026

## Phase 4: Data Coordinators

- [ ] **T-028** Create `coordinator.py` with OctohaBaseCoordinator `[M]` ← T-026
- [ ] **T-029** Implement ElectricityCoordinator with 5-minute update interval `[M]` ← T-028
- [ ] **T-030** Implement GasCoordinator with 5-minute update interval `[M]` ← T-028
- [ ] **T-031** Implement TariffCoordinator with 30-minute update interval `[M]` ← T-028
- [ ] **T-032** Implement DispatchCoordinator for Intelligent Go `[M]` ← T-028
- [ ] **T-033** Implement coordinator error handling and retry logic `[S]` ← T-029, T-030, T-031, T-032
- [ ] **T-034** Write unit tests for coordinator update logic `[M]` ← T-033

## Phase 5: Entity Platforms

- [ ] **T-035** Create `sensor.py` with base OctohaSensorEntity class `[S]` ← T-029
- [ ] **T-036** Implement electricity consumption sensors (current, daily) `[M]` ← T-035
- [ ] **T-037** Implement gas consumption sensors (current, daily) `[M]` ← T-035, T-030
- [ ] **T-038** Implement electricity rate sensor with off-peak detection `[M]` ← T-035, T-031
- [ ] **T-039** Implement gas rate sensor `[S]` ← T-035, T-031
- [ ] **T-040** Implement dispatch sensors (next dispatch, active dispatch) `[M]` ← T-035, T-032
- [ ] **T-041** Create `binary_sensor.py` with off-peak and dispatch active sensors `[M]` ← T-031, T-032
- [ ] **T-042** Implement entity attributes (metadata, timestamps, MPAN/MPRN) `[S]` ← T-036, T-037, T-038, T-039, T-040, T-041
- [ ] **T-043** Ensure Energy Dashboard compatibility (state_class, device_class) `[S]` ← T-036, T-037
- [ ] **T-044** Write unit tests for sensor state calculations `[M]` ← T-043

## Phase 6: Automation Support

- [ ] **T-045** Implement octoha_off_peak_start/end events `[M]` ← T-038
- [ ] **T-046** Implement octoha_dispatch_start/end events `[M]` ← T-040
- [ ] **T-047** Document automation trigger examples in README `[S]` ← T-045, T-046
- [ ] **T-048** Write integration tests for event firing `[S]` ← T-046

## Phase 7: Diagnostics & Error Handling

- [ ] **T-049** Create `diagnostics.py` for debug data export (sanitized) `[S]` ← T-026
- [ ] **T-050** Implement graceful degradation on API outages (cached values) `[M]` ← T-033
- [ ] **T-051** Implement stale data indication in entity states `[S]` ← T-050
- [ ] **T-052** Add comprehensive DEBUG-level logging `[S]` ← T-012, T-028

## Phase 8: Documentation

- [ ] **T-053** Write README.md with project overview and features `[M]` ← T-043
- [ ] **T-054** Write installation guide (manual GitHub install) `[S]` ← T-053
- [ ] **T-055** Write configuration guide with screenshots `[S]` ← T-054
- [ ] **T-056** Write troubleshooting guide with common issues `[M]` ← T-055
- [ ] **T-057** Add inline code documentation (docstrings, type hints) `[M]` ← T-044
- [ ] **T-058** Create CHANGELOG.md `[XS]` ← T-053
- [x] **T-059** Create LICENSE file with MIT license and open-octopus attribution `[XS]` ← T-001

## Phase 9: Testing & Release

- [ ] **T-060** Run full test suite and achieve >80% coverage `[M]` ← T-044, T-048
- [ ] **T-061** Manual testing on personal HA instance (7-day stability run) `[L]` ← T-060
- [ ] **T-062** Validate gas readings against Smart Meter IHD `[M]` ← T-061
- [ ] **T-063** Fix bugs identified during testing `[M]` ← T-062
- [ ] **T-064** Create GitHub release v0.1.0 with release notes `[S]` ← T-063

---

## Legend

- `[XS]` Extra Small - trivial task
- `[S]` Small - straightforward task
- `[M]` Medium - moderate complexity
- `[L]` Large - significant effort
- `[XL]` Extra Large - major undertaking
- `←` Dependencies (tasks that must complete first)
