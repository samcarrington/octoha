# Octoha Automation Examples

This document provides examples of Home Assistant automations using Octoha events and sensors.

## Events

Octoha fires the following events that can be used as automation triggers:

| Event | Description |
|-------|-------------|
| `octoha_off_peak_start` | Fired when electricity rate transitions to off-peak |
| `octoha_off_peak_end` | Fired when electricity rate transitions from off-peak |
| `octoha_dispatch_start` | Fired when an Intelligent dispatch begins |
| `octoha_dispatch_end` | Fired when an Intelligent dispatch ends |

### Event Data

All events include the following data:

```yaml
entry_id: "config_entry_id"  # Useful for multi-account setups
account: "A-FB05ED6C"        # Octopus account number
```

#### Off-Peak Events Additional Data

```yaml
rate: 7.5              # Current rate in p/kWh
is_off_peak: true      # Whether currently off-peak
period_end: "2026-01-18T05:30:00+00:00"  # When this rate period ends
next_rate: 24.5        # Rate after period_end (if known)
tariff_name: "Intelligent Octopus Go"
tariff_code: "INTELLI-VAR-22-10-14"
```

#### Dispatch Events Additional Data

```yaml
is_dispatching: true   # Whether dispatch is active
dispatch_start: "2026-01-18T01:00:00+00:00"
dispatch_end: "2026-01-18T05:00:00+00:00"
source: "smart-charge"  # or "bump-charge"
duration_minutes: 240
```

---

## Automation Examples

### 1. Run Appliances During Off-Peak

Turn on high-power appliances when off-peak electricity starts:

```yaml
alias: "Start dishwasher when off-peak begins"
trigger:
  - platform: event
    event_type: octoha_off_peak_start
condition: []
action:
  - service: switch.turn_on
    target:
      entity_id: switch.dishwasher
  - service: notify.mobile_app
    data:
      title: "Off-Peak Started"
      message: "Electricity rate is now {{ trigger.event.data.rate }}p/kWh"
mode: single
```

### 2. Stop Appliances When Off-Peak Ends

Ensure appliances are off before peak rates begin:

```yaml
alias: "Stop high-power appliances when off-peak ends"
trigger:
  - platform: event
    event_type: octoha_off_peak_end
condition: []
action:
  - service: switch.turn_off
    target:
      entity_id:
        - switch.dishwasher
        - switch.washing_machine
        - switch.tumble_dryer
  - service: notify.mobile_app
    data:
      title: "Off-Peak Ended"
      message: "Electricity rate is now {{ trigger.event.data.rate }}p/kWh"
mode: single
```

### 3. Charge Batteries During Intelligent Dispatch

Enable home battery charging during Intelligent Octopus dispatch windows:

```yaml
alias: "Charge home battery during dispatch"
trigger:
  - platform: event
    event_type: octoha_dispatch_start
condition: []
action:
  - service: number.set_value
    target:
      entity_id: number.battery_charge_rate
    data:
      value: 100
  - service: select.select_option
    target:
      entity_id: select.battery_mode
    data:
      option: "charge"
mode: single
```

### 4. Stop Battery Charging When Dispatch Ends

```yaml
alias: "Stop battery charging when dispatch ends"
trigger:
  - platform: event
    event_type: octoha_dispatch_end
condition: []
action:
  - service: select.select_option
    target:
      entity_id: select.battery_mode
    data:
      option: "auto"
mode: single
```

### 5. Notify on Dispatch Schedule

Send notification when a dispatch is planned:

```yaml
alias: "Notify upcoming dispatch"
trigger:
  - platform: state
    entity_id: sensor.octoha_next_dispatch
condition:
  - condition: template
    value_template: "{{ trigger.to_state.state != 'unavailable' }}"
action:
  - service: notify.mobile_app
    data:
      title: "Intelligent Dispatch Scheduled"
      message: >
        Next dispatch: {{ trigger.to_state.state | as_datetime | as_local }}
        Duration: {{ state_attr('sensor.octoha_next_dispatch', 'duration_minutes') }} minutes
mode: single
```

### 6. Use Binary Sensor for Off-Peak Automations

Alternatively, use the binary sensor instead of events:

```yaml
alias: "Start appliances during off-peak (sensor-based)"
trigger:
  - platform: state
    entity_id: binary_sensor.octoha_off_peak_rate
    to: "on"
condition: []
action:
  - service: switch.turn_on
    target:
      entity_id: switch.ev_charger
mode: single
```

### 7. Dashboard Conditional Card

Show different content based on off-peak status:

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
    Ends: {{ state_attr('sensor.octoha_electricity_rate', 'period_end') | as_datetime | as_local }}
```

### 8. Energy Dashboard Integration

The daily usage sensors are compatible with Home Assistant's Energy Dashboard:

1. Go to **Settings > Dashboards > Energy**
2. Under **Electricity grid**, click **Add consumption**
3. Select `sensor.octoha_electricity_daily_usage`
4. For gas, select `sensor.octoha_gas_daily_usage`

The sensors use `state_class: total_increasing` for proper long-term statistics.

---

## Sensors Reference

| Sensor | Unit | Description |
|--------|------|-------------|
| `sensor.octoha_electricity_consumption` | kWh | Latest half-hourly reading |
| `sensor.octoha_electricity_daily_usage` | kWh | Today's total usage |
| `sensor.octoha_electricity_rate` | p/kWh | Current electricity rate |
| `sensor.octoha_gas_consumption` | kWh | Latest gas reading |
| `sensor.octoha_gas_daily_usage` | kWh | Today's gas usage |
| `sensor.octoha_gas_rate` | p/kWh | Current gas rate |
| `sensor.octoha_next_dispatch` | timestamp | Next Intelligent dispatch |
| `binary_sensor.octoha_off_peak_rate` | on/off | Off-peak period active |
| `binary_sensor.octoha_dispatch_active` | on/off | Dispatch currently running |

---

## Tips

1. **Event vs Sensor**: Use events for immediate reactions (starting appliances). Use sensors for conditions and templates.

2. **Multi-Account**: If you have multiple Octopus accounts, check `trigger.event.data.entry_id` to differentiate.

3. **Rate Changes**: Off-peak events only fire on transitions, not every update. Use the rate sensor for current value.

4. **Testing**: Use Developer Tools > Events to listen for `octoha_*` events and test your automations.
