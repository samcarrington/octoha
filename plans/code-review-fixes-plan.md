# Plan: Code Review Fixes for Octoha Integration

## 1. Title

Resolve Code Review Findings from Branch fix/copilot-review-issues

## 2. Short description

Address all blocking, recommended, and nit-level findings from the comprehensive code review of the Octoha Home Assistant integration. Focus on test coverage gaps, security hardening, Home Assistant pattern compliance, and performance optimizations to prepare the integration for production release.

## 3. Current status

```yaml
owner: Sam Carrington <sam@example.com>
state: proposed
last_updated: 2026-01-23
blockers: []
```

## 4. Objectives

1. Achieve 90%+ test coverage for core integration modules (`__init__.py`, `api/` layer)
2. Eliminate all blocking security concerns (rate limiting, timeouts)
3. Align entity patterns with Home Assistant 2024+ best practices
4. Improve coordinator performance with concurrent API calls
5. Pass all CI checks (mypy, ruff, pytest) after implementation

## 5. Success criteria

| Name | Metric | Target | Verification |
|------|--------|--------|--------------|
| Test coverage | Overall line coverage | >= 90% | `pytest --cov` report |
| Core module coverage | Coverage for `__init__.py`, `api/*.py` | >= 95% | `pytest --cov` with module filter |
| CI pipeline | All checks pass | 100% pass | GitHub Actions workflow |
| Rate limit resilience | Handles 429 responses | Exponential backoff implemented | Unit test with mock 429 response |
| Request timeouts | All HTTP calls have explicit timeout | 30s default | Code review + unit test |
| Unique ID stability | Entities use MPAN/MPRN-based IDs | 100% of entities | Code inspection |

## 6. Scope

```yaml
in:
  - Add integration lifecycle tests (test_init.py)
  - Add REST client tests (test_api_rest.py)
  - Add GraphQL client tests (test_api_graphql.py)
  - Implement rate limit backoff in api/rest.py and api/auth.py
  - Add explicit request timeouts to all HTTP calls
  - Fix entity unique IDs to use stable identifiers
  - Add asyncio.gather() for concurrent coordinator updates
  - Clean up event listeners on integration unload
  - Fix bare except Exception clauses
  - Address all 6 nit-level polish items
out:
  - Adding new features beyond review scope
  - Refactoring API client architecture
  - Changing coordinator update intervals
  - Adding new sensors or entities
  - Modifying GraphQL queries
```

## 7. Stakeholders & Roles

| Name | Role | Responsibility | Contact |
|------|------|----------------|---------|
| Sam Carrington | Owner | Delivery and implementation | sam@example.com |
| Code Reviewer | Reviewer | Validate fixes address findings | N/A |

## 8. High-level timeline & milestones

1. M1 — Plan approved — 2026-01-24 — Sam Carrington
2. M2 — Blocking fixes complete (tests) — 2026-01-25 — Sam Carrington
3. M3 — Security fixes complete — 2026-01-26 — Sam Carrington
4. M4 — HA pattern fixes complete — 2026-01-26 — Sam Carrington
5. M5 — Performance fixes complete — 2026-01-27 — Sam Carrington
6. M6 — Nit fixes and polish — 2026-01-27 — Sam Carrington
7. M7 — PR ready for merge — 2026-01-27 — Sam Carrington

## 9. Task list

### Phase 1: Blocking Fixes (Test Coverage)

| ID | Title | Owner | Complexity | Dependencies | Done |
|----|-------|-------|------------|--------------|------|
| T-001 | Create tests/test_init.py with integration lifecycle tests | Sam Carrington | M | [] | false |
| T-002 | Test async_setup_entry success with electricity-only config | Sam Carrington | S | [T-001] | false |
| T-003 | Test async_setup_entry success with gas-only config | Sam Carrington | S | [T-001] | false |
| T-004 | Test async_setup_entry success with both meters | Sam Carrington | S | [T-001] | false |
| T-005 | Test async_setup_entry with Intelligent tariff (dispatch coordinator) | Sam Carrington | S | [T-001] | false |
| T-006 | Test async_setup_entry authentication failure raises ConfigEntryAuthFailed | Sam Carrington | S | [T-001] | false |
| T-007 | Test async_setup_entry connection failure raises ConfigEntryNotReady | Sam Carrington | S | [T-001] | false |
| T-008 | Test async_unload_entry cleans up API client | Sam Carrington | S | [T-001] | false |
| T-009 | Test async_unload_entry removes data from hass.data | Sam Carrington | S | [T-001] | false |
| T-010 | Test async_update_options triggers reload | Sam Carrington | S | [T-001] | false |
| T-011 | Test async_migrate_entry returns True | Sam Carrington | XS | [T-001] | false |
| T-012 | Create tests/test_api_rest.py for REST client | Sam Carrington | M | [] | false |
| T-013 | Test REST URL construction with valid parameters | Sam Carrington | S | [T-012] | false |
| T-014 | Test REST HTTP 200 success response parsing | Sam Carrington | S | [T-012] | false |
| T-015 | Test REST HTTP 401 raises AuthenticationError | Sam Carrington | S | [T-012] | false |
| T-016 | Test REST HTTP 429 raises RateLimitError | Sam Carrington | S | [T-012] | false |
| T-017 | Test REST HTTP 500 raises OctopusError | Sam Carrington | S | [T-012] | false |
| T-018 | Test extract_product_code with various tariff formats | Sam Carrington | S | [T-012] | false |
| T-019 | Create tests/test_api_graphql.py for GraphQL queries | Sam Carrington | S | [] | false |
| T-020 | Test GraphQL query string syntax validity | Sam Carrington | S | [T-019] | false |
| T-021 | Test build_account_variables helper | Sam Carrington | XS | [T-019] | false |
| T-022 | Test build_dispatch_variables helper | Sam Carrington | XS | [T-019] | false |

