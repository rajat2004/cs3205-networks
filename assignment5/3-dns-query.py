from scapy.all import DNS, DNSQR, IP, sr1, UDP

# Useful - https://thepacketgeek.com/scapy/building-network-tools/part-09/
dns_req = IP(dst='192.168.43.175')/UDP(dport=53)/DNS(rd=1, qd=DNSQR(qname='www.google.com'))
# dns_req = IP(dst='8.8.8.8')/UDP(dport=53)/DNS(rd=1, qd=DNSQR(qname='www.cse.iitm.ac.in'))


answer = sr1(dns_req, verbose=0)
print(answer[DNS].ancount)
for x in range(answer[DNS].ancount):
    print(answer[DNS][x][DNSQR])

print(answer[DNS].summary())
