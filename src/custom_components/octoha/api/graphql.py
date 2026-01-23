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
    properties {
      addressLine1
      postcode
      electricityMeterPoints {
        mpan
        meters(includeInactive: false) {
          serialNumber
          smartDevices {
            deviceId
          }
        }
        agreements(active: true) {
          validFrom
          validTo
          tariff {
            ... on StandardTariff {
              tariffCode
              productCode
            }
            ... on HalfHourlyTariff {
              tariffCode
              productCode
            }
            ... on DayNightTariff {
              tariffCode
              productCode
            }
            ... on ThreeRateTariff {
              tariffCode
              productCode
            }
            ... on PrepayTariff {
              tariffCode
              productCode
            }
          }
        }
      }
      gasMeterPoints {
        mprn
        meters(includeInactive: false) {
          serialNumber
        }
        agreements(active: true) {
          validFrom
          validTo
          tariff {
            ... on StandardTariff {
              tariffCode
              productCode
            }
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

# ============================================================================
# Intelligent Octopus Queries
# ============================================================================

INTELLIGENT_DISPATCH_QUERY = """
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
query getLivePower($accountNumber: String!) {
  smartMeterTelemetry(accountNumber: $accountNumber) {
    demand
    readAt
  }
}
"""

LIVE_CONSUMPTION_QUERY = """
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


def build_live_consumption_variables(
    account_number: str,
    start_iso: str,
    end_iso: str,
) -> dict:
    """Build variables for live consumption query.

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
