import RPi.GPIO as GPIO
import Adafruit_DHT as dht

import sql
#constants of the sensors

DHT_SENSOR = dht.DHT22
DHT_PIN = [9,10,11]
SQL_SENSORS_NAME = ['quatre', 'deux', 'zero']
INSERT_DELAY = 300

def get_and_insert():
    while True:
        GPIO.setmode(GPIO.BCM)
        for dht_sensor_port in DHT_PIN:
            GPIO.setup(dht_sensor_port, GPIO.IN)
        now = sql.datetime.now()
        date = now.strftime('%Y-%m-%d %H:%M:%S')
        i = 0
        for table_name in SQL_SENSORS_NAME:
            hum, temp = dht.read_retry(DHT_SENSOR, DHT_PIN[i] )
            if hum:
                sql.insert_record(table_name , str(date), format(temp, '.2f'), format(hum, '.2f'))
            else:
                if sql.VERBOSE:
                    print(date," error while reading dht22 on pin {}".format(DHT_PIN[i]))
            i += 1
        sql.time.sleep(INSERT_DELAY)