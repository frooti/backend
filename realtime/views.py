# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.
DEFAULT_RESPONSE = '{"status":false, "msg": "bad request."}'

from django.http import HttpResponse
import boto3
import redis
import json
import uuid
import time
from decimal import Decimal

# utilities
def default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

dynamodb = boto3.resource('dynamodb')
iot = boto3.client('iot')
iotdata = boto3.client('iot-data')

USER = dynamodb.Table('user')
PROJECT = dynamodb.Table('project')
DEVICE = dynamodb.Table('device')
TIMESERIES = dynamodb.Table('timeseries')

# redis
HOST = 'redis.cntdpk.0001.apse1.cache.amazonaws.com'
PORT = 6379
REDIS = redis.Redis(host=HOST, port=PORT)

## HELPERS ##
def getDeviceInfo(devices):
	data = []
	if isinstance(devices, list):
		keys = []
		for d in devices:
			keys.append({'devid': d})

		if keys:
			requestItems = {'device': {'Keys': keys}}
			q = dynamodb.meta.client.batch_get_item(RequestItems=requestItems)

			if q['Responses'].get('device', None):
				for d in q['Responses']['device']:
					data.append(d)

	return data

def getProjectData(projects):
	data = []
	if isinstance(projects, list):
		keys = []
		for p in projects:
			keys.append({'pid': p})
		
		if keys:
			requestItems = {'project': {'Keys': keys}}
			q = dynamodb.meta.client.batch_get_item(RequestItems=requestItems)

			if q['Responses'].get('project', None):
				for p in q['Responses']['project']:
					data.append(p)
			for p in data:
				p['devices'] = getDeviceInfo(p.get('devices', []))

	return data

def getDeviceData(devices):
	data = []
	if isinstance(devices, list):
		keys = []
		
		for d in devices:
			keys.append({'devid': d})

		if keys:
			requestItems = {'device': {'Keys': keys}}
			q = dynamodb.meta.client.batch_get_item(RequestItems=requestItems)

		if q['Responses'].get('device', None):
			for d in q['Responses']['device']:
				data.append(d)

		for device in data:
			devid = device['devid']
			sensor_config = device['sensor_config']

			for sensor_no in sensor_config:
				sid = sensor_config[sensor_no]['sid']

				for vid in sensor_config[sensor_no].get('variables', None):
					key = devid+'_'+sid+'_'+vid
					r = REDIS.zrevrange(key, 0, -1)
					if r:
						sensor_config[sensor_no]['variables'][vid]['data'] = r
	return data

def logindata(user):
	data = {}
	if user:
		data['email'] = user.get('email', None)
		data['organisation'] = user.get('organisation', None)
		projects = list(set(user.get('projects', []).get('owner', [])+user.get('projects', []).get('access', [])))
		data['projects'] = getProjectData(projects)
	return data
## HELPERS ##

def login(request):
	res = json.loads(DEFAULT_RESPONSE)
	email = request.GET.get('email', None)
	password = request.GET.get('password', None)
	
	if email and password:
		try:
			q = USER.get_item(Key={'email':email})
			user = q.get('Item', None)
			if user:
				if password == user.get('password', None):
					res['status'] = True
					res['msg'] = 'success'
					res['data'] = logindata(user)
				else:
					res['status'] = False
					res['msg'] = 'Email/Password is wrong.'
			else:
				res['status'] = False
				res['msg'] = 'Email/Password is wrong.'
		except Exception, e:
			print e
			res['status'] = False
			res['msg'] = 'Someting went wrong.'

	return HttpResponse(json.dumps(res, default=default))

def logout(request):
	res = json.loads(DEFAULT_RESPONSE)
	return HttpResponse(json.dumps(res, default=default))

def project(request):
	res = json.loads(DEFAULT_RESPONSE)
	pid = request.GET.get('pid', None)
	
	if pid:
		try:
			res['status'] = True
			res['msg'] = 'success'
 			res['data'] = getProjectData([pid])[0]  
		except Exception, e:
			print e
			res['status'] = False
			res['msg'] = 'Someting went wrong.'
	return HttpResponse(json.dumps(res, default=default))

def device(request):
	res = json.loads(DEFAULT_RESPONSE)
	devid = request.GET.get('devid', None)
	
	if devid:
		try:
			res['status'] = True
			res['msg'] = 'success'
 			res['data'] = getDeviceData([devid])[0]
		except Exception, e:
			print e
			res['status'] = False
			res['msg'] = 'Someting went wrong.'
	return HttpResponse(json.dumps(res, default=default))

def registerDevice(request):
	res = json.loads(DEFAULT_RESPONSE)
	devid = str(uuid.uuid4())
	
	pid = request.GET.get('pid', None)
	name = request.GET.get('name', None)
	organisation = request.GET.get('organisation', None)
	description = request.GET.get('description', None)

	if pid and name and organisation and description: # TRANSACTION
		try:
			item = {}
			item['devid'] = devid
			item['pid'] = pid
			item['name'] = name
			item['organisation'] = organisation
			item['description'] = description
			item['created_at'] = int(time.time())
			DEVICE.put_item(Item=item)
			
			# create IOT thing
			iot.create_thing(
				thingName=devid,
				attributePayload={
					'attributes': {
						'organisation': organisation,
						'pid': pid
					}
				}
			)

			# # upate device shadow
			# payload = {
			# 	"state": {
			# 		"desired": {
			# 			"sid": sid,
			# 			"regex": [],
			# 			"baudrate": [],
			# 		} 
			# 	}
			# }
			# iotdata.update_thing_shadow(thingName=devid, payload=json.dumps(payload))

			# update project devices
			PROJECT.update_item(
				Key={'pid': pid},
				AttributeUpdates={
					'devices': {
						'Value': [devid],
						'Action': 'ADD'
					}
				}
			)

			res['status'] = True
			res['msg'] = 'success'
			res['data'] = {'devid': devid}
		except Exception, e:
			print e
			res['status'] = False
			res['msg'] = 'Someting went wrong.'
	return HttpResponse(json.dumps(res, default=default))