### Phase 2: Security Fixes

| ID | Title | Owner | Complexity | Dependencies | Done |
|----|-------|-------|------------|--------------|------|
| T-023 | Implement exponential backoff for 429 responses in api/rest.py | Sam Carrington | M | [] | false |
| T-024 | Implement exponential backoff for 429 responses in api/auth.py | Sam Carrington | S | [T-023] | false |
| T-025 | Create RateLimitError exception with retry_after field | Sam Carrington | S | [] | false |
| T-026 | Add explicit 30s timeout to all REST API calls | Sam Carrington | S | [] | false |
| T-027 | Add explicit 30s timeout to all GraphQL API calls | Sam Carrington | S | [T-026] | false |
| T-028 | Add explicit 30s timeout to token fetch calls | Sam Carrington | S | [T-026] | false |
| T-029 | Add tests for rate limit backoff behavior | Sam Carrington | S | [T-023, T-024] | false |
| T-030 | Add tests for request timeout behavior | Sam Carrington | S | [T-026, T-027] | false |

### Phase 3: Home Assistant Pattern Improvements

| ID | Title | Owner | Complexity | Dependencies | Done |
|----|-------|-------|------------|--------------|------|
| T-031 | Fix sensor unique IDs to use MPAN instead of entry_id | Sam Carrington | S | [] | false |
| T-032 | Fix binary_sensor unique IDs to use stable identifiers | Sam Carrington | S | [T-031] | false |
| T-033 | Change update_before_add=True to False in sensor.py | Sam Carrington | XS | [] | false |
| T-034 | Change update_before_add=True to False in binary_sensor.py | Sam Carrington | XS | [T-033] | false |
| T-035 | Add event listener cleanup on integration unload | Sam Carrington | S | [] | false |
| T-036 | Store event manager unsubscribe callbacks in runtime_data | Sam Carrington | S | [T-035] | false |
| T-037 | Call unsubscribe callbacks in async_unload_entry | Sam Carrington | S | [T-036] | false |
| T-038 | Add tests for event listener cleanup | Sam Carrington | S | [T-037] | false |

### Phase 4: Performance Optimizations

| ID | Title | Owner | Complexity | Dependencies | Done |
|----|-------|-------|------------|--------------|------|
| T-039 | Use asyncio.gather() in ElectricityCoordinator._async_update_data | Sam Carrington | S | [] | false |
| T-040 | Use asyncio.gather() in GasCoordinator._async_update_data | Sam Carrington | S | [T-039] | false |
| T-041 | Use asyncio.gather() in TariffCoordinator._async_update_data | Sam Carrington | S | [T-039] | false |
| T-042 | Handle individual failures from gather with return_exceptions=True | Sam Carrington | S | [T-039, T-040, T-041] | false |
| T-043 | Add tests for concurrent coordinator updates | Sam Carrington | S | [T-042] | false |

### Phase 5: Python Best Practice Fixes

| ID | Title | Owner | Complexity | Dependencies | Done |
|----|-------|-------|------------|--------------|------|
| T-044 | Replace bare except Exception with specific exceptions in coordinator.py | Sam Carrington | S | [] | false |
| T-045 | Replace bare except Exception with specific exceptions in config_flow.py | Sam Carrington | S | [T-044] | false |
| T-046 | Ensure all catch-all handlers use _LOGGER.exception() | Sam Carrington | XS | [T-044, T-045] | false |

### Phase 6: Nit/Polish Items

