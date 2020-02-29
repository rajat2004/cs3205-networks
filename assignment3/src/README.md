## HTTP Proxy Implementation

### Usage

1. First compile the code
  
   `$ make`

2. Running the Proxy server

    `$ ./proxy <port-no>`

    Ex: `$ ./proxy 12345`

### Testing

Open another terminal and run `telnet localhost <port-no>`

Eg:
```
$ telnet localhost 12345
Trying 127.0.0.1...
Connected to localhost.
Escape character is '^]'.
```

Type `GET http://www.cse.iitm.ac.in/ HTTP/1.0` and press Enter twice, HTML reponse from server will be shown

Compare with direct telnet connection - `telnet www.cse.iitm.ac.in 80` and use the same GET request

Run multiple telnet connections from different terminals to test multiple clients

