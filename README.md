# ADS1115 ADC Sensor (Home Assistant)

Home Assistant custom integration for the Texas Instruments ADS1115 ADC.

## Installation

### Option 1: HACS (Custom Repository)
- Add this repository to HACS as a custom integration.
- Install **ADS1115 ADC Sensor** from HACS.
- Restart Home Assistant.

### Option 2: Manual
- Copy `custom_components/ads1115` into your Home Assistant `config/custom_components` directory.
- Restart Home Assistant.

## Configuration Example

Use this configuration from `configuration.yaml`:

```yaml
ads1115:
  - address: 0x48
    i2c_bus: 1

sensor:
  - platform: ads1115
    multiplexer: A0_GND
    gain: 4.096
    name: "A1"
    multiplier: 1.51
  - platform: ads1115
    multiplexer: A1_GND
    gain: 4.096
    name: "A2"
    multiplier: 1.51
  - platform: ads1115
    multiplexer: A2_GND
    gain: 4.096
    name: "A3"
    multiplier: 6.67
    device_class: current
    unit_of_measurement: mA
  - platform: ads1115
    multiplexer: A3_GND
    gain: 4.096
    name: "A4"
    multiplier: 6.67
    device_class: current
    unit_of_measurement: mA
```

## Screenshot

![Sensor card](docs/screenshot.png)
