import os
import sys
import _thread as thread
import socket
import argparse

BACKLOG = 50
MAX_DATA = 8192
DEBUG = True

def proxy_thread(conn, client_addr):
    request = conn.recv(MAX_DATA)
    srequest = request.decode('utf-8')
    print(srequest)
    first_line = srequest.split(' ')[0]
    url = srequest.split(' ')[1]

    if (DEBUG):
        print(first_line)
        print("URL: " + url)

    http_pos = url.find("://")
    if (http_pos == -1):
        temp = url
    else:
        temp = url[(http_pos+3):]

    port_pos = temp.find(":")

    webserver_pos = temp.find("/")
    if webserver_pos == -1:
        webserver_pos = len(temp)

    webserver = ""
    port = -1
    if (port_pos == -1 or webserver_pos < port_pos):
        port = 80
        webserver = temp[:webserver_pos]
    else:
        port = int((temp[(port_pos+1):])[:webserver_pos-port_pos-1])
        webserver = temp[:port_pos]

    print("Connect to " + webserver + ':' + str(port))

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((webserver, port))
        s.send(request)
        print("Client's Request sent")

        while 1:
            data = s.recv(MAX_DATA)

            if (len(data) > 0):
                conn.send(data)
            else:
                break

        print("Client's Request processed")
        s.close()
        conn.close()
    except (socket.error, value, message):
        if s:
            s.close()
        if conn:
            conn.close()
        print("Runtime Error: " + message)
        sys.exit(1)

class HTTP_Proxy:
    def __init__(self):
        return

    def start(self):
        return

    def proxy_thread(self):
        return

    def filter(self):
        return

    def exit(self):
        return

def main():

    if (len(sys.argv) < 2):
        print("Usage: python3 http_proxy.py <hostname> <port>")
        return sys.stdout

    host = ''
    port = int(sys.argv[1])

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((host, port))
        s.listen(BACKLOG)
    except (socket.error, value, message):
        if s:
            s.close()
        print("Couldn't open socket: " + message)
        sys.exit(1)

    while 1:
        conn, client_addr = s.accept()
        print("Client Request! Accepted! New Thread .....")
        thread.start_new_thread(proxy_thread, (conn, client_addr))

    s.close()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n[KeyboardInterrupt]: Exiting!")
        sys.exit()
