# Scapy

This assignment deals with [Scapy](https://scapy.net/) - [Download & instalation](https://scapy.readthedocs.io/en/latest/installation.html)

VirtualBox with Ubuntu 18.04 VM and Wireshark are also used

Determine IP address of host system & VM. Bridged Adapter with WiFi is used in Virtualbox so that both machines are able to ping each other.

1. ICMP Ping

```shell
>>> packet=IP(dst="192.168.43.175")/ICMP()
>>> srloop(packet, count=5)
RECV 1: IP / ICMP 192.168.43.175 > 192.168.43.31 echo-reply 0 / Padding
RECV 1: IP / ICMP 192.168.43.175 > 192.168.43.31 echo-reply 0 / Padding
RECV 1: IP / ICMP 192.168.43.175 > 192.168.43.31 echo-reply 0 / Padding
RECV 1: IP / ICMP 192.168.43.175 > 192.168.43.31 echo-reply 0 / Padding
RECV 1: IP / ICMP 192.168.43.175 > 192.168.43.31 echo-reply 0 / Padding

Sent 5 packets, received 5 packets. 100.0% hits.
(<Results: TCP:0 UDP:0 ICMP:5 Other:0>,
 <PacketList: TCP:0 UDP:0 ICMP:0 Other:0>)
```

2. ICMP Ping with custom reply

```python
>>> def custom_action(packet):
        # Get IP from where the packet came, that will be our destination
        dest = packet[0][1].src
        reply_packet = IP(dst=dest)/ICMP(type="echo-reply")/"CS17B042"
        send(reply_packet)
>>> sniff(filter="icmp and host 192.168.43.31", prn=custom_action)
.
Sent 1 packets.
...
```

From VM, run the `srloop` command from the 1st part. There should be 2 replies for each request in Wireshark, with one reply having payload in hexadecimal

When running in VM, I had to specify the interface, otherwise `sniff` wouldn't work for some reason.

```python
>>> sniff(iface="enp0s8", filter="icmp and host 192.168.43.175", prn=custom_action)
```

3. DNS Query & Response

Useful resources:
https://thepacketgeek.com/scapy/building-network-tools/part-09/
http://lost-and-found-narihiro.blogspot.com/2016/02/craft-dns-responses-with-python-scapy.html

Query -

```python
>>> dns_req = IP(dst='192.168.43.175')/UDP(dport=53)/DNS(rd=1, qd=DNSQR(qname='www.google.com'))
>>> p = send(dns_req)
Begin emission:
Finished sending 1 packets.
*
Received 1 packets, got 1 answers, remaining 0 packets
```

Python Code for response - [3-dns-response.py](3-dns-response.py)

4. TCP File transfer

First to avoid RST packet from kernel (on both client & server, change IPs)

```shell
$ sudo iptables -A OUTPUT -p tcp --tcp-flags RST RST -s 192.168.43.31 -j DROP
```

Resources -
Various Google searches for TCP handshake in Scapy
https://packetlife.net/blog/2010/jun/7/understanding-tcp-sequence-acknowledgment-numbers/

Files - [4-tcp-client.py](4-tcp-client.py) & [4-tcp-server.py](4-tcp-server.py)

First open `client.py` & `server.py` and set the values such as `PORT`, `IFACE`.
Currently values are set to Host being client, VM being server

Start server first, start Wireshark on client with filter like `tcp and tcp port 12345`, then run client

Accordingly change values & filter when running in the opposite direction.
