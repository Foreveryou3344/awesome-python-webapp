#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Fangyu'
# 主要实现了create_engine：创建一个数据库连接实例，并提供connect方法创建数据库连接
# 然后update insert 等语句默认调用_ConnectionCtx上下文，这个上下文主要用于通过_LasyConnection创建_db_ctx数据库连接实例
# 并且每个语句会创建游标，执行完提交并释放游标，和_TransactionCtx上下文的区别就是前者是每条语句提交一次，后者在上下文中的语句执行完才会提交
import time, uuid, functools, threading, logging
engine = None


def next_id(t=None):
	if t is None:
		t = time.time()
	return '%015d%s000' % (int(t*1000), uuid.uuid4().hex)


def _profiling(start, sql=''):
	t = time.time()-start
	if t > 0.1:
		logging.warning('[profiling][db] %s: %s' % (t, sql))
	else:
		logging.info('[profiling][db] %s : %s' % (t, sql))


class _TransactionCtx(object):
	"""docstring for _TransactionCtx"""
	def __enter__(self):
		global _db_ctx
		self.should_close_conn = False
		if not _db_ctx.is_init():
			_db_ctx.init()
			self.should_close_conn = True
		_db_ctx.transactions = _db_ctx.transactions + 1
		logging.info('begin transactions...' if _db_ctx.transactions == 1 else 'join current transaction')
		return self

	def __exit__(self, exctype, excvalue, traceback):
		global _db_ctx
		_db_ctx.transactions = _db_ctx.transactions-1
		try:
			if _db_ctx.transactions == 0:
				if exctype is None:
					self.commit
				else:
					self.rollback()
		finally:
			if self.should_close_conn:
				_db_ctx.cleanup()

	def commit(self):
		global _db_ctx
		logging.info('commit transaction..')
		try:
			_db_ctx.connection.commit()
			logging.info('commit ok')
		except:
			logging.warning('commit failed.try rollback...')
			_db_ctx.connection.rollback()
			logging.warning('rollback ok')
			raise

	def rollback(self):
		global _db_ctx
		logging.warning('rollback transaction')
		_db_ctx.connection.rollback()
		logging.info('rollback ok')


def transaction():
	return _TransactionCtx()


def with_transaction(func):
	@functools.wraps(func)
	def _wrapper(*args, **kw):
		_start = time.time()
		with _TransactionCtx():
			func(*args, **kw)
		_profiling(_start)
	return _wrapper


class _Engine(object):
	def __init__(self, connect):
		self._connect = connect

	def connect(self):
		return self._connect()


class DBError(Exception):
	"""docstring for DBError"""
	pass


def create_engine(user, password, database, host='127.0.0.1', port=3306, **kw):
	import mysql.connector
	global engine
	"""
	global 声明变量是全局变量，没有global不能给函数外的变量赋值，但是可以使用函数外的对象，不过不建议这样做
	"""
	if engine is not None:
		raise DBError('Engine is already initialized.')
	params = dict(user=user, password=password, database=database, host=host, port=port)
	defaults = dict(use_unicode=True, charset='utf8', collation='utf8_general_ci', autocommit=False)
	for k, v in defaults.iteritems():
		params[k] = kw.pop(k, v)
	params.update(kw)
	"""
	dict.pop(key,default) 字典的pop方法在字典中找到key的项删除并返回对应的value，找不到则返回default默认值
	dict.update(kw)将kw字典的内容添加到dict中去，如果key重复，则会覆盖dict的
	"""
	params['buffered'] = True
	# engine存储数据库连接函数的实例，实例中含有connect调用方法
	engine = _Engine(lambda: mysql.connector.connect(**params))
	# hex（）转换为十六进制0x
	logging.info('Init mysql engine <%s> ok' % hex(id(engine)))


class _LasyConnection(object):
	def __init__(self):
		self.connection = None

	def cursor(self):
		if self.connection is None:
			_connection = engine.connect()
			logging.info('[CONNECTION] [OPEN] connection <%s>' % hex(id(_connection)))
			self.connection = _connection
		return self.connection.cursor()

	def commit(self):
		self.connection.commit()

	def rollback(self):
		self.connection.rollback()

	def cleanup(self):
		if self.connection:
			_connection = self.connection
			self.connection = None
			logging.info('[connection][close] connection <%s>' % hex(id(_connection)))
			_connection.close()


