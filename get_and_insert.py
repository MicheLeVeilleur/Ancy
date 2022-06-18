import RPi.GPIO as GPIO
import Adafruit_DHT as dht

import sql
#constants of the sensors

DHT_SENSOR = dht.DHT22
DHT_PIN = [9,10,11]
SQL_SENSORS_NAME = ['quatre', 'deux', 'zero']
INSERT_DELAY = 300

def get_and_insert():
    GPIO.setmode(GPIO.BCM)
    for dht_sensor_port in DHT_PIN:
            GPIO.setup(dht_sensor_port, GPIO.IN)
    while True:

        date = sql.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for i,table_name in enumerate(SQL_SENSORS_NAME):
            hum, temp = dht.read_retry(DHT_SENSOR, DHT_PIN[i] )
            if hum:
                sql.insert_record(table_name , str(date), format(temp, '.2f'), format(hum, '.2f'))
                if sql.VERBOSE: print("inserting record on",table_name,"of ",temp,hum)
            else:
                if sql.VERBOSE: print(date," error while reading dht22 on pin {}".format(DHT_PIN[i]))
        sql.time.sleep(INSERT_DELAY)