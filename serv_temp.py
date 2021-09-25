#!/usr/bin/python

import MySQLdb
import time
import RPi.GPIO as GPIO
import datetime
import Adafruit_DHT as dht


hostname = 'localhost'
username = 'pi'
password = 'raspberry'
database = 'Sensors'
sensors = [4, 2, 0]
sensors_name = ['quatre', 'deux', 'zero']
DHT_SENSOR = dht.DHT22
DHT_PIN = [9,10,11]

GPIO.setmode(GPIO.BCM)
for dht_sensor_port in sensors:
	GPIO.setup(dht_sensor_port, GPIO.IN)

def insert_record(table_name, datetime, temp, hum):
	print("inserting record on",table_name,"of ",temp,hum)
	query = "INSERT INTO {} ( date, temp, hum) VALUES (%s, %s, %s)".format(table_name)
	args = ( datetime, temp, hum)
	
	try:
		conn = MySQLdb.connect(host=hostname, user=username, passwd=password, db=database)
		cursor = conn.cursor()
		cursor.execute(query, args )
		conn.commit()

	except Exception as error:
		print(error)

	finally:
		cursor.close()
		conn.close()

#main loop

try:
	while True:
		now = datetime.datetime.now()
		date = now.strftime('%Y-%m-%d %H:%M:%S')
		i = 0
		for table_name in sensors_name:
			hum, temp = dht.read_retry(DHT_SENSOR, DHT_PIN[i] )
			#print(hum,temp)
			if hum:
				insert_record(table_name , str(date), format(temp, '.2f'), format(hum, '.2f'))
			else:
				print(date," error while reading dht22 on pin {}".format(DHT_PIN[i]))
			i += 1
		time.sleep(15)

except (IOError, TypeError ) as e:
	print(e)
	print("Exiting...")

except KeyboardInterrupt:
	print("Stopping..")

finally:
	print("Cleaning up...")
	GPIO.cleanup()
