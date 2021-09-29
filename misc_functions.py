import datetime
import MySQLdb
import time
from http.server import BaseHTTPRequestHandler
import matplotlib.pyplot as plt
import Adafruit_DHT as dht
import RPi.GPIO as GPIO

# constants of connection to MariaDB

HOSTNAME = 'localhost'
USERNAME = 'pi'
PASSWORD = 'raspberry'
DATABASE = 'Sensors'
SENSORS_NAME = ['quatre', 'deux', 'zero']

#constants of the sensors

DHT_SENSOR = dht.DHT22
DHT_PIN = [9,10,11]

def make_custom_handler(q):
    class handler(BaseHTTPRequestHandler):
        t_status = False
        def __init__(self, *args, **kwargs):
             super(handler, self).__init__(*args, **kwargs)
            
        def do_GET(self):

            self.send_response(200)
            if self.path.endswith(".png"):
                mimetype='image/png'
            else:
                mimetype='text/html'
            self.send_header('Content-type',mimetype)
            self.end_headers()
            if self.path == "/":
                c_variables = get_last_record('deux')
                checked = (lambda x:["checked",""] if x else ["","checked"])(self.t_status)
                display = '<html><body>'
                display  += '<body><img src=\"/quatre_last.png\"width><img src=\"/deux_last.png\"><img src=\"/zero_last.png\">'
                display += '<p><h3>Current temperature is : {} <form method="POST" enctype="multipart/form-data" action="/">'.format(c_variables)
                display += '<div><input name= "OnOff" type="radio" value="On"{}>ON</div>'.format(checked[0])
                display += '<div><input name= "OnOff" type="radio" value="Off"{}>OFF</div>'.format(checked[1])
                display += '<input type="submit">'
                display += '</form> <a href="/deux_last_step_12.png">50 dernieres heures deux</a> <a href="/quatre_last_step_12.png">50 dernieres heures quatre</a>'
                display += ' <a href="/zero_last_step_12.png">50 dernieres heures zero</a> '
                display += '</h3></p></body></html>'

                self.wfile.write(bytes(display, "utf8"))
            
            elif self.path == "/quatre_last.png":
                make_recent_plot('quatre',50)
                with open(r'quatre_last.png','rb') as f:
                    self.wfile.write(f.read())

            elif self.path == "/deux_last.png":
                make_recent_plot('deux',50)
                with open(r'deux_last.png','rb') as f:
                    self.wfile.write(f.read())

            elif self.path == "/zero_last.png":
                with open(r'zero_last.png','rb') as f:
                    make_recent_plot('zero',50)
                    self.wfile.write(f.read())

            elif self.path == "/deux_last_step_12.png":
                make_recent_step_plots('deux',12,50)
                with open(r'deux_last_step_12.png','rb') as f:
                    self.wfile.write(f.read())
            elif self.path == "/quatre_last_step_12.png":
                make_recent_step_plots('quatre',12,50)
                with open(r'quatre_last_step_12.png','rb') as f:
                    self.wfile.write(f.read())
            elif self.path == "/zero_last_step_12.png":
                make_recent_step_plots('zero',12,50)
                with open(r'zero_last_step_12.png','rb') as f:
                    self.wfile.write(f.read())

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
    return handler

