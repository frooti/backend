import AWSIoTPythonSDK.MQTTLib
import time
import os
import serial
import json
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('config')
logger.propagate = False

# create a file handler
handler = RotatingFileHandler('/var/log/config.log', maxBytes=1000000, backupCount=2)
handler.setLevel(logging.DEBUG)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)

## CONFIG ##
DEVID = None
ROOT = '/home/pi/projects/backend/'
MQTT = None
## CONFIG ##


def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

SETTINGS = {
	"sensor": {
		"s1": {
			"BAUDRATE": None,
			"BYTESIZE": serial.EIGHTBITS,
			"PARITY": serial.PARITY_NONE,
			"STOPBITS": serial.STOPBITS_ONE,
			"XONXOFF": False
		},
	}
}

def loadSettings():
	try:
		f = open('config.json', 'r')
		SETTINGS = json.loads(f.read())
	except:
		pass

def deviceConfig(delta):
	loadSettings()
	# apply delta
	try:
		if 'sensor' in delta:
			for s in delta['sensor']:
				for p in delta['sensor'][s]:
					SETTINGS['sensor'][s][p] = delta['sensor'][s][p]
		else:
			return False
	except Exception, e:
		logger.error('Invalid delta.', exc_info=True)
		return False

	# validation
	try:
		if list(set(['s1'])-set(SETTINGS['sensor'].keys())):
			raise Exception('Invalid sensor name')

		for sensor in SETTINGS['sensor']:		
			baudrate = int(SETTINGS['sensor'][sensor]['BAUDRATE'])
			if baudrate<0:
				raise Exception('Invalid baudrate')
			bytesize = int(SETTINGS['sensor'][sensor]['BYTESIZE'])
			if bytesize not in [5, 6, 7, 8]:
				raise Exception('Invalid bytesize')
			stopbits = int(SETTINGS['sensor'][sensor]['STOPBITS'])
			if stopbits not in [1, 1.5, 2]:
				raise Exception('Invalid stopbits')
			parity = SETTINGS['sensor'][sensor]['PARITY']
			if parity not in ['N', 'E', 'O', 'M', 'S']:
				raise Exception('Invalid parity')
			xonxoff = SETTINGS['sensor'][sensor]['XONXOFF']
			if not isinstance(xonxoff, bool):
				raise Exception('Invalid xonxoff')
	except Exception, e:
		logger.error('error', exc_info=True)
		return False

	f = open('config.json', 'w+')
	f.write(json.dumps(SETTINGS))
	return True

def restartServices():
	pass

def shadowDelta(msg):
	logger.info('msg\n'+str(msg))

def shadowUpdate(srcJSONPayload, srcCallback, srcTimeout):
	pass

def closeConnections():
	try:
		MQTT.disconnect()
	except:
		pass

while True:
	try:
		if os.path.isfile(ROOT+'datalogger/certs/root-CA.crt') and os.path.isfile(ROOT+'datalogger/certs/private.pem.key') and os.path.isfile(ROOT+'datalogger/certs/certificate.pem.crt'):
			if DEVID:
				MQTT = AWSIoTPythonSDK.MQTTLib.AWSIoTMQTTShadowClient(DEVID+'_shadow')
				MQTT.configureEndpoint("a28c009dzez6uk.iot.ap-southeast-1.amazonaws.com", 8883)
				MQTT.configureCredentials(ROOT+"datalogger/certs/root-CA.crt", ROOT+"datalogger/certs/private.pem.key", ROOT+"datalogger/certs/certificate.pem.crt")
				MQTT.connect()
				logger.info('MQTT CONNECTION OK.')

				DeviceShadow = MQTT.createShadowHandlerWithName("device", True)
				# Update Shadow
				loadSettings()
				DeviceShadow.shadowUpdate(json.dumps(SETTINGS), shadowUpdate, 5)
				# Delta Callback
				DeviceShadow.shadowRegisterDeltaCallback(shadowDelta)

			else:
				logger.debug('NO DEVID.')
				time.sleep(1)
		else:
			logger.debug('NO CERTIFICATES.')
			time.sleep(1)

	except Exception,e:
		logger.error('error', exc_info=True)
		time.sleep(1)

	closeConnections()
