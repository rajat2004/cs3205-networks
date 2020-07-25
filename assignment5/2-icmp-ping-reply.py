from scapy.all import sniff, send
from scapy.layers.inet import IP, UDP, TCP, ICMP

def custom_action(packet):
    # Get IP from where the packet came, that will be our destination
    dest = packet[0][1].src
    reply_packet = IP(dst=dest)/ICMP(type="echo-reply")/"CS17B042"
    send(reply_packet)

sniff(filter="icmp and host 192.168.43.31", prn=custom_action)
