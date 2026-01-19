# Changelog

All notable changes to the Octoha project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Diagnostics export with automatic redaction of sensitive data (API keys, MPAN/MPRN)
- Graceful degradation during API outages with cached data display
- Stale data indication via entity attributes (`is_stale`, `data_age_seconds`)
- Comprehensive DEBUG-level logging for troubleshooting
- Complete documentation (README, installation, configuration, troubleshooting guides)

## [0.1.0] - 2026-01-19

### Added

#### Core Integration
- Home Assistant custom integration for Octopus Energy smart meter data
- Config flow with API key validation and meter discovery
- Options flow for configuring update intervals
- MIT License with open-octopus attribution

#### API Client Layer
- GraphQL authentication with token refresh and expiry tracking
- REST API consumption and tariff endpoint support
- Custom exception classes with error message sanitisation
- Input validation for MPAN/MPRN parameters

#### Sensors
- `sensor.octoha_electricity_consumption` - Latest half-hourly electricity reading (kWh)
- `sensor.octoha_electricity_daily_usage` - Today's total electricity usage (kWh)
- `sensor.octoha_electricity_rate` - Current electricity rate (p/kWh)
- `sensor.octoha_gas_consumption` - Latest gas reading (kWh)
- `sensor.octoha_gas_daily_usage` - Today's gas usage (kWh)
- `sensor.octoha_gas_rate` - Current gas rate (p/kWh)
- `sensor.octoha_next_dispatch` - Next Intelligent dispatch timestamp

#### Binary Sensors
- `binary_sensor.octoha_off_peak_rate` - ON during off-peak electricity periods
- `binary_sensor.octoha_dispatch_active` - ON during Intelligent dispatch windows

#### Automation Events
- `octoha_off_peak_start` - Fired when off-peak period begins
- `octoha_off_peak_end` - Fired when off-peak period ends
- `octoha_dispatch_start` - Fired when Intelligent dispatch begins
- `octoha_dispatch_end` - Fired when Intelligent dispatch ends

#### Data Coordinators
- `ElectricityCoordinator` - 5-minute electricity consumption updates
- `GasCoordinator` - 5-minute gas consumption updates
- `TariffCoordinator` - 30-minute tariff rate updates with off-peak detection
- `DispatchCoordinator` - 5-minute Intelligent dispatch schedule updates

#### Data Models
- `Account`, `MeterPoint`, `Agreement` models for account structure
- `Consumption`, `DailyUsage` models for meter readings
- `Tariff`, `CurrentRate` models for tariff information
- `Dispatch`, `DispatchSource` models for Intelligent scheduling

#### Home Assistant Integration
- Energy Dashboard compatible sensors (`state_class: total_increasing`)
- Device grouping by Octopus account
- Entity attributes with MPAN/MPRN, tariff details, and timestamps
- Automatic entity naming following HA conventions

### Technical Details
- Python 3.11+ required
- Home Assistant 2024.1.0+ required
- Async/await architecture throughout
- Comprehensive test suite (255+ tests)
- Ruff linting with strict configuration

### Acknowledgements
- API patterns derived from [open-octopus](https://github.com/abracadabra50/open-octopus)

---

[Unreleased]: https://github.com/samcarrington/octoha/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/samcarrington/octoha/releases/tag/v0.1.0
