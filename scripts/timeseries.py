import boto3
import redis
import json

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
			if sensor_config:
				sensor_config = json.loads(sensor_config)
			REDIS.set(devid+'_sensor_config', json.dumps(sensor_config))
	return sensor_config


while True:
	for message in timeseries.receive_messages(WaitTimeSeconds=10):
		try:
			payload = json.loads(message.body)
			devid = payload.get('devid', None)
			sensor = int(payload.get('sensor', 0))
			variables = payload.get('variables', [])
			timestamp = payload.get('timestamp', 0)

			sensor_config = getSensorConfig(devid)
			sensor_config = sensor_config.get(sensor, None)
			
			if sensor_config and sensor_config['record']:
				sid = sensor_config['sid']
				for vid, d in enumerate(variables):
					if d and sensor_config['variables'][vid]:
						if sensor_config['variables'][vid]['type'] == 'number':
							d = float(d)
							key = devid+'_'+sid+'_'+vid
							REDIS.ZADD(key, timestamp, d)

			message.delete()
		except Exception, e:
			print 