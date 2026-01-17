"""Support for ADS1115 ADC sensors."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricPotential
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_I2C_ADDRESS,
    DOMAIN,
    MANUFACTURER,
    MEASUREMENT_DIFFERENTIAL,
    MODEL,
)
from .coordinator import ADS1115Coordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ADS1115 sensor entities."""
    coordinator: ADS1115Coordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Create sensor entities for each configured channel
    entities = []
    for channel_id, channel_config in coordinator.channels_config.items():
        entities.append(
            ADS1115Sensor(
                coordinator=coordinator,
                config_entry=config_entry,
                channel_id=channel_id,
                channel_config=channel_config,
            )
        )

    async_add_entities(entities)
    _LOGGER.debug("Added %d ADS1115 sensor entities", len(entities))


class ADS1115Sensor(CoordinatorEntity[ADS1115Coordinator], SensorEntity):
    """Representation of an ADS1115 ADC sensor."""

    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ADS1115Coordinator,
        config_entry: ConfigEntry,
        channel_id: str,
        channel_config: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._channel_id = channel_id
        self._channel_config = channel_config
        self._config_entry = config_entry

        # Generate unique ID
        i2c_address = config_entry.data[CONF_I2C_ADDRESS]
        self._attr_unique_id = f"{DOMAIN}_{i2c_address:02x}_{channel_id}"

        # Set entity name
        custom_name = channel_config.get("name")
        if custom_name:
            self._attr_name = custom_name
        else:
            # Auto-generate name based on measurement type
            if channel_config.get("measurement_type") == MEASUREMENT_DIFFERENTIAL:
                diff_pair = channel_config.get("differential_pair", "0-1")
                self._attr_name = f"Differential {diff_pair}"
            else:
                channel_num = channel_config.get("channel", 0)
                self._attr_name = f"Channel {channel_num}"

        _LOGGER.debug(
            "Created sensor: id=%s, name=%s, unique_id=%s",
            channel_id,
            self._attr_name,
            self._attr_unique_id,
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        i2c_address = self._config_entry.data[CONF_I2C_ADDRESS]
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name=f"ADS1115 (0x{i2c_address:02x})",
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
            "gain": channel_data.get("gain"),
            "max_voltage": channel_data.get("max_voltage"),
        }

        # Add channel-specific attributes
        if self._channel_config.get("measurement_type") == MEASUREMENT_DIFFERENTIAL:
            attributes["differential_pair"] = self._channel_config.get(
                "differential_pair"
            )
            attributes["measurement_type"] = "differential"
        else:
            attributes["channel"] = self._channel_config.get("channel")
            attributes["measurement_type"] = "single-ended"

        return attributes
