# Octoha Troubleshooting Guide

This guide covers common issues and their solutions when using the Octoha integration.

## Installation Issues

### Integration Not Found

**Symptom:** "Octoha" doesn't appear when searching for integrations.

**Solutions:**

1. **Verify file location:**
   ```
   /config/custom_components/octoha/
   ```
   Ensure the folder contains `manifest.json` and `__init__.py`.

2. **Check for nested folders:**
   Incorrect: `/config/custom_components/octoha/octoha/`
   Correct: `/config/custom_components/octoha/`

3. **Restart Home Assistant:**
   Go to **Settings > System > Restart** and perform a full restart.

4. **Clear browser cache:**
   Force refresh your browser (Ctrl+Shift+R or Cmd+Shift+R).

5. **Check Home Assistant logs:**
   Go to **Settings > System > Logs** and search for "octoha" errors.

### Missing Dependencies

**Symptom:** Error messages about missing modules.

**Solutions:**

1. Octoha should work with standard Home Assistant dependencies.
2. Ensure you're running Home Assistant 2024.1.0 or later.
3. If using Home Assistant Core, install dependencies:
   ```bash
   pip install aiohttp
   ```

## Authentication Issues

### "Authentication Failed"

**Symptom:** Error during setup saying authentication failed.

**Causes and Solutions:**

