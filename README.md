# Octoha - Octopus Energy for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]

[![Project Maintenance][maintenance-shield]][user_profile]

A Home Assistant custom integration for Octopus Energy smart meter data. Get accurate electricity and gas consumption readings, real-time tariff rates, and intelligent dispatch schedules directly in your Home Assistant dashboard.

## Why Octoha?

The Bright app and SMETS integration often provide inaccurate energy data, and gas readings are frequently broken. Octoha pulls data directly from the Octopus Energy API, delivering:

- **Accurate gas readings** that match your Smart Meter IHD (In-Home Display)
- **Real-time electricity consumption** data updated every 5 minutes
- **Tariff rate tracking** for Agile, Tracker, Go, and flexible tariffs
- **Intelligent Octopus Go** dispatch schedule integration
- **Energy Dashboard** compatible sensors for long-term statistics

## Features

### Sensors

| Sensor | Description |
|--------|-------------|
| `sensor.octoha_electricity_consumption` | Latest half-hourly electricity reading (kWh) |
| `sensor.octoha_electricity_daily_usage` | Today's total electricity usage (kWh) |
| `sensor.octoha_electricity_rate` | Current electricity rate (p/kWh) |
| `sensor.octoha_gas_consumption` | Latest gas reading (kWh) |
| `sensor.octoha_gas_daily_usage` | Today's total gas usage (kWh) |
| `sensor.octoha_gas_rate` | Current gas rate (p/kWh) |
| `sensor.octoha_next_dispatch` | Next Intelligent dispatch start time |

### Binary Sensors

| Binary Sensor | Description |
|---------------|-------------|
| `binary_sensor.octoha_off_peak_rate` | ON when electricity rate is off-peak |
| `binary_sensor.octoha_dispatch_active` | ON when Intelligent dispatch is active |

### Automation Events

Octoha fires events when tariff periods change or dispatches start/end:

| Event | Description |
|-------|-------------|
| `octoha_off_peak_start` | Triggered when off-peak period begins |
| `octoha_off_peak_end` | Triggered when off-peak period ends |
| `octoha_dispatch_start` | Triggered when Intelligent dispatch begins |
| `octoha_dispatch_end` | Triggered when Intelligent dispatch ends |

### Key Features

- **Energy Dashboard Compatible**: Daily usage sensors use `state_class: total_increasing` for proper HA statistics
- **Off-Peak Detection**: Automatically identifies off-peak periods for time-of-use tariffs
- **Graceful Degradation**: Continues showing cached data during API outages with staleness indicators
- **Diagnostics Export**: Debug data export with automatic redaction of sensitive information
- **Configurable Intervals**: Customise polling intervals to match your needs

## Requirements

- Home Assistant 2024.1.0 or later
- Python 3.11 or later
- Octopus Energy account with API access
- Smart meter enrolled and sending data to Octopus

## Installation

### Manual Installation

1. Download the latest release from the [releases page][releases]
2. Extract the `octoha` folder from the archive
3. Copy the `octoha` folder to your `custom_components` directory:
   ```
   <config>/custom_components/octoha/
   ```
4. Restart Home Assistant
5. Go to **Settings > Devices & Services > Add Integration**
6. Search for "Octoha" and follow the setup wizard

### HACS Installation (Coming Soon)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots menu and select "Custom repositories"
4. Add `https://github.com/samcarrington/octoha` with category "Integration"
5. Click "Install"
6. Restart Home Assistant
7. Go to **Settings > Devices & Services > Add Integration**
8. Search for "Octoha" and follow the setup wizard

## Configuration

### Getting Your API Key

