import os
import sys
import _thread as thread
import socket
import argparse

BACKLOG = 50
MAX_DATA = 8192
DEBUG = True

class HTTP_Proxy:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def start(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((self.host, self.port))
            s.listen(BACKLOG)
        except (socket.error, value, message):
            if s:
                s.close()
            print("Couldn't open socket: " + message)
            sys.exit(1)

        while 1:
            conn, client_addr = s.accept()
            print("Client Request! Accepted! New Thread .....")
            thread.start_new_thread(self.proxy_thread, (conn, client_addr))

        s.close()
        

    def proxy_thread(self, conn, client_addr):
        request = conn.recv(MAX_DATA)
        srequest = request.decode('utf-8')
        self.check_version(srequest, conn)
        first_line = srequest.split(' ')[0]
        url = srequest.split(' ')[1]

        if (DEBUG):
            print(first_line)
            print("URL: " + url)

        self.check_method(first_line, conn)

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
            self.close(s=s, conn=conn)
            print("Runtime Error: " + message)
            sys.exit(1)

    def check_version(self, request, conn):
        version = request.split(' ')[2].split('/')[1].split('\n')[0].strip()
        if version == '1.1' or version == '1.0':
            pass
        else:
            print("ERROR 505: HTTP Version Not Supported")
            data = b"ERROR 505: HTTP Version Not Supported\n"
            conn.send(data)
            self.close(conn=conn)
            sys.exit(1)

    def check_method(self, method, conn):
        if method == 'GET' or method == 'POST' or method == 'HEAD':
            pass
        else:
            print("ERROR 501: Not Implemented")
            data = b"ERROR 501: Not Implemented\n"
            conn.send(data)
            self.close(conn=conn)
            sys.exit(1)

    def filter(self):
        return

    def close(self, s=None, conn=None):
        self.close_server(s)
        self.close_client(conn)

    def close_server(self, s):
        if s:
            s.close()

    def close_client(self, conn):
        if conn:
            conn.close()

def main():

    parser = argparse.ArgumentParser(
            description='Simple HTTP Proxy for CS425 Project',)
    parser.add_argument("-ip", "--hostname", default="127.0.0.1",
                    help="default IP 127.0.0.1")
    parser.add_argument("-p", "--port", default="8000",
                    help="default port number 8000")
    args = parser.parse_args()

    host = args.hostname
    port = int(args.port)

    proxy = HTTP_Proxy(host, port)
    proxy.start()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n[KeyboardInterrupt]: Exiting!")
        sys.exit()