1. **Incorrect API key:**
   - Your API key should start with `sk_live_`
   - Copy the full key from [Octopus Developer Dashboard](https://octopus.energy/dashboard/developer/)
   - Ensure no extra spaces before or after the key

2. **Expired API key:**
   - Generate a new API key from the Octopus dashboard
   - Try the new key in Octoha setup

3. **Account issues:**
   - Verify you can log in to octopus.energy
   - Check your account is active and in good standing

4. **Network issues:**
   - Ensure Home Assistant can reach the internet
   - Check if a firewall is blocking HTTPS connections

### "Failed to Connect"

**Symptom:** Setup fails with connection error.

**Solutions:**

1. **Check internet connectivity:**
   ```bash
   # From HA terminal or container
   curl -I https://api.octopus.energy/v1/
   ```

2. **Check DNS resolution:**
   ```bash
   nslookup api.octopus.energy
   ```

3. **Temporary API outage:**
   - Wait a few minutes and try again
   - Check [Octopus Energy status](https://status.octopus.energy/)

## Meter Discovery Issues

### "No Meters Found"

**Symptom:** Setup completes but no meters are available to select.

**Solutions:**

1. **Smart meter not enrolled:**
   - Contact Octopus Energy to ensure your smart meter is enrolled
   - Enrolment can take 24-48 hours to propagate

2. **Account mismatch:**
   - Verify the API key belongs to the correct account
   - Check your account has active meter points

3. **API rate limiting:**
   - Wait 5 minutes and try again
   - The API may be temporarily throttled

### Only Electricity (No Gas) Found

**Symptom:** Electricity meter appears but no gas meter.

**Causes:**

1. Gas meter may not be a smart meter
2. Gas meter enrolment may be pending
3. Some properties don't have gas

**Solution:**

- Contact Octopus Energy to verify gas meter status
- Proceed with electricity-only setup if gas is unavailable

## Sensor Issues

### Sensors Show "Unavailable"

**Symptom:** All sensors display "unavailable" state.

**Causes and Solutions:**

1. **API authentication issue:**
   - Check your API key is still valid
   - Try reconfiguring the integration with the same key

2. **Network connectivity:**
   - Verify Home Assistant can reach the internet
   - Check for DNS or firewall issues

3. **Coordinator update failure:**
   - Check logs for error messages
   - Enable debug logging (see below)

4. **API outage:**
   - Check [Octopus Energy status](https://status.octopus.energy/)
   - Wait and retry

### Sensors Show "Unknown"

**Symptom:** Sensors appear but show "unknown" instead of values.

**Causes and Solutions:**

1. **No data available yet:**
   - Smart meters can take 24-48 hours to provide initial data
   - Wait for the first data sync

2. **Data delay:**
   - Electricity data: typically 30 mins - 2 hours delay
   - Gas data: typically 2-24 hours delay

3. **No consumption today:**
   - Daily usage sensors show "unknown" until consumption is recorded
   - Check after some energy usage

### Stale Data Indicator

**Symptom:** Sensors show `is_stale: true` in attributes.

**Explanation:**

This indicates the data is older than expected. Octoha continues displaying cached values during API outages rather than going unavailable.

**Actions:**

1. Check `data_age_seconds` attribute to see how old data is
2. Check `last_update_success` to see if updates are working
3. Wait for next successful update
4. If persistent, check logs for API errors

### Incorrect Energy Values

**Symptom:** Energy values don't match your bill or IHD.

**Causes and Solutions:**

1. **Timing differences:**
   - API data may be delayed by hours
   - Compare data from the same time period

2. **Unit differences:**
   - Octoha reports in kWh
   - Your IHD may show in different units

3. **Aggregation period:**
   - Daily totals reset at midnight UTC
   - Your supplier may use a different reset time

## Binary Sensor Issues

### Off-Peak Always Shows OFF

**Symptom:** `binary_sensor.octoha_off_peak_rate` never turns on.

**Causes:**

1. **Flat rate tariff:**
   - If your tariff has a single rate, there's no "off-peak"
   - This sensor is only useful for time-of-use tariffs

2. **Incorrect tariff detection:**
   - Check `sensor.octoha_electricity_rate` attributes
   - Verify `tariff_name` is correct

3. **Timing issue:**
   - Check when off-peak periods are scheduled
   - For Octopus Go, off-peak is typically 00:30-04:30

### Dispatch Sensor Issues

**Symptom:** Dispatch sensors not working for Intelligent Octopus Go.

**Causes:**

1. **Not on Intelligent tariff:**
   - Dispatch sensors only work with Intelligent Octopus Go
   - Standard Go doesn't have dispatch schedules

2. **No vehicle registered:**
   - Intelligent Go requires a registered EV or home battery
   - Check your Octopus account for vehicle registration

3. **No dispatches scheduled:**
   - If no charging is needed, no dispatches are scheduled
   - This is normal behaviour

## Event Issues

### Events Not Firing

**Symptom:** Automations using `octoha_off_peak_start` etc. don't trigger.

**Debugging Steps:**

1. **Listen for events:**
   - Go to **Developer Tools > Events**
   - Enter `octoha_off_peak_start` in "Listen to events"
   - Click "Start listening"
   - Wait for an off-peak transition

2. **Check tariff coordinator:**
   - Events fire on rate transitions
   - Verify the rate sensor is updating

3. **Check logs:**
   - Enable debug logging
   - Look for event firing messages

### Events Fire Multiple Times

**Symptom:** Automation triggers multiple times per transition.

**Solutions:**

1. **Add `mode: single` to automation:**
   ```yaml
   alias: "My automation"
   mode: single
   trigger:
     - platform: event
       event_type: octoha_off_peak_start
   ```

2. **Add a condition:**
   ```yaml
   condition:
     - condition: state
       entity_id: binary_sensor.octoha_off_peak_rate
       state: "on"
   ```

## Performance Issues

### High CPU Usage

**Symptom:** Home Assistant CPU usage increases after installing Octoha.

**Solutions:**

1. **Increase update intervals:**
   - Go to integration options
   - Increase all intervals to 15-30 minutes

2. **Check for rate limiting:**
   - Rapid API failures cause retry loops
   - Check logs for authentication errors

### Memory Usage

**Symptom:** Memory usage increases over time.

**Solutions:**

1. **Restart Home Assistant:**
   - This clears any accumulated data

2. **Check for log spam:**
   - Excessive logging can consume memory
   - Reduce log verbosity if debug logging is enabled

## Debug Logging

Enable detailed logging to troubleshoot issues:

### Enable Debug Logging

Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.octoha: debug
    custom_components.octoha.api: debug
    custom_components.octoha.coordinator: debug
```

Restart Home Assistant after making changes.

### View Logs

1. **Web interface:**
   Go to **Settings > System > Logs**

2. **File:**
   ```bash
   tail -f /config/home-assistant.log | grep octoha
   ```

3. **Docker:**
   ```bash
   docker logs -f homeassistant 2>&1 | grep octoha
   ```

### Disable Debug Logging

After troubleshooting, remove or comment out the logger entries to reduce log size.

## Diagnostics

Download diagnostic data for bug reports:

1. Go to **Settings > Devices & Services**
2. Find **Octoha**
3. Click the three-dot menu
4. Select **Download diagnostics**

The diagnostics file contains:

- Integration configuration (API keys redacted)
- Coordinator status
- Sensor data summaries
- Error information

> **Note:** Sensitive data like API keys and full MPAN/MPRN numbers are automatically redacted.

## Common Error Messages

### "UpdateFailed: Authentication failed"

**Meaning:** API key is invalid or expired.

**Solution:** Reconfigure with a valid API key.

### "UpdateFailed: API request failed"

**Meaning:** Network issue or API outage.

**Solution:** Check internet connectivity; wait if API is down.

### "Failed to set up octoha"

**Meaning:** Integration couldn't initialise.

**Solution:** Check logs for specific error; verify all files present.

### "Rate limit exceeded"

**Meaning:** Too many API requests.

**Solution:** Increase update intervals; wait 5-10 minutes.

## Getting More Help

If you can't resolve an issue:

1. **Search existing issues:**
   [GitHub Issues](https://github.com/samcarrington/octoha/issues)

2. **Create a new issue with:**
   - Home Assistant version
   - Octoha version
   - Description of the problem
   - Relevant log entries (with sensitive data redacted)
   - Diagnostics file (if available)

3. **Home Assistant Community:**
   [Home Assistant Community Forums](https://community.home-assistant.io/)

## FAQ

**Q: How often does data update?**

A: By default, consumption data updates every 5 minutes. However, actual smart meter data from Octopus is typically delayed by 30 minutes to 24 hours.

**Q: Why don't my readings match my smart meter display?**

A: The API data has a delay. Compare readings from the same time period. Also, some IHDs show real-time data while the API provides half-hourly aggregated data.

**Q: Does Octoha work with solar panels or battery systems?**

A: The current version focuses on consumption data. Export data for solar may be added in future versions.

**Q: Can I use Octoha with multiple properties?**

A: Yes, add the integration multiple times with different API keys for each property.

**Q: What tariffs are supported?**

A: All Octopus tariffs that provide data via the API, including Go, Agile, Tracker, Flexible, and fixed-rate tariffs.
