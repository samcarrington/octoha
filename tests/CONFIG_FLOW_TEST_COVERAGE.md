# Octoha Config Flow - Comprehensive Test Suite

**Test File Location:** `tests/test_config_flow.py`
**Total Lines:** 806
**Status:** ✅ Config flow implemented at `src/custom_components/octoha/config_flow.py`

## Overview

This is a comprehensive, behavior-driven test suite for the Octoha Home Assistant integration config flow. The config flow has been implemented and includes:

- User step for API key validation
- Account number discovery from API key
- Meter selection for accounts with multiple meters
- Proper error handling

The tests serve as verification that the implementation covers:

1. **Expected user interactions** (form submission, meter selection)
2. **API interaction patterns** (credential validation, account fetching)
3. **Error handling scenarios** (invalid API keys, connection failures)
4. **Edge cases and boundary conditions** (multiple meters, no meters, gas-only, etc.)

## Test Structure

### Test Classes

#### 1. **TestOctohaConfigFlow** (Main Test Suite)

Comprehensive tests covering all config flow scenarios.

#### 2. **TestOctohaConfigFlowIntegration** (Integration Tests)

End-to-end tests verifying complete user flows.

## Test Coverage (16 Tests Total)

### ✅ User Step Tests - Happy Path (2 tests)

#### `test_form_shows_user_step`

- **Scenario:** Config flow initialization
- **Expected Behavior:**
  - Form is displayed with `user` step
  - `api_key` field is present
  - Form schema is correctly configured

#### `test_user_step_success_single_meter`

- **Scenario:** User enters valid API key for single-meter account
- **Expected Behavior:**
  - `validate_credentials()` succeeds
  - `get_account()` returns account with one meter
  - Config entry created immediately (no meter selection)
  - Entry contains: api_key, account, mpan, meter_serial

#### `test_user_step_success_multiple_meters`

- **Scenario:** User enters valid API key for multi-meter account
- **Expected Behavior:**
  - `validate_credentials()` succeeds
  - `get_account()` returns account with multiple meters
  - Flow proceeds to `meter_selection` step
  - Meter options are displayed

### ❌ User Step Tests - Error Handling (3 tests)

#### `test_user_step_invalid_api_key`

- **Scenario:** User enters invalid/expired API key
- **Expected Behavior:**
  - `validate_credentials()` raises `AuthenticationError`
  - Form error key: `"invalid_api_key"`
  - User can retry

#### `test_user_step_cannot_connect`

- **Scenario:** API connection fails
- **Expected Behavior:**
  - `validate_credentials()` raises `OctopusError`
  - Form error key: `"cannot_connect"`
  - User can retry

#### `test_user_step_unknown_error`

- **Scenario:** Unexpected exception during validation
- **Expected Behavior:**
  - Generic exception raised
  - Form error key: `"unknown"`
  - User can retry

### 🎯 Meter Selection Step Tests (2 tests)

#### `test_meter_step_displays_options`

- **Scenario:** Meter selection form presentation
- **Expected Behavior:**
  - All electricity meter points displayed
  - All gas meter points displayed
  - Proper labels for each meter

#### `test_meter_step_creates_entry`

- **Scenario:** User selects meters and completes flow
- **Expected Behavior:**
  - Config entry created with correct data
  - Entry contains all meter references
  - Entry title uses account number

### 🚫 Duplicate Account Tests (1 test)

#### `test_abort_already_configured`

- **Scenario:** User attempts to add same account twice
- **Expected Behavior:**
  - Flow detects existing entry
  - Flow aborts with reason: `"already_configured"`

### 📊 Edge Cases - Account Data Variations (3 tests)

#### `test_account_with_no_meters`

- **Scenario:** Account has no electricity or gas meters
- **Expected Behavior:**
  - Account validation fails
  - Error displayed
  - Entry not created

#### `test_account_electricity_only`

- **Scenario:** Account has only electricity meter (no gas)
- **Expected Behavior:**
  - Config entry created
  - Contains MPAN data only
  - MPRN/gas data are None/absent

