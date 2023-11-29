"""Button entities for the MotionBlinds RS485 integration."""

import logging

from homeassistant.components.button import (
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_START, ATTR_STOP, DOMAIN, ICON_START, ICON_STOP
from .select import SceneSelect
from collections.abc import Callable
from dataclasses import dataclass

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


@dataclass
class CommandButtonEntityDescription(ButtonEntityDescription):
    command_callback: Callable[[SceneSelect], None] | None = None


async def command_start(scene_select: SceneSelect) -> None:
    await scene_select.start()


async def command_stop(scene_select: SceneSelect) -> None:
    await scene_select.stop()


BUTTON_TYPES: dict[str, CommandButtonEntityDescription] = {
    ATTR_START: CommandButtonEntityDescription(
        key=ATTR_START,
        translation_key=ATTR_START,
        icon=ICON_START,
        entity_category=EntityCategory.CONFIG,
        has_entity_name=True,
        command_callback=command_start,
    ),
    ATTR_STOP: CommandButtonEntityDescription(
        key=ATTR_STOP,
        translation_key=ATTR_STOP,
        icon=ICON_STOP,
        entity_category=EntityCategory.CONFIG,
        has_entity_name=True,
        command_callback=command_stop,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up buttons based on a config entry."""
    scene_select: SceneSelect = hass.data[DOMAIN][entry.entry_id]

    _LOGGER.info("Setting up buttons")
    async_add_entities(
        [
            GenericCommandButton(scene_select, entity_description)
            for entity_description in BUTTON_TYPES.values()
        ]
    )


class GenericCommandButton(ButtonEntity):
    """Representation of a command button."""

    def __init__(
        self,
        scene_select: SceneSelect,
        entity_description: CommandButtonEntityDescription,
    ) -> None:
        """Initialize the command button."""
        _LOGGER.info(f"Setting up {entity_description.key} button")
        self.entity_description = entity_description
        self._scene_select = scene_select
        self._attr_unique_id = f"{scene_select.unique_id}_{entity_description.key}"
        self._attr_device_info = scene_select.device_info

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.entity_description.command_callback(self._scene_select)
