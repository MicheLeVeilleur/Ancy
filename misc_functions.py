from datetime import datetime
import MySQLdb
import time
from http.server import BaseHTTPRequestHandler
import matplotlib.pyplot as plt
import Adafruit_DHT as dht
import RPi.GPIO as GPIO
import os

# constants of connection to MariaDB

HOSTNAME = 'localhost'
USERNAME = 'pi'
PASSWORD = 'raspberry'
DATABASE = 'Sensors'
SENSORS_NAME = ['quatre', 'deux', 'zero']

#constants of the sensors

DHT_SENSOR = dht.DHT22
DHT_PIN = [9,10,11]
INSERT_DELAY = 300

def make_custom_handler(q):
    class handler(BaseHTTPRequestHandler):
        t_status = False
        def __init__(self, *args, **kwargs):
             super(handler, self).__init__(*args, **kwargs)
            
        def do_GET(self):
            self.send_response(200)

            if self.path.endswith(".png"):
                mimetype='image/png'
            elif self.path.endswith(".mp4"):
                mimetype = 'video/mp4'
            else:
                mimetype='text/html'
            self.send_header('Content-type',mimetype)
            self.end_headers()


            if self.path == "/":
                for filename in os.listdir(os.path.abspath('graphs')):
                    file_path = os.path.join(os.path.abspath('graphs'), filename)
                    os.unlink(file_path)

                c_variables = get_last_record('deux')
                checked = (lambda x:["checked",""] if x else ["","checked"])(self.t_status)

                display = '<html><body>'
                display  += '<body><img src=\"/graphs/quatre_last.png\"width><img src=\"/graphs/deux_last.png\"><img src=\"/graphs/zero_last.png\">'

                display += '<p><h3>Current temperature is : {} <form method="POST" enctype="multipart/form-data" action="/">'.format(c_variables)
                display += '<div><input name= "OnOff" type="radio" value="On"{}>ON</div>'.format(checked[0])
                display += '<div><input name= "OnOff" type="radio" value="Off"{}>OFF</div>'.format(checked[1])
                display += '<input type="submit"> </form> <br/>'

                display += 'Current temperature is : {} <form method="POST" enctype="multipart/form-data" action="/">'.format(c_variables)
                display += '<input type="datetime-local" id="date-inf" name="date-inf" value="2021-09-10T00:00"> '
                display += '<input type="datetime-local" id="date-sup" name="date-sup" value="2021-10-01T00:00"> '
                display += ' <input type="submit"> </form> <br/>'

                display += ' <a href="/graphs/quatre_last_step_3.png">12 dernieres heures quatre</a> <a href="/graphs/deux_last_step_3.png">12 dernieres heures deux</a> '
                display += ' <a href="/graphs/zero_last_step_3.png">12 dernieres heures zero</a> <br/>'
                
                display += ' <a href="/graphs/quatre_last_step_12.png">50 dernieres heures quatre</a> <a href="/graphs/deux_last_step_12.png">50 dernieres heures deux</a> '
                display += ' <a href="/graphs/zero_last_step_12.png">50 dernieres heures zero</a> <br/>'

                display += '</h3></p></body></html>'

                self.wfile.write(bytes(display, "utf8"))
            
            elif 'last' in self.path:
                split = self.path.split('_')
                if len(split) == 2:
                    table_name = split[0][8:]
                    make_recent_plot(table_name,50)
                    with open('graphs/{}_last.png'.format(table_name),'rb') as f:
                        self.wfile.write(f.read())
                
                elif len(split) == 4:
                    table_name = split[0][8:]
                    step = int(split[3].split(".")[0])
                    make_recent_step_plots(table_name,step,50)
                    with open('graphs/{0}_last_step_{1}.png'.format(table_name,step),'rb') as f:
                        self.wfile.write(f.read())
            
            elif 'period' in self.path:
                split = self.path.split('_')
                date_sup,date_inf = split[2], split[3][:-4]
                table_name = split[0][1:]
                make_period_plot(table_name,date_sup,date_inf,100)
                with open('graphs/{0}_period_{1}.png'.format(table_name,date_sup),'rb') as f:
                    self.wfile.write(f.read())
            
            elif 'anniv' in self.path:
                with open('Papa_anniv.mp4','rb') as f:
                    self.wfile.write(f.read())


        def do_POST(self):
            
            content_len = int(self.headers.get('Content-Length'))
            post_body = str(self.rfile.read(content_len))
            if  "OnOff" in post_body:
                if 'On\r' in post_body:
                    q.put(True)
                else:
                    q.put(False)
            
            else:
                date_inf = "20"+post_body.split("\\n20")[1][:14].replace('T',' ')+":00"
                date_sup = "20"+post_body.split("\\n20")[2][:14].replace('T',' ')+":00"
                self.path = "/deux_period_{0}_{1}.png".format(date_sup,date_inf)
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
    query = "SELECT * FROM (SELECT date, temp, hum FROM {0}\
            ORDER BY TIMEDIFF('{1}', date)\
            LIMIT {2}) as foo\
            ORDER BY foo.date ASC".format(table_name,datetime,limit)
    return send_query(query, None, return_result=True)

