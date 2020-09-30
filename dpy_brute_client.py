import socket
import sys
import threading
import hashlib
import queue
import os
import signal
import time
import multiprocessing
import re

ip = ""
port = 0
thread_size = 0
quitstatus = multiprocessing.Value('i', 0)


def usage():
    print("usage: python3 dpy_brute_cli.py <server ip> <server port> <thread>")
    print("warning: normal thread size is not more than 3")
    sys.exit(1)


def status(Q, i):  # thread main
    avg = 0
    while True:
        oldsize = Q.qsize()
        if oldsize == 0:
            print("Quit status = ", quitstatus.value,
                  " and crack(per second) = ", avg, " and thread number = ", i)
            break
        print("Quit status = ", quitstatus.value,
              " and crack(per second) = ", avg, " and thread number = ", i)
        time.sleep(2)
        avg = oldsize - Q.qsize()


def keycapture():  # thread main
    while True:
        raw = input()
        if raw == "q":
            quitstatus.value = 1


def handle(i):
    while True:
        Q = queue.Queue()
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            conn.connect((ip, port))
        except:
            print("server refused ")
            break

        rawhash = conn.recv(1000).decode()
        time.sleep(0.5)
        mode = conn.recv(10).decode()
        time.sleep(0.5)
        size = int(conn.recv(100).decode())
        time.sleep(0.5)

        print("hash and mode and size = ", rawhash, mode, size)

        print("Queue receiving")
        pattern = r"\n.+\n"
        s = 0
        while Q.qsize() != size:
            w = conn.recv(9000).decode()
            lst = re.findall(pattern, w)
            for ff in lst:
                striped = ff.strip()
                Q.put(striped)
                s += 1

        print("Finish receiving (size = %d)" % s)

        thread = threading.Thread(target=status, args=(Q, i))
        thread.start()

        if mode == "md5":
            while not Q.empty():
                word = Q.get()
                calhash = hashlib.md5(word.encode())
                if rawhash == calhash.hexdigest():
                    print("hash cracked %s" % word)
                    conn.sendall("found".encode())
                    conn.sendall(word.encode())
                    os.kill(os.getpid(), signal.SIGINT)
            conn.sendall("ok".encode())

        elif mode == "sha1":
            while not Q.empty():
                word = Q.get()
                calhash = hashlib.sha1(word.encode())
                if rawhash == calhash.hexdigest():
                    print("hash cracked %s" % word)
                    conn.sendall("found".encode())
                    conn.sendall(word.encode())
                    os.kill(os.getpid(), signal.SIGINT)
            conn.sendall("ok".encode())

        elif mode == "sha256":
            while not Q.empty():
                word = Q.get()
                calhash = hashlib.sha256(word.encode())
                if rawhash == calhash.hexdigest():
                    print("hash cracked %s" % word)
                    conn.sendall("found".encode())
                    conn.sendall(word.encode())
                    os.kill(os.getpid(), signal.SIGINT)
            conn.sendall("ok".encode())
        if quitstatus.value == 1:
            print("Finished (due to quit)")
            break


def main():
    global ip
    global port
    global thread_size

    if len(sys.argv) < 3:
        usage()
    ip = socket.gethostbyname(sys.argv[1])
    port = int(sys.argv[2])
    thread_size = int(sys.argv[3])

    thread2 = threading.Thread(target=keycapture, args=())
    thread2.start()

    for i in range(0, thread_size):
        thread3 = multiprocessing.Process(target=handle, args=(i,))
        thread3.start()

    print("THread started")


if __name__ == '__main__':
    main()
