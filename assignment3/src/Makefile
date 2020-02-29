CC=gcc
CFLAGS=-Wall -Werror

all: proxy

proxy: proxy.c
	$(CC) $(CFLAGS) -o proxy_parse.o -c proxy_parse.c
	$(CC) $(CFLAGS) -o proxy.o -c proxy.c
	$(CC) $(CFLAGS) -o proxy proxy_parse.o proxy.o

try: try.c
	$(CC) $(CFLAGS) -o proxy_parse.o -c proxy_parse.c
	$(CC) $(CFLAGS) -o try.o -c try.c
	$(CC) $(CFLAGS) -o try try.o proxy_parse.o

clean:
	rm -f proxy try *.o

tar:
	tar -cvzf Assignment3-CS17B042.tgz proxy.c README Makefile proxy_parse.c proxy_parse.h
