"""Support for ADS1115 ADC sensors."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import CONF_ADDRESS, CONF_NAME, UnitOfElectricPotential
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_GAIN,
    CONF_HUB_ID,
    CONF_I2C_BUS,
    CONF_MULTIPLEXER,
    CONF_MULTIPLIER,
    DEFAULT_GAIN,
    DEFAULT_I2C_ADDRESS,
    DEFAULT_I2C_BUS,
    DEFAULT_MULTIPLIER,
    DOMAIN,
    GAIN_OPTIONS,
    MANUFACTURER,
    MEASUREMENT_DIFFERENTIAL,
    MEASUREMENT_SINGLE,
    MODEL,
    MULTIPLEXER_MAP,
)
from .coordinator import ADS1115Coordinator

_LOGGER = logging.getLogger(__name__)

def validate_gain(value):
    """Validate and convert gain to string."""
    # Convert to string if it's a number
    gain_str = str(value)
    if gain_str not in GAIN_OPTIONS:
        raise vol.Invalid(f"Invalid gain value: {value}. Must be one of {list(GAIN_OPTIONS.keys())}")
    return gain_str


def _validate_hub_or_direct_config(config: dict) -> dict:
    """Validate that either hub_id OR (i2c_bus + i2c_address) is provided."""
    has_hub_id = CONF_HUB_ID in config
    has_i2c_bus = CONF_I2C_BUS in config
    has_address = CONF_ADDRESS in config
    
    # If hub_id is provided, i2c_bus and address are optional (will be fetched from hub)
    if has_hub_id:
        return config
    
    # If hub_id is NOT provided, i2c_bus and address must be provided (with defaults)
    # The schema already has defaults, so this is automatically satisfied
    return config


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_HUB_ID): cv.string,
        vol.Optional(CONF_I2C_BUS, default=DEFAULT_I2C_BUS): cv.positive_int,
        vol.Optional(CONF_ADDRESS, default=DEFAULT_I2C_ADDRESS): cv.positive_int,
        vol.Required(CONF_MULTIPLEXER): vol.In(list(MULTIPLEXER_MAP.keys())),
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_GAIN, default=DEFAULT_GAIN): validate_gain,
        vol.Optional(CONF_MULTIPLIER, default=DEFAULT_MULTIPLIER): vol.All(
            vol.Coerce(float), vol.Range(min=0.001, max=1000.0)
        ),
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up ADS1115 sensor platform."""
    hub_id = config.get(CONF_HUB_ID)
    i2c_bus = config.get(CONF_I2C_BUS)
    i2c_address = config.get(CONF_ADDRESS)
    multiplexer = config[CONF_MULTIPLEXER]

    # Initialize hass.data[DOMAIN] if needed
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    # Determine which coordinator to use
    coordinator = None
    
    if hub_id:
        # User provided hub_id - look up the hub
        if hub_id not in hass.data[DOMAIN]:
            raise vol.Invalid(
                f"Hub '{hub_id}' not found. Make sure the hub is defined in the ads1115 component configuration."
            )
        coordinator = hass.data[DOMAIN][hub_id]
        
        # Get i2c_bus and i2c_address from the coordinator (for logging and entity creation)
        i2c_bus = coordinator.i2c_bus
        i2c_address = coordinator.i2c_address
        
        _LOGGER.debug(
            "Using hub '%s' (bus=%d, address=0x%02x) for sensor",
            hub_id,
            i2c_bus,
            i2c_address,
        )
    else:
        # No hub_id - use direct i2c_bus and i2c_address
        # Try to find existing coordinator by address key
        coordinator_key = f"{i2c_bus}_{i2c_address}"
        
        if coordinator_key in hass.data[DOMAIN]:
            coordinator = hass.data[DOMAIN][coordinator_key]
            _LOGGER.debug(
                "Using existing implicit hub at bus=%d, address=0x%02x",
                i2c_bus,
                i2c_address,
            )
        else:
            # Create new implicit coordinator
            _LOGGER.info(
                "Creating implicit ADS1115 hub at 0x%02x on bus %d (no hub configuration found)",
                i2c_address,
                i2c_bus,
            )
            coordinator = ADS1115Coordinator(hass, i2c_bus, i2c_address, {})
            hass.data[DOMAIN][coordinator_key] = coordinator

    # Parse multiplexer to determine measurement type
    mux_config = MULTIPLEXER_MAP[multiplexer]
    measurement_type = mux_config["type"]

    # Generate a unique channel ID based on multiplexer setting
    channel_id = f"mux_{multiplexer.replace('-', '_').replace('_GND', '')}"

    # Build channel config
    channel_config = {
        CONF_NAME: config[CONF_NAME],
        CONF_MULTIPLEXER: multiplexer,
        "measurement_type": measurement_type,
        CONF_GAIN: config[CONF_GAIN],
        CONF_MULTIPLIER: config[CONF_MULTIPLIER],
    }

    # Add channel or differential pair info
    if measurement_type == MEASUREMENT_SINGLE:
        channel_config["channel"] = mux_config["channel"]
    else:
        channel_config["differential_pair"] = mux_config["pair"]

    _LOGGER.debug(
        "Setting up ADS1115 sensor: bus=%d, address=0x%02x, multiplexer=%s",
        i2c_bus,
        i2c_address,
        multiplexer,
    )

    # Add this channel to the coordinator
    coordinator.channels_config[channel_id] = channel_config

    # Initialize coordinator if this is the first channel
    if coordinator.adc is None:
        await coordinator.async_setup()
        await coordinator.async_config_entry_first_refresh()

    # Create sensor entity
    async_add_entities([
        ADS1115Sensor(
            coordinator=coordinator,
            channel_id=channel_id,
            channel_config=channel_config,
            i2c_address=i2c_address,
        )
    ])

    _LOGGER.debug("Added ADS1115 sensor: %s (%s)", config[CONF_NAME], multiplexer)


