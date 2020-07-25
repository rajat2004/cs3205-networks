from scapy.all import IP, TCP, sr1, send, sniff, Raw
import sys
import logging
import time

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

# Running on Host
# iface="wlp0s20f3"

# Running on VM
iface="enp0s8"

PORT = 5042
filter = f"tcp and tcp port {PORT}"

class TCPServer:
    def __init__(self):
        self.seq_no = 10000
        self.ack_no = -1

    def send_synack(self, pkt):
        """
        Send SYNACK
        """
        # print(pkt.show())
        self.ack_no = pkt[TCP].seq+1

        synack = IP(dst=pkt[IP].src)/\
                 TCP(sport=pkt[TCP].dport, dport=pkt[TCP].sport, flags="SA", seq=self.seq_no, ack=self.ack_no)
        send(synack)

        self.seq_no += 1


    def send_ack(self, pkt):
        """
        Send ACK for payloads
        """
        print(pkt.show())
        print(f"Payload size: {len(pkt[TCP].payload)}")

        payload_size = len(pkt[TCP].payload)
        self.ack_no += payload_size

        ack = IP(dst=pkt[IP].src)/\
              TCP(sport=pkt[TCP].dport, dport=pkt[TCP].sport, flags="A", seq=self.seq_no, ack=self.ack_no)
        send(ack)


    def send_finack(self, pkt):
        """
        Send ACK for FIN packet, and send FIN packet
        """
        self.ack_no = pkt[TCP].seq + 1
        ack = IP(dst=pkt[IP].src)/\
              TCP(sport=pkt[TCP].dport, dport=pkt[TCP].sport, flags="A", seq=self.seq_no, ack=self.ack_no)
        send(ack)

        time.sleep(1)

        fin = IP(dst=pkt[IP].src)/\
              TCP(sport=pkt[TCP].dport, dport=pkt[TCP].sport, flags="FA", seq=self.seq_no, ack=self.ack_no)
        send(fin)



    def handle_data(self, pkt):
        if pkt and pkt.haslayer(IP) and pkt.haslayer(TCP):
            if pkt[TCP].flags & 0x3f == 0x02:       # SYN
                logger.debug("RCV: SYN, sending SYNACK")
                self.send_synack(pkt)

            elif pkt[TCP].flags & 0x3f == 0x18:     # PA
                logger.debug("RCV: PA, sending ACK")
                self.send_ack(pkt)

            elif pkt[TCP].flags & 0x3f == 0x11:     # FIN,ACK
                logger.debug("RCV: FIN")
                return self.send_finack(pkt)

            else:
                logger.warning("Unknown Packet")
                print(pkt.show())


if __name__ == "__main__":
    tcp_server = TCPServer()

    # Receive packets
    sniff(iface=iface, filter=filter, prn=tcp_server.handle_data)
