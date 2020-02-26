#include "proxy_parse.h"

#include <unistd.h> 
#include <stdio.h> 
#include <sys/socket.h> 
#include <stdlib.h> 
#include <netinet/in.h> 
#include <string.h> 
#include <arpa/inet.h>
#include <sys/wait.h>
#include <sys/types.h>

int proxy_fd;
int MAX_CHILD = 100;

// Read data till "\r\n\r\n"
char* readDataFromSocket(int sock_fd) {
    int BUFFER_SIZE = 4096;

    char* request;
    char buf[BUFFER_SIZE+1];            // 1 for '\0'

    request = (char*)malloc(BUFFER_SIZE+1);

    int curr_request_size = BUFFER_SIZE;
    int recv_length = 0;
    int required_length = 0;
    request[0]='\0';                    // Needed for string concatenation

    // Keep reading till we find "\r\n\r\n"
    while(strstr(request, "\r\n\r\n") == NULL) {
        // Not found, read
        recv_length = recv(sock_fd, buf, BUFFER_SIZE, 0);

        if (recv_length < 0) {
            perror("Recv error\n");
            exit(EXIT_FAILURE);
        }
        if (recv_length == 0) {
            // Nothing more to read
            break;
        }
        buf[recv_length]='\0';

        required_length += recv_length;
        if (required_length > curr_request_size) {
            // Allocate more memory for request string
            curr_request_size *= 2;
            request = (char*)realloc(request, curr_request_size+1);
        }

        strcat(request, buf);
    }
    return request;
}


// Handles request from client socket with fd client_fd
void handleRequest(int client_fd) {
    // Fork child to handle request
    int pid = fork();

    if(pid < 0) {
        // error
        perror("Forking error!\n");
        return;
    }

    // Inside child
    if(pid == 0) {
        char *client_req_str = readDataFromSocket(client_fd);

        struct ParsedRequest *req = ParsedRequest_create();

        if (ParsedRequest_parse(req, client_req_str, strlen(client_req_str)) < 0) {
            printf("Parse failed");
            exit(EXIT_FAILURE);
        }
        printf("Method: %s\n", req->method);
        printf("Protocol: %s\n", req->protocol);
        printf("Host: %s\n", req->host);
        printf("Port: %s\n", req->port);
        printf("Path: %s\n", req->path);
        printf("Version: %s\n", req->version);

        exit(EXIT_SUCCESS);
    }

    int status;
    wait(&status);
}

int main(int argc, char * argv[]) {
    int portno; // Port for proxy to bind, command-line arg

    if (argc < 2) {
        printf("Usage: %s <port-number>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    portno = atoi(argv[1]);

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

    if(listen(proxy_fd, MAX_CHILD) < 0) {
        perror("Error while Listening\n");
        exit(EXIT_FAILURE);
    }

    // First test single client
    int client_fd;
    struct sockaddr_in client_addr;
    int addrlen = sizeof(client_addr);

    if ((client_fd = accept(proxy_fd, (struct sockaddr *)&client_addr, (socklen_t*)&addrlen)) < 0) {
        perror("Accept error\n");
        exit(EXIT_FAILURE);
    }
    handleRequest(client_fd);


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
