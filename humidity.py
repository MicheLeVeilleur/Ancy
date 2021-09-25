import Adafruit_DHT as dht
from time import sleep
from datetime import datetime


DHT_SENSOR = dht.DHT22
DHT_PIN = 10
while True:
    hum,temp = dht.read_retry(DHT_SENSOR,DHT_PIN)
    if hum == None:
        print("failed to retrive temp")
    else:
        print(datetime.now(),"Hum = {0:0.1f}% Temp = {1:0.1f}°C".format(hum,temp))
    sleep(1)
