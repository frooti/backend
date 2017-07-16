from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import sqlite3
from datetime
import time
import json
import uuid
import logging
from logging.handlers import RotatingFileHandler

## CONFIG ##
DEVID = None
CHANNEL = 'device/'+DEVID
DB = None
## CONFIG ##

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('telemetry')

# create a file handler
handler = RotatingFileHandler('telemetry.log', maxBytes=1000000, backupCount=2)
handler.setLevel(logging.INFO)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)

# Telemetry
MQTT = AWSIoTMQTTClient(uuid.uuid4())
MQTT.configureEndpoint("a28c009dzez6uk.iot.ap-southeast-1.amazonaws.com", 8883)
MQTT.configureCredentials("certs/root-CA.crt", "certs/private.pem.key", "certs/certificate.pem.crt")
MQTT.configureOfflinePublishQueueing(100000, MQTT.DROP_OLDEST) # offlne queue
MQTT.configureDrainingFrequency(25)  # Draining: 25 Hz
MQTT.configureConnectDisconnectTimeout(10)  # 10 sec
MQTT.configureMQTTOperationTimeout(5)  # 5 sec
MQTT.connect()

def closeConnections():
	try:
		if DB:
			DB.close()
		MQTT.disconnect()
	except:
		pass

while True:
	try:		
		## DATABASE CONNECTION ##
		DB = sqlite3.connect('sensordata.db')
		cursor = DB.cursor()
		cursor.execute('CREATE TABLE IF NOT EXISTS sensor (sensor INT NOT NULL, timestamp INT NOT NULL, payload CHAR(500) NOT NULL);')
		DB.commit()
		try:
			cursor = DB.cursor()
			cursor.execute('CREATE INDEX timestamp ON sensor (timestamp);')
			DB.commit()
		except:
			pass
		logger.info('DB CONNECTION OK.')

		while True:
			q = conn.execute('SELECT * FROM sensor ORDER BY timestamp LIMIT 100;')
			to_timestamp = 0 # epoch
			from_timestamp = int(time.time())+315360000
			
			for r in q:
				if r[1] > to_timestamp:
					to_timestamp = r[1]
				if from_timestamp > r[1]:
					from_timestamp = r[1]

				payload = {
					'devid': DEVID,
					'sensor': r[0],
					'timestamp': r[1],
					'payload': json.loads(r[2])
				}
				MQTT.publish(CHANNEL, json.dumps(payload), 1)

			if to_timestamp and from_timestamp:
				cursor = DB.cursor()
				cursor.execute('DELETE FROM sensor WHERE timestamp>='+str(from_timestamp)+'AND timestamp<='+str(to_timestamp)+';')
				DB.commit()
	except Exception,e:
		logger.error('error', exc_info=True)
		time.sleep(1)

	closeConnections()