class ADS1115Sensor(CoordinatorEntity[ADS1115Coordinator], SensorEntity):
    """Representation of an ADS1115 ADC sensor."""

    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True
    _attr_suggested_display_precision = 3

    def __init__(
        self,
        coordinator: ADS1115Coordinator,
        channel_id: str,
        channel_config: dict[str, Any],
        i2c_address: int,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._channel_id = channel_id
        self._channel_config = channel_config
        self._i2c_address = i2c_address

        # Generate unique ID
        multiplexer = channel_config[CONF_MULTIPLEXER]
        self._attr_unique_id = f"{DOMAIN}_{i2c_address:02x}_{multiplexer.replace('-', '_')}"

        # Set entity name from config
        self._attr_name = channel_config.get(CONF_NAME, f"ADS1115 {multiplexer}")

        _LOGGER.debug(
            "Created sensor: id=%s, name=%s, unique_id=%s",
            channel_id,
            self._attr_name,
            self._attr_unique_id,
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"ads1115_{self._i2c_address:02x}")},
            name=f"ADS1115 (0x{self._i2c_address:02x})",
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version="1.0.0",
        )

    @property
    def native_value(self) -> float | None:
        """Return the voltage reading."""
        if self.coordinator.data is None:
            return None

        channel_data = self.coordinator.data.get(self._channel_id)
        if channel_data is None:
            return None

        return channel_data.get("voltage")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self.coordinator.last_update_success:
            return False

        if self.coordinator.data is None:
            return False

        channel_data = self.coordinator.data.get(self._channel_id)
        return channel_data is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if self.coordinator.data is None:
            return None

        channel_data = self.coordinator.data.get(self._channel_id)
        if channel_data is None:
            return None

        attributes = {
            "raw_value": channel_data.get("raw"),
            "raw_voltage": channel_data.get("raw_voltage"),
            "multiplier": channel_data.get("multiplier"),
            "gain": channel_data.get("gain"),
            "max_voltage": channel_data.get("max_voltage"),
            "multiplexer": self._channel_config[CONF_MULTIPLEXER],
        }

        # Add measurement-specific attributes
        if self._channel_config.get("measurement_type") == MEASUREMENT_DIFFERENTIAL:
            attributes["differential_pair"] = self._channel_config.get("differential_pair")
            attributes["measurement_type"] = "differential"
        else:
            attributes["channel"] = self._channel_config.get("channel")
            attributes["measurement_type"] = "single-ended"

        return attributes
