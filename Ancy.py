from queue import Queue
from threading import Thread
import custom_http_server as f
import api_interface as a

##### ---- THREADS

# Thread handling HTTP server
def server(out_q):
    with f.http.server.HTTPServer(('192.168.1.88', 8000), f.make_custom_handler(q)) as server:
        print ("serving at port 8000")
        server.serve_forever()

#Thread handling thermostat + calls to Legrand API
def thermostat(in_q):
    thermostat_status = False
    force_status = False
    thermostat_temp = None
    last_current_state = False

    #api_interface = a.API_Interface()

    while True:
        new_command = in_q.get()
        print(new_command)
        last_temp = float(f.sql.get_last_record('deux')[0])
        if new_command:
            if "Force" in new_command:
                arg = new_command.split(" ")[1]
                if arg == "On":
                    force_status = True
                elif arg == "Off":
                    force_status = False
                elif arg == "Auto":
                    force_status = None
            elif "Thermostat" in new_command:
                arg,thermostat_temp = new_command.split(" ")[1:3]
                if arg == "On":
                    thermostat_status = True
                elif arg == "Off":
                    thermostat_status = False
        
        if not force_status is None:
            current_state = force_status
        elif thermostat_status:
            if last_temp < int(thermostat_temp):
                current_state = True
            else: 
                current_state = False
    
        if last_current_state != current_state:
            print(current_state)
            last_current_state = current_state
            #api_interface.set_module(a.CONTACTORS_ID[0],current_state)
            


#Thread handling sensors + inserting on MariaDB
def sensor_to_sql():
    while True:
        f.sql.get_and_insert()

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
