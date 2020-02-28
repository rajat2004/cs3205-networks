#include "proxy_parse.h"

int main() {
    struct ParsedRequest *req = ParsedRequest_create();

    const char *c = 
    "GET http://www.google.com:80/index.html/ HTTP/1.0\r\nContent-Length:"
    " 80\r\nIf-Modified-Since: Sat, 29 Oct 1994 19:43:31 GMT\r\n\r\n";
    // "GET http://www.cse.iitm.ac.in/ HTTP/1.0\r\n\r\n";

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

    ParsedHeader_set(req, "Connection", "close");

    struct ParsedHeader *r = ParsedHeader_get(req, "If-Modified-Since");
    if (r != NULL)
        printf("Modified value: %s\n", r->value);

    r = ParsedHeader_get(req, "Connection");
    if (r != NULL)
        printf("Connection: %s\n", r->value);
    
    return 0;
}