class _DbCtx(threading.local):
	# 保证每个线程的数据库连接或者事务是独立的，所以从threading.local派生
	def __init__(self):
		self.connection = None
		self.transactions = 0

	def is_init(self):
		return self.connection is not None

	def init(self):
		logging.info('open lazy connection')
		self.connection = _LasyConnection()
		self.transactions = 0

	def cleanup(self):
		self.connection.cleanup()
		self.connection = None

	def cursor(self):
		return self.connection.cursor()


_db_ctx = _DbCtx()


class _ConnectionCtx(object):
	def __enter__(self):
		global _db_ctx
		self.should_cleanup = False
		if not _db_ctx.is_init():
			_db_ctx.init()
			self.should_cleanup = True
		return self

	def __exit__(self, exctype, excvalue, traceback):
		global _db_ctx
		if self.should_cleanup:
			_db_ctx.cleanup()


"""
with 上下文管理器 应该实现__enter__和__exit__方法，分别在with语句块进入和退出时执行
"""


def with_connection(func):
	@functools.wraps(func)
	def _wrapper(*args, **kw):
		with _ConnectionCtx():
			return func(*args, **kw)
	return _wrapper


@with_connection
def _update(sql, *args):
	global _db_ctx
	cursor = None
	sql = sql.replace('?', '%s')
	logging.info('SQL:%s,args:%s' % (sql, args))
	try:
		cursor = _db_ctx.connection.cursor()
		cursor.execute(sql, args)
		r = cursor.rowcount
		if _db_ctx.transactions == 0:
			logging.info('auto commit')
			_db_ctx.connection.commit()
		return r
	finally:
		if cursor:
			cursor.close()


def update(sql, *args):
	return _update(sql, *args)


def insert(table, **kw):
	cols, args = zip(*kw.iteritems())
	sql = 'insert into `%s` (%s) values (%s)' % (table, ','.join(['`%s`' % col for col in cols]), ','.join(['?' for i in range(len(cols))]))
	return _update(sql, *args)
	"""
	zip 接受多个序列，将对应位置的元素组成tuple，tuple构成一个list
	x=[[1,2,3],[4,5,6],[7,8,9]]
	y=zip(*x)
	print y 
    结果：[(1,4, 7),(2,5,8),(3,6,9)]
	join str.join(sequence) 返回指定字符串连接序列之后的新字符串
	[表达式 for key in list]列表生成式
	"""


class Dict(dict):
	def __init__(self, names=(), values=(), **kw):
		super(Dict, self).__init__(**kw)
		for k, v in zip(names, values):
			self[k] = v

	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

	def __setattr__(self, key, value):
		self[key] = value
	"""
	super 调用父类的方法 py3中用super().xxx代替py2中的super(class,self).xxx
	__getattr__  __setattr__ dict.key时调用
	"""


@with_connection
def _select(sql, first, *args):
	global _db_ctx
	cursor = None
	sql = sql.replace('?', '%s')
	logging.info('sql:%s,args:%s' % (sql, args))
	try:
		cursor = _db_ctx.connection.cursor()
		cursor.execute(sql, args)
		if cursor.description:
			names = [x[0] for x in cursor.description]
		if first:
			values = cursor.fetchone()
			if not values:
				return None
			return Dict(names, values)
		return [Dict(names, x) for x in cursor.fetchall()]
	finally:
		if cursor:
			cursor.close()
        """
        cursor.description 只用于select语句，返回一行的列名，为了Python DB API兼容，返回值为1*7的数组，但事实上后面的六个数为None
        fetchone()  返回单个的元组，也就是一条记录(row)，如果没有结果 则返回 None
        fetchall()  返回多个元组，即返回多个记录(rows),如果没有结果 则返回 ()
        """


def select(sql, *args):
	return _select(sql, False, *args)


class MultiColumnsError(DBError):
	"""docstring for MultiColumnsError"""
	pass


def select_int(sql, *args):
	d= _select(sql, True, *args)
	if len(d) != 1:
		raise MultiColumnsError('Expect only one column')
	return d.values()[0]


def select_one(sql, *args):
	return _select(sql, True, *args)


if __name__ == '__main__':
	logging.basicConfig(level=logging.DEBUG)
	create_engine('root', '123456', 'mypython', '127.0.0.1')
	update('drop table if exists user')
	update('create table user (id int primary key,name text,email text,passwd text,last_modified real)')
	userdic = dict(id=200, name='Wall.E', email='wall.e@test.org', passwd='back-to-earth', last_modified=time.time())
	insert('user', **userdic)
	L = select('select * from user where id=?', 200)
	L[0].email
	select_int('select count(*) from user where email=?', 'notexist@test.org')
	u = select_one('select * from user where id=?', 200)
	u.name
	import doctest
	doctest.testmod()
