# Octoha Configuration Guide

This guide walks you through configuring the Octoha integration after installation.

## Initial Setup

### Step 1: Add the Integration

1. Go to **Settings > Devices & Services**
2. Click **+ Add Integration** (bottom right corner)
3. Search for "Octoha" or "Octopus"
4. Select **Octoha - Octopus Energy**

### Step 2: Enter Your API Key

When prompted, enter your Octopus Energy API key:

```
┌─────────────────────────────────────────────────────┐
│  Set up Octoha - Octopus Energy                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Enter your Octopus Energy API key.                 │
│  You can find this in your Octopus account under    │
│  Developer settings.                                │
│                                                     │
│  API Key                                            │
│  ┌─────────────────────────────────────────────┐    │
│  │ your_octopus_api_key_here                   │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│                              [Submit]               │
└─────────────────────────────────────────────────────┘
```

- Your API key starts with `sk_live_`
- Paste the complete key without extra spaces
- Click **Submit**

The integration will validate your API key and retrieve your account details.

### Step 3: Select Your Meters

After validation, you'll see your available meters:

```
┌─────────────────────────────────────────────────────┐
│  Select Meters                                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Account: A-FB05ED6C                                │
│                                                     │
│  Electricity Meter (MPAN)                           │
│  ┌─────────────────────────────────────────────┐    │
│  │ 1234567890123 (Serial: 12A3456789)      ▼   │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│  Gas Meter (MPRN)                                   │
│  ┌─────────────────────────────────────────────┐    │
│  │ 9876543210 (Serial: G12345678)          ▼   │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│                              [Submit]               │
└─────────────────────────────────────────────────────┘
```

- Select your electricity meter (MPAN)
- Select your gas meter (MPRN) if available
- Click **Submit**

### Step 4: Complete Setup

Once setup is complete, you'll see:

```
┌─────────────────────────────────────────────────────┐
│  Success!                                           │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Octoha has been successfully configured.           │
│                                                     │
│  Area: Kitchen                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │ (Default area)                          ▼   │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│                             [Finish]                │
└─────────────────────────────────────────────────────┘
```

Click **Finish** to complete the setup.

## Configuration Options

After initial setup, you can adjust settings via the Options flow.

### Accessing Options

1. Go to **Settings > Devices & Services**
2. Find the **Octoha** integration
3. Click **Configure**

### Available Options

| Option | Default | Range | Description |
|--------|---------|-------|-------------|
| Electricity Interval | 5 min | 1-60 min | How often to fetch electricity consumption |
| Gas Interval | 5 min | 1-60 min | How often to fetch gas consumption |
| Tariff Interval | 30 min | 5-120 min | How often to fetch tariff rates |
| Dispatch Interval | 5 min | 1-60 min | How often to check for Intelligent dispatches |

### Recommended Settings

| Use Case | Electricity | Gas | Tariff | Dispatch |
|----------|-------------|-----|--------|----------|
| Standard monitoring | 5 min | 5 min | 30 min | 5 min |
| Agile tariff tracking | 5 min | 10 min | 15 min | 5 min |
| Battery optimisation | 1 min | 10 min | 5 min | 1 min |
| Low API usage | 15 min | 15 min | 60 min | 15 min |

> **Note:** Shorter intervals mean more API requests. The Octopus API has rate limits, so extremely short intervals may cause throttling.

## Entity Naming

Octoha creates entities with the following naming pattern:

```
sensor.octoha_<type>
binary_sensor.octoha_<type>
```

### Sensors Created

| Entity ID | Name | Description |
|-----------|------|-------------|
| `sensor.octoha_electricity_consumption` | Electricity Consumption | Latest half-hourly reading |
| `sensor.octoha_electricity_daily_usage` | Electricity Daily Usage | Today's total usage |
| `sensor.octoha_electricity_rate` | Electricity Rate | Current rate (p/kWh) |
| `sensor.octoha_gas_consumption` | Gas Consumption | Latest gas reading |
| `sensor.octoha_gas_daily_usage` | Gas Daily Usage | Today's gas usage |
| `sensor.octoha_gas_rate` | Gas Rate | Current rate (p/kWh) |
| `sensor.octoha_next_dispatch` | Next Dispatch | Next Intelligent dispatch time |

### Binary Sensors Created

