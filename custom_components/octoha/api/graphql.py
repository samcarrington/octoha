"""GraphQL queries for Octopus Energy API.

Query definitions adapted from the open-octopus project
(https://github.com/abracadabra50/open-octopus) under MIT license.
"""

from __future__ import annotations

# ============================================================================
# Account Queries
# ============================================================================

ACCOUNT_QUERY = """
query getAccount($accountNumber: String!) {
  account(accountNumber: $accountNumber) {
    number
    balance
    electricityAgreements(active: true) {
      meterPoint {
        mpan
        meters(includeInactive: false) {
          serialNumber
          smartImportElectricityMeter {
            deviceId
          }
        }
        agreements {
          validFrom
          validTo
          tariff {
            ... on TariffType {
              tariffCode
              productCode
            }
          }
        }
      }
    }
    gasAgreements(active: true) {
      meterPoint {
        mprn
        meters(includeInactive: false) {
          serialNumber
          smartGasMeter {
            deviceId
          }
        }
        agreements {
          validFrom
          validTo
          tariff {
            tariffCode
            productCode
          }
        }
      }
    }
  }
}
"""

ACCOUNT_NUMBER_QUERY = """
query getAccountNumber {
  viewer {
    accounts {
      number
    }
  }
}
"""

# ============================================================================
# Intelligent Octopus Queries
# ============================================================================

INTELLIGENT_DISPATCH_QUERY = """
query getIntelligentDispatches($accountNumber: String!, $deviceId: String!) {
  flexPlannedDispatches(deviceId: $deviceId) {
    start
    end
    type
    energyAddedKwh
  }
  completedDispatches(accountNumber: $accountNumber) {
    start
    end
    delta
    meta {
      source
      location
    }
  }
}
"""

# Legacy dispatch query for accounts without device ID
INTELLIGENT_DISPATCH_QUERY_LEGACY = """
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
"""

INTELLIGENT_DEVICE_QUERY = """
query getIntelligentDevices($accountNumber: String!) {
  devices(accountNumber: $accountNumber) {
    id
    provider
    deviceType
    status {
      current
    }
    ... on SmartFlexVehicle {
      make
      model
      batterySize
    }
    ... on SmartFlexChargePoint {
      make
      model
      powerInKw
    }
  }
}
"""

# Legacy device query for backward compatibility
INTELLIGENT_DEVICE_QUERY_LEGACY = """
query getIntelligentDevice($accountNumber: String!) {
  registeredKrakenflexDevice(accountNumber: $accountNumber) {
    krakenflexDeviceId
    vehicleMake
    vehicleModel
    vehicleBatterySizeInKwh
    chargePointMake
    chargePointModel
    chargePointPowerInKw
    status {
      current
    }
    suspended
    hasToken
  }
}
"""

SMART_DEVICE_QUERY = """
query getSmartDevice($accountNumber: String!) {
  smartDevice(accountNumber: $accountNumber) {
    deviceId
    deviceType
    authorizationStatus
  }
}
"""

# ============================================================================
# Saving Sessions / Free Electricity Queries
# ============================================================================

SAVING_SESSIONS_QUERY = """
query getSavingSessions($accountNumber: String!) {
  savingSessions {
    events(getDevEvents: false) {
      id
      code
      startAt
      endAt
      rewardPerKwhInOctoPoints
      devEvent
    }
    account(accountNumber: $accountNumber) {
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
"""

JOINED_SESSIONS_QUERY = """
query getJoinedSessions($accountNumber: String!) {
  joinedSavingSessionEvents(accountNumber: $accountNumber) {
    code
    startAt
    endAt
    rewardPerKwh
  }
}
"""

# ============================================================================
# Live Power Queries (requires Home Mini)
# ============================================================================

LIVE_POWER_QUERY = """
query getLivePower($deviceId: String!) {
  smartMeterTelemetry(deviceId: $deviceId) {
    demand
    readAt
    consumption
    consumptionDelta
    export
  }
}
"""

LIVE_CONSUMPTION_QUERY = """
query getLiveConsumption($deviceId: String!, $start: DateTime!, $end: DateTime!) {
  smartMeterTelemetry(
    deviceId: $deviceId
    grouping: HALF_HOURLY
    start: $start
    end: $end
  ) {
    consumption
    consumptionDelta
    demand
    export
    readAt
  }
}
"""

# Legacy queries for accounts without device ID
LIVE_POWER_QUERY_LEGACY = """
query getLivePower($accountNumber: String!) {
  smartMeterTelemetry(accountNumber: $accountNumber) {
    demand
    readAt
  }
}
"""

LIVE_CONSUMPTION_QUERY_LEGACY = """
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
"""

# ============================================================================
# Product and Tariff Queries
# ============================================================================

PRODUCTS_QUERY = """
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
"""

# ============================================================================
# Wheel of Fortune Queries
# ============================================================================

WHEEL_OF_FORTUNE_QUERY = """
query getWheelOfFortune($accountNumber: String!) {
  wheelOfFortuneSpins(accountNumber: $accountNumber) {
    electricity {
      remainingSpinsThisMonth
      lastSpinWin
        }
    gas {
      remainingSpinsThisMonth
      lastSpinWin
    }
  }
}
"""

# ============================================================================
# Helper to build account query from account number
# ============================================================================


def build_account_variables(account_number: str) -> dict:
    """Build variables for account queries.

    Args:
        account_number: Octopus account number.

    Returns:
        Variable dictionary for GraphQL query.
    """
    return {"accountNumber": account_number}


def build_dispatch_variables(account_number: str, device_id: str) -> dict:
    """Build variables for dispatch queries.

    Args:
        account_number: Octopus account number.
        device_id: Smart device ID for flexPlannedDispatches.

    Returns:
        Variable dictionary for GraphQL query.
    """
    return {"accountNumber": account_number, "deviceId": device_id}


def build_device_variables(device_id: str) -> dict:
    """Build variables for device-based queries.

    Args:
        device_id: Smart device ID.

    Returns:
        Variable dictionary for GraphQL query.
    """
    return {"deviceId": device_id}


def build_live_consumption_variables(
    device_id: str,
    start_iso: str,
    end_iso: str,
) -> dict:
    """Build variables for live consumption query.

    Args:
        device_id: Smart device ID.
        start_iso: Start datetime in ISO 8601 format.
        end_iso: End datetime in ISO 8601 format.

    Returns:
        Variable dictionary for GraphQL query.
    """
    return {
        "deviceId": device_id,
        "start": start_iso,
        "end": end_iso,
    }


def build_live_consumption_variables_legacy(
    account_number: str,
    start_iso: str,
    end_iso: str,
) -> dict:
    """Build variables for legacy live consumption query.

    Args:
        account_number: Octopus account number.
        start_iso: Start datetime in ISO 8601 format.
        end_iso: End datetime in ISO 8601 format.

    Returns:
        Variable dictionary for GraphQL query.
    """
    return {
        "accountNumber": account_number,
        "start": start_iso,
        "end": end_iso,
    }
