#!/usr/bin/env python3

import socket
import sys
import argparse

import sched, time
import threading

from packet import *
from timer import *

parser = argparse.ArgumentParser(description="Sender script for Go Back N protocol")

# Arguments required 
parser.add_argument("-d", "--debug", action="store_true",
                    help="Turn on DEBUG mode")
parser.add_argument("-s", "--receiver_ip", required=True, type=str, 
                    help="Receiver's IP address")
parser.add_argument("-p", "--port", required=True, type=int, 
                    help="Receiver's port number")
parser.add_argument("-L", "--length", required=True, type=int, 
                    help="Packet length in bytes")
parser.add_argument("-R", "--rate", required=True, type=int, 
                    help="Rate of packets generation, per second")
parser.add_argument("-N", "--max_packets", required=True, type=int, 
                    help="Max packets to be sent")
parser.add_argument("-W", "--window", required=True, type=int, 
                    help="Window size")
parser.add_argument("-B", "--buffer_size", required=True, type=int,
                    help="Packet buffer size")
parser.add_argument("-n", "--seq_length", required=True, type=int,
                    help="Sequence number field length in bits")

parser.add_argument("-ddd", "--debug_max", action="store_true",
                    help="Turn on all DEBUG statments")

args = parser.parse_args()

receiver_port = args.port
receiver_ip = args.receiver_ip
addr = (receiver_ip, receiver_port)

DEBUG = args.debug
DEBUG_MAX = args.debug_max

if DEBUG_MAX:
    DEBUG = True

PACKET_LENGTH = args.length             # bytes

PACKET_GEN_RATE = args.rate             # Packets gen. per second
MAX_BUFFER_SIZE = args.buffer_size      # Max packets in buffer

WINDOW_SIZE = args.window               # Window size for broadcasting
MAX_PACKETS = args.max_packets+1        # No. of packets to be Ack

seq_field_length = args.seq_length
WINDOW_SIZE = min(WINDOW_SIZE, 2**(seq_field_length-1))

TIMEOUT_INTERVAL = 300  # 300ms


# Packet related variables
pckt = Packet(PACKET_LENGTH)

# List of packets to be sent
packets_buffer = [pckt.create(0)]
# packets_buffer.append(pckt.create(0))
packets_in_buffer = 0

sequence_no = 1


# Lock for accessing packets_buffer and related variables
lock = threading.Lock()
# Lock for receiving thread to update base
lock2 = threading.Lock()

# Timers for packets being sent
timers = [Timer()]
# No. of attempts for each packet
attempts = [0]

# Unack'ed packets
ack_left = []

min_unack_pckt = sys.maxsize

rtt_avg = 0
total_packets_sent = 0
total_acks = 0

next_seq_num  = 1

flag = 0

# Shared across sending and receiving threads
base = 1
send_timer = Timer()
send_timer.set_duration(TIMEOUT_INTERVAL)


######################################
#
#       Packet generating code
#
def gen_packet():
    '''
    Generates packet and stores in Buffer
    '''
    global packets_in_buffer
    global packets_buffer
    global sequence_no
    global lock
    global timers
    global attempts

    lock.acquire()
    if packets_in_buffer < MAX_BUFFER_SIZE:
        packets_buffer.append(pckt.create(sequence_no))

        # Add packet timer
        timers.append(Timer())
        attempts.append(0)

        if DEBUG_MAX:
            print("Added Packet with seq_no %d in buffer" % (sequence_no))
        sequence_no += 1
        packets_in_buffer += 1
        
    
    lock.release()


def packet_generating_func(pckt_gen_rate):
    '''
    Scheduled calls to gen_packet() `pckt_gen_rate` times per second
    '''
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
# thread1 = threading.Thread(target=packet_generating_func, args=(PACKET_GEN_RATE,), daemon=True)
# thread1.start()

def gen_packets_temp():
    '''
    Temporary function which generates MAX_PACKETS no. of packets and stores it
    '''
    global packets_buffer
    global timers
    global attempts

    for i in range(MAX_PACKETS):
        packets_buffer.append(pckt.create(i))
        timers.append(Timer())
        attempts.append(0)
    


#
#       Packet generating code ends
#
####################################


