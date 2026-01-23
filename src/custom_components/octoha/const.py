"""Constants for the Octoha integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

# Integration domain
DOMAIN: Final = "octoha"

# Integration version (should match manifest.json)
VERSION: Final = "0.1.0"

# Config entry keys
CONF_API_KEY: Final = "api_key"
CONF_ACCOUNT: Final = "account"
CONF_MPAN: Final = "mpan"
CONF_MPRN: Final = "mprn"
CONF_METER_SERIAL: Final = "meter_serial"
CONF_GAS_METER_SERIAL: Final = "gas_meter_serial"
CONF_REGION: Final = "region"

# Options keys
CONF_ELECTRICITY_INTERVAL: Final = "electricity_interval"
CONF_GAS_INTERVAL: Final = "gas_interval"
CONF_TARIFF_INTERVAL: Final = "tariff_interval"
CONF_DISPATCH_INTERVAL: Final = "dispatch_interval"

# API endpoints
GRAPHQL_URL: Final = "https://api.octopus.energy/v1/graphql/"
REST_API_URL: Final = "https://api.octopus.energy/v1"

# Update intervals (in seconds for options, timedelta for coordinators)
DEFAULT_ELECTRICITY_INTERVAL: Final = 300  # 5 minutes
DEFAULT_GAS_INTERVAL: Final = 300  # 5 minutes
DEFAULT_TARIFF_INTERVAL: Final = 1800  # 30 minutes
DEFAULT_DISPATCH_INTERVAL: Final = 300  # 5 minutes

UPDATE_INTERVAL_ELECTRICITY: Final = timedelta(seconds=DEFAULT_ELECTRICITY_INTERVAL)
UPDATE_INTERVAL_GAS: Final = timedelta(seconds=DEFAULT_GAS_INTERVAL)
UPDATE_INTERVAL_TARIFF: Final = timedelta(seconds=DEFAULT_TARIFF_INTERVAL)
UPDATE_INTERVAL_DISPATCH: Final = timedelta(seconds=DEFAULT_DISPATCH_INTERVAL)

# Token management
TOKEN_EXPIRY_BUFFER: Final = timedelta(minutes=5)
TOKEN_LIFETIME: Final = timedelta(hours=1)

# API request timeout (in seconds)
REQUEST_TIMEOUT: Final = 30

# Defaults
DEFAULT_REGION: Final = "J"  # Scotland

# Attribution
ATTRIBUTION: Final = "Data from Octopus Energy"

# Event names
EVENT_OFF_PEAK_START: Final = f"{DOMAIN}_off_peak_start"
EVENT_OFF_PEAK_END: Final = f"{DOMAIN}_off_peak_end"
EVENT_DISPATCH_START: Final = f"{DOMAIN}_dispatch_start"
EVENT_DISPATCH_END: Final = f"{DOMAIN}_dispatch_end"
