#!/usr/bin/env python3

import socket
import sys
import argparse

import sched, time
import threading

from packet import *

parser = argparse.ArgumentParser(description="Sender script for Go Back N protocol")

# TODO: Add arguments required 


receiver_port = 60000
receiver_ip = "127.0.0.1"
addr = (receiver_ip, receiver_port)

packet_length = 1024    # bytes

packet_gen_rate = 10     # Packets gen. per second
max_buffer_size = 10    # Max packets in buffer

window_size = 5         # Window size for broadcasting
max_packets = 100       # No. of packets to be Ack


# List of packets to be sent
packets_buffer = []
packets_in_buffer = 0

sequence_no = 0


pckt = Packet(packet_length)

# Lock for accessing packets_buffer and related variables
lock = threading.Lock()


def gen_packet():
    '''
    Generates packet and stores in Buffer
    '''
    global packets_in_buffer
    global packets_buffer
    global sequence_no

    lock.acquire()
    if packets_in_buffer < max_buffer_size:
        packets_buffer.append(pckt.create(sequence_no))
        sequence_no += 1
        packets_in_buffer += 1
        print("Added Packet with seq_no %d in buffer", sequence_no)
    
    lock.release()


def main_thread_func(pckt_gen_rate):
    ## Timed calls to gen_packet()
    scheduler = sched.scheduler(time.time, time.sleep)

    def new_timed_call(calls_per_second, callback, *args, **kw):
        period = 1.0 / calls_per_second
        def reload():
            callback(*args, **kw)
            scheduler.enter(period, 0, reload, ())
        scheduler.enter(period, 0, reload, ())

    new_timed_call(pckt_gen_rate, gen_packet)

    scheduler.run()

## Packet generating thread
thread1 = threading.Thread(target=main_thread_func, args=(packet_gen_rate,), daemon=True)
thread1.start()

# Main sender code
def send(sock):
    global packets_buffer
    global packets_in_buffer

    total_packets_sent = 0

    while total_packets_sent <= max_packets:
        lock.acquire()
        if packets_in_buffer == 0:
            print("Buffer empty, releasing lock")
            lock.release()
            # sleep for some time
            time.sleep(1.0/packet_gen_rate)
        else:
            message = packets_buffer.pop(0)
            packets_in_buffer-=1
            sock.sendto(message, addr)
            total_packets_sent+=1
            
            lock.release()




# print("Hello, still running!")

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error as err:
    print("Socket creation error %s" %(err))


print("Starting!")
send(s)

# message = pckt.create(sequence_no)

# message = "Hello World".encode()
# s.sendto(message, addr)