def MakeHandlerClassFromArgv(init_args):
    class CustomHandler(BaseHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
             super(CustomHandler, self).__init__(*args, **kwargs)
    return CustomHandler
##### --- Misc fcts
def send_query(query,args,return_result = False):
	try:
		conn = MySQLdb.connect(host=HOSTNAME, user=USERNAME, passwd=PASSWORD, db=DATABASE)
		cursor = conn.cursor()
		cursor.execute(query, args )
		conn.commit()
		if return_result:
			return cursor.fetchall()

	except Exception as error:
		print(error)

	finally:
		cursor.close()
		conn.close()

def insert_record(table_name, datetime, temp, hum):
	print("inserting record on",table_name,"of ",temp,hum)
	query = "INSERT INTO {} ( date, temp, hum) VALUES (%s, %s, %s)".format(table_name)
	args = ( datetime, temp, hum)
	send_query(query, args)

def get_record(table_name, datetime):
	query = "SELECT temp, hum, TIMEDIFF('{1}', date) as SecondsBetweenDates FROM {0}\
            ORDER BY TIMEDIFF('{1}', date)\
            LIMIT 1".format(table_name,datetime)
	return send_query(query, None, return_result=True)[0]

def get_records(table_name, datetime,limit):
    query = "SELECT * FROM (SELECT temp, hum, date FROM {0}\
            ORDER BY TIMEDIFF('{1}', date)\
            LIMIT {2}) as foo\
            ORDER BY foo.date ASC".format(table_name,datetime,limit)
    return send_query(query, None, return_result=True)

def get_records_step(table_name, datetime, step, limit):
    query = "CREATE SEQUENCE s START WITH 1 INCREMENT BY 1"
    send_query(query, None)
    time.sleep(1)
    query = "SELECT date,temp,hum FROM \
                (SELECT date,temp,hum, NEXTVAL(s) as a \
                FROM {2} HAVING a % {0} = 0 \
                ORDER BY TIMEDIFF('{3}', date) LIMIT {1} ) AS T\
            ORDER BY T.date ASC".format(step,limit,table_name,datetime)
    result =  send_query(query, None, return_result=True)
    query = "DROP SEQUENCE s"
    time.sleep(1)
    send_query(query, None)
    return result

def get_last_record(table_name):
	now = datetime.datetime.now()
	date = now.strftime('%Y-%m-%d %H:%M:%S')
	return get_record(table_name, date)

def get_last_records(table_name,limit):
	now = datetime.datetime.now()
	date = now.strftime('%Y-%m-%d %H:%M:%S')
	return get_records(table_name, date,limit)

def get_last_step_records(table_name, step, limit):
    now = datetime.datetime.now()
    date = now.strftime('%Y-%m-%d %H:%M:%S')
    return get_records_step(table_name, date,step,limit)

def make_recent_plot(table_name, limit):
    tuples = get_last_records(table_name,limit)
    dates_full  = []
    temp = []
    hum = []
    for line in tuples:
        temp.append(line[0])
        hum.append(line[1])
        dates_full.append(line[2])
    
    fig, (ax1, ax2) = plt.subplots(2, sharex=True)
    fig.suptitle('{0} dernières mesures de {1}'.format(limit,table_name))
    ax1.plot(dates_full, temp)
    ax2.plot(dates_full, hum)
    ax1.set_title('Temperature')
    ax2.set_title('Humidite')
    plt.ylim(bottom=0)
    plt.ylim(top=100)
    plt.xticks(dates_full,rotation=90)
    plt.savefig('{}_last.png'.format(table_name),dpi=70,bbox_inches='tight')

def make_recent_step_plots(table_name, step, limit):
    tuples = get_last_step_records(table_name,step,limit)
    dates_full  = []
    temp = []
    hum = []
    for line in tuples:
        temp.append(line[1])
        hum.append(line[2])
        dates_full.append(line[0])
    
    fig, (ax1, ax2) = plt.subplots(2, sharex=True)
    fig.suptitle('{0} dernières heures de {1}'.format(round(limit*step*5/60),table_name))
    ax1.plot(dates_full, temp)
    ax2.plot(dates_full, hum)
    ax1.set_title('Temperature')
    ax2.set_title('Humidite')
    plt.ylim(bottom=0)
    plt.ylim(top=100)
    plt.xticks(dates_full,rotation=90)
    plt.savefig('{0}_last_step_{1}.png'.format(table_name,step),dpi=70,bbox_inches='tight')

def get_and_insert():
    GPIO.setmode(GPIO.BCM)
    for dht_sensor_port in DHT_PIN:
	    GPIO.setup(dht_sensor_port, GPIO.IN)
    now = datetime.datetime.now()
    date = now.strftime('%Y-%m-%d %H:%M:%S')
    i = 0
    for table_name in SENSORS_NAME:
        hum, temp = dht.read_retry(DHT_SENSOR, DHT_PIN[i] )
        if hum:
            insert_record(table_name , str(date), format(temp, '.2f'), format(hum, '.2f'))
        else:
            print(date," error while reading dht22 on pin {}".format(DHT_PIN[i]))
        i += 1
    time.sleep(300) #step queries are set on a base of 5min, DONT CHANGE SLEEP DURATION