from zeroconf import Zeroconf, ServiceBrowser, ServiceListener
import time


class MotionBlindsRS485Listener(ServiceListener):
    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        # print(f"Service {name} updated")
        pass

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        # print(f"Service {name} removed")
        pass

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        print(f"Service {name} added, service info: {info}")
        print(info._ipv4_addresses[0])

    # def add_service(self, zeroconf, type, name):
    #     info = zeroconf.get_service_info(type, name)
    #     if info:
    #         print(f"Service {name} added, IP: {info.parsed_addresses()[0]}")
    #         self.get_mac_address(info.parsed_addresses()[0])

    # def update_service():
    #     pass


zeroconf = Zeroconf()
browser = ServiceBrowser(zeroconf, "_http._tcp.local.", MotionBlindsRS485Listener())

try:
    time.sleep(1)
finally:
    zeroconf.close()
