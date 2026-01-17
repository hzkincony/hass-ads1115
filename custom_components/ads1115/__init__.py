"""The ADS1115 ADC Sensor integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_CHANNELS, CONF_I2C_ADDRESS, CONF_I2C_BUS, DOMAIN
from .coordinator import ADS1115Coordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ADS1115 from a config entry."""
    i2c_bus = entry.data[CONF_I2C_BUS]
    i2c_address = entry.data[CONF_I2C_ADDRESS]
    channels_config = entry.data[CONF_CHANNELS]

    _LOGGER.debug(
        "Setting up ADS1115 integration: bus=%d, address=0x%02x, channels=%s",
        i2c_bus,
        i2c_address,
        list(channels_config.keys()),
    )

    # Create coordinator
    coordinator = ADS1115Coordinator(hass, i2c_bus, i2c_address, channels_config)

    # Initialize the ADC device
    try:
        setup_success = await coordinator.async_setup()
        if not setup_success:
            raise ConfigEntryNotReady("Failed to initialize ADS1115")
    except Exception as err:
        _LOGGER.error("Failed to set up ADS1115: %s", err)
        raise ConfigEntryNotReady(f"Failed to initialize ADS1115: {err}") from err

    # Perform first data fetch
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward entry setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading ADS1115 integration entry: %s", entry.entry_id)

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Remove coordinator from hass.data
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