# Main sender code
def send(sock):
    global packets_buffer
    global packets_in_buffer
    global send_timer
    global lock2
    global lock
    global base

    global attempts
    global timers
    global total_packets_sent
    global ack_left
    global min_unack_pckt

    global next_seq_num

    total_packets_sent = 0

    # Start Packet Generating thread
    thread1 = threading.Thread(target=packet_generating_func, args=(PACKET_GEN_RATE,), daemon=True)
    thread1.start()

    # Start receiving thread
    thread2 = threading.Thread(target=receive, args=(sock,), daemon=True)
    thread2.start()

    next_seq_num = 1

    # Create MAX_PACKETS
    # gen_packets_temp()

    window_size = WINDOW_SIZE

    # TODO: Figure out race condition with `base`
    # Idea: Add lock2.acquire() below this, replace acquire with release and vice-versa everywhere else
    while base < MAX_PACKETS:
        lock2.acquire()

        # Send all packets in window
        while next_seq_num < (base + window_size - len(ack_left)):
            lock2.release()
            # print("Sending %d, Window size: %d" %(next_seq_num, window_size))

            # Acquire lock for reading packets from buffer
            lock.acquire()
            if packets_in_buffer != 0:
                # Buffer is not empty, decrease count and release
                packets_in_buffer-=1
                lock.release()

            else:
                # Buffer is empty, release and retry
                lock.release()
                # sleep for some time, so that packet is added to buffer
                time.sleep(1.0/PACKET_GEN_RATE)
                lock2.acquire()
                continue

            # If no. of unACK'ed packets is more than sender, then don't send 
            if len(ack_left) >= window_size:
                break
            if flag == 1:
                return

            lock2.acquire()
            if DEBUG_MAX:
                print("Sending %d" %(next_seq_num))
            sock.sendto(packets_buffer[next_seq_num], addr)

            min_unack_pckt = min(min_unack_pckt, next_seq_num)
            
            ack_left.append(next_seq_num)
            # Start timer for each packet, used to calculate RTT
            timers[next_seq_num].start()
            if next_seq_num > 10:
                timers[next_seq_num].set_duration(2*rtt_avg)
            else:
                timers[next_seq_num].set_duration(300)

            lock2.release()

            # Keep count of transmission attempts for each sequence no.
            attempts[next_seq_num]+=1

            # If no. of retries for a packet exceeds 10, terminate
            if attempts[next_seq_num] >= 11:
                if DEBUG_MAX:
                    print("No, of retries for %d exceeded 10, exiting!" %(next_seq_num))
                # sys.exit()
                return

            next_seq_num+=1
            total_packets_sent+=1

            lock2.acquire()

        lock2.release()

        lock2.acquire()

        for pckt_left in ack_left:
            if not pckt_left in ack_left:
                if DEBUG_MAX:
                    print("%d not in ack_left!" %(pckt_left))
                continue

            if timers[pckt_left].timeout():

                timers[pckt_left].start()
                if pckt_left > 10:
                    timers[pckt_left].set_duration(2*rtt_avg)
                else:
                    timers[pckt_left].set_duration(300)

                lock2.release()

                # Transmit the packets with timeout
                if DEBUG_MAX:
                    print("Packet %d timeout!" %(pckt_left))
                sock.sendto(packets_buffer[pckt_left], addr)

                # timers[pckt_left].start()
                # if pckt_left > 10:
                #     timers[pckt_left].set_duration(2*rtt_avg)
                # else:
                #     timers[pckt_left].set_duration(300)

                attempts[pckt_left]+=1
                if attempts[pckt_left] >= 11:
                    if DEBUG_MAX:
                        print("Attempts for %d exceeded 10, exiting" %(pckt_left) )
                    # sys.exit()
                    return

                total_packets_sent+=1

                # time.sleep(rtt_avg/2)

                lock2.acquire()

        lock2.release()




########## Receiving Thread ##################

def receive(sock):
    global send_timer
    global base
    global lock2
    global total_acks

    global timers
    global rtt_avg

    global ack_left
    global min_unack_pckt

    global next_seq_num

    global flag

    while True:
        msg, _ = sock.recvfrom(PACKET_LENGTH)
        ack = pckt.extract(msg)

        if DEBUG_MAX:
            print("Got ACK: %d, Time Received: %s" %(ack, str(datetime.now().timestamp()*1000.0)))
        total_acks+=1

        lock2.acquire()

        # We might get repeat ACKs for already sent packet
        if ack in ack_left:
            ack_left.remove(ack)

        if ack==min_unack_pckt:
            if len(ack_left) is not 0:
                min_unack_pckt = min(ack_left)
            else:
                min_unack_pckt = next_seq_num

        if timers[ack].check_if_running():
            timers[ack].stop()
            rtt_avg += (timers[ack].get_rtt() - rtt_avg)/total_acks
        lock2.release()
        
        if DEBUG:
            print("Seq " + str(ack) + ":\t Time Gen: " + str(timers[ack].start_time.timestamp()*1000.0)+ 
                  "\t RTT: " + str(rtt_avg) + "\t Attempts: " + str(attempts[ack]))

        if ack==base:
            lock2.acquire()
            # Advance base till the next non ack'ed packet
            while not timers[base].check_if_running():
                base+=1
                if DEBUG_MAX:
                    print("Updating base to %d, min_unack_pckt is %d" %(base, min_unack_pckt))
                if base == min_unack_pckt:
                    break
            lock2.release()

        if base > MAX_PACKETS:
            # Exit
            if DEBUG_MAX:
                print("MAX_PACKETS acknowledged!")
            flag = 1
            sys.exit()


####### Receiving thread ends #########

if __name__ == "__main__":    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except socket.error as err:
        print("Socket creation error %s" %(err))


    # print("Starting!")
    send(s)
    s.close()
    print("PktRate: %d, Length: %d, Retran ratio: %f, Avg RTT: %f" %(PACKET_GEN_RATE, PACKET_LENGTH, (total_packets_sent/total_acks), rtt_avg))
