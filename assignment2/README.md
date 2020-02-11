## Go Back N & Selective Repeat Protocols

Implementation of the above protocols in Python3

### Usage

There are 2 main files for each protocol, `senderGBN.py` & `receiverGBN.py` for GBN, and `senderSR.py` & `receiverSR.py` for Selective Repeat respectively

Command-Line arguments for each file are described below. Each file takes `-d` argument which turns on debug statements. There's also another argument `-ddd` which enables *all* debug statments

No Makefile, etc. is needed. All 4 files are directly executable

#### Go Back N

```
$ ./senderGBN.py --help
usage: senderGBN.py [-h] [-d] -s RECEIVER_IP -p PORT -l LENGTH -r RATE -n
                    MAX_PACKETS -w WINDOW -b BUFFER_SIZE [-ddd]

Sender script for Go Back N protocol

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           Turn on DEBUG mode
  -s RECEIVER_IP, --receiver_ip RECEIVER_IP
                        Receiver's IP address
  -p PORT, --port PORT  Receiver's port number
  -l LENGTH, --length LENGTH
                        Packet length in bytes
  -r RATE, --rate RATE  Rate of packets generation, per second
  -n MAX_PACKETS, --max_packets MAX_PACKETS
                        Max packets to be sent
  -w WINDOW, --window WINDOW
                        Window size
  -b BUFFER_SIZE, --buffer_size BUFFER_SIZE
                        Packet buffer size
  -ddd, --debug_max     Turn on all DEBUG statments

```

```
$ ./receiverGBN.py --help
usage: receiverGBN.py [-h] [-d] -p PORT -n MAX_PACKETS -e DROP_PROB -l LENGTH
                      [-ddd]

Receiver script for Go Back N protocol

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           Turn on DEBUG mode
  -p PORT, --port PORT  Receiver's port number
  -n MAX_PACKETS, --max_packets MAX_PACKETS
                        Max packets to be received
  -e DROP_PROB, --drop_prob DROP_PROB
                        Probability of packet being corrupted
  -l LENGTH, --length LENGTH
                        Packet length in bytes
  -ddd, --debug_max     Turn on all DEBUG statments

```

Example:

```
$ ./receiverGBN.py -p 12345 -n 100 -e 0.001 -l 512
```

```
$ ./senderGBN.py -s 127.0.0.1 -p 12345 -l 512 -r 50 -n 100 -w 3 -b 10

PktRate: 50, Length: 512, Retran ratio: 1.029703, Avg RTT: 0.269921
```

### Selective Repeat

```
$ ./senderSR.py --help
usage: senderSR.py [-h] [-d] -s RECEIVER_IP -p PORT -L LENGTH -R RATE -N
                   MAX_PACKETS -W WINDOW -B BUFFER_SIZE -n SEQ_LENGTH [-ddd]

Sender script for Go Back N protocol

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           Turn on DEBUG mode
  -s RECEIVER_IP, --receiver_ip RECEIVER_IP
                        Receiver's IP address
  -p PORT, --port PORT  Receiver's port number
  -L LENGTH, --length LENGTH
                        Packet length in bytes
  -R RATE, --rate RATE  Rate of packets generation, per second
  -N MAX_PACKETS, --max_packets MAX_PACKETS
                        Max packets to be sent
  -W WINDOW, --window WINDOW
                        Window size
  -B BUFFER_SIZE, --buffer_size BUFFER_SIZE
                        Packet buffer size
  -n SEQ_LENGTH, --seq_length SEQ_LENGTH
                        Sequence number field length in bits
  -ddd, --debug_max     Turn on all DEBUG statments
```

```
$ ./receiverSR.py --help
usage: receiverSR.py [-h] [-d] -p PORT -N MAX_PACKETS -e DROP_PROB -l LENGTH
                     -W WINDOW -n SEQ_LENGTH -B BUFFER_SIZE [-ddd]

Receiver script for Go Back N protocol

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           Turn on DEBUG mode
  -p PORT, --port PORT  Receiver's port number
  -N MAX_PACKETS, --max_packets MAX_PACKETS
                        Max packets to be received
  -e DROP_PROB, --drop_prob DROP_PROB
                        Probability of packet being corrupted
  -l LENGTH, --length LENGTH
                        Packet length in bytes
  -W WINDOW, --window WINDOW
                        Window size
  -n SEQ_LENGTH, --seq_length SEQ_LENGTH
                        Sequence number field length in bits
  -B BUFFER_SIZE, --buffer_size BUFFER_SIZE
                        Packet buffer size
  -ddd, --debug_max     Turn on all DEBUG statments
```

Example:

```
$ ./receiverSR.py -p 12345 -N 400 -e 0.01 -B 100 -W 4 -l 512 -n 8
```

```
$ ./senderSR.py -s 127.0.0.1 -p 12345 -L 512 -R 100 -N 400 -W 4 -B 100 -n 8

PktRate: 100, Length: 512, Retran ratio: 1.016129, Avg RTT: 0.261601
```
