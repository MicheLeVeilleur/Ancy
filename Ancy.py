from queue import Queue
from threading import Thread

import custom_http_server as s
import get_and_insert as g
import thermostat as t



##### ---- THREADS

# Thread handling HTTP server
def server(q,in_q):
    s.server(q,in_q)

#Thread handling thermostat + calls to Legrand API
def thermostat(in_q,out_q):
    t.thermostat(in_q,out_q)

#Thread handling sensors + inserting on MariaDB
def sensor_to_sql():
    g.get_and_insert()

#### ---- LAUNCH THREADS
q = Queue() #the queue has to be global to be used by HTTPServer
q2 = Queue()

def main():
    
    t1 = Thread(target = server, args =(q, q2, ))
    t2 = Thread(target = thermostat, args =(q, q2, ))
    t3 = Thread(target = sensor_to_sql)
    t1.start()
    t2.start()
    t3.start()

if __name__ == "__main__":
    # execute only if run as a script
    main()
