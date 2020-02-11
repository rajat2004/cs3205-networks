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

# Arguments required 
parser.add_argument("-d", "--debug", action="store_true",
                    help="Turn on DEBUG mode")
parser.add_argument("-p", "--port", required=True, type=int, 
                    help="Receiver's port number")
parser.add_argument("-N", "--max_packets", required=True, type=int, 
                    help="Max packets to be received")
parser.add_argument("-e", "--drop_prob", required=True, type=float,
                    help="Probability of packet being corrupted")
parser.add_argument("-l", "--length", required=True, type=int, 
                    help="Packet length in bytes")
parser.add_argument("-W", "--window", required=True, type=int, 
                    help="Window size")
parser.add_argument("-n", "--seq_length", required=True, type=int,
                    help="Sequence number field length in bits")
parser.add_argument("-B", "--buffer_size", required=True, type=int,
                    help="Packet buffer size")

parser.add_argument("-ddd", "--debug_max", action="store_true",
                    help="Turn on all DEBUG statments")

args = parser.parse_args()

receiver_port = args.port 
packet_length = args.length # bytes

random_drop_prob = args.drop_prob # Probabilty of packet being corrupted

MAX_PACKETS = args.max_packets
DEBUG = args.debug
DEBUG_MAX = args.debug_max

WINDOW_SIZE = args.window         # Window size for receiving

seq_field_length = args.seq_length
WINDOW_SIZE = min(WINDOW_SIZE, 2**(seq_field_length-1))

MAX_BUFFER_SIZE = args.buffer_size    # Max packets in buffer


try:
    recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error as err:
    print("Socket creation error %s" %(err))


recv_socket.bind(('0.0.0.0', receiver_port))
# print("Socket bound to port %d" %(receiver_port))

pckt = Packet(packet_length)

expected_num = 1 # Sequence no. of expected packet

recv_time = {}

start_time = datetime.now()

curr_buffer_size = 0
total_acks = 0
recv_base = 1

while True:
    message, address = recv_socket.recvfrom(packet_length)
    total_acks+=1
    seq_num = pckt.extract(message)

    if DEBUG_MAX:
        print("Received pckt: ", seq_num)

    if(random.random() <= random_drop_prob):
        # Packet is corrupted
        if DEBUG_MAX:
            print("Dropping packet ", seq_num)
        continue
    
    # Check this logic!
    if curr_buffer_size > MAX_BUFFER_SIZE:
        # Buffer is full
        if DEBUG_MAX:
            print("Buffer full, dropping ", seq_num)
        continue

    curr_time = datetime.now()

    if seq_num>=recv_base and seq_num<(recv_base+WINDOW_SIZE):
        # Falls within window, send selective ACK
        pkt = pckt.create(seq_num)
        recv_socket.sendto(pkt, address)

        if not seq_num in recv_time.keys():
            # Packet being received for the first time
            recv_time[seq_num] = curr_time
            # Packet stored in buffer
            curr_buffer_size+=1

        if seq_num == recv_base:
            # Advance base
            while recv_base in recv_time.keys():
                if DEBUG:
                    print("Seq %d: Time Received: %s" %(recv_base, recv_time[recv_base].timestamp()*1000.0) )
                recv_base+=1
                # Buffer being emptied
                curr_buffer_size-=1


    elif seq_num<recv_base and seq_num>=(recv_base-WINDOW_SIZE):
        # Already ACK'ed, but generate packet
        pkt = pckt.create(seq_num)
        recv_socket.sendto(pkt, address)
    else:
        # Do nothing
        pass

    if(total_acks > MAX_PACKETS):
        break

