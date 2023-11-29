"""Select entities for the MotionBlinds RS485 integration."""

import logging
from collections.abc import Callable
from datetime import datetime

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.entity import DeviceInfo

from .motionblinds_rs485.device import MotionBlindsRS485Device

import socket

from homeassistant.components.zeroconf import (
    async_get_async_instance,
    async_get_zeroconf,
    async_get_instance,
    HaAsyncServiceBrowser,
    HaAsyncZeroconf,
    HaZeroconf,
)

from zeroconf import (
    BadTypeInNameException,
    InterfaceChoice,
    IPVersion,
    ServiceStateChange,
)

from zeroconf.asyncio import (
    AsyncServiceBrowser,
    AsyncServiceInfo,
    AsyncZeroconf,
    AsyncZeroconfServiceTypes,
)

from .const import (
    ATTR_SCENE,
    CONF_IP_ADDRESS,
    CONF_KEY,
    DOMAIN,
    ICON_SCENE,
    ENTITY_NAME,
    CONF_HOSTNAME,
    MANUFACTURER,
)

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


SELECT_TYPES: dict[str, SelectEntityDescription] = {
    ATTR_SCENE: SelectEntityDescription(
        key=ATTR_SCENE,
        translation_key=ATTR_SCENE,
        icon=ICON_SCENE,
        entity_category=EntityCategory.CONFIG,
        options=list(str(num) for num in range(1, 16)),
        has_entity_name=True,
    )
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up speed select entities based on a config entry."""
    _LOGGER.info("Setting up SpeedSelect")

    _LOGGER.info("Setting up cover with data %s", entry.data)

    scene_select = SceneSelect(entry)
    hass.data[DOMAIN][entry.entry_id] = scene_select
    async_add_entities([scene_select])


class SceneSelect(SelectEntity):
    """Representation of a speed select entity."""

    rs485_device: MotionBlindsRS485Device
    hostname: str
    zeroconf: HaAsyncZeroconf
    async_service_browser: HaAsyncServiceBrowser

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the speed select entity."""
        super().__init__()
        self.hostname = entry.data[CONF_HOSTNAME]
        self.entity_description = SELECT_TYPES[ATTR_SCENE]
        self.config_entry: ConfigEntry = entry

        self._attr_unique_id: str = self.hostname
        self._attr_current_option: str = None
        self._attr_name: str = ENTITY_NAME.format(mac_code=self.hostname[-5:-1])
        self._attr_device_info: DeviceInfo = DeviceInfo(
            identifiers={(DOMAIN, self.hostname)},
            manufacturer=MANUFACTURER,
            name=self._attr_name,
        )

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        self.rs485_device = MotionBlindsRS485Device(
            f"{self.hostname}.local", key=self.config_entry.data[CONF_KEY], use_ha=True
        )
        if (
            CONF_IP_ADDRESS in self.config_entry.data
            and self.config_entry.data[CONF_IP_ADDRESS] is not None
        ):
            self.rs485_device.set_ip_address(self.config_entry.data[CONF_IP_ADDRESS])
        zeroconf_types = await async_get_zeroconf(self.hass)
        self.zeroconf: HaZeroconf = await async_get_instance(self.hass)
        self.async_service_browser = HaAsyncServiceBrowser(
            False,
            self.zeroconf,
            list(zeroconf_types),
            handlers=[self.async_service_update],
        )
        return await super().async_added_to_hass()

    @callback
    def async_service_update(
        self,
        zeroconf: HaZeroconf,
        service_type: str,
        name: str,
        state_change: ServiceStateChange,
    ) -> None:
        # print(zeroconf)
        # print(name)
        # print(service_type)
        # print(state_change)
        if self.hostname in name:
            async_service_info = AsyncServiceInfo(service_type, name)
            async_service_info.load_from_cache(self.zeroconf)
            # print(async_service_info.get_address_and_nsec_records())
            if len(async_service_info.addresses) == 0:
                _LOGGER.warning("Received empty IP address list for %s", self.hostname)
                self.rs485_device.set_ip_address("10.15.3.32")
            else:
                ip_address = socket.inet_ntoa(async_service_info.addresses[0])
                _LOGGER.info("Set IP address of %s to %s", self.hostname, ip_address)
                self.rs485_device.set_ip_address(ip_address)
                updated_data = {
                    **self.config_entry.data,
                    CONF_IP_ADDRESS: ip_address,
                }
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data=updated_data,
                )

    async def async_select_option(self, option: str) -> None:
        """Change the selected speed_level."""
        _LOGGER.info("Selected scene %s", option)
        self._attr_current_option = option
        self.async_write_ha_state()

    async def start(self):
        if self.current_option is None:
            raise Exception("No scene selected")
        await self.rs485_device.start(int(self._attr_current_option))

    async def stop(self):
        if self.current_option is None:
            raise Exception("No scene selected")
        await self.rs485_device.stop(int(self._attr_current_option))
