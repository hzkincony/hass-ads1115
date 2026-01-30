"""DataUpdateCoordinator for ADS1115 ADC."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    GAIN_OPTIONS,
    MEASUREMENT_DIFFERENTIAL,
    MEASUREMENT_SINGLE,
)

_LOGGER = logging.getLogger(__name__)


class ADS1115Coordinator(DataUpdateCoordinator):
    """Class to manage fetching ADS1115 data from I2C."""

    def __init__(
        self,
        hass: HomeAssistant,
        i2c_bus: int,
        i2c_address: int,
        channels_config: dict[str, Any],
    ) -> None:
        """Initialize the coordinator."""
        self.i2c_bus = i2c_bus
        self.i2c_address = i2c_address
        self.channels_config = channels_config
        self.adc = None

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{hex(i2c_address)}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def async_setup(self) -> bool:
        """Set up the ADS1115 device."""

        def setup_adc():
            """Set up ADC in executor thread."""
            try:
                from ADS1x15 import ADS1115
            except ImportError as err:
                raise UpdateFailed(f"Failed to import ADS1x15 library: {err}") from err

            adc = ADS1115(self.i2c_bus, self.i2c_address)
            return adc

        try:
            self.adc = await self.hass.async_add_executor_job(setup_adc)
            _LOGGER.info(
                "Successfully initialized ADS1115 at I2C address 0x%02x on bus %d",
                self.i2c_address,
                self.i2c_bus,
            )
            return True
        except OSError as err:
            if err.errno == 13:  # Permission denied
                _LOGGER.error(
                    "Permission denied accessing I2C bus %d. "
                    "Add your user to the i2c group: sudo usermod -a -G i2c $USER",
                    self.i2c_bus,
                )
            else:
                _LOGGER.error(
                    "Failed to connect to ADS1115 at 0x%02x on bus %d: %s",
                    self.i2c_address,
                    self.i2c_bus,
                    err,
                )
            raise UpdateFailed(f"Failed to initialize ADS1115: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error setting up ADS1115: %s", err)
            raise UpdateFailed(f"Failed to initialize ADS1115: {err}") from err

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from ADC."""

        def read_channels():
            """Read all configured channels."""
            data = {}
            
            _LOGGER.debug(
                "Starting ADC read cycle - channels_config keys: %s",
                list(self.channels_config.keys()),
            )

            for channel_id, config in self.channels_config.items():
                try:
                    measurement_type = config.get("measurement_type", MEASUREMENT_SINGLE)
                    gain_str = config.get("gain", "4.096")
                    gain_value, max_voltage = GAIN_OPTIONS[gain_str]

                    # Set gain for this channel
                    self.adc.setGain(gain_value)
                    
                    # Get voltage conversion factor for current gain setting
                    voltage_factor = self.adc.toVoltage()

                    channel_num = None

                    # Read based on measurement type
                    if measurement_type == MEASUREMENT_DIFFERENTIAL:
                        diff_pair = config.get("differential_pair", "0-1")
                        raw_value = self._read_differential(diff_pair)
                    else:
                        channel_num = config.get("channel")
                        raw_value = self.adc.readADC(channel_num)

                    # Convert to voltage using current voltage factor
                    voltage = raw_value * voltage_factor

                    # Apply multiplier (for voltage dividers, etc.)
                    multiplier = config.get("multiplier", 1.0)
                    calibrated_voltage = voltage * multiplier

                    data[channel_id] = {
                        "voltage": round(calibrated_voltage, 4),
                        "raw_voltage": round(voltage, 4),
                        "raw": raw_value,
                        "gain": f"±{gain_str}V",
                        "max_voltage": max_voltage,
                        "multiplier": multiplier,
                    }

                    _LOGGER.debug(
                        "Read complete: channel_id=%s, multiplexer=%s, ADC_channel=%s, name=%s, raw=%d, voltage=%.4fV, factor=%.6f",
                        channel_id,
                        config.get("multiplexer"),
                        channel_num,
                        config.get("name", "unknown"),
                        raw_value,
                        voltage,
                        voltage_factor,
                    )

                except Exception as err:
                    _LOGGER.error("Error reading channel %s: %s", channel_id, err)
                    data[channel_id] = None

            return data

        try:
            return await self.hass.async_add_executor_job(read_channels)
        except OSError as err:
            raise UpdateFailed(f"I2C communication error: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Error reading ADC: {err}") from err

    def _read_differential(self, pair: str) -> int:
        """Read differential measurement."""
        if pair == "0-1":
            return self.adc.readADC_Differential_0_1()
        elif pair == "0-3":
            return self.adc.readADC_Differential_0_3()
        elif pair == "1-3":
            return self.adc.readADC_Differential_1_3()
        elif pair == "2-3":
            return self.adc.readADC_Differential_2_3()
        else:
            raise ValueError(f"Invalid differential pair: {pair}")
