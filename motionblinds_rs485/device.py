from aiohttp import ClientTimeout, ClientSession, ClientResponse
from requests.exceptions import ConnectionError
import asyncio
from json import JSONDecodeError
from zeroconf import Zeroconf, ServiceBrowser, ServiceListener, IPVersion


class MotionBlindsRS485Listener(ServiceListener):
    def __init__(self, rs485) -> None:
        self.rs485 = rs485
        super().__init__()

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        print(f"Service {name} updated")
        pass

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        print("Removed")
        pass

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        # print(f"Service {name} added, service info: {info}")
        # print(info._ipv4_addresses[0])
        if self.rs485.hostname == info.server:
            ip_address = info.ip_addresses_by_version(IPVersion.V4Only)[0]
            print(f"Found IP of {info.server}: {ip_address}")
            self.rs485.set_ip_address(ip_address)


class MotionBlindsRS485Device:
    hostname: str
    key: str
    ip_address: str | None = None

    zeroconf: Zeroconf
    browser: ServiceBrowser

    def __init__(self, hostname: str, key: str = "", use_ha: bool = False) -> None:
        self.hostname = hostname
        self.key = key
        if not use_ha:
            self.zeroconf = Zeroconf()
            self.browser = ServiceBrowser(
                self.zeroconf, "_http._tcp.local.", MotionBlindsRS485Listener(self)
            )

    def set_key(self, key: str) -> None:
        self.key = key

    def set_ip_address(self, ip_address: str) -> None:
        self.ip_address = ip_address

    async def request(self, url: str, timeout: int = 3):
        timeout = ClientTimeout(total=timeout)  # Set the timeout
        async with ClientSession() as session:  # Create a session
            async with session.get(url) as response:  # Perform a GET request
                return await response.json()

    async def ping(self) -> bool:
        if self.ip_address == None:
            raise Exception(f"No IP address for {self.hostname}")
        try:
            await self.request(f"http://{self.ip_address}", timeout=3)
            return True
        except ConnectionError:
            return False

    async def _scene_control(self, command: str, scene: int) -> None:
        if self.ip_address == None:
            raise Exception(f"No IP address for {self.hostname}")
        if scene < 1 or scene > 15:
            raise ValueError("Scene must be between 0 and 15")
        url = f"http://{self.ip_address}/{command}?scene={scene}"
        if self.key != "":
            url += f"&key={self.key}"
        print(url)

        json = await self.request(
            url,
            timeout=3,
        )
        if "status" in json and json["status"] == "error":
            if "message" in json and json["message"] == "invalid key":
                raise InvalidKeyException("Invalid key")

    async def start(self, scene: int) -> None:
        return await self._scene_control("start", scene)

    async def stop(self, scene: int) -> None:
        return await self._scene_control("stop", scene)


class InvalidKeyException(Exception):
    """Used to indicate the key was invalid."""


if __name__ == "__main__":

    async def main():
        rs485 = MotionBlindsRS485Device("motionblinds-rs485-D4D4DA8512FC.local.", False)

        await asyncio.sleep(2)

        print(await rs485.start(7))

        await asyncio.sleep(100)

    asyncio.run(main())
