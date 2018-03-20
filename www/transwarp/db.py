#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__='Fangyu'

import time, uuid, functools, threading, logging
engine=None
def next_id(t=None):
	if t is None:
		t=time.time()
	return '%015d%s000' %(int(t*1000),uuid.uuid4().hex)

def _profiling(start,sql=''):
	t=time.time()-start
	if t>0.1:
		logging.warning('[profiling][db] %s: %s' % (t,sql))
	else:
		logging.info('[profiling][db] %s : %s' % (t,sql))

def create_engine(user,password,database,host='127.0.0.1',port=3306,**kw):
	import mysql.connector
	global engine
	if engine is not None:
		raise DBError('Engine is already initialized.')
	params =dict(user=user,password=password,database=database,host=host,port=port)
	defaults =dict(use_unicode=True,charset='utf-8',collation='utf8_general_ci',autocommit=False)
	for k,v in defaults.iteritems():
		params[k]=kw.pop(k,v)
	params.update(kw)
	params.['buffered']=True
	engine=_Engine(lambda:mysql.connector.connect(**params))
	logging.info('Init mysql engine <%s> ok' % hex(id(engine)))
class _Engine(object):
	def __init__(self,connect):
		self._connect=connect
	def connect(self):
		return self._connect()

def connection():
	return _ConnectionCtx()

