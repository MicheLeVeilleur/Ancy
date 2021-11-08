from http.server import HTTPServer
from queue import Queue
from threading import Thread
import misc_functions as f


##### ---- THREADS

# Thread handling HTTP server
def server(out_q):
    with HTTPServer(('192.168.1.88', 8000), f.make_custom_handler(q)) as server:
        print ("serving at port 8000")
        server.serve_forever()

#Thread handling thermostat + calls to Legrand API
def thermostat(in_q):
    while True:
        print(in_q.get())

#Thread handling sensors + inserting on MariaDB
def sensor_to_sql():
    while True:
        f.get_and_insert()

#### ---- LAUNCH THREADS
q = Queue() #the queue has to be global to be used by HTTPServer
def main():
    
    t1 = Thread(target = server, args =(q, ))
    t2 = Thread(target = thermostat, args =(q, ))
    t3 = Thread(target = sensor_to_sql)
    t1.start()
    t2.start()
    t3.start()

if __name__ == "__main__":
    # execute only if run as a script
    main()