1. Log in to your [Octopus Energy account](https://octopus.energy/dashboard/developer/)
2. Navigate to the Developer dashboard
3. Copy your API key (starts with `sk_live_`)

### Setup Wizard

1. Enter your Octopus Energy API key
2. The integration will discover your account and meter points
3. Select your electricity meter (MPAN) and gas meter (MPRN)
4. Optionally configure update intervals

### Options

After setup, you can configure the following options:

| Option | Default | Description |
|--------|---------|-------------|
| Electricity Interval | 5 min | How often to fetch electricity data |
| Gas Interval | 5 min | How often to fetch gas data |
| Tariff Interval | 30 min | How often to fetch tariff rates |
| Dispatch Interval | 5 min | How often to check for dispatches |

## Automation Examples

### Start Appliances During Off-Peak

```yaml
alias: "Start dishwasher when off-peak begins"
trigger:
  - platform: event
    event_type: octoha_off_peak_start
action:
  - service: switch.turn_on
    target:
      entity_id: switch.dishwasher
  - service: notify.mobile_app
    data:
      title: "Off-Peak Started"
      message: "Electricity rate is now {{ trigger.event.data.rate }}p/kWh"
```

### Charge Batteries During Intelligent Dispatch

```yaml
alias: "Charge home battery during dispatch"
trigger:
  - platform: event
    event_type: octoha_dispatch_start
action:
  - service: select.select_option
    target:
      entity_id: select.battery_mode
    data:
      option: "charge"
```

### Dashboard Conditional Card

```yaml
type: conditional
conditions:
  - entity: binary_sensor.octoha_off_peak_rate
    state: "on"
card:
  type: markdown
  content: |
    ## ⚡ Off-Peak Active!
    Current rate: {{ states('sensor.octoha_electricity_rate') }}p/kWh
```

See [Automation Examples](docs/automation-examples.md) for more examples.

## Troubleshooting

### Common Issues

**"Authentication failed" during setup**
- Verify your API key is correct (starts with `sk_live_`)
- Ensure you copied the full key without extra spaces
- Check that your Octopus account has API access enabled

**"No meters found" during setup**
- Verify your smart meter is enrolled with Octopus
- Check that your meter is sending data (may take 24-48 hours after enrolment)
- Try logging into the Octopus web dashboard to confirm meter visibility

**Sensors showing "unavailable"**
- Check your internet connection
- Verify the Octopus API is accessible (https://api.octopus.energy/v1/)
- Review Home Assistant logs for error messages

**Data appears stale**
- Check the `is_stale` attribute on sensors
- Smart meter data typically has a 30-minute to 24-hour delay
- Verify your update intervals in integration options

### Debug Logging

Enable debug logging to troubleshoot issues:

```yaml
logger:
  default: info
  logs:
    custom_components.octoha: debug
```

### Diagnostics

Download diagnostics data from **Settings > Devices & Services > Octoha > 3 dots menu > Download diagnostics**. Sensitive data (API keys, MPAN/MPRN) is automatically redacted.

## Data Freshness

Smart meter data availability depends on Octopus Energy's systems:

| Data Type | Typical Delay |
|-----------|---------------|
| Electricity consumption | 30 minutes - 2 hours |
| Gas consumption | 2 - 24 hours |
| Tariff rates | Near real-time |
| Dispatch schedules | Near real-time |

## Supported Tariffs

- Octopus Go / Intelligent Octopus Go
- Octopus Agile
- Octopus Tracker
- Octopus Flexible
- Fixed tariffs
- Any tariff with API-accessible rate data

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests (`pytest tests/`)
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Acknowledgements

This project includes code adapted from [open-octopus](https://github.com/abracadabra50/open-octopus), which provided the foundation for the API client patterns and GraphQL queries.

## Support

- [Report a bug][issues]
- [Request a feature][issues]
- [View documentation][docs]

---

[releases-shield]: https://img.shields.io/github/release/samcarrington/octoha.svg?style=for-the-badge
[releases]: https://github.com/samcarrington/octoha/releases
[license-shield]: https://img.shields.io/github/license/samcarrington/octoha.svg?style=for-the-badge
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[hacs]: https://github.com/hacs/integration
[maintenance-shield]: https://img.shields.io/badge/maintainer-Sam%20Carrington-blue.svg?style=for-the-badge
[user_profile]: https://github.com/samcarrington
[issues]: https://github.com/samcarrington/octoha/issues
[docs]: https://github.com/samcarrington/octoha#readme
