import sqlite3
import time
import serial
import re
import json
import uuid
import logging
from logging.handlers import RotatingFileHandler

## CONFIG ##
SETTINGS = {}
try:
	f = open('/home/pi/projects/backend/datalogger/config.json', 'r')
	SETTINGS = json.loads(f.read())
except:
	pass
SERIAL_PORT = '/dev/sensor1'
SENSOR = 's1'
BAUDRATE = SETTINGS.get('sensor', {}).get(SENSOR, {}).get('BAUDRATE', 0)
BYTESIZE = SETTINGS.get('sensor', {}).get(SENSOR, {}).get('BYTESIZE', serial.EIGHTBITS)
PARITY = SETTINGS.get('sensor', {}).get(SENSOR, {}).get('PARITY', serial.PARITY_NONE)
STOPBITS = SETTINGS.get('sensor', {}).get(SENSOR, {}).get('STOPBITS', serial.STOPBITS_ONE)
XONXOFF = SETTINGS.get('sensor', {}).get(SENSOR, {}).get('XONXOFF', False)
REGEX = None
DB = None
SER = None
## CONFIG ##

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('sensor'+str(SENSOR))
logger.propagate = False

# create a file handler
handler = RotatingFileHandler('/var/log/backend/sensor'+str(SENSOR)+'.log', maxBytes=1000000, backupCount=2)
handler.setLevel(logging.DEBUG)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)

def closeConnections():
	try:
		if DB:
			DB.close()
		if SER.isOpen():
			SER.close()
	except:
		pass

## SENSOR CONNECTION ##
while True:
	try:
		if BAUDRATE:
			with serial.Serial() as SER:
				SER.port = SERIAL_PORT
				SER.baudrate = BAUDRATE
				SER.bytesize = BYTESIZE
				SER.parity = PARITY
				SER.stopbits = STOPBITS
				SER.xonxoff = XONXOFF
				SER.timeout = 5

				while not SER.isOpen():
					try:
						## SERIAL CONNECTION ##
						SER.open()
						logger.info('SERIAL CONNECTION OK.')
						
						## DATABASE CONNECTION ##
						DB = sqlite3.connect('/var/sensordata.db')
						cursor = DB.cursor()
						cursor.execute('CREATE TABLE IF NOT EXISTS sensor (sensor CHAR(2) NOT NULL, timestamp INT NOT NULL, payload CHAR(500) NOT NULL);')
						DB.commit()
						try:
							cursor = DB.cursor()
							cursor.execute('CREATE INDEX timestamp ON sensor (timestamp);')
							DB.commit()
						except:
							pass
						logger.info('DB CONNECTION OK.')
					except:
						time.sleep(1)

				while True: # read data
					data = SER.readline()
					if data:
						rdata = [data]
						if REGEX: # extract
							match = re.search(r, data)
							if match:
								rdata = list(match.groups())
						
						rdata = json.dumps(rdata)
						logger.debug(rdata)
						cursor = DB.cursor()
						cursor.execute("INSERT INTO sensor (sensor, timestamp, payload) VALUES ('"+str(SENSOR)+"', "+str(int(time.time()))+", '"+rdata+"')")
						DB.commit()
		else:
			logger.debug('NO BAUDRATE.')
			time.sleep(1)
	except Exception, e:
		logger.error('error', exc_info=True)
		time.sleep(1)

	## close connections ##
	closeConnections()