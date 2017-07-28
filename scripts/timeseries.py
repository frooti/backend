import boto3
import redis
import json
import re

# dynamodb
dynamodb = boto3.resource('dynamodb')
PROJECT = dynamodb.Table('project')
DEVICE = dynamodb.Table('device')
TIMESERIES = dynamodb.Table('timeseries')

# redis
HOST = 'redis.cntdpk.0001.apse1.cache.amazonaws.com'
PORT = 6379
REDIS = redis.Redis(host=HOST, port=PORT)

# sqs
sqs = boto3.resource('sqs')
timeseries = sqs.get_queue_by_name(QueueName='timeseries')

def getSensorConfig(devid):
	sensor_config = REDIS.get(devid+'_sensor_config')
	
	if sensor_config:
		sensor_config = json.loads(sensor_config)
	else:
		device = DEVICE.get_item(Key={'devid':devid})
		if 'Item' in device:
			sensor_config = device['Item'].get('sensor_config', None)
			REDIS.set(devid+'_sensor_config', json.dumps(sensor_config))
	return sensor_config


while True:
	for message in timeseries.receive_messages(WaitTimeSeconds=10):
		try:
			payload = json.loads(message.body)
			
			devid = payload.get('devid', None)
			sensor = str(payload.get('sensor', 0))
			timestamp = int(payload.get('timestamp', 0))
			payload = payload.get('payload', '')
			if payload:
				payload = str(payload[0])
			
			
			sensor_config = getSensorConfig(devid)
			sensor_config = sensor_config.get(sensor, None)
			
			if sensor_config and sensor_config['record']:
				sid = sensor_config['sid']
				values = []
				if sensor_config['regex']:
					match = re.search(re.compile(sensor_config['regex']), payload)
					if match:
						values = list(match.groups())

				for vid, value in enumerate(values):
					vid = str('v'+vid+1)
					variable_config = sensor_config['variables'][vid]
					
					if value and variable_config:
						if variable_config['type'] == 'number':
							value = float(value)
							key = devid+'_'+sid+'_'+vid
							# redis
							REDIS.zadd(key, str(value)+'::'+str(timestamp), timestamp)
							# dynamoDB
							item = {}
							item['devid_sid_vid'] = key
							item['timestamp'] = timestamp
							item['value'] = value
							TIMESERIES.put_item(Item=item)
			message.delete()
		except Exception, e:
			print e