from zeroconf import ServiceBrowser, Zeroconf
import time
from scapy.all import ARP, Ether, srp


# sudo /Users/lennperik/.pyenv/versions/3.10.0/bin/python /Users/lennperik/Downloads/wetransfer_currenttorque-zip_2023-11-16_2031/ESP32/discover.py


class MyListener:
    def remove_service(self, zeroconf, type, name):
        print(f"Service {name} removed")

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            print(info)
            print(f"Service {name} added, IP: {info.parsed_addresses()[0]}")
            self.get_mac_address(info.parsed_addresses()[0])

    def get_mac_address(self, ip):
        arp_request = ARP(pdst=ip)
        broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
        arp_request_broadcast = broadcast / arp_request
        answered_list = srp(arp_request_broadcast, timeout=1, verbose=False)[0]

        if answered_list:
            for sent, received in answered_list:
                print(f"IP: {received.psrc}, MAC: {received.hwsrc}")
        else:
            print(f"No MAC address found for IP {ip}")


zeroconf = Zeroconf()
listener = MyListener()
browser = ServiceBrowser(zeroconf, "_http._tcp.local.", listener)

try:
    time.sleep(1000)
finally:
    zeroconf.close()
