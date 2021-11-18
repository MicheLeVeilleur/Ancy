import RPi.GPIO as GPIO
import Adafruit_DHT as dht
import MySQLdb
import time
from datetime import datetime

from sys import argv

args = argv
if len(args) > 1:
    if "-v" in args:
        verbose = True
else:
    verbose = False


# constants of connection to MariaDB

SQL_HOSTNAME = 'localhost'
SQL_USERNAME = 'pi'
SQL_PASSWORD = 'raspberry'
SQL_DATABASE = 'Sensors'
SQL_SENSORS_NAME = ['quatre', 'deux', 'zero']
INSERT_DELAY = 300

#constants of the sensors

DHT_SENSOR = dht.DHT22
DHT_PIN = [9,10,11]

def send_query(query,args,return_result = False):
	try:
		conn = MySQLdb.connect(host=SQL_HOSTNAME, user=SQL_USERNAME, passwd=SQL_PASSWORD, db=SQL_DATABASE)
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
    if verbose: 
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


def get_and_insert():
    GPIO.setmode(GPIO.BCM)
    for dht_sensor_port in DHT_PIN:
	    GPIO.setup(dht_sensor_port, GPIO.IN)
    now = datetime.now()
    date = now.strftime('%Y-%m-%d %H:%M:%S')
    i = 0
    for table_name in SQL_SENSORS_NAME:
        hum, temp = dht.read_retry(DHT_SENSOR, DHT_PIN[i] )
        if hum:
            insert_record(table_name , str(date), format(temp, '.2f'), format(hum, '.2f'))
        else:
            if verbose:
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
