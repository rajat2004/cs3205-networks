#!/usr/bin/env python3

import socket
import sys
import argparse

parser = argparse.ArgumentParser(description="Receiver script for Go Back N protocol")

# TODO: Add arguments required 


port = 60000
packet_length = 1024 # bytes

try:
    recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error as err:
    print("Socket creation error %s" %(err))

host = socket.gethostname()
print("Host- " + host)

recv_socket.bind(('', port))
print("Socket bound to port %d" %(port))

message, address = recv_socket.recvfrom(packet_length)
print(message.decode())