| ID | Title | Owner | Complexity | Dependencies | Done |
|----|-------|-------|------------|--------------|------|
| T-047 | Standardize logging to use %-style formatting throughout | Sam Carrington | S | [] | false |
| T-048 | Add explicit _attr_should_poll = False to base entity classes | Sam Carrington | XS | [] | false |
| T-049 | Add translation placeholders to config_flow forms | Sam Carrington | S | [] | false |
| T-050 | Reorganize test file structure for consistency | Sam Carrington | S | [] | false |
| T-051 | Add inline TODOs for known limitations in coordinator.py | Sam Carrington | XS | [] | false |
| T-052 | Replace magic numbers with named constants in api/client.py | Sam Carrington | S | [] | false |

### Phase 7: Final Validation

| ID | Title | Owner | Complexity | Dependencies | Done |
|----|-------|-------|------------|--------------|------|
| T-053 | Run full test suite and verify 90%+ coverage | Sam Carrington | S | [T-001 to T-052] | false |
| T-054 | Run mypy and verify no new errors | Sam Carrington | XS | [T-053] | false |
| T-055 | Run ruff and fix any linting issues | Sam Carrington | XS | [T-054] | false |
| T-056 | Update recommendations.md with resolution status | Sam Carrington | S | [T-055] | false |
| T-057 | Create commit with all fixes | Sam Carrington | S | [T-056] | false |
| T-058 | Push to fix/copilot-review-issues branch | Sam Carrington | XS | [T-057] | false |

## 10. Risks and mitigations

| ID | Description | Probability | Impact | Mitigation | Owner |
|----|-------------|-------------|--------|------------|-------|
| R-001 | Unique ID migration breaks existing entities | Medium | High | Add entity migration code; test with existing installation | Sam Carrington |
| R-002 | asyncio.gather changes coordinator error handling | Low | Medium | Use return_exceptions=True; handle each result individually | Sam Carrington |
| R-003 | Rate limit backoff adds complexity | Low | Low | Keep implementation simple; well-tested | Sam Carrington |
| R-004 | Test coverage target not achievable | Low | Medium | Prioritize critical paths; document uncovered edge cases | Sam Carrington |

## 11. Assumptions

- The `fix/copilot-review-issues` branch is the target for all changes
- Home Assistant core type stubs will continue to have some Pyright incompatibilities (mypy is authoritative)
- No breaking changes to Octopus Energy API during implementation
- All existing tests continue to pass after changes
- GitHub Actions CI environment remains available

## 12. Implementation approach / Technical narrative

### TL;DR
This plan addresses code review findings in three waves: (1) critical test coverage gaps, (2) security and HA pattern compliance, (3) performance and polish. Each wave is independently releasable.

### Architecture Decisions

**Rate Limit Backoff Strategy**

Implement exponential backoff with jitter for 429 responses:

```python
class RateLimitError(OctopusError):
    """Rate limit exceeded."""
    def __init__(self, message: str, retry_after: int = 60) -> None:
        super().__init__(message)
        self.retry_after = retry_after

async def _handle_rate_limit(self, response: aiohttp.ClientResponse) -> None:
    retry_after = int(response.headers.get("Retry-After", 60))
    raise RateLimitError(f"Rate limited, retry after {retry_after}s", retry_after=retry_after)
```

The coordinator will catch this and respect the retry_after value.

**Unique ID Migration**

Entity unique IDs will change from:
```
{entry_id}_electricity_consumption
```
To:
```
{mpan}_electricity_consumption
```

This provides stability across re-adds but requires entity migration for existing installations.

**Concurrent Coordinator Updates**

Transform sequential calls:
```python
# Before
consumption = await self.client.get_electricity_consumption()
daily_usage = await self.client.get_daily_usage()

# After
results = await asyncio.gather(
    self.client.get_electricity_consumption(),
    self.client.get_daily_usage(),
    return_exceptions=True
)
consumption = results[0] if not isinstance(results[0], Exception) else []
daily_usage = results[1] if not isinstance(results[1], Exception) else []
```

**Event Listener Cleanup**

Store unsubscribe callbacks:
```python
@dataclass
class OctohaRuntimeData:
    client: OctohaApiClient
    # ... existing fields
    event_unsubscribes: list[Callable[[], None]] = field(default_factory=list)
```

Clean up on unload:
```python
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Clean up event listeners
    for unsub in entry.runtime_data.event_unsubscribes:
        unsub()
    # ... rest of cleanup
```

### Testing Strategy

Each phase has corresponding tests:
- Phase 1: Unit tests for integration lifecycle and API clients
- Phase 2: Tests for rate limit behavior and timeout enforcement
- Phase 3: Tests for entity unique IDs and event cleanup
- Phase 4: Tests for concurrent coordinator behavior

### Rollback Strategy

Each phase is an independent commit. If issues arise:
1. Revert specific commits
2. Or revert entire phase
3. All changes are backwards compatible (except unique ID migration)

## 13. Testing & validation plan

