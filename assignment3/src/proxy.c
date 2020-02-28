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
#include <netdb.h>

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

// Sends message to the (ip,port) the socket is connected to
void sendToSocket(char *msg, int sockfd) {
    int sent = 0;
    int totalSent = 0;
    int msglen = strlen(msg);

    while(totalSent < msglen) {
        sent = send(sockfd, (msg + totalSent), msglen-totalSent, 0);
        // TODO: Error handling?
        totalSent += sent;
    }
}

// Returns socket connected to specified address and port no.
int createServerSocket(char *addr, char *port) {
    int sockfd;

    // Resolve hostname
    struct addrinfo hints;
    struct addrinfo *servinfo;

    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC;     // don't care IPv4 or IPv6
    hints.ai_socktype = SOCK_STREAM; // TCP

    if (getaddrinfo(addr, port, &hints, &servinfo) != 0) {
        perror("Error getting server addrinfo\n");
        exit(EXIT_FAILURE);
    }

    // Create socket and connect
    if ((sockfd = socket(servinfo->ai_family, servinfo->ai_socktype, servinfo->ai_protocol)) < 0) {
        perror("Server socket creation error, exiting\n");
        exit(EXIT_FAILURE);
    }

    if(connect(sockfd, servinfo->ai_addr, servinfo->ai_addrlen) < 0) {
        perror("Connect to server failed\n");
        exit(EXIT_FAILURE);
    }

    freeaddrinfo(servinfo);

    return sockfd;
}


char* createServerRequest(struct ParsedRequest *req) {
    if (req->port == NULL) {
        printf("Port is empty, setting to 80\n");
        req->port = "80";
    }

    if (strcmp(req->method, "GET") != 0) {
        // TODO: Send error message to client
        printf("Method recevied: %s, expected GET, exiting\n", req->method);
        exit(EXIT_FAILURE);
    }

    // Set Connection Close header
    ParsedHeader_set(req, "Connection", "close");

    // Set Host header
    ParsedHeader_set(req, "Host", req->host);

    // Prepare headers string for concatenation
    int headers_len = ParsedHeader_headersLen(req);
    char* headers_str = (char*)malloc(headers_len + 1);     // +1 for null-termination
    ParsedRequest_unparse_headers(req, headers_str, headers_len);
    headers_str[headers_len] = '\0';

    // Prepare Request to be sent to server

    // Example: GET http://www.cse.iitm.ac.in/ HTTP/1.0
    // Length =            "GET" " "     "/"             " "   "HTTP/1.0"         "\r\n"
    int serverRequestLength = 3 + 1 + strlen(req->path) + 1 + strlen(req->version) + 2;
    serverRequestLength += headers_len;

    char *serverRequest = (char*)malloc(serverRequestLength+1);

    // Finally add everything
    serverRequest[0] = '\0';
    strcat(serverRequest, "GET ");
    strcat(serverRequest, req->path);
    strcat(serverRequest, " ");
    strcat(serverRequest, req->version);
    strcat(serverRequest, "\r\n");
    strcat(serverRequest, headers_str);

    printf("Server request: %s\n", serverRequest);

    return serverRequest;
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
            // TODO: Send error message to Cient
            printf("Parse failed");
            exit(EXIT_FAILURE);
        }
        printf("Method: %s\n", req->method);
        printf("Protocol: %s\n", req->protocol);
        printf("Host: %s\n", req->host);
        printf("Port: %s\n", req->port);
        printf("Path: %s\n", req->path);
        printf("Version: %s\n", req->version);

        // Get request message to be sent to server
        char* req_to_server = createServerRequest(req);

        // Socket connected to server
        int serverfd = createServerSocket(req->host, req->port);

        // Send request to server
        sendToSocket(req_to_server, serverfd);

        // Receive response from server
        char* server_response = readDataFromSocket(serverfd);

        // Send server response to client
        sendToSocket(server_response, client_fd);

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


    return 0;
}
