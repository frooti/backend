import usb.core
import time
import requests
import os

PING_URL = 'http://www.google.com'

# find our device
dev_stick = usb.core.find(idVendor=0x12d1, idProduct=0x1446)
dev_modem = usb.core.find(idVendor=0x12d1, idProduct=0x1506)

try: # network ok
	r = requests.head(PING_URL)
except Exception, e: # reconnect
	# reset usb
	if dev_stick:
		dev_stick.reset()
	elif dev_modem:
		dev_modem.reset()

	time.sleep(3)

	# modem mode
	os.system('usb_modeswitch -c /etc/usb_modeswitch.conf')

	time.sleep(1)

	os.system('pkill ppp0')

	time.sleep(3)

	# dial up
	os.system('wvdial a &')