"""Config flow for Pstryk Energy Meter"""
# https://developers.home-assistant.io/docs/data_entry_flow_index/

import logging
from functools import partial
from homeassistant import config_entries
#from homeassistant.core import callback
#from homeassistant.data_entry_flow import FlowResultType
import voluptuous as vol
import requests

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCHEMA = vol.Schema({
    vol.Required("name"): str,
    vol.Required("hostname"): str,
})

class PstrykEnergyMeterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config Flow for Pstryk Energy Meter"""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=SCHEMA,
            )

        errors = {}

        hostname = user_input["hostname"]
        response = await self.hass.async_add_executor_job(partial(requests.get, f"http://{hostname}/info", timeout=2))
        try:
            response.raise_for_status()
        except requests.exceptions.RequestException as ex:
            errors["base"] = f"Error connecting to meter {ex}"

        info = response.json()
        device = info.get("device", {})
        serial = device.get("id")
        product = device.get("product")

        if not errors:
            if device.get("product") != "PstrykEnergyMeter":
                errors["base"] = "Not a Pstryk Energy Meter?"
            elif device.get("type") != "multiSensor":
                errors["base"] = "Not a multi sensor?"

        if errors:
            return self.async_show_form(
                step_id="user",
                data_schema=SCHEMA,
                errors=errors,
            )

        await self.async_set_unique_id(serial)
        self._abort_if_unique_id_configured()

        name = user_input["name"]
        return self.async_create_entry(title=f"{product} {name}", data=user_input)
