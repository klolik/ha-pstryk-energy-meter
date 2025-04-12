"""The Pstryk Energy Meter integration"""

import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    Platform,
    CONF_HOST,
)

from .const import DOMAIN
from .config_flow import PstrykEnergyMeterConfigFlow

PLATFORMS = [Platform.SENSOR]


_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Setup the integration"""
    if DOMAIN not in hass.data:
        hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup config entry"""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload config entry"""
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return True


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Migrate old entry"""
    _LOGGER.debug("Migrating configuration from version %s.%s", config_entry.version, config_entry.minor_version)

    # Can't migrate back from future...
    if config_entry.version > 2:
        return False

    if config_entry.version == 1:
        data = {**config_entry.data}
        data[CONF_HOST] = data.pop("hostname") # renamed `hostname` => `host`
        hass.config_entries.async_update_entry(config_entry, data=data, version=PstrykEnergyMeterConfigFlow.VERSION)

    _LOGGER.debug("Migration to configuration version %s.%s successful", config_entry.version, config_entry.minor_version)
    return True
