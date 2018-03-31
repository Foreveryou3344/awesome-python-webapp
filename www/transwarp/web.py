#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'fangyu'

import types,os,re,cgi,sys,time,datetime,functools,mimetypes,threading,logging,urllib,traceback

try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO

ctx = threading.local()

class Dict(dict):
	def __init__(self,names=(),values=(),**kw):
		super(Dict,self).__init__(**kw)
		for k,v in zip(names,values):
			self[k] = v

	def __getattr__(self,key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(r"'Dict' object has no Attribute '%s'" % key)

	def __setattr__(self,key,value):
		self[key] = value

_TIMEDELTA_ZERO = datetime.timedelta(0)

