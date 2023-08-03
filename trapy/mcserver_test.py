from concurrent.futures.thread import ThreadPoolExecutor
from random import betavariate
from trapy import close, accept, send, listen

def sender(conn):
    f = open("server_data.txt", "r")
    s = bytes(f.read(), "utf8")
    print("Bytes read",len(s))
    f.close()
    sent = send(conn, s)
    print("Bytes Sent",sent)
    close(conn)

server = listen("127.0.0.1:6")
executor = ThreadPoolExecutor()
while True:
    try:
        conn = accept(server)
        if conn:
            executor.submit(sender, conn)
    except KeyboardInterrupt:
        print("Shutting Down Server")
        break
close(server)
executor.shutdown(True)