def get_step_records(table_name, datetime, step, limit):
    query = "CREATE SEQUENCE s START WITH 1 INCREMENT BY 1"
    send_query(query, None)
    time.sleep(1)
    query = "SELECT date,temp,hum FROM \
                (SELECT date,temp,hum, NEXTVAL(s) as a \
                FROM {2} HAVING a % {0} = 0 \
                ORDER BY TIMEDIFF('{3}', date) LIMIT {1} ) AS T\
            ORDER BY T.date ASC".format(step,limit,table_name,datetime)
    print(query)
    result =  send_query(query, None, return_result=True)
    query = "DROP SEQUENCE s"
    time.sleep(1)
    send_query(query, None)
    return result

def get_last_record(table_name):
	now = datetime.now()
	date = now.strftime('%Y-%m-%d %H:%M:%S')
	return get_record(table_name, date)

def get_last_records(table_name,limit):
	now = datetime.now()
	date = now.strftime('%Y-%m-%d %H:%M:%S')
	return get_records(table_name, date,limit)

def get_last_step_records(table_name, step, limit):
    now = datetime.now()
    date = now.strftime('%Y-%m-%d %H:%M:%S')
    return get_step_records(table_name, date,step,limit)

def make_plot(tuples):
    dates_full  = []
    temp = []
    hum = []
    for line in tuples:
        dates_full.append(line[0])
        temp.append(line[1])
        hum.append(line[2])
    fig, (ax1, ax2) = plt.subplots(2, sharex=True)
    ax1.plot(dates_full, temp)
    ax2.plot(dates_full, hum)
    plt.xticks(dates_full,rotation=90)
    ax1.set_title('Temperature')
    ax2.set_title('Humidite')
    plt.ylim(bottom=0)
    plt.ylim(top=100)
    return fig, (ax1,ax2)

def make_recent_plot(table_name, limit):
    tuples = get_last_records(table_name,limit)
    fig,(ax1,ax2) = make_plot(tuples)
    fig.suptitle('{0} dernières mesures de {1}'.format(limit,table_name))
    plt.savefig('graphs/{}_last.png'.format(table_name),dpi=70,bbox_inches='tight')


def make_recent_step_plots(table_name, step, limit):
    tuples = get_last_step_records(table_name,step,limit)
    fig, (ax1, ax2) = make_plot(tuples)
    fig.suptitle('{0} dernières heures de {1}'.format(round(limit*step*INSERT_DELAY/3600),table_name))
    plt.savefig('graphs/{0}_last_step_{1}.png'.format(table_name,step),dpi=100,bbox_inches='tight')

def make_period_plot(table_name, date_sup, date_inf, limit):
    date_sup_t = datetime. strptime(date_sup, '%Y-%m-%d %H:%M:%S')
    date_inf_t = datetime. strptime(date_inf, '%Y-%m-%d %H:%M:%S')
    diff_s = (date_sup_t - date_inf_t).total_seconds()
    print(diff_s/INSERT_DELAY)
    step = round(diff_s / INSERT_DELAY /limit)

    tuples = get_step_records(table_name,date_sup,step,limit)
    fig, (ax1, ax2) = make_plot(tuples)
    m, d, h = s_to_m_d_h(limit*step*INSERT_DELAY)
    fig.suptitle('{0}m, {1}d, {2}h de {3}'.format(m,d,h,table_name))
    plt.savefig('graphs/{0}_period_{1}.png'.format(table_name,date_sup),dpi=100,bbox_inches='tight')

def get_and_insert():
    GPIO.setmode(GPIO.BCM)
    for dht_sensor_port in DHT_PIN:
	    GPIO.setup(dht_sensor_port, GPIO.IN)
    now = datetime.now()
    date = now.strftime('%Y-%m-%d %H:%M:%S')
    i = 0
    for table_name in SENSORS_NAME:
        hum, temp = dht.read_retry(DHT_SENSOR, DHT_PIN[i] )
        if hum:
            insert_record(table_name , str(date), format(temp, '.2f'), format(hum, '.2f'))
        else:
            print(date," error while reading dht22 on pin {}".format(DHT_PIN[i]))
        i += 1
    time.sleep(INSERT_DELAY)

def s_to_m_d_h(seconds):
    hours = seconds // 3600

    days = hours // 24
    hours -= days * 24

    months = days // 30
    days -= months * 30

    return int(months), int(days), int(hours)
