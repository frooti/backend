import usb.core
import time
import requests
import os
os.environ["PATH"] += os.pathsep + '/usr/sbin'
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('network')
logger.propagate = False

# create a file handler
handler = RotatingFileHandler('/var/log/backend/network.log', maxBytes=10000000, backupCount=2)
handler.setLevel(logging.DEBUG)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)



PING_URL = 'http://www.google.com'

# find our device
dev_stick = usb.core.find(idVendor=0x12d1, idProduct=0x1446)
dev_modem = usb.core.find(idVendor=0x12d1, idProduct=0x1506)

try: # network ok
	r = requests.head(PING_URL)
	logger.info('network ok.')
except Exception, e: # reconnect
	#os.system('pkill network.py')

	# reset usb
	# if dev_stick:
	# 	dev_stick.reset()
	# elif dev_modem:
	# 	dev_modem.reset()
	# logger.info('usb reset.')
	# time.sleep(3)

	# modem mode
	os.system('usb_modeswitch -c /etc/usb_modeswitch.conf')
	time.sleep(1)
	os.system('usb_modeswitch -c /etc/usb_modeswitch.conf')
	time.sleep(1)
	os.system('usb_modeswitch -c /etc/usb_modeswitch.conf')
	logger.info('modem mode.')
	
	os.system('pkill pppd')

	time.sleep(3)

	# dial up
	os.system('nohup wvdial a &')
	logger.info('dailed up.')
