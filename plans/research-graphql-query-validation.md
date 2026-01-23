# GraphQL Query Validation Research

## Context

This document captures findings from validating the Octoha GraphQL queries against production-tested reference implementations. The goal was to ensure our queries match the current Octopus Energy API schema and will work correctly in production.

## Reference Sources

Two production-tested implementations were used for validation:

1. **open-octopus** (https://github.com/abracadabra50/open-octopus)
   - MIT licensed Python client and Mac app
   - Our original inspiration source
   - Last updated: December 2024

2. **BottlecapDave's HomeAssistant-OctopusEnergy** (https://github.com/BottlecapDave/HomeAssistant-OctopusEnergy)
   - The most mature Home Assistant integration for Octopus Energy
   - Actively maintained with large user base
   - Provides the most reliable API patterns

## Validation Summary

| Query | Status | Severity | Action Required |
|-------|--------|----------|-----------------|
| Auth Mutation | VALID | - | None |
| ACCOUNT_QUERY | MOSTLY VALID | Low | Optional enhancement |
| ACCOUNT_NUMBER_QUERY | VALID | - | None |
| INTELLIGENT_DISPATCH_QUERY | NEEDS UPDATE | **Critical** | Must fix before release |
| INTELLIGENT_DEVICE_QUERY | NEEDS UPDATE | Medium | Should fix |
| SAVING_SESSIONS_QUERY | MINOR DIFF | Medium | Should fix |
| LIVE_POWER_QUERY | NEEDS UPDATE | **Critical** | Must fix before release |
| LIVE_CONSUMPTION_QUERY | NEEDS UPDATE | **Critical** | Must fix before release |
| PRODUCTS_QUERY | VALID | - | None |
| WHEEL_OF_FORTUNE_QUERY | DIFFERENT API | Low | Optional fix |

## Detailed Findings

### 1. Authentication Mutation

**Status:** VALID

**Our Implementation (`auth.py`):**
```graphql
mutation krakenTokenAuthentication($apiKey: String!) {
  obtainKrakenToken(input: { APIKey: $apiKey }) {
    token
  }
}
```

**Reference Implementation:**
```graphql
mutation {
  obtainKrakenToken(input: { APIKey: "{api_key}" }) {
    token
    refreshToken
    refreshExpiresIn
  }
}
```

**Analysis:** 
- Core structure is identical and will work correctly
- Reference implementations also request `refreshToken` and `refreshExpiresIn` for better token lifecycle management

**Recommendation:** 
- No immediate changes needed
- Consider adding refresh token support in a future enhancement

---

### 2. ACCOUNT_QUERY

**Status:** MOSTLY VALID

**Our Implementation (`graphql.py`):**
```graphql
query getAccount($accountNumber: String!) {
  account(accountNumber: $accountNumber) {
    number
    balance
    properties {
      addressLine1
      postcode
      electricityMeterPoints {
        mpan
        meters(includeInactive: false) {
          serialNumber
          smartDevices { deviceId }
        }
        agreements(active: true) {
          validFrom
          validTo
          tariff {
            ... on StandardTariff { tariffCode, productCode }
            ... on HalfHourlyTariff { tariffCode, productCode }
            ... on DayNightTariff { tariffCode, productCode }
            ... on ThreeRateTariff { tariffCode, productCode }
            ... on PrepayTariff { tariffCode, productCode }
          }
        }
      }
      gasMeterPoints { ... }
    }
  }
}
```

**Reference Implementation (BottlecapDave):**
```graphql
query {
  account(accountNumber: "{account_id}") {
    electricityAgreements(active: true) {
      meterPoint {
        mpan
        meters(includeInactive: false) {
          serialNumber
          smartImportElectricityMeter { deviceId }
        }
        agreements(includeInactive: true) {
          validFrom
          validTo
          tariff {
            ... on TariffType { productCode, tariffCode }
          }
        }
      }
    }
    gasAgreements(active: true) {
      meterPoint { ... }
    }
  }
}
```

**Key Differences:**
1. We use `properties.electricityMeterPoints` vs reference uses `electricityAgreements.meterPoint`
2. We use `smartDevices` vs reference uses `smartImportElectricityMeter`/`smartExportElectricityMeter`
3. Reference uses generic `TariffType` fragment vs our specific tariff type fragments

**Analysis:**
- Both approaches may work, but the reference approach is more aligned with current API structure
- Our specific tariff fragments (StandardTariff, HalfHourlyTariff, etc.) may be more future-proof

**Recommendation:**
- Test our current implementation against live API
- Consider adopting `electricityAgreements`/`gasAgreements` pattern if issues arise

---

### 3. ACCOUNT_NUMBER_QUERY

**Status:** VALID

**Our Implementation:**
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

**Analysis:** Standard GraphQL connection pattern for account discovery. Matches expected API structure.

**Recommendation:** No changes needed.

---

### 4. INTELLIGENT_DISPATCH_QUERY

**Status:** NEEDS UPDATE - CRITICAL

**Our Implementation:**
```graphql
query getIntelligentDispatches($accountNumber: String!) {
  plannedDispatches(accountNumber: $accountNumber) {
    start
    end
    source
  }
  completedDispatches(accountNumber: $accountNumber) {
    start
    end
    delta
  }
}
```

**Reference Implementation (BottlecapDave):**
```graphql
query {
  devices(accountNumber: "{account_id}", deviceId: "{device_id}") {
    id
    status { currentState }
  }
  flexPlannedDispatches(deviceId: "{device_id}") {
    start
    end
    type
    energyAddedKwh
  }
  completedDispatches(accountNumber: "{account_id}") {
    start
    end
    delta
    meta { source, location }
  }
}
```

**Critical Issues:**
1. `plannedDispatches` query appears deprecated - should use `flexPlannedDispatches`
2. `flexPlannedDispatches` requires `deviceId` parameter, not `accountNumber`
3. We're missing the `type` and `energyAddedKwh` fields
4. `completedDispatches` should include `meta { source, location }`

**Impact:** Dispatch features will likely fail or return incomplete data.

**Recommendation:**
1. Update to use `flexPlannedDispatches(deviceId: ...)` 
2. Add device discovery flow to get device ID first
3. Add missing fields to response handling

---

### 5. INTELLIGENT_DEVICE_QUERY

**Status:** NEEDS UPDATE - MEDIUM

**Our Implementation:**
```graphql
query getIntelligentDevice($accountNumber: String!) {
  registeredKrakenflexDevice(accountNumber: $accountNumber) {
    krakenflexDeviceId
    vehicleMake
    vehicleModel
    vehicleBatterySizeInKwh
    chargePointMake
    chargePointModel
    chargePointPowerInKw
    status { current }
    suspended
    hasToken
  }
}
```

**Reference Implementation:**
```graphql
query {
  electricVehicles {
    make
    models { model, batterySize }
  }
  chargePointVariants {
    make
    models { model, powerInKw }
  }
  devices(accountNumber: "{account_id}") {
    id
    provider
    deviceType
    status { current }
    __typename
    ... on SmartFlexVehicle { make, model }
    ... on SmartFlexChargePoint { make, model }
  }
}
```

**Key Differences:**
1. Reference uses `devices(accountNumber: ...)` instead of `registeredKrakenflexDevice`
2. Reference queries EV/charger catalogs separately for battery/power specs
3. Uses GraphQL fragments for device type-specific fields

**Analysis:** The `registeredKrakenflexDevice` query may still work but appears to be older API.

**Recommendation:** Update to use `devices` query for better compatibility.

---

### 6. SAVING_SESSIONS_QUERY

**Status:** MINOR DIFFERENCE - MEDIUM

**Our Implementation:**
```graphql
query getSavingSessions($accountNumber: String!) {
  savingSessions(accountNumber: $accountNumber) {
    events {
      code
      startAt
      endAt
      rewardPerKwh
    }
    signedUp
  }
}
```

**Reference Implementation:**
```graphql
query {
  savingSessions {
    events(getDevEvents: false) {
      id
      code
      rewardPerKwhInOctoPoints
      startAt
      endAt
      devEvent
    }
    account(accountNumber: "{account_id}") {
      hasJoinedCampaign
      joinedEvents {
        eventId
        startAt
        endAt
        rewardGivenInOctoPoints
      }
    }
  }
}
```

**Key Differences:**
1. Field name: `rewardPerKwh` vs `rewardPerKwhInOctoPoints`
2. Missing `id` field in events
3. Different structure for account-specific data
4. Reference filters out dev events with `getDevEvents: false`

**Impact:** May cause parsing failures if API returns `rewardPerKwhInOctoPoints`.

**Recommendation:** Update field name and add missing fields.

---

### 7. LIVE_POWER_QUERY & LIVE_CONSUMPTION_QUERY

**Status:** NEEDS UPDATE - CRITICAL

**Our Implementation:**
```graphql
query getLivePower($accountNumber: String!) {
  smartMeterTelemetry(accountNumber: $accountNumber) {
    demand
    readAt
  }
}

query getLiveConsumption($accountNumber: String!, $start: DateTime!, $end: DateTime!) {
  smartMeterTelemetry(
    accountNumber: $accountNumber
    grouping: HALF_HOURLY
    start: $start
    end: $end
  ) {
    consumption
    readAt
  }
}
```

**Reference Implementation:**
```graphql
query {
  smartMeterTelemetry(
    deviceId: "{device_id}"
    grouping: HALF_HOURLY 
    start: "{period_from}"
    end: "{period_to}"
  ) {
    readAt
    consumption
    consumptionDelta
    demand
    export
  }
}
```

**Critical Issues:**
1. API uses `deviceId` parameter, NOT `accountNumber`
2. Missing `consumptionDelta` and `export` fields
3. Requires device discovery before telemetry can be fetched

**Impact:** Live power/consumption queries will fail.

**Recommendation:**
1. Update to use `deviceId` parameter
2. Implement device discovery from account data
3. Add missing response fields

---

### 8. PRODUCTS_QUERY

**Status:** VALID

**Our Implementation:**
```graphql
query getProducts {
  products(isAvailable: true, isOccupierOwned: true) {
    code
    displayName
    description
    fullName
    term
    isVariable
    isBusiness
    isGreen
    isTracker
    isPrepay
  }
}
```

**Analysis:** Standard products query structure. Should work correctly.

**Recommendation:** No changes needed.

---

### 9. WHEEL_OF_FORTUNE_QUERY

**Status:** DIFFERENT API - LOW PRIORITY

**Our Implementation:**
```graphql
query getWheelOfFortune($accountNumber: String!) {
  wheelOfFortuneSpins(accountNumber: $accountNumber) {
    electricity { remainingSpinsThisMonth, lastSpinWin }
    gas { remainingSpinsThisMonth, lastSpinWin }
  }
}
```

**Reference Implementation:**
```graphql
query {
  electricity: wheelOfFortuneSpinsAllowed(fuelType: ELECTRICITY, accountNumber: "{account_id}") {
    spinsAllowed
  }
  gas: wheelOfFortuneSpinsAllowed(fuelType: GAS, accountNumber: "{account_id}") {
    spinsAllowed
  }
}
```

**Key Differences:**
1. Different query name: `wheelOfFortuneSpins` vs `wheelOfFortuneSpinsAllowed`
2. Different parameter structure
3. Reference uses backend URL (`api.backend.octopus.energy`) not main API

**Analysis:** Wheel of Fortune is a lower-priority feature and may have multiple valid API patterns.

**Recommendation:** Test current implementation; update if needed for release.

---

## Priority Action Items

### Critical (Must Fix Before Release)

1. **INTELLIGENT_DISPATCH_QUERY**
   - Update to use `flexPlannedDispatches(deviceId: ...)`
   - Implement device ID discovery flow
   - Update response parsing for new fields

2. **LIVE_POWER_QUERY / LIVE_CONSUMPTION_QUERY**
   - Change from `accountNumber` to `deviceId` parameter
   - Implement device ID discovery (can share with dispatch)
   - Add missing response fields

### Medium (Should Fix Before Release)

3. **SAVING_SESSIONS_QUERY**
   - Update `rewardPerKwh` to `rewardPerKwhInOctoPoints`
   - Add `id` field to events
   - Consider adopting reference query structure

4. **INTELLIGENT_DEVICE_QUERY**
   - Evaluate switching to `devices` query
   - May be required for dispatch device discovery

### Low (Optional Enhancements)

5. **Auth Enhancement**
   - Add `refreshToken` and `refreshExpiresIn` support

6. **ACCOUNT_QUERY**
   - Consider `electricityAgreements`/`gasAgreements` pattern

7. **WHEEL_OF_FORTUNE_QUERY**
   - Update if feature is actively used

---

## Implementation Notes

### Device ID Discovery Pattern

Several queries require a `deviceId` that must be discovered from account data. The reference implementation handles this by:

1. Fetching account data with `smartImportElectricityMeter { deviceId }`
2. Storing device IDs during account setup
3. Using stored device IDs for telemetry/dispatch queries

**Suggested Implementation:**
```python
async def _discover_meter_device(self) -> Optional[str]:
    """Discover smart meter device ID from account data."""
    account = await self.get_account()
    for prop in account.properties:
        for meter_point in prop.electricity_meter_points:
            for meter in meter_point.meters:
                if meter.device_id:
                    return meter.device_id
    return None
```

### API Endpoints

- Main API: `https://api.octopus.energy/v1/graphql/`
- Backend API: `https://api.backend.octopus.energy/v1/graphql/` (used for some queries like Wheel of Fortune)

---

## Testing Recommendations

1. **Unit Tests:** Update mocks to match new query structures
2. **Integration Tests:** Test against live API with valid credentials
3. **Error Handling:** Ensure graceful degradation if queries fail

---

## References

- [open-octopus client.py](https://github.com/abracadabra50/open-octopus/blob/main/src/open_octopus/client.py)
- [BottlecapDave API Client](https://github.com/BottlecapDave/HomeAssistant-OctopusEnergy/blob/develop/custom_components/octopus_energy/api_client/__init__.py)
- [Octopus Energy Developer API](https://developer.octopus.energy/) (official, but limited GraphQL docs)

---

## Document History

| Date | Author | Changes |
|------|--------|---------|
| 2026-01-23 | Developer Agent | Initial research and validation |
