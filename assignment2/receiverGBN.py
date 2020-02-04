#!/usr/bin/env python3

import socket
import sys
import argparse

from packet import *

parser = argparse.ArgumentParser(description="Receiver script for Go Back N protocol")

# TODO: Add arguments required 


receiver_port = 60000
packet_length = 1024 # bytes

try:
    recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error as err:
    print("Socket creation error %s" %(err))


recv_socket.bind(('', receiver_port))
print("Socket bound to port %d" %(receiver_port))

packet = Packet(packet_length)

message, address = recv_socket.recvfrom(packet_length)
print(packet.extract(message))