| Entity ID | Name | Description |
|-----------|------|-------------|
| `binary_sensor.octoha_off_peak_rate` | Off-Peak Rate | ON during off-peak periods |
| `binary_sensor.octoha_dispatch_active` | Dispatch Active | ON during Intelligent dispatch |

## Entity Attributes

Each sensor includes additional attributes for advanced use.

### Consumption Sensors

| Attribute | Description |
|-----------|-------------|
| `mpan` / `mprn` | Meter point identifier |
| `last_reading_start` | Start time of last reading |
| `last_reading_end` | End time of last reading |
| `is_stale` | True if data is outdated |
| `data_age_seconds` | How old the data is |
| `last_update_success` | Whether last API call succeeded |

### Rate Sensors

| Attribute | Description |
|-----------|-------------|
| `is_off_peak` | True during off-peak periods |
| `period_end` | When current rate period ends |
| `next_rate` | Rate after period_end (if known) |
| `tariff_name` | Display name of tariff |
| `standing_charge` | Daily standing charge |

### Dispatch Sensors

| Attribute | Description |
|-----------|-------------|
| `dispatch_end` | When dispatch ends |
| `dispatch_source` | Source type (smart-charge, bump-charge) |
| `duration_minutes` | Duration of dispatch in minutes |

## Energy Dashboard Integration

Octoha sensors are compatible with Home Assistant's Energy Dashboard.

### Adding to Energy Dashboard

1. Go to **Settings > Dashboards > Energy**
2. Click **Add consumption** under Electricity grid
3. Select `sensor.octoha_electricity_daily_usage`
4. Repeat for gas with `sensor.octoha_gas_daily_usage`

The daily usage sensors use `state_class: total_increasing` which enables proper long-term statistics in Home Assistant.

## Device Grouping

All Octoha entities are grouped under a single device for easy management:

```
Device: Octopus Energy A-FB05ED6C
├── sensor.octoha_electricity_consumption
├── sensor.octoha_electricity_daily_usage
├── sensor.octoha_electricity_rate
├── sensor.octoha_gas_consumption
├── sensor.octoha_gas_daily_usage
├── sensor.octoha_gas_rate
├── sensor.octoha_next_dispatch
├── binary_sensor.octoha_off_peak_rate
└── binary_sensor.octoha_dispatch_active
```

## Reconfiguration

### Changing API Key

If you need to update your API key:

1. Go to **Settings > Devices & Services**
2. Find the **Octoha** integration
3. Click **Configure**
4. Enter the new API key
5. Click **Submit**

### Changing Meters

To select different meters:

1. Delete the current integration
2. Re-add the integration with the same API key
3. Select the desired meters during setup

## Multiple Accounts

Octoha supports multiple Octopus Energy accounts:

1. Complete setup for your first account
2. Click **+ Add Integration** again
3. Search for "Octoha"
4. Enter the API key for your second account
5. Complete setup as normal

Each account creates a separate device with its own sensors.

## Dashboard Examples

### Basic Energy Card

```yaml
type: entities
title: Energy Consumption
entities:
  - entity: sensor.octoha_electricity_consumption
    name: Current Electricity
  - entity: sensor.octoha_electricity_daily_usage
    name: Today's Electricity
  - entity: sensor.octoha_gas_consumption
    name: Current Gas
  - entity: sensor.octoha_gas_daily_usage
    name: Today's Gas
```

### Rate Display Card

```yaml
type: glance
title: Current Rates
entities:
  - entity: sensor.octoha_electricity_rate
    name: Electricity
  - entity: sensor.octoha_gas_rate
    name: Gas
  - entity: binary_sensor.octoha_off_peak_rate
    name: Off-Peak
```

### Conditional Off-Peak Card

```yaml
type: conditional
conditions:
  - entity: binary_sensor.octoha_off_peak_rate
    state: "on"
card:
  type: markdown
  content: |
    ## ⚡ Off-Peak Active!
    **Rate:** {{ states('sensor.octoha_electricity_rate') }}p/kWh
    **Ends:** {{ state_attr('sensor.octoha_electricity_rate', 'period_end') | as_datetime | as_local }}
```

## Next Steps

- [Automation Examples](automation-examples.md) - Create automations using Octoha events
- [Troubleshooting](troubleshooting.md) - Solve common issues
- [README](../README.md) - Return to main documentation
