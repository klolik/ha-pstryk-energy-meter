"""Sensors for Pstryk Energy Meter"""
# https://developers.home-assistant.io/docs/core/entity/sensor/

import logging
from datetime import timedelta
from functools import partial
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    UnitOfPower,
    UnitOfElectricPotential,
    UnitOfElectricCurrent,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
#from homeassistant.util import dt as dt_util
import requests


from .const import DOMAIN, MANUFACTURER, DEFAULT_NAME, HOME_URL


_LOGGER = logging.getLogger(__name__)

MULTISENSOR_TYPES = [
    "activePower",
    "apparentEnergy",
    "apparentPower",
    "current",
    "forwardActiveEnergy",
    "forwardReactiveEnergy",
    "frequency",
    "reactivePower",
    "reverseActiveEnergy",
    "reverseReactiveEnergy",
    "voltage",
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> bool:
    """Setup device integration"""
    _LOGGER.debug("setting up coordinator for %s", entry)

    #TODO# separate coordinator for /info? how should we poll for firmware updates?
    host = entry.data.get(CONF_HOST)
    response = await hass.async_add_executor_job(partial(requests.get, f"http://{host}/info", timeout=2))
    info = response.json()

    coordinator = PstrykEnergyMeterDataUpdateCoordinator(hass, entry, info)
    _LOGGER.debug("awaiting coordinator first refresh %s", entry)
    await coordinator.async_config_entry_first_refresh()
    _LOGGER.debug("assigning coordinator %s", entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    _LOGGER.debug("setting up sensors")

    entities = [
        PstrykEnergyMeterVoltageSensor(coordinator, f"voltage_{n}", f"Voltage {n}") for n in range(1, 4)
    ]
    entities.extend([
        PstrykEnergyMeterCurrentSensor(coordinator, f"current_{n}", f"Current {n}") for n in range(1, 4)
    ])
    entities.extend([
        PstrykEnergyMeterPowerSensor(coordinator, f"activePower_{n}", f"Active Power {n}") for n in range(1, 4)
    ])
    entities.extend([
        PstrykEnergyMeterPowerSensor(coordinator, "activePower_0", "Active Power Total")
    ])

    async_add_entities(entities)
    return True


class PstrykEnergyMeterDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator for device state polling"""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, info) -> None:
        _LOGGER.debug("initializing coordinator: %s", entry)
        super().__init__(
            hass,
            _LOGGER,
            name=entry.title,
            update_interval=timedelta(seconds=30) #TODO# User configurable update interval with lower bound
        )

        self.entry = entry
        self.host = entry.data.get(CONF_HOST)
        _LOGGER.debug("host: %s", self.host)

        self._raw_data = None
        self.data = None
        self.last_update_success = None

        device = info.get("device", {})
        self.serial_number = device.get("id")

        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, device.get("id"))},
            name=DEFAULT_NAME, #info.product
            model=device.get("hv"),
            sw_version=device.get("fv"),
            manufacturer=MANUFACTURER,
            configuration_url=HOME_URL,
        )

    async def _async_update_data(self):
        try:
            _LOGGER.debug("calling %s", self.host)
            response = await self.hass.async_add_executor_job(requests.get, f"http://{self.host}/state")
            response.raise_for_status()
            self._raw_data = response.json()
            _LOGGER.debug("received %s", self._raw_data)
            self.last_update_success = True

            data = {}
            for it in self._raw_data.get("multiSensor", {}).get("sensors", []):
                data["{type}_{id}".format(**it)] = it

            self.data = data
            return self.data
        except requests.exceptions.RequestException as ex:
            self.last_update_success = False
            raise UpdateFailed(f"Error communicating with API: {ex}") from ex


class PstrykEnergyMeterBaseSensor(SensorEntity):
    """Base class with common attributes"""

    def __init__(self, coordinator: DataUpdateCoordinator, src: str, sid: str, name: str) -> None:
        """Initialize sensor with src: json data key, sid: entity id, name: display name"""
        super().__init__()
        _LOGGER.debug("setting up %s", sid)
        self._coordinator = coordinator
        self.src = src
        self._attr_name = f"{DEFAULT_NAME} {name}"
        self._attr_unique_id = f"{self._coordinator.entry.entry_id}_{sid}"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_info = self._coordinator.device_info

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )

    @property
    def available(self) -> bool:
        return self._coordinator.last_update_success


class PstrykEnergyMeterVoltageSensor(PstrykEnergyMeterBaseSensor):
    """Voltage sensor"""

    def __init__(self, coordinator: DataUpdateCoordinator, key: str, name: str) -> None:
        super().__init__(coordinator, key, key, name)
        self._attr_device_class = SensorDeviceClass.VOLTAGE
        self._attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        return self._coordinator.data[self.src].get("value") / 10


class PstrykEnergyMeterPowerSensor(PstrykEnergyMeterBaseSensor):
    """Power sensor"""

    def __init__(self, coordinator: DataUpdateCoordinator, key: str, name: str) -> None:
        super().__init__(coordinator, key, key, name)
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        return self._coordinator.data[self.src].get("value")


class PstrykEnergyMeterCurrentSensor(PstrykEnergyMeterBaseSensor):
    """Electric current sensor"""

    def __init__(self, coordinator: DataUpdateCoordinator, key: str, name: str) -> None:
        super().__init__(coordinator, key, key, name)
        self._attr_device_class = SensorDeviceClass.CURRENT
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.MILLIAMPERE
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        return self._coordinator.data[self.src].get("value")