### Unit Tests

| Scope | Files | Expected Coverage |
|-------|-------|-------------------|
| Integration lifecycle | test_init.py | 95% of `__init__.py` |
| REST client | test_api_rest.py | 90% of `api/rest.py` |
| GraphQL client | test_api_graphql.py | 85% of `api/graphql.py` |
| Rate limiting | test_api_rest.py | 100% of rate limit paths |
| Timeouts | test_api_*.py | 100% of timeout configuration |

### Integration Tests

- Test full setup/unload cycle with mock API
- Test coordinator updates with concurrent calls
- Test event firing and cleanup

### End-to-End Scenarios

| Scenario | Validation |
|----------|------------|
| Fresh installation | Config flow → setup → entities created |
| Reconfiguration | Options change → reload → new intervals |
| API outage | Coordinator fails → graceful degradation → recovery |
| Rate limiting | 429 response → backoff → retry → success |

## 14. Deployment plan & roll-back strategy

### Deployment Order

1. Merge plan to `plan/code-review-fixes` branch
2. Implement fixes on `fix/copilot-review-issues` branch
3. Run CI pipeline
4. Review and merge PR #3
5. Tag release

### Rollback Criteria

- Test coverage drops below 80%
- CI pipeline fails
- Existing functionality breaks

### Rollback Steps

1. Revert merge commit on main
2. Create hotfix branch
3. Cherry-pick valid fixes
4. Re-test and merge

## 15. Monitoring & observability

N/A - This is a code quality improvement plan, not a runtime feature.

Post-implementation, integration logs will show:
- Rate limit backoff events (`WARNING` level)
- Request timeout events (`ERROR` level)

## 16. Compliance, security & privacy considerations

### Security Checklist

- [x] API keys not logged
- [x] Tokens not logged
- [x] Error messages sanitized
- [ ] Rate limiting implemented (this plan)
- [ ] Request timeouts implemented (this plan)
- [x] Sensitive data redacted in diagnostics

### Privacy

No changes to data handling. Existing GDPR-compliant patterns maintained.

## 17. Communication plan

| Event | Channel | Recipients |
|-------|---------|------------|
| Plan approved | GitHub PR | Stakeholders |
| Implementation complete | GitHub PR comment | Reviewers |
| PR ready for merge | GitHub PR | Approvers |

## 18. Related documents & links

- [Recommendations (Review Findings)](/Users/Scarring/dev/octopus-ha/recommendations.md)
- [PR #3](https://github.com/samcarrington/octoha/pull/3)
- [Home Assistant Development Docs](https://developers.home-assistant.io/)
- [Plan Template](/Users/Scarring/dev/octopus-ha/plans/plan-template.md)

## 19. Appendix

### Task Summary by Phase

| Phase | Tasks | Total Complexity |
|-------|-------|------------------|
| Phase 1: Blocking (Tests) | T-001 to T-022 | 2M + 17S + 3XS |
| Phase 2: Security | T-023 to T-030 | 1M + 7S |
| Phase 3: HA Patterns | T-031 to T-038 | 6S + 2XS |
| Phase 4: Performance | T-039 to T-043 | 5S |
| Phase 5: Python Practices | T-044 to T-046 | 2S + 1XS |
| Phase 6: Polish | T-047 to T-052 | 4S + 2XS |
| Phase 7: Validation | T-053 to T-058 | 3S + 3XS |

### Complexity Totals

- XS: 11 tasks
- S: 44 tasks
- M: 3 tasks
- L: 0 tasks
- XL: 0 tasks

**Total: 58 tasks**

### Finding to Task Mapping

| Finding # | Description | Tasks |
|-----------|-------------|-------|
| 1 (Blocking) | Missing integration lifecycle tests | T-001 to T-011 |
| 2 (Blocking) | Missing REST/GraphQL tests | T-012 to T-022 |
| 3 (Recommended) | No rate limit backoff | T-023 to T-025, T-029 |
| 4 (Recommended) | Missing request timeouts | T-026 to T-028, T-030 |
| 5 (Recommended) | Unique IDs use entry_id | T-031, T-032 |
| 6 (Recommended) | update_before_add=True | T-033, T-034 |
| 7 (Recommended) | Bare except Exception | T-044 to T-046 |
| 8 (Recommended) | Sequential coordinator calls | T-039 to T-043 |
| 11 (Recommended) | Event listeners not cleaned up | T-035 to T-038 |
| 15 (Nit) | Mixed logging format | T-047 |
| 17 (Nit) | Explicit should_poll | T-048 |
| 16 (Nit) | Translation placeholders | T-049 |
| 18 (Nit) | Test organization | T-050 |
| 19 (Nit) | Inline TODOs | T-051 |
| 20 (Nit) | Magic numbers | T-052 |
