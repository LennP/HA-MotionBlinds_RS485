"""The MotionBlinds RS485 integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from .const import DOMAIN, ATTR_SCENE, SERVICE_START, SERVICE_STOP
from homeassistant.const import ATTR_ENTITY_ID, Platform
from dataclasses import dataclass
from collections.abc import Callable
from typing import Optional
from homeassistant.helpers import config_validation as cv
import voluptuous as vol
from .select import SceneSelect

_LOGGER = logging.getLogger(__name__)

PLATFORMS = []


SCENE_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
        vol.Required(ATTR_SCENE): vol.All(vol.Coerce(int)),
    }
)


@dataclass
class Service:
    service: str
    service_func: Callable
    schema: Optional[vol.Schema] = None


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up MotionBlinds RS485 integration."""

    _LOGGER.warning("Loading MotionBlinds RS485 integration")

    def generic_entity_service(
        callback: Callable[[SceneSelect], None]
    ) -> Callable[[ServiceCall], None]:
        async def service_func(call: ServiceCall) -> None:
            for scene_select_entity_id in call.data[ATTR_ENTITY_ID]:
                scene_select_entity: SceneSelect = hass.data[DOMAIN].get(
                    scene_select_entity_id
                )
                if scene_select_entity:
                    await callback(scene_select_entity, call)

        return service_func

    async def start_service(scene_select: SceneSelect, call: ServiceCall) -> None:
        print("a")
        await scene_select.start(str(call.data[ATTR_SCENE]))

    async def stop_service(scene_select: SceneSelect, call: ServiceCall) -> None:
        print("b")
        await scene_select.stop(str(call.data[ATTR_SCENE]))

    services = [
        Service(
            SERVICE_START,
            generic_entity_service(start_service),
            SCENE_SERVICE_SCHEMA,
        ),
        Service(
            SERVICE_STOP,
            generic_entity_service(stop_service),
            SCENE_SERVICE_SCHEMA,
        ),
    ]

    for serv in services:
        hass.services.async_register(
            DOMAIN, serv.service, serv.service_func, schema=serv.schema
        )

    _LOGGER.warning("Done registering services")

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MotionBlinds RS485 device from a config entry."""

    _LOGGER.info("Entering async_setup_entry")

    hass.data.setdefault(DOMAIN, {})

    await hass.config_entries.async_forward_entry_setups(entry, [Platform.SELECT])
    await hass.config_entries.async_forward_entry_setups(entry, [Platform.BUTTON])

    _LOGGER.info("Fully loaded entity")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload MotionBlinds RS485 device from a config entry."""

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
