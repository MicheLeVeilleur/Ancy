# Ancy

Python program which :
1. retrieve temperature and humidity from DHT22 sensors then insert them in a mariaDB server
2. run a HTTP server where displays graphs of sensors
3. run a thermostat algorithm getting temperature and humidity from the SQL server and sending calls to the connected circuit-breaker Legrand API
