# Octoha Installation Guide

This guide covers the installation and initial setup of the Octoha Home Assistant integration.

## Prerequisites

Before installing Octoha, ensure you have:

- **Home Assistant** version 2024.1.0 or later
- **Python** 3.11 or later (included with Home Assistant)
- **Octopus Energy account** with a valid API key
- **Smart meter** enrolled and sending data to Octopus Energy

## Getting Your Octopus Energy API Key

1. Log in to your Octopus Energy account at [octopus.energy](https://octopus.energy)
2. Navigate to your account dashboard
3. Go to **Developer** settings (or visit [octopus.energy/dashboard/developer/](https://octopus.energy/dashboard/developer/))
4. Your API key will be displayed - it starts with `sk_live_`
5. Copy the full API key and store it securely

> **Note:** Your API key provides access to your account data. Keep it private and never share it publicly.

## Installation Methods

### Method 1: Manual Installation (Recommended)

This is the most reliable installation method.

#### Step 1: Download the Integration

1. Visit the [Octoha releases page](https://github.com/samcarrington/octoha/releases)
2. Download the latest release (`.zip` file)
3. Extract the archive

#### Step 2: Copy to Custom Components

1. Locate your Home Assistant configuration directory
   - For Home Assistant OS: `/config/`
   - For Home Assistant Container: The directory you mapped to `/config`
   - For Home Assistant Core: `~/.homeassistant/`

2. Create the `custom_components` directory if it doesn't exist:
   ```bash
   mkdir -p /config/custom_components
   ```

3. Copy the `octoha` folder from the extracted archive to `custom_components`:
   ```
   /config/
   ├── custom_components/
   │   └── octoha/
   │       ├── __init__.py
   │       ├── manifest.json
   │       ├── config_flow.py
   │       ├── coordinator.py
   │       ├── sensor.py
   │       ├── binary_sensor.py
   │       ├── diagnostics.py
   │       ├── const.py
   │       ├── strings.json
   │       ├── translations/
   │       │   └── en.json
   │       ├── api/
   │       │   ├── __init__.py
   │       │   ├── auth.py
   │       │   ├── client.py
   │       │   ├── exceptions.py
   │       │   ├── graphql.py
   │       │   └── rest.py
   │       └── models/
   │           ├── __init__.py
   │           ├── account.py
   │           ├── consumption.py
   │           ├── dispatch.py
   │           └── tariff.py
   ```

#### Step 3: Restart Home Assistant

1. Go to **Settings > System > Restart**
2. Click **Restart** to reload Home Assistant with the new integration

#### Step 4: Add the Integration

1. Go to **Settings > Devices & Services**
2. Click **+ Add Integration** (bottom right)
3. Search for "Octoha" or "Octopus Energy"
4. Select **Octoha - Octopus Energy**
5. Follow the [Configuration Guide](configuration.md)

### Method 2: HACS Installation

> **Note:** HACS installation will be available after the first public release.

#### Prerequisites

- [HACS](https://hacs.xyz/) installed and configured in Home Assistant

#### Steps

1. Open HACS in Home Assistant
2. Navigate to **Integrations**
3. Click the three-dot menu (top right)
4. Select **Custom repositories**
5. Add repository URL: `https://github.com/samcarrington/octoha`
6. Select category: **Integration**
7. Click **Add**
8. Find "Octoha" in the HACS integrations list
9. Click **Install**
10. Restart Home Assistant
11. Add the integration via **Settings > Devices & Services**

### Method 3: Git Clone (For Developers)

For development or testing the latest code:

```bash
cd /config/custom_components
git clone https://github.com/samcarrington/octoha.git
```

To update:

```bash
cd /config/custom_components/octoha
git pull origin main
```

## Verifying Installation

After restarting Home Assistant:

1. Go to **Settings > Devices & Services**
2. Click **+ Add Integration**
3. Search for "Octoha"
4. If "Octoha - Octopus Energy" appears, installation was successful

If the integration doesn't appear:

1. Check that files are in the correct location
2. Review Home Assistant logs for errors
3. Ensure the `manifest.json` file is present in the `octoha` folder
4. Try clearing your browser cache and refreshing

## Directory Structure

After installation, your configuration should look like this:

```
/config/
├── configuration.yaml
├── custom_components/
│   └── octoha/
│       ├── __init__.py          # Integration setup
│       ├── manifest.json        # Integration metadata
│       ├── config_flow.py       # Setup wizard
│       ├── coordinator.py       # Data update coordinators
│       ├── sensor.py            # Sensor entities
│       ├── binary_sensor.py     # Binary sensor entities
│       ├── diagnostics.py       # Debug data export
│       ├── const.py             # Constants and configuration
│       ├── strings.json         # UI strings
│       ├── translations/
│       │   └── en.json          # English translations
│       ├── api/                  # API client layer
│       │   ├── __init__.py
│       │   ├── auth.py          # Authentication
│       │   ├── client.py        # Main API client
│       │   ├── exceptions.py    # Custom exceptions
│       │   ├── graphql.py       # GraphQL queries
│       │   └── rest.py          # REST endpoints
│       └── models/              # Data models
│           ├── __init__.py
│           ├── account.py       # Account/meter models
│           ├── consumption.py   # Consumption data
│           ├── dispatch.py      # Dispatch schedules
│           └── tariff.py        # Tariff information
```

## Updating the Integration

### Manual Update

1. Download the latest release
2. Stop Home Assistant
3. Delete the existing `custom_components/octoha` folder
4. Copy the new `octoha` folder to `custom_components`
5. Start Home Assistant

### HACS Update

1. Open HACS
2. Navigate to Integrations
3. Find Octoha
4. Click **Update** if available
5. Restart Home Assistant

## Uninstalling

1. Go to **Settings > Devices & Services**
2. Find the Octoha integration
3. Click the three-dot menu
4. Select **Delete**
5. Restart Home Assistant
6. Delete the `custom_components/octoha` folder (optional)

## Next Steps

- [Configuration Guide](configuration.md) - Set up your meters and options
- [Automation Examples](automation-examples.md) - Create automations with Octoha
- [Troubleshooting](troubleshooting.md) - Solve common issues

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Review Home Assistant logs (**Settings > System > Logs**)
3. Download diagnostics (**Devices & Services > Octoha > Download diagnostics**)
4. [Open an issue](https://github.com/samcarrington/octoha/issues) on GitHub
