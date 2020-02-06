#!/usr/bin/env python3

import socket
import sys
import argparse
import random

from datetime import datetime
from datetime import timedelta

from packet import *

parser = argparse.ArgumentParser(description="Receiver script for Go Back N protocol")

# TODO: Add arguments required 


receiver_port = 60000
packet_length = 1024 # bytes

random_drop_prob = 0 # Probabilty of packet being corrupted

debug = True

try:
    recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error as err:
    print("Socket creation error %s" %(err))


recv_socket.bind(('', receiver_port))
print("Socket bound to port %d" %(receiver_port))

pckt = Packet(packet_length)

expected_num = 0 # Sequence no. of expected packet

start_time = datetime.now()


def millis(dt_now):
    dt = dt_now - start_time
    ms = (dt.days * 24 * 60 * 60 + dt.seconds) * 1000 + dt.microseconds / 1000.0
    return ms


while True:
    message, address = recv_socket.recvfrom(packet_length)
    
    if(random.random() <= random_drop_prob):
        # Packet is corrupted
        print("Dropping packet ", pckt.extract(message))
        continue
    
    seq_num = pckt.extract(message)
    print("Received pckt: ", seq_num)

    if debug:
        dt_now = datetime.now()
        print("Seq %d: Time Received: %d:%d   Packet Dropped: false" % (seq_num, millis(dt_now), dt_now.microsecond%1000))

    if (seq_num == expected_num):
        print("Got expected packet, sending ACK ", expected_num)
        pkt = pckt.create(expected_num)
        recv_socket.sendto(pkt, address)
        expected_num += 1
    else:
        print("Unexpected packet, sending ACK ", expected_num-1)
        pkt = pckt.create(expected_num-1)
        recv_socket.sendto(pkt, address)



# message, address = recv_socket.recvfrom(packet_length)
# print(pckt.extract(message))
