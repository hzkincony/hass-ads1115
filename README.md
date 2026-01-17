# ADS1115 ADC Sensor for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

A Home Assistant custom component for the **ADS1115** 16-bit analog-to-digital converter (ADC). Read analog sensor values over I2C on Raspberry Pi and similar single-board computers.

## Features

- **4 Analog Input Channels**: Monitor up to 4 single-ended analog inputs
- **Differential Measurements**: Support for differential measurements between channel pairs (0-1, 0-3, 1-3, 2-3)
- **Configurable Gain**: Choose from 6 programmable gain settings (±0.256V to ±6.144V)
- **Multiple Devices**: Support multiple ADS1115 devices on the same I2C bus
- **UI Configuration**: Easy setup through Home Assistant UI (no YAML required)
- **Auto-Discovery**: Automatic sensor entity creation with customizable names
- **Robust Error Handling**: Automatic recovery from I2C communication errors

## Hardware Requirements

- ADS1115 16-bit ADC module
- Raspberry Pi (or compatible SBC) with I2C enabled
- I2C connection between your device and the ADS1115

## Wiring

Connect the ADS1115 to your Raspberry Pi:

| ADS1115 Pin | Raspberry Pi Pin | Description |
|-------------|------------------|-------------|
| VDD         | Pin 1 (3.3V)     | Power supply |
| GND         | Pin 6 (GND)      | Ground |
| SCL         | Pin 5 (GPIO 3)   | I2C Clock |
| SDA         | Pin 3 (GPIO 2)   | I2C Data |
| ADDR        | GND/VDD/SDA/SCL  | I2C address selection |
| A0-A3       | Analog sensors   | Analog input channels |

### I2C Address Selection

The ADDR pin determines the I2C address:

- **ADDR → GND**: 0x48 (default)
- **ADDR → VDD**: 0x49
- **ADDR → SDA**: 0x4A
- **ADDR → SCL**: 0x4B

This allows up to 4 ADS1115 devices on the same I2C bus.

## Installation

### Method 1: HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/idreamshen/hacs-ads1115`
6. Select category: "Integration"
7. Click "Add"
8. Search for "ADS1115 ADC Sensor"
9. Click "Download"
10. Restart Home Assistant

### Method 2: Manual Installation

1. Download the latest release from GitHub
2. Copy the `custom_components/ads1115` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## System Setup

### Enable I2C on Raspberry Pi

```bash
# Enable I2C interface
sudo raspi-config
# Navigate to: Interface Options → I2C → Enable

# Verify I2C is enabled
ls /dev/i2c-*

# Detect ADS1115 device (should show address like 48)
sudo i2cdetect -y 1
```

### Set Permissions

Add the Home Assistant user to the `i2c` group:

```bash
sudo usermod -a -G i2c homeassistant
sudo reboot
```

For Docker installations:

```bash
# Add to your docker-compose.yml or docker run command:
devices:
  - /dev/i2c-1:/dev/i2c-1
```

## Configuration

### Adding the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **ADS1115**
4. Follow the configuration steps:

#### Step 1: Device Configuration
- **I2C Bus Number**: Usually `1` for Raspberry Pi
- **I2C Address**: Select based on your ADDR pin connection

The integration will test the connection before proceeding.

#### Step 2: Channel Selection
- **Channels**: Select which channels to monitor (0-3)
- **Gain**: Choose voltage range (default: ±4.096V)

#### Step 3: Per-Channel Configuration
For each selected channel:
- **Measurement Type**: Single-ended or Differential
- **Differential Pair**: If differential, select pair (0-1, 0-3, 1-3, 2-3)
- **Sensor Name**: Custom name (or use auto-generated name)

### Example Configuration

**Single-Ended Setup:**
- Monitor 4 independent analog sensors on channels 0-3
- Each sensor measures voltage relative to ground
- Gain: ±4.096V (suitable for 0-3.3V sensors)

**Differential Setup:**
- Measure voltage difference between two channels
- Example: Battery voltage monitoring (positive on A0, negative on A1)
- Gain: ±0.256V for precise low-voltage measurements

## Usage

### Sensor Entities

Each configured channel creates a sensor entity:

```
sensor.ads1115_channel_0
sensor.ads1115_channel_1
sensor.ads1115_differential_0_1
```

### Sensor Attributes

