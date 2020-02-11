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
parser.add_argument("-l", "--length", required=True, type=int, 
                    help="Packet length in bytes")
parser.add_argument("-r", "--rate", required=True, type=int, 
                    help="Rate of packets generation, per second")
parser.add_argument("-n", "--max_packets", required=True, type=int, 
                    help="Max packets to be sent")
parser.add_argument("-w", "--window", required=True, type=int, 
                    help="Window size")
parser.add_argument("-b", "--buffer_size", required=True, type=int,
                    help="Packet buffer size")

parser.add_argument("-ddd", "--debug_max", action="store_true",
                    help="Turn on all DEBUG statments")

args = parser.parse_args()

receiver_port = args.port
receiver_ip = args.receiver_ip
addr = (receiver_ip, receiver_port)

DEBUG = args.debug
DEBUG_MAX = args.debug_max
if DEBUG_MAX:
    DEBUG=True

PACKET_LENGTH = args.length    # bytes

PACKET_GEN_RATE = args.rate   # Packets gen. per second
MAX_BUFFER_SIZE = args.buffer_size    # Max packets in buffer

WINDOW_SIZE = args.window         # Window size for broadcasting
MAX_PACKETS = args.max_packets+1  # No. of packets to be Ack

TIMEOUT_INTERVAL = 100  # 100ms


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

rtt_avg = 0
total_packets_sent = 0
total_acks = 0


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

        # print("Added Packet with seq_no %d in buffer" % (sequence_no))
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

    global flag

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
    # lock2.acquire()
    while base < MAX_PACKETS:
        # lock2.release() 
        lock2.acquire()

        # Send all packets in window
        while next_seq_num < base + window_size:
            lock2.release()
            if DEBUG_MAX:
                print("Sending %d, Window size: %d, Base: %d" 
                        %(next_seq_num, window_size, base))

            # Acquire lock for reading packets from buffer
            lock.acquire()
            if packets_in_buffer != 0:
                # Buffer is not empty, decrease count and release
                packets_in_buffer-=1
                lock.release()
                
                if not send_timer.check_if_running():
                    # print("Starting timer")
                    send_timer.start()
                    if next_seq_num <= 10:
                        send_timer.set_duration(100)
                    else:
                        send_timer.set_duration(2*rtt_avg)

            else:
                # Buffer is empty, release and retry
                lock.release()
                # sleep for some time, so that pakcet is added to buffer
                time.sleep(1.0/PACKET_GEN_RATE)
                lock2.acquire()
                continue

            if flag is 1:
                return

            # print("Sending %d" %(next_seq_num))
            sock.sendto(packets_buffer[next_seq_num], addr)

            # Keep count of transmission attempts for each sequence no.
            attempts[next_seq_num]+=1
            if DEBUG_MAX:
                print("Seq no %d: Attempt %d" %(next_seq_num, attempts[next_seq_num]))
            # If no. of retries for a packet exceeds 5, terminate
            if attempts[next_seq_num] >= 6:
                if DEBUG_MAX:
                    print("No, of retries exceeded 5, exiting!")
                # sys.exit()
                return
            
            lock2.acquire()
            # Start timer for each packet, used to calculate RTT
            timers[next_seq_num].start()

            next_seq_num+=1
            total_packets_sent+=1            


        # if not send_timer.check_if_running():
        #     # print("Starting timer")
        #     send_timer.start()

        # lock2.release()
        # Wait until timeout or ACK is received
        while send_timer.check_if_running() and not send_timer.timeout():
            # pass
            lock2.release()
            if DEBUG_MAX:
                print("Sleeping")
            time.sleep(1.0/PACKET_GEN_RATE)
            lock2.acquire()

        # lock2.acquire()
        # If timeout, need to retransmit all packets from un-ack pakcet
        if send_timer.timeout():
            if DEBUG_MAX:
                print("Timeout: ", base)
            send_timer.stop()
            next_seq_num = base
        else:
            # Got ACK, update window size
            # So as to not run into seg fault when sending the last packets
            window_size = min(WINDOW_SIZE, MAX_PACKETS-base)
            if DEBUG_MAX:
                print("Updating window_size, base = %d, window_size = %d" %(base, window_size))

        lock2.release()
        # lock2.acquire()




########## Receiving Thread ##################

def receive(sock):
    global send_timer
    global base
    global lock2
    global total_acks

    global timers
    global rtt_avg

    global flag

    while True:
        msg, _ = sock.recvfrom(PACKET_LENGTH)
        ack = pckt.extract(msg)

        # print("Got ACK: ", ack)
        total_acks+=1
        if ack >= base:
            lock2.acquire()
            send_timer.stop()
            # Calculate RTT for each packet and update rtt_avg
            for i in range(base, ack+1):
                timers[i].stop()
                rtt_avg += (timers[i].get_rtt() - rtt_avg)/i

                if DEBUG:
                    print("Seq " + str(ack) + ":\t Time Gen: " + str(timers[i].start_time.timestamp()*1000.0)+ 
                          "\t RTT: " + str(rtt_avg) + "\t Attempts: " + str(attempts[i]))
            
            # Cumulative ACKs
            base = ack + 1
            # total_acks+=1
            if DEBUG_MAX:
                print("Base updated: ", base)

            if base > MAX_PACKETS:
                # Exit
                if DEBUG_MAX:
                    print("MAX_PACKETS acknowledged!")
                flag = 1 
                lock2.release()
                
                sys.exit()

            
            lock2.release()

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

