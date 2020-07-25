from scapy.all import IP, TCP, sr1, send, sniff
import time
import os

# When running on Host
SERVER_IP = "192.168.43.175"
SERVER_PORT = 5042
PORT = 12345
IFACE = "wlp0s20f3"

# Running on VM
# SERVER_IP = "192.168.43.31"
# SERVER_PORT = 5042
# PORT = 12345
# IFACE = "enp0s8"


class TCPClient:
    def __init__(self, server_ip, server_port, port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.port = port

        # Base IP packet
        self.ip = IP(dst=server_ip)

        self.seq_no = 100
        self.ack_no = -1


    def start(self):
        """
        Do 3-Way handshake between client-server
        """
        # Create SYN packet
        syn = TCP(sport=self.port, dport=self.server_port, flags="S", seq=self.seq_no)
        synack = sr1(self.ip/syn)

        self.ack_no = synack.seq+1
        self.seq_no = synack.ack
        # Send ACK for SYNACK
        ack = TCP(sport=self.port, dport=self.server_port, flags="A", seq=self.seq_no, ack=self.ack_no)
        send(self.ip/ack)


    def send_data(self, length):
        """
        Send TCP packets with payload of random `length` bytes
        """
        payload = os.urandom(length)
        pyl_pkt = TCP(sport=self.port, dport=self.server_port, flags="PA", seq=self.seq_no, ack=self.ack_no)/payload

        self.seq_no += length

        reply = sr1(self.ip/pyl_pkt)

        print(reply.show())
        print(f"ACK payload length: {len(reply[TCP].payload)}")


    def send_fin(self):
        """
        Send FIN packet, wait for ACK from server,
        Then receive FIN from server and send ACK
        """
        fin_pkt = TCP(sport=self.port, dport=self.server_port, flags="FA", seq=self.seq_no, ack=self.ack_no)
        fin_ack = sr1(self.ip/fin_pkt)

        def send_ack(pkt):
            """
            Send ACK packet
            """
            self.seq_no = pkt.ack
            self.ack_no = pkt.seq+1
            ack = TCP(sport=self.port, dport=self.server_port, flags="A", seq=self.seq_no, ack=self.ack_no)
            send(self.ip/ack)

        # Listen for FIN by server and send ack
        filter = f"tcp and tcp port {self.port}"
        sniff(iface=IFACE, filter=filter, prn=send_ack, count=1)



if __name__ == "__main__":
    tcp_client = TCPClient(SERVER_IP, SERVER_PORT, PORT)

    # TCP Handshake
    tcp_client.start()

    # Send 1000 bytes 2 times with some time between them
    for i in range(2):
        tcp_client.send_data(1000)
        time.sleep(1)

    # Close connection
    tcp_client.send_fin()
