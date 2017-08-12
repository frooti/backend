import serial
import json

def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

SETTINGS = {
	"sensor": {
		"s1": {
			"BAUDRATE": None,
			"BYTESIZE": serial.EIGHTBITS,
			"PARITY": serial.PARITY_NONE,
			"STOPBITS": serial.STOPBITS_ZERO,
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

def deviceConfig(settings):
	# validation
	try:
		settings = json.loads(settings)

		if list(set(['s1'])-set(settings['sensor'].keys())):
			raise Exception('Invalid sensor name')

		for sensor in settings['sensor']:		
			baudrate = int(settings['sensor'][sensor]['BAUDRATE'])
			if baudrate<0:
				raise Exception('Invalid baudrate')
			bytesize = int(settings['sensor'][sensor]['BYTESIZE'])
			if bytesize not in [5, 6, 7, 8]:
				raise Exception('Invalid bytesize')
			stopbits = int(settings['sensor'][sensor]['STOPBITS'])
			if stopbits not in [1, 1.5, 2]:
				raise Exception('Invalid stopbits')
			parity = settings['sensor'][sensor]['PARITY']
			if parity not in ['N', 'E', 'O', 'M', 'S']:
				raise Exception('Invalid parity')
			xonxoff = settings['sensor'][sensor]['XONXOFF']
			if not isinstance(xonxoff, bool):
				raise Exception('Invalid xonxoff')
	except Exception, e:
		print e
		return False

	f = open('config.json', 'w+')
	f.write(json.dumps(settings))
	return True


