#!/usr/bin/env python3

import socket
import sys
import argparse
import random

from datetime import datetime
from datetime import timedelta

from packet import *
from timer import *

parser = argparse.ArgumentParser(description="Receiver script for Go Back N protocol")

# TODO: Add arguments required 
parser.add_argument("-d", "--debug", action="store_true",
                    help="Turn on DEBUG mode")
parser.add_argument("-p", "--port", required=True, type=int, 
                    help="Receiver's port number")
parser.add_argument("-n", "--max_packets", required=True, type=int, 
                    help="Max packets to be received")
parser.add_argument("-e", "--drop_prob", required=True, type=float,
                    help="Probability of packet being corrupted")
parser.add_argument("-l", "--length", required=True, type=int, 
                    help="Packet length in bytes")

parser.add_argument("-ddd", "--debug_max", action="store_true",
                    help="Turn on all DEBUG statments")

args = parser.parse_args()

receiver_port = args.port 
packet_length = args.length # bytes

random_drop_prob = args.drop_prob # Probabilty of packet being corrupted

MAX_PACKETS = args.max_packets
DEBUG = args.debug
DEBUG_MAX = args.debug_max
if DEBUG_MAX:
    DEBUG = True

try:
    recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error as err:
    print("Socket creation error %s" %(err))


recv_socket.bind(('0.0.0.0', receiver_port))
# print("Socket bound to port %d" %(receiver_port))

pckt = Packet(packet_length)

expected_num = 1 # Sequence no. of expected packet

start_time = datetime.now()


while True:
    message, address = recv_socket.recvfrom(packet_length)

    seq_num = pckt.extract(message)
    if DEBUG_MAX:
        print("Received pckt: ", seq_num)
    
    if(random.random() <= random_drop_prob):
        # Packet is corrupted
        if DEBUG_MAX:
            print("Dropping packet ", pckt.extract(message))
        continue

    if DEBUG:
        dt_now = datetime.now()
        print("Seq %d: Time Received: %s  Packet Dropped: false" % (seq_num, str(dt_now.timestamp()*1000.0)))

    if (seq_num == expected_num):
        if DEBUG_MAX:
            print("Got expected packet, sending ACK ", expected_num)
        pkt = pckt.create(expected_num)
        recv_socket.sendto(pkt, address)
        expected_num += 1
        if expected_num > MAX_PACKETS:
            break
    else:
        if DEBUG_MAX:
            print("Unexpected packet, sending ACK ", expected_num-1)
        pkt = pckt.create(expected_num-1)
        recv_socket.sendto(pkt, address)
