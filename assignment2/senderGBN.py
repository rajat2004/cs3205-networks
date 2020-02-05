#!/usr/bin/env python3

import socket
import sys
import argparse

import sched, time

from packet import *

parser = argparse.ArgumentParser(description="Sender script for Go Back N protocol")

# TODO: Add arguments required 


receiver_port = 60000
receiver_ip = "127.0.0.1"
addr = (receiver_ip, receiver_port)

packet_length = 1024 # bytes

packet_gen_rate = 1 # Packets gen. per second
max_buffer_size = 10 # Max packets in buffer


# List of packets to be sent
packets_buffer = []
packets_in_buffer = 0

sequence_no = 0


pckt = Packet(packet_length)


def gen_packet():
    '''
    Generates packet and stores in Buffer
    '''
    global packets_in_buffer
    global packets_buffer
    global sequence_no

    if packets_in_buffer < max_buffer_size:
        packets_buffer.append(pckt.create(sequence_no))
        sequence_no += 1
        packets_in_buffer += 1


## Timed calls to gen_packet()
scheduler = sched.scheduler(time.time, time.sleep)

def new_timed_call(calls_per_second, callback, *args, **kw):
    period = 1.0 / calls_per_second
    def reload():
        callback(*args, **kw)
        scheduler.enter(period, 0, reload, ())
    scheduler.enter(period, 0, reload, ())

new_timed_call(packet_gen_rate, gen_packet)


scheduler.run()




try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error as err:
    print("Socket creation error %s" %(err))

# message = pckt.create(sequence_no)

# message = "Hello World".encode()
# s.sendto(message, addr)
