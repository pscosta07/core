"""Support for Airzone Webserver."""
import copy
from datetime import timedelta
import logging
from typing import List, Optional

import voluptuous as vol

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    HVAC_MODE_COOL,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_OFF,
    PRESET_NONE,
    SUPPORT_FAN_MODE,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import ATTR_TEMPERATURE, CONF_HOST, TEMP_CELSIUS
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import async_track_time_interval

from .airzone_base import Airozne
from .utils import FancoilSpeed, ZoneMode

_LOGGER = logging.getLogger(__name__)

DEFAULT_SCAN_INTERVAL = timedelta(seconds=10)

ZONE_HVAC_MODES = [HVAC_MODE_FAN_ONLY, HVAC_MODE_HEAT, HVAC_MODE_COOL, HVAC_MODE_OFF]
ZONE_HVAC_MODES_SIMPLE = [HVAC_MODE_HEAT_COOL, HVAC_MODE_OFF]
PRESET_SLEEP = "SLEEP"
ZONE_PRESET_MODES = [PRESET_NONE, PRESET_SLEEP]
ZONE_FAN_MODES = [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH]
ZONE_SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE

PLATFORM_SCHEMA = vol.Schema(
    vol.All(
        PLATFORM_SCHEMA.extend(
            {
                vol.Required(CONF_HOST): cv.url,
            }
        )
    )
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up of Airzone platform."""
    sensors = set()
    session = async_get_clientsession(hass)
    airzone = Airozne(session, config[CONF_HOST])

    zones = {}
    try:
        zones = await airzone.get_all_machine_data()
    except ConnectionError:
        _LOGGER.error("Failed to update: connection error")
    except ValueError:
        _LOGGER.error(
            "Failed to update: invalid response returned."
            "Maybe the configured device is not supported"
        )

    if not zones:
        return

    new_sensors = []
    # Creates all adapters for monitored conditions
    for i in zones:
        if str(i["zoneID"]) not in sensors:
            if "modes" in i:
                """ Its a master zone. """
                sensors.add("master")
                master = copy.deepcopy(i)
                master["zone"] = master["zoneID"]
                master["zoneID"] = "master"
                master["name"] = "Master"
                new_sensors.append(AirzoneTemplateSensor(airzone, master))
                i.pop("modes")
                i.pop("speeds")
                i.pop("speed")

            sensors.add(str(i["zoneID"]))
            new_sensors.append(AirzoneTemplateSensor(airzone, i))
            _LOGGER.info("Airzone device " + str(i))
    async_add_entities(new_sensors)

    # Creates a lamdba that fetches an update when called
    def adapter_data_fetcher(data_adapter):
        async def fetch_data(*_):
            await data_adapter.async_update()

        return fetch_data

    # Set up the fetching in a fixed interval for each adapter
    for adapter in new_sensors:
        fetch = adapter_data_fetcher(adapter)
        # fetch data once at set-up
        await fetch()
        async_track_time_interval(hass, fetch, DEFAULT_SCAN_INTERVAL)


class AirzoneTemplateSensor(ClimateEntity):
    """Sensor for the single values (e.g. pv power, ac power)."""

    def __init__(self, airzone, airzone_zone):
        """Initialize the device."""
        self.parent = airzone
        self._name = "Airzone " + str(airzone_zone["name"])
        _LOGGER.info("Airzone configure zone " + self._name)
        self._operational_modes = [e.name for e in ZoneMode]
        self._fan_list = [e.name for e in FancoilSpeed]
        self._airzone_zone = airzone_zone

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def supported_features(self):
        """Return the list of supported features."""
        if "zone" in self._airzone_zone:
            return SUPPORT_FAN_MODE
        else:
            return ZONE_SUPPORT_FLAGS

    @property
    def temperature_unit(self):
        """Return the unit of measurement that is used."""
        return TEMP_CELSIUS

    def turn_on(self):
        """Turn on."""
        self.parent.put_zone_data(self._airzone_zone["zoneID"], "on", 1)

    def turn_off(self):
        """Turn off."""
        self.parent.put_zone_data(self._airzone_zone["zoneID"], "on", 0)

    @property
    def hvac_mode(self) -> str:
        """Return hvac operation ie. heat, cool mode.

        Need to be one of HVAC_MODE_*.
        """
        is_on = bool(self._airzone_zone["on"])
        if "modes" not in self._airzone_zone:
            if is_on:
                return HVAC_MODE_HEAT_COOL
            else:
                return HVAC_MODE_OFF
        else:
            if self._airzone_zone["mode"] == 4:
                return HVAC_MODE_FAN_ONLY
            if self._airzone_zone["mode"] == 3:
                return HVAC_MODE_HEAT
            if self._airzone_zone["mode"] == 2:
                return HVAC_MODE_COOL
            if self._airzone_zone["mode"] == 1:
                return HVAC_MODE_OFF

    @property
    def hvac_modes(self) -> List[str]:
        """Return the list of available hvac operation modes.

        Need to be a subset of HVAC_MODES.
        """
        if "modes" in self._airzone_zone:
            return ZONE_HVAC_MODES
        else:
            return ZONE_HVAC_MODES_SIMPLE

    def set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        if "modes" not in self._airzone_zone:
            if hvac_mode == HVAC_MODE_HEAT_COOL:
                self.parent.put_zone_data(self._airzone_zone["zoneID"], "on", 1)
            else:
                self.parent.put_zone_data(self._airzone_zone["zoneID"], "on", 0)
            return
        if hvac_mode == HVAC_MODE_FAN_ONLY:
            self.parent.put_zone_data(self._airzone_zone["zoneID"], "mode", 4)
            return
        if hvac_mode == HVAC_MODE_HEAT:
            self.parent.put_zone_data(self._airzone_zone["zoneID"], "mode", 3)
            return
        if hvac_mode == HVAC_MODE_COOL:
            self.parent.put_zone_data(self._airzone_zone["zoneID"], "mode", 2)
            return
        if hvac_mode == HVAC_MODE_OFF:
            self.parent.put_zone_data(self._airzone_zone["zoneID"], "mode", 1)
            return

    @property
    def current_humidity(self):
        """Return the current humidity."""
        return self._airzone_zone["humidity"]

    @property
    def current_temperature(self):
        """Return the current temperature."""
        if "zone" in self._airzone_zone:
            return 0
        else:
            return self._airzone_zone["roomTemp"]

    @property
    def target_temperature(self):
        """Set the target temperature for device."""
        return self._airzone_zone["setpoint"]

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return None
        self.parent.put_zone_data(
            self._airzone_zone["zoneID"], "setpoint", round(float(temperature), 1)
        )

    @property
    def preset_mode(self) -> Optional[str]:
        """Return the current preset mode, e.g., home, away, temp.

        Requires SUPPORT_PRESET_MODE.
        """
        # if self._airzone_zone.is_sleep_on():
        #    return PRESET_SLEEP
        return PRESET_NONE

    @property
    def preset_modes(self) -> Optional[List[str]]:
        """Return a list of available preset modes.

        Requires SUPPORT_PRESET_MODE.
        """
        return ZONE_PRESET_MODES

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if preset_mode == PRESET_NONE:
            self._airzone_zone.turnoff_sleep()
        else:
            self._airzone_zone.turnon_sleep()

    @property
    def fan_mode(self) -> Optional[str]:
        """Return the fan setting.

        Requires SUPPORT_FAN_MODE.
        """
        if "speed" in self._airzone_zone:
            fan_mode = self._airzone_zone["speed"]
            if fan_mode == FancoilSpeed.AUTOMATIC:
                return FAN_AUTO
            if fan_mode == FancoilSpeed.SPEED_1:
                return FAN_LOW
            if fan_mode == FancoilSpeed.SPEED_2:
                return FAN_MEDIUM
            if fan_mode == FancoilSpeed.SPEED_3:
                return FAN_HIGH
            return FAN_AUTO
        else:
            return FAN_AUTO

    @property
    def fan_modes(self) -> Optional[List[str]]:
        """Return the list of available fan modes.

        Requires SUPPORT_FAN_MODE.
        """
        if "speed" in self._airzone_zone:
            return ZONE_FAN_MODES
        else:
            return [FAN_AUTO]

    def set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""

        if fan_mode == FAN_AUTO:
            self._airzone_zone.get_speed_selection("AUTOMATIC")
            return
        if fan_mode == FAN_LOW:
            self._airzone_zone.get_speed_selection("SPEED_1")
            return FAN_LOW
        if fan_mode == FAN_MEDIUM:
            self._airzone_zone.get_speed_selection("SPPED_2")
            return FAN_MEDIUM
        if fan_mode == FAN_HIGH:
            self._airzone_zone.get_speed_selection("SPEED_3")

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return self._airzone_zone["minTemp"]

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return self._airzone_zone["maxTemp"]

    @property
    def should_poll(self):
        """Device should not be polled, returns False."""
        return True

    async def async_update(self):
        """Update the internal state."""
        if self._airzone_zone["zoneID"] == "master":
            updated_data = await self.parent.get_zone_data(self._airzone_zone["zone"])
            updated_zone = updated_data[0]
            updated_zone["zone"] = updated_zone["zoneID"]
            updated_zone["zoneID"] = "master"
            updated_zone["name"] = "Master"
        else:
            updated_data = await self.parent.get_zone_data(self._airzone_zone["zoneID"])
            updated_zone = updated_data[0]
            if "modes" in updated_zone:
                updated_zone.pop("modes")
                updated_zone.pop("speeds")
                updated_zone.pop("speed")
        self._airzone_zone = updated_zone
