"""Constants for the ADS1115 ADC Sensor integration."""

DOMAIN = "ads1115"

# Configuration keys
CONF_I2C_BUS = "i2c_bus"
CONF_CHANNELS = "channels"
CONF_GAIN = "gain"
CONF_MEASUREMENT_TYPE = "measurement_type"
CONF_DIFFERENTIAL_PAIR = "differential_pair"
CONF_MULTIPLIER = "multiplier"
CONF_MULTIPLEXER = "multiplexer"

# Default values
DEFAULT_I2C_BUS = 1
DEFAULT_I2C_ADDRESS = 0x48
DEFAULT_GAIN = "4.096"
DEFAULT_SCAN_INTERVAL = 30  # seconds
DEFAULT_NAME = "ADS1115"
DEFAULT_MULTIPLIER = 1.0

# Programmable Gain Amplifier settings
# Format: "voltage_range": (ADS1x15 constant value, max voltage)
GAIN_OPTIONS = {
    "6.144": (0, 6.144),    # ±6.144V
    "4.096": (1, 4.096),    # ±4.096V
    "2.048": (2, 2.048),    # ±2.048V
    "1.024": (4, 1.024),    # ±1.024V
    "0.512": (8, 0.512),    # ±0.512V
    "0.256": (16, 0.256),   # ±0.256V
}

# Measurement types
MEASUREMENT_SINGLE = "single"
MEASUREMENT_DIFFERENTIAL = "differential"

# Differential pairs
DIFFERENTIAL_PAIRS = {
    "0-1": "0-1",
    "0-3": "0-3",
    "1-3": "1-3",
    "2-3": "2-3",
}

# Channels
CHANNELS = [0, 1, 2, 3]

# Device info
MANUFACTURER = "Texas Instruments"
MODEL = "ADS1115"

# Multiplexer configuration (ESPHome-style)
# Maps multiplexer names to channel configuration
MULTIPLEXER_MAP = {
    # Single-ended measurements
    "A0_GND": {"type": MEASUREMENT_SINGLE, "channel": 0},
    "A1_GND": {"type": MEASUREMENT_SINGLE, "channel": 1},
    "A2_GND": {"type": MEASUREMENT_SINGLE, "channel": 2},
    "A3_GND": {"type": MEASUREMENT_SINGLE, "channel": 3},
    # Differential measurements
    "A0_A1": {"type": MEASUREMENT_DIFFERENTIAL, "pair": "0-1"},
    "A0_A3": {"type": MEASUREMENT_DIFFERENTIAL, "pair": "0-3"},
    "A1_A3": {"type": MEASUREMENT_DIFFERENTIAL, "pair": "1-3"},
    "A2_A3": {"type": MEASUREMENT_DIFFERENTIAL, "pair": "2-3"},
}
