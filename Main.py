#DO NOT FORGET TO UNCOMMENT TEST PARTS !!!!!!!!!

from http.server import BaseHTTPRequestHandler, HTTPServer
from queue import Queue
from threading import Thread
import MySQLdb
import time
#import RPi.GPIO as GPIO
import datetime
#import Adafruit_DHT as dht

# constants of connection to MariaDB

HOSTNAME = 'localhost'
USERNAME = 'pi'
PASSWORD = 'raspberry'
DATABASE = 'Sensors'
SENSORS_NAME = ['quatre', 'deux', 'zero']

#constants of the sensors

#DHT_SENSOR = dht.DHT22
DHT_PIN = [9,10,11]

class handler(BaseHTTPRequestHandler):
    t_status = False
    def do_GET(self):
        checked = (lambda x:["checked",""] if x else ["","checked"])(self.t_status)
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        display = '<html><body>'
        display += '<h1>Choice<h1>'
        display += '<p><h3>Currenttemperature is : <form method="POST" enctype="multipart/form-data" action="/">'
        display += '<div><input name= "OnOff" type="radio" value="On"{}>ON</div>'.format(checked[0])
        display += '<div><input name= "OnOff" type="radio" value="Off"{}>OFF</div>'.format(checked[1])
        display += '<input type="submit">'
        display += '</form></h3></p></body></html>'
        

        self.wfile.write(bytes(display, "utf8"))
        
    def do_POST(self):
        
        content_len = int(self.headers.get('Content-Length'))
        post_body = str(self.rfile.read(content_len))
        post = post_body.split("OnOff")[1]
        if "On" in post:
            self.t_status = True
        elif "Off" in post:
            self.t_status = False
        q.put(self.t_status)
        self.do_GET()

##### ---- THREADS

# Thread handling HTTP server
def server(out_q):
    with HTTPServer(('localhost', 8000), handler) as server:
        print ("serving at port 8000")
        server.serve_forever()

#Thread handling thermostat + calls to Legrand API
def thermostat(in_q):
    while True:
        print(in_q.get())

#Thread handling sensors + inserting on MaiaDB
def sensor_to_sql():
    """GPIO.setmode(GPIO.BCM)
    for dht_sensor_port in DHT_PIN:
	    GPIO.setup(dht_sensor_port, GPIO.IN)"""
    
    while True:
        now = datetime.datetime.now()
        date = now.strftime('%Y-%m-%d %H:%M:%S')
        i = 0
        for table_name in SENSORS_NAME:
            #hum, temp = dht.read_retry(DHT_SENSOR, DHT_PIN[i] )
            hum, temp = -100,-100
            if hum:
                insert_record(table_name , str(date), format(temp, '.2f'), format(hum, '.2f'))
            else:
                print(date," error while reading dht22 on pin {}".format(DHT_PIN[i]))
            i += 1
        time.sleep(15)

##### --- Misc fcts
def insert_record(table_name, datetime, temp, hum):
	print("inserting record on",table_name,"of ",temp,hum)
	query = "INSERT INTO {} ( date, temp, hum) VALUES (%s, %s, %s)".format(table_name)
	args = ( datetime, temp, hum)
	
	try:
		conn = MySQLdb.connect(host=HOSTNAME, user=USERNAME, passwd=PASSWORD, db=DATABASE)
		cursor = conn.cursor()
		cursor.execute(query, args )
		conn.commit()

	except Exception as error:
		print(error)

	finally:
		cursor.close()
		conn.close()

#### ---- LAUNCH THREADS
def main():
    q = Queue()
    t1 = Thread(target = server, args =(q, ))
    t2 = Thread(target = thermostat, args =(q, ))
    t3 = Thread(target = sensor_to_sql)
    t1.start()
    t2.start()
    t3.start()

if __name__ == "__main__":
    # execute only if run as a script
    main()