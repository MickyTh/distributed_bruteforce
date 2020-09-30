import sys
import queue
import socket
import threading
import hashlib
import time
import os
import getopt
import multiprocessing
import signal

rawhash = ""
wordfile = ""
resume = 0
mode = ""
Q = queue.Queue()
quitcode = multiprocessing.Value('i', 0)
client = multiprocessing.Value('i', 0)


def usage():
    print("distributed bruteforce project")
    print("usage: python3 dpy_brute.py -h <hash> -m <mode> -w <wordlist> -r <resume> -b <binding address> -p <port>")
    print()
    print("-h = hash ")
    print("-m = mode(md5,sha1,sha256)")
    print("-w = wordlist")
    print("-b = binding address to listen")
    print("-p = port")
    print("-r = resume(0/1)")
    print()
    sys.exit(1)


def status():  # thread main
    global Q
    avg = 0
    while True:
        oldsize = Q.qsize()
        print("queue words = ", Q.qsize(), " and client = ", client.value, " and quit status = ", quitcode.value,
              " and crack(per second) = ", avg)
        time.sleep(2)
        avg = oldsize - Q.qsize()


def quitthread():  # thread main
    while True:
        if client.value == 0 and quitcode.value == 1:
            print("server is closing")
            os.kill(os.getpid(), signal.SIGINT)


def keycapture():  # thread main
    while True:
        raw = input()
        if raw == "q":
            quitcode.value = 1


def handle(q, fd):
    global Q
    while not q.empty():
        word = q.get()
        word = "\n" + word + "\n"
        try:
            fd.sendall(word.encode())
        except:
            client.value = client.value - 1
            while not q.empty():
                Q.put(q.get())
            break
    print("sending...")


def listenclient(fd):
    while True:
        raw = fd.recv(5).decode()
        if raw == "found":
            raw = fd.recv(1000).decode()
            print("hash cracked %s" % raw)
            quitcode.value = 1
            time.sleep(2)
            os.kill(os.getpid(), signal.SIGINT)
        elif raw == "ok":
            fd.close()
            client.value -= 1
            break


def brute():  # thread main
    global rawhash
    global mode
    global Q
    while not Q.empty():
        if not quitcode.value:
            if mode == "md5":
                word = Q.get()
                calhash = hashlib.md5(word.encode())
                if rawhash == calhash.hexdigest():
                    print("hash cracked %s" % word)
                    quitcode.value = 1
                    time.sleep(2)
                    os.kill(os.getpid(), signal.SIGINT)
                else:
                    pass
            elif mode == "sha1":
                word = Q.get()
                calhash = hashlib.sha1(word.encode())
                if rawhash == calhash.hexdigest():
                    print("hash cracked %s" % word)
                    quitcode.value = 1
                    time.sleep(2)
                    os.kill(os.getpid(), signal.SIGINT)
                else:
                    pass
            elif mode == "sha256":
                word = Q.get()
                calhash = hashlib.sha256(word.encode())
                if rawhash == calhash.hexdigest():
                    print("hash cracked %s" % word)
                    quitcode.value = 1
                    time.sleep(2)
                    os.kill(os.getpid(), signal.SIGINT)
                else:
                    pass
        else:
            fdd = open("resume.txt", "w+")
            fdd.write(Q.get())
            fdd.close()
            break


def build():
    global resume
    global wordfile
    global Q
    fdd = open("resume.txt", "rb")
    go = 0
    resumeword = ""
    print("wordlist location = ", wordfile)
    fd = open(wordfile, "rb")
    wlist = fd.readlines()
    if resume == 1:
        resumeword = fdd.readline().decode('utf-8', "ignore").rstrip()
    if not resumeword and resume == 1:
        print("no resume file found")
        resume = 0
    for word in wlist:
        word = word.decode('utf-8', "ignore").strip()
        if resume == 1:
            if go == 1:
                Q.put(word)
            else:
                if resumeword == word:
                    go = 1
                    print("resuming after %s" % resumeword)
                else:
                    pass
        else:
            Q.put(word)
    print("words build= ", Q.qsize())
    fd.close()
    fdd.close()


def main():
    global rawhash
    global mode
    global resume
    global wordfile
    global Q
    leng = 0
    if len(sys.argv) < 6:
        usage()
    try:
        opts, rem = getopt.getopt(sys.argv[1:], "h:m:p:r:w:b:l:",
                                  ["hash=", "mode=", "port=", "resume=", "wordlist=", "bind="])
    except getopt.GetoptError as err:
        print(str(err))
        usage()
        sys.exit(1)
    for arg, val in opts:
        if arg in ["-h", "--hash"]:
            rawhash = val
        if arg in ["-m", "--mode"]:
            if val in ["md5", "sha1", "sha256"]:
                mode = val
            else:
                usage()
        if arg in ["-p", "--port"]:
            port = int(val)
        if arg in ["-r", "--resume"]:
            resume = int(val)
        if arg in ["-w", "--wordlist"]:
            wordfile = val
        if arg in ["-b", "--bind"]:
            ip = socket.gethostbyname(val)

    print("enter q to quit")
    print("starting program.....")
    time.sleep(2)
    build()

    thread2 = threading.Thread(target=status, args=())
    thread2.start()
    thread3 = threading.Thread(target=brute, args=())
    thread3.start()
    thread4 = threading.Thread(target=quitthread, args=())
    thread4.start()
    thread5 = threading.Thread(target=keycapture, args=())
    thread5.start()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((ip, port))
    server.listen(100)

    while not quitcode.value:
        client_fd, addr = server.accept()
        client_fd.sendall(rawhash.encode())
        time.sleep(0.5)
        client_fd.sendall(mode.encode())
        time.sleep(0.5)
        Q2 = queue.Queue()
        while Q2.qsize() != 1000:
            if not Q.empty():
                Q2.put(Q.get())
            elif Q.empty() and Q2.qsize():
                break
            else:
                quitcode.value = 1
                time.sleep(5)
                break
        client_fd.sendall(str(Q2.qsize()).encode())
        time.sleep(0.5)

        client.value += 1

        thread = multiprocessing.Process(target=handle, args=(Q2, client_fd))
        thread.start()

        thread1 = threading.Thread(target=listenclient, args=(client_fd,))
        thread1.start()


if __name__ == '__main__':
    main()
