import os
import sys
import _thread as thread
import socket
import argparse
import signal

BACKLOG = 50
MAX_DATA = 8192
DEBUG = True
CWD = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = CWD +"/cache/"
LOG_FILE = CWD +"/log.txt"
BLOCKED_LIST = CWD + "/blocked.txt"
session_requests = 0
cache_requests = 0
fresh_requests = 0
total_requests = 0

class HTTP_Proxy:
    def __init__(self, host=None, port=None):
        self.host = host
        self.port = port
        self.number = 0
        self.fresh_requests = 0
        self.cache_requests = 0
        self.update_stats()

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
        http_method = srequest.split(' ')[0]
        url = srequest.split(' ')[1]

        if (DEBUG):
            print(http_method)
            print("URL: " + url)
        

        self.check_version(srequest, conn)
        # self.check_allowed(url,conn)
        self.check_method(http_method, conn)

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
            handled = self.check_cache(webserver, s, conn, client_addr, http_method, url)

            if not handled:
                while 1:
                    data = s.recv(MAX_DATA)

                    cache_file = open(CACHE_DIR + webserver, 'wb')
                    cache_file.write(data)

                    if (len(data) > 0):
                        conn.send(data)
                    else:
                        break
                    cache_file.close()
                self.fresh_requests += 1
            
            self.update_log(client_addr, http_method, url)
            self.number += 1
            self.close(s=s, conn=conn)
            print("Client's Request processed")
            print("Request Number: " + str(self.number))
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

    def check_allowed(self, url, conn):
    	fo = open(BLOCKED_LIST, 'r')
    	test=url.split("/")[2].split(".")
    	while True:
    		line = fo.readline()
    		if line:    			
    			linetest=line.split(".")[1].strip()
    		for part in test:
    			part1=part.strip()
	    		if linetest==part1:
		            print("url is blocked\n")
		            data = b"url IS BLOCKED!!\n"
		            conn.send(data)
		            self.close(conn=conn)
		            sys.exit(1)
    		if not line: 
        		break

    def check_cache(self, filename, s, conn, client_addr, method, url):
        file_path = CACHE_DIR + filename
        try:
            f = open(file_path, 'rb')
            print("Using Cached File ......")
            data = f.read()
            self.update_log(client_addr, method, url)
            self.cache_requests += 1
            found = True
            conn.send(data)
            f.close()
        except IOError:
            found = False
        return found

    def filter(self, action, handle):
        if action == 'block':
            for line in open(BLOCKED_LIST, 'r'):
                for address in handle:
                    if address == line.strip():
                        print("Already blocked")
                        handle.remove(address)
            for address in handle:
                with open(BLOCKED_LIST, 'a') as f:
                    f.write(address+'\n')

        elif action == 'unblock':
            print("Unblocking")
            f = open(BLOCKED_LIST, 'r')
            lines = f.readlines()
            f.close()
            f = open(BLOCKED_LIST, 'w')
            for line in lines:
                if line.strip() not in handle:
                    f.write(line.strip() + '\n')
            f.close()

    def update_log(self, client_addr, method, url):
        log_file = open(LOG_FILE, 'a')
        log_file.write(client_addr[0] + ': ' + method + ' ' + url + '\n')
        log_file.close()

    def update_stats(self):
        global session_requests
        global cache_requests
        global fresh_requests
        global total_requests
        print("Updating stats....")
        session_requests = self.number
        cache_requests = self.cache_requests
        fresh_requests = self.fresh_requests
        with open(LOG_FILE) as log_file:
            for i, l in enumerate(log_file):
                pass
        total_requests = i + 1
        print('Total Requests: ' + str(total_requests))

    def close(self, s=None, conn=None):
        self.update_stats()
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
    parser.add_argument("-b", "--block", metavar="HOST", nargs='*',
                    default=None, help="Block address, default no action")
    parser.add_argument("-ub", "--unblock", metavar="HOST", nargs='*',
                    default=None, help="Block address, default no action")
    args = parser.parse_args()

    host = args.hostname
    port = int(args.port)
    block_list = args.block
    unblock_list = args.unblock

    if block_list:
        proxy = HTTP_Proxy()
        proxy.filter(action='block', handle=block_list)
    elif unblock_list:
        proxy = HTTP_Proxy()
        proxy.filter(action='unblock', handle=unblock_list)
    else:
        proxy = HTTP_Proxy(host, port)
        proxy.start()

def exit(signal, frame):
    print('Received: SIGUSR2 (' + str(signal) + ')')
    print('Exiting')
    sys.exit()

def stats(signal, frame):
    print('Received: SIGUSR1 (' + str(signal) + ')')
    print('Printing stats....')
    print('Total requests processed by the Proxy:\t\t' + str(total_requests))
    print('Requests processed in the current session:\t' + str(session_requests))
    print('Requests processed via Cache:\t\t\t' + str(cache_requests))
    print('Fresh requests processed:\t\t\t' + str(fresh_requests))

def do_nothing(signal, frame):
    print()
    print('Received: SIGINT (' + str(signal) + '), ignoring.....')

signal.signal(signal.SIGUSR2, exit)
signal.signal(signal.SIGUSR1, stats)
# signal.signal(signal.SIGINT, do_nothing)

if __name__ == '__main__':
    print(os.getpid())
    try:
        main()
    except KeyboardInterrupt:
        # print("Detected SIGINT signal....")
        print("\n[KeyboardInterrupt]: Exiting!")
        sys.exit()
