import sqlite3
import time
import serial
import re
import json
import uuid
import logging
from logging.handlers import RotatingFileHandler
import traceback

## CONFIG ##
SERIAL_PORT = '/dev/ttyUSB0'
SENSOR = 1
DEVID = None
BAUDRATE = None
REGEX = None
DB = None
SER = None
## CONFIG ##

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('sensor'+str(SENSOR))

# create a file handler
handler = RotatingFileHandler('sensor'+str(SENSOR)+'.log', maxBytes=1000000, backupCount=2)
handler.setLevel(logging.INFO)

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
		with serial.Serial() as SER:
			SER.port = SERIAL_PORT
			SER.baudrate = BAUDRATE
			SER.bytesize = serial.EIGHTBITS
			SER.parity = serial.PARITY_NONE
			SER.stopbits = serial.STOPBITS_ONE
			SER.timeout = 5

			while not SER.isOpen():
				try:
					## SERIAL CONNECTION ##
					SER.open()
					logger.info('SERIAL CONNECTION OK.')
					
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

					logger.DEBUG(rdata)
					cursor = DB.cursor()
					cursor.execute("INSERT INTO sensor (sensor, timestamp, payload) VALUES ("+str(SENSOR)+", "+str(int(time.time()))+", '"+rdata+"')")
					DB.commit()
	except Exception, e:
		logger.error('error', exc_info=True)
		time.sleep(1)

	## close connections ##
	closeConnections()