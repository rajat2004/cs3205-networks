#!/usr/bin/env python3

import socket
import sys
import argparse

from packet import *

parser = argparse.ArgumentParser(description="Sender script for Go Back N protocol")

# TODO: Add arguments required 


receiver_port = 60000
receiver_ip = "127.0.0.1"
addr = (receiver_ip, receiver_port)

packet_length = 1024 # bytes

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error as err:
    print("Socket creation error %s" %(err))

sequence_no = 100
packet = Packet(packet_length)
message = packet.create(sequence_no)

# message = "Hello World".encode()
s.sendto(message, addr)