#### `test_account_gas_only`

- **Scenario:** Account has only gas meter (no electricity)
- **Expected Behavior:**
  - Config entry created
  - Contains MPRN data only
  - MPAN/electricity data are None/absent

### 🔍 Input Validation Tests (2 tests)

#### `test_user_step_empty_api_key`

- **Scenario:** User submits empty API key
- **Expected Behavior:**
  - Input rejected before API call
  - Form validation error displayed

#### `test_user_step_whitespace_api_key`

- **Scenario:** User submits whitespace-only API key
- **Expected Behavior:**
  - Whitespace rejected
  - Form validation error displayed

### 🏷️ Config Entry Title Tests (1 test)

#### `test_config_entry_title_format`

- **Scenario:** Config entry title formatting
- **Expected Behavior:**
  - Entry title is account number (e.g., "A-FB05ED6C")
  - Matches expected format

### 🔄 Integration Tests (2 tests)

#### `test_complete_flow_single_meter`

- **Complete flow:** init → form → validate → fetch → create entry
- **Path:** Single meter (no meter selection step)

#### `test_complete_flow_multiple_meters`

- **Complete flow:** init → form → validate → fetch → meter selection → create entry
- **Path:** Multi-meter with selection step

## Config Flow Requirements Covered

| Requirement                             | Tests Covering                                             |
| --------------------------------------- | ---------------------------------------------------------- |
| User step displays api_key field        | `test_form_shows_user_step`                                |
| Validate credentials                    | All user step + integration tests                          |
| Fetch account data                      | All success tests + integration tests                      |
| Show meter selection if multiple meters | `test_user_step_success_multiple_meters`, meter step tests |
| Handle invalid_api_key error            | `test_user_step_invalid_api_key`                           |
| Handle cannot_connect error             | `test_user_step_cannot_connect`                            |
| Handle unknown errors                   | `test_user_step_unknown_error`                             |
| Abort if account already configured     | `test_abort_already_configured`                            |
| Create entry with correct data          | All success tests                                          |
| Support single meter config             | `test_user_step_success_single_meter`                      |
| Support multi-meter config              | `test_user_step_success_multiple_meters`                   |

## Test Fixtures

### Account Fixtures

- **`single_meter_account`**: Single electricity meter with tariff agreement
- **`multi_meter_account`**: Electricity + gas meters with tariff agreements

### Mock Fixtures (from conftest.py)

- **`mock_api_client`**: Mocked OctohaApiClient
- **`api_key`**: "sk_test_abc123def456"
- **`account_number`**: "A-FB05ED6C"
- **`mpan`**: "1234567890123"
- **`mprn`**: "1234567890"
- **`meter_serial`**: "20P1234567"
- **`gas_meter_serial`**: "G4P12345678"

## Expected Test Status

### Implementation Status

The config flow is implemented at `src/custom_components/octoha/config_flow.py`.

Key features:

- Account number discovery from API key via GraphQL
- Meter selection persists user choices
- Proper detection of multiple meter points
- Standard options flow registration pattern

## Implementation Checklist

The config flow implementation should:

1. **Extend `config_entries.ConfigFlow`**
2. **Implement `async_step_user()`**
   - Display form with `CONF_API_KEY`
   - Validate credentials
   - Fetch account
   - Route: single meter → CREATE_ENTRY; multiple meters → meter_selection
3. **Implement `async_step_meter_selection()`**
   - Display meter selection form
   - Create entry with selected meters
4. **Implement deduplication**
   - Prevent duplicate account entries
   - Use account number as unique identifier

## Running the Tests

```bash
cd /Users/Scarring/dev/octopus-ha

# Run all config flow tests (expect failures)
pytest tests/test_config_flow.py -v

# Run specific test
pytest tests/test_config_flow.py::TestOctohaConfigFlow::test_user_step_invalid_api_key -v

# Run with more detail
pytest tests/test_config_flow.py -vv --tb=short
```
