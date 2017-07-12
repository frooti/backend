# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.
DEFAULT_RESPONSE = '{"status":false, "msg": "bad request."}'

from django.http import HttpResponse
import boto3
import json

dynamodb = boto3.resource('dynamodb')

USER = dynamodb.Table('user')
PROJECT = dynamodb.Table('project')
DEVICE = dynamodb.Table('device')
TIMESERIES = dynamodb.Table('timeseries')

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

	return HttpResponse(json.dumps(res))

def logout(request):
	res = json.loads(DEFAULT_RESPONSE)
	return HttpResponse(json.dumps(res))

def logindata(user):
	data = {}
	if user:
		data['email'] = user.get('email', None)
		data['organisation'] = user.get('organisation', None)
		data['projects'] = user.get('projects', {})
	return data


