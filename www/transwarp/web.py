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

_RE_TZ = re.compile('^([\+\-])([0-9]{1,2})\:([0-9]{1,2})$')

class UTC(datetime.tzinfo):
	def __init__(self,utc):
		utc = str(utc.strip().upper())
		mt = _RE_TZ.match(utc)
		if mt:
			minus = mt.group(1) == '-'
			h = int(mt.group(2))
			m = int(mt.group(3))
			if minus:
				h,m = (-h),(-m)
			self._utcoffset = datetime.timedelta(hours=h,minutes=m)
			self._tzname = 'UTC%s' % utc
		else:
			raise ValueError('bad utc time zone')

	def utcoffset(self,dt):
		return self._utcoffset

	def dst(self,dt):
		return _TIMEDELTA_ZERO

	def tzname(self.dt):
		return self._tzname

	def __str__(self):
		return 'UTC tzinfo object (%s)' % self._tzname

	__repr__ = __str__