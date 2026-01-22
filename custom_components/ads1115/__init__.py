"""The ADS1115 ADC Sensor integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.const import CONF_ADDRESS, CONF_ID
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_I2C_BUS,
    DEFAULT_I2C_ADDRESS,
    DEFAULT_I2C_BUS,
    DOMAIN,
)
from .coordinator import ADS1115Coordinator

_LOGGER = logging.getLogger(__name__)

# Schema for individual ADS1115 hub configuration
ADS1115_HUB_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_ADDRESS, default=DEFAULT_I2C_ADDRESS): cv.positive_int,
        vol.Optional(CONF_I2C_BUS, default=DEFAULT_I2C_BUS): cv.positive_int,
        vol.Optional(CONF_ID): cv.string,
    }
)

# Schema for the ads1115 component (supports multiple hubs)
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(cv.ensure_list, [ADS1115_HUB_SCHEMA]),
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the ADS1115 component."""
    if DOMAIN not in config:
        return True

    hass.data[DOMAIN] = {}

    # Process each ADS1115 hub defined in the configuration
    for hub_config in config[DOMAIN]:
        i2c_bus = hub_config[CONF_I2C_BUS]
        i2c_address = hub_config[CONF_ADDRESS]
        hub_id = hub_config.get(CONF_ID, f"ads1115_{i2c_address:02x}")

        _LOGGER.debug(
            "Setting up ADS1115 hub: id=%s, bus=%d, address=0x%02x",
            hub_id,
            i2c_bus,
            i2c_address,
        )

        # Create coordinator for this hub (initially with no channels)
        coordinator_key = f"{i2c_bus}_{i2c_address}"
        coordinator = ADS1115Coordinator(hass, i2c_bus, i2c_address, {})

        # Store coordinator by both the internal key and the user-defined ID
        hass.data[DOMAIN][coordinator_key] = coordinator
        if hub_id != coordinator_key:
            hass.data[DOMAIN][hub_id] = coordinator

        _LOGGER.info(
            "Registered ADS1115 hub '%s' at 0x%02x on I2C bus %d",
            hub_id,
            i2c_address,
            i2c_bus,
        )

    return True