Each sensor provides:
- **State**: Voltage reading (in Volts)
- **Attributes**:
  - `raw_value`: Raw ADC value (0-32767 for ADS1115)
  - `gain`: Current gain setting (e.g., "±4.096V")
  - `max_voltage`: Maximum measurable voltage
  - `channel`: Channel number (for single-ended)
  - `measurement_type`: "single-ended" or "differential"

### Automation Examples

**Monitor Soil Moisture:**

```yaml
automation:
  - alias: "Low Soil Moisture Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.ads1115_soil_moisture
        below: 1.5  # Voltage threshold
    action:
      - service: notify.mobile_app
        data:
          message: "Plant needs watering!"
```

**Battery Monitoring:**

```yaml
automation:
  - alias: "Low Battery Warning"
    trigger:
      - platform: numeric_state
        entity_id: sensor.ads1115_differential_0_1
        below: 3.0  # Battery voltage
    action:
      - service: light.turn_on
        target:
          entity_id: light.warning_light
        data:
          color_name: red
```

**Log Sensor Data:**

```yaml
sensor:
  - platform: template
    sensors:
      moisture_percentage:
        friendly_name: "Soil Moisture %"
        unit_of_measurement: "%"
        value_template: >
          {% set voltage = states('sensor.ads1115_soil_moisture') | float %}
          {{ ((voltage / 3.3) * 100) | round(1) }}
```

## Troubleshooting

### I2C Permission Denied

**Error**: `Permission denied accessing I2C`

**Solution**:
```bash
sudo usermod -a -G i2c homeassistant
sudo reboot
```

### Device Not Found

**Error**: `Failed to connect to ADS1115`

**Check**:
1. Verify wiring connections
2. Run `sudo i2cdetect -y 1` to see if device is detected
3. Check I2C address matches ADDR pin configuration
4. Ensure I2C is enabled: `ls /dev/i2c-*`

### Sensor Shows "Unavailable"

**Causes**:
- I2C communication error
- Loose wiring
- Power supply issue

**Solution**:
1. Check Home Assistant logs: **Settings** → **System** → **Logs**
2. Verify wiring and power supply
3. Restart the integration

### Incorrect Readings

**Check**:
1. **Gain setting**: Ensure gain matches your sensor voltage range
2. **Voltage range**: Sensor output should be within selected gain range
3. **Calibration**: Some sensors may need calibration in automations

## Technical Details

### Specifications

- **Resolution**: 16-bit (32768 levels)
- **Sample Rate**: 8-860 samples per second (depends on ADS1115 configuration)
- **Update Interval**: 30 seconds (default)
- **I2C Bus Speed**: Standard (100 kHz) or Fast (400 kHz)

### Gain Settings

| Gain | Voltage Range | Best For |
|------|---------------|----------|
| ±6.144V | -6.144V to +6.144V | 5V sensors |
| ±4.096V | -4.096V to +4.096V | 3.3V sensors (default) |
| ±2.048V | -2.048V to +2.048V | Precision measurements |
| ±1.024V | -1.024V to +1.024V | Low voltage sensors |
| ±0.512V | -0.512V to +0.512V | Very low voltage |
| ±0.256V | -0.256V to +0.256V | Ultra-precise measurements |

**Note**: Input voltage should never exceed VDD + 0.3V or go below GND - 0.3V, regardless of gain setting.

### Dependencies

This integration automatically installs:
- `ADS1x15-ADC==1.2.2` - ADS1115 Python library
- `smbus2` - I2C communication library

## Roadmap

Future enhancements planned:

- **v1.1.0**:
  - ADS1015 support (12-bit variant)
  - Per-channel calibration (offset/scale)
  - Configurable update intervals

- **v1.2.0**:
  - Comparator/alert support (ALERT/RDY pin)
  - Continuous conversion mode
  - Service calls for on-demand reads

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

- **Issues**: [GitHub Issues](https://github.com/idreamshen/hacs-ads1115/issues)
- **Discussions**: [GitHub Discussions](https://github.com/idreamshen/hacs-ads1115/discussions)

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Credits

- Developed by [@idreamshen](https://github.com/idreamshen)
- Uses the [ADS1x15-ADC](https://github.com/chandrawi/ADS1x15-ADC) library by chandrawi
- Inspired by the Home Assistant community

## Disclaimer

This is a third-party custom component and is not affiliated with or endorsed by Home Assistant or Texas Instruments.
