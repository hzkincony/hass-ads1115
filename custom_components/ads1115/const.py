"""Constants for the ADS1115 ADC Sensor integration."""

DOMAIN = "ads1115"

# Configuration keys
CONF_I2C_BUS = "i2c_bus"
CONF_I2C_ADDRESS = "i2c_address"
CONF_CHANNELS = "channels"
CONF_GAIN = "gain"
CONF_MEASUREMENT_TYPE = "measurement_type"
CONF_DIFFERENTIAL_PAIR = "differential_pair"
CONF_MULTIPLIER = "multiplier"

# Default values
DEFAULT_I2C_BUS = 1
DEFAULT_I2C_ADDRESS = 0x48
DEFAULT_GAIN = "4.096"
DEFAULT_SCAN_INTERVAL = 30  # seconds
DEFAULT_NAME = "ADS1115"
DEFAULT_MULTIPLIER = 1.0

# I2C addresses (based on ADDR pin connection)
I2C_ADDRESSES = {
    "0x48": {"value": 0x48, "label": "0x48 (ADDR -> GND)"},
    "0x49": {"value": 0x49, "label": "0x49 (ADDR -> VDD)"},
    "0x4A": {"value": 0x4A, "label": "0x4A (ADDR -> SDA)"},
    "0x4B": {"value": 0x4B, "label": "0x4B (ADDR -> SCL)"},
}

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

# Error messages
ERROR_CANNOT_CONNECT = "cannot_connect"
ERROR_UNKNOWN = "unknown"
ERROR_PERMISSION_DENIED = "permission_denied"
