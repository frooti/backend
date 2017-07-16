from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import sqlite3
from datetime
import time
import json
import uuid

# config
DEVID = None
CHANNEL = 'device/'+DEVID

# Telemetry
MQTT = AWSIoTMQTTClient(uuid.uuid4())
MQTT.configureEndpoint("a28c009dzez6uk.iot.ap-southeast-1.amazonaws.com", 8883)
MQTT.configureCredentials("certs/root-CA.crt", "certs/2d1ec1d18e-private.pem.key", "certs/2d1ec1d18e-certificate.pem.crt")
MQTT.configureOfflinePublishQueueing(100000, MQTT.DROP_OLDEST) # No offlne queue
MQTT.configureDrainingFrequency(2)  # Draining: 2 Hz
MQTT.configureConnectDisconnectTimeout(10)  # 10 sec
MQTT.configureMQTTOperationTimeout(5)  # 5 sec
MQTT.connect()

while True:
	try:		
		## DATABASE CONNECTION ##
		conn = sqlite3.connect('sensordata.db')

		cursor = conn.cursor()
		cursor.execute('CREATE TABLE IF NOT EXISTS sensor (SENSOR INT NOT NULL, TIMESTAMP INT NOT NULL, DATA CHAR(500) NOT NULL); CREATE INDEX timestamp ON sensor (timestamp);')
		conn.commit()

		q = conn.execute('SELECT * FROM sensor ORDER BY timestamp LIMIT 100;')
		to_timestamp = 0 # epoch
		
		for r in q:
			if r[1] > to_timestamp:
				to_timestamp = r[1]

			payload = {
				'devid': DEVID,
				'sensor': str(r[0]),
				'timestamp': r[1],
				'variables': json.loads(r[2])
			}
			MQTT.publish(CHANNEL, json.dumps(payload), 1)

		if to_timestamp:
			cursor = conn.cursor()
			cursor.execute('DELETE FROM sensor WHERE timestamp<='+str(to_timestamp)+';')
			conn.commit()
	except Exception,e:
		print e

conn.close()
MQTT.disconnect()