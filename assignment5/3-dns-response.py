from scapy.all import DNS, DNSRR, DNSQR, IP, UDP, send, sniff

dns_hosts = {
    b"www.google.com.": "172.217.160.228",
    b"www.cse.iitm.ac.in.": "14.139.160.81"
}
LOCAL_IP="192.168.43.31"

def send_reply(pkt):
    qname = pkt[DNSQR].qname
    spf_resp = IP(dst=pkt[IP].src)/UDP(dport=pkt[UDP].sport, sport=53)/\
        DNS(id=pkt[DNS].id, qd=pkt[DNS].qd, aa=1, qr=1, ancount=1, an=DNSRR(rrname=qname, rdata=dns_hosts[qname]))

    send(spf_resp)


# sniff(iface="enp0s8", filter=f"udp port 53 and ip dst {LOCAL_IP}", prn=send_reply)
sniff(filter=f"udp port 53 and ip dst {LOCAL_IP}", prn=send_reply)
