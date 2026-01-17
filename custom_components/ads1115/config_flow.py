"""Config flow for ADS1115 ADC Sensor integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CHANNELS,
    CONF_CHANNELS,
    CONF_DIFFERENTIAL_PAIR,
    CONF_GAIN,
    CONF_I2C_ADDRESS,
    CONF_I2C_BUS,
    CONF_MEASUREMENT_TYPE,
    DEFAULT_GAIN,
    DEFAULT_I2C_ADDRESS,
    DEFAULT_I2C_BUS,
    DEFAULT_NAME,
    DIFFERENTIAL_PAIRS,
    DOMAIN,
    ERROR_CANNOT_CONNECT,
    ERROR_PERMISSION_DENIED,
    ERROR_UNKNOWN,
    GAIN_OPTIONS,
    I2C_ADDRESSES,
    MEASUREMENT_DIFFERENTIAL,
    MEASUREMENT_SINGLE,
)

_LOGGER = logging.getLogger(__name__)


class ADS1115ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ADS1115."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._i2c_bus: int | None = None
        self._i2c_address: int | None = None
        self._selected_channels: list[int] = []
        self._channels_config: dict[str, Any] = {}
        self._current_channel_index: int = 0

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - device configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            i2c_bus = user_input[CONF_I2C_BUS]
            i2c_address_str = user_input[CONF_I2C_ADDRESS]
            i2c_address = I2C_ADDRESSES[i2c_address_str]["value"]

            # Test connection
            error = await self._test_connection(i2c_bus, i2c_address)
            if error:
                errors["base"] = error
            else:
                self._i2c_bus = i2c_bus
                self._i2c_address = i2c_address

                # Move to channel selection
                return await self.async_step_select_channels()

        # Show device configuration form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_I2C_BUS, default=DEFAULT_I2C_BUS): int,
                vol.Required(
                    CONF_I2C_ADDRESS, default="0x48"
                ): vol.In(
                    {k: v["label"] for k, v in I2C_ADDRESSES.items()}
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_select_channels(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle channel selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            selected_channels = user_input.get("channels", [])
            gain = user_input.get(CONF_GAIN, DEFAULT_GAIN)

            if not selected_channels:
                errors["base"] = "no_channels"
            else:
                # Convert string channel IDs to integers
                self._selected_channels = sorted([int(ch) for ch in selected_channels])
                self._current_channel_index = 0

                # Store default gain for all channels
                for channel in self._selected_channels:
                    channel_id = f"channel_{channel}"
                    self._channels_config[channel_id] = {
                        "channel": channel,  # Now it's an int
                        "gain": gain,
                    }

                # Move to per-channel configuration
                return await self.async_step_configure_channel()

        # Show channel selection form
        data_schema = vol.Schema(
            {
                vol.Required("channels"): cv.multi_select(
                    {str(ch): f"Channel {ch}" for ch in CHANNELS}
                ),
                vol.Required(CONF_GAIN, default=DEFAULT_GAIN): vol.In(
                    {k: f"±{k}V" for k in GAIN_OPTIONS.keys()}
                ),
            }
        )

        return self.async_show_form(
            step_id="select_channels",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "device": f"ADS1115 (0x{self._i2c_address:02x})",
            },
        )

    async def async_step_configure_channel(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure individual channel settings."""
        if self._current_channel_index >= len(self._selected_channels):
            # All channels configured, create entry
            return self.async_create_entry(
                title=f"{DEFAULT_NAME} (0x{self._i2c_address:02x})",
                data={
                    CONF_I2C_BUS: self._i2c_bus,
                    CONF_I2C_ADDRESS: self._i2c_address,
                    CONF_CHANNELS: self._channels_config,
                },
            )

        channel = self._selected_channels[self._current_channel_index]
        channel_id = f"channel_{channel}"

        if user_input is not None:
            measurement_type = user_input.get(
                CONF_MEASUREMENT_TYPE, MEASUREMENT_SINGLE
            )
            custom_name = user_input.get("name", "").strip()

            # Update channel config
            self._channels_config[channel_id][CONF_MEASUREMENT_TYPE] = measurement_type

            if measurement_type == MEASUREMENT_DIFFERENTIAL:
                diff_pair = user_input.get(CONF_DIFFERENTIAL_PAIR, "0-1")
                self._channels_config[channel_id][CONF_DIFFERENTIAL_PAIR] = diff_pair

                # Default name for differential
                if not custom_name:
                    custom_name = f"Differential {diff_pair}"

            else:
                # Default name for single-ended
                if not custom_name:
                    custom_name = f"Channel {channel}"

            self._channels_config[channel_id]["name"] = custom_name

            # Move to next channel
            self._current_channel_index += 1
            return await self.async_step_configure_channel()

        # Build form for current channel
        default_name = f"Channel {channel}"

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_MEASUREMENT_TYPE, default=MEASUREMENT_SINGLE
                ): vol.In(
                    {
                        MEASUREMENT_SINGLE: "Single-ended",
                        MEASUREMENT_DIFFERENTIAL: "Differential",
                    }
                ),
                vol.Optional(CONF_DIFFERENTIAL_PAIR, default="0-1"): vol.In(
                    {k: f"AIN{k}" for k in DIFFERENTIAL_PAIRS.keys()}
                ),
                vol.Optional("name", default=default_name): str,
            }
        )

        return self.async_show_form(
            step_id="configure_channel",
            data_schema=data_schema,
            description_placeholders={
                "channel": str(channel),
                "progress": f"{self._current_channel_index + 1}/{len(self._selected_channels)}",
            },
        )

    async def _test_connection(self, i2c_bus: int, i2c_address: int) -> str | None:
        """Test I2C connection to ADS1115."""

        def test_i2c():
            """Test I2C connection in executor."""
            try:
                from ADS1x15 import ADS1115
            except ImportError:
                return ERROR_UNKNOWN

            try:
                adc = ADS1115(i2c_bus, i2c_address)
                # Try to read from channel 0 to verify device responds
                adc.setGain(1)  # ±4.096V
                adc.readADC(0)
                return None  # Success
            except OSError as err:
                if err.errno == 13:
                    return ERROR_PERMISSION_DENIED
                return ERROR_CANNOT_CONNECT
            except Exception:
                return ERROR_CANNOT_CONNECT

        try:
            error = await self.hass.async_add_executor_job(test_i2c)
            return error
        except Exception:
            _LOGGER.exception("Unexpected error testing I2C connection")
            return ERROR_UNKNOWN


# Import cv after all class definitions to avoid circular import
from homeassistant.helpers import config_validation as cv
