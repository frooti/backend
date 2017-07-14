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

for message in queue.receive_messages(WaitTimeSeconds=10):
	print message.body
	message.delete()