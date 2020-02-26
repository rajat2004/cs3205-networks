#include "proxy_parse.h"

#include <unistd.h> 
#include <stdio.h> 
#include <sys/socket.h> 
#include <stdlib.h> 
#include <netinet/in.h> 
#include <string.h> 
#include <arpa/inet.h>

int main(int argc, char * argv[]) {
    int portno; // Port for proxy to bind, command-line arg

    if (argc < 2) {
        printf("Usage: %s <port-number>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    portno = atoi(argv[1]);

    int proxy_fd;

    if ((proxy_fd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        perror("Socket Creation error\n");
        exit(EXIT_FAILURE);
    }

    int reuse = 1;
    if (setsockopt(proxy_fd, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, &reuse, sizeof(reuse))) {
        perror("Socket Reuse Addr,Port failed\n");
    }

    struct sockaddr_in proxy_addr;

    proxy_addr.sin_family = AF_INET;
    proxy_addr.sin_addr.s_addr = INADDR_ANY;
    proxy_addr.sin_port = htons(portno);

    if (bind(proxy_fd, (struct sockaddr *)&proxy_addr, sizeof(proxy_addr)) < 0) {
        perror("Binding Error\n");
        exit(EXIT_FAILURE);
    }

    int max_clients = 100;

    if(listen(proxy_fd, max_clients) < 0) {
        perror("Error while Listening\n");
        exit(EXIT_FAILURE);
    }
    

    /*
    struct ParsedRequest *req = ParsedRequest_create();

    const char *c = 
    "GET http://www.google.com:80/index.html/ HTTP/1.0\r\nContent-Length:"
    " 80\r\nIf-Modified-Since: Sat, 29 Oct 1994 19:43:31 GMT\r\n\r\n";

    int len = strlen(c);
    if (ParsedRequest_parse(req, c, len) < 0) {
        printf("Parse failed\n");
        return -1;
    }

    printf("Method: %s\n", req->method);
    printf("Protocol: %s\n", req->protocol);
    printf("Host: %s\n", req->host);
    printf("Port: %s\n", req->port);
    printf("Path: %s\n", req->path);
    printf("Version: %s\n", req->version);

    int rlen = ParsedRequest_totalLen(req);
    printf("Total len: %d, %d\n", rlen, len);

    char *b = (char*)malloc(rlen+1);
    if (ParsedRequest_unparse(req, b, rlen) < 0) {
        printf("Unparse failed\n");
        return -1;
    }
    b[rlen]='\0';

    struct ParsedHeader *r = ParsedHeader_get(req, "If-Modified-Since");
    printf("Modified value: %s\n", r->value);
    */
    return 0;
}
