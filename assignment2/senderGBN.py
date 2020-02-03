#!/usr/bin/env python3

import socket
import sys
import argparse

parser = argparse.ArgumentParser(description="Sender script for Go Back N protocol")

# TODO: Add arguments required 


port = 60000
ip = "127.0.0.1"
addr = (ip, port)

packet_length = 1024 # bytes

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error as err:
    print("Socket creation error %s" %(err))

sequence_no = 1
message = str(sequence_no).ljust(packet_length)

# message = "Hello World".encode()
s.sendto(bytes(message, "utf-8"), addr)
