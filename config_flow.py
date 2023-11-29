"""Config flow for MotionBlinds BLE integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import (
    ConfigFlow,
    FlowResult,
    ConfigEntry,
    OptionsFlow,
)
from homeassistant.components.zeroconf import ZeroconfServiceInfo
from homeassistant.core import callback
from .const import DOMAIN, CONF_HOSTNAME, CONF_IP_ADDRESS, DISCOVERY_NAME, CONF_KEY

from .select import SceneSelect

import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({vol.Optional(CONF_KEY): str})


class FlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MotionBlinds RS485."""

    VERSION = 1

    _discovery_info: ZeroconfServiceInfo

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> FlowResult:
        """Handle zeroconf discovery."""

        _LOGGER.info("Discovered MotionBlinds RS485 device: %s", discovery_info)
        self._discovery_info = discovery_info

        # discovery_info: ZeroconfServiceInfo(host='10.15.3.32', addresses=['10.15.3.32'], port=80, hostname='motionblinds-rs485-D4D4DA8512FC.local.', type='_http._tcp.local.', name='motionblinds-rs485-D4D4DA8512FC._http._tcp.local.', properties={})
        hostname = discovery_info.hostname.replace(".local.", "")
        await self.async_set_unique_id(hostname)
        self._abort_if_unique_id_configured()

        self.context["local_name"] = "X"
        self.context["title_placeholders"] = {
            "name": DISCOVERY_NAME.format(
                mac_code=hostname.replace("motionblinds-rs485-", "")[-5:-1]
            )
        }
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, any] | None = None
    ) -> FlowResult:
        """Confirm a single device."""
        hostname = self._discovery_info.hostname.replace(".local.", "")
        ip_address = (
            self._discovery_info.addresses[0]
            if len(self._discovery_info.addresses) != 0
            else None
        )
        if user_input is not None:
            return self.async_create_entry(
                title=hostname,
                data={
                    CONF_HOSTNAME: hostname,
                    CONF_IP_ADDRESS: ip_address,
                    CONF_KEY: user_input[CONF_KEY] if CONF_KEY in user_input else "",
                },
            )

        return self.async_show_form(
            step_id="confirm",
            data_schema=STEP_USER_DATA_SCHEMA,
            description_placeholders={"display_name": hostname},
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(OptionsFlow):
    config_entry: ConfigEntry

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        scene_select: SceneSelect = self.hass.data[DOMAIN][self.config_entry.entry_id]
        if user_input is not None:
            updated_data = {
                **self.config_entry.data,
                CONF_KEY: user_input[CONF_KEY],
            }
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=updated_data,
            )
            scene_select.set_key(user_input[CONF_KEY])
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_KEY,
                        default=self.config_entry.data[CONF_KEY],
                    ): str
                }
            ),
        )
