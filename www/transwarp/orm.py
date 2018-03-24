#!/usr/bin/env python
# _*_ coding: utf-8 _*_
import db
import time
import logging

class Model(dict):
	__metaclass__ = ModelMetaclass
	def __init__(self,**kw):
		super(Model,self).__init__(**kw)
	def __getattr__(self,key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(r"'Dict' object has no attribute '%s'" % key)
	def __serattr__(self,key,value):
		self[key]=value
	@classmethod
	def get(cls,pk):
		d=db.select_one('select * from %s where %s=?'%(cls.__table__,cls.__primary_key__.name),pk)
		return cls(**d) if d else None

	@classmethod
	def find_first(cls,where,*args):
		d=db.select_one('select * from %s %s' (cls.__table__,where),*args)
		return cls(**d) if d else None

	@classmethod
	def find_all(cls,*args):
		L=db.select('select * from `%s`' %cls.__table__)
		return [cls(**d) for d in L]

	@classmethod
	def find_by(cls,where,*args):
		L=db.select('select * from `%s` %s' %(cls.__table__,where),*args)
		return [cls(**d) for d in L]

	@classmethod
	def count_all(cls):
		return db.select ('select count(`%s`) from `%s`' %(cls.__primary_key__.name,cls.__table__))

	@classmethod
	def count_by(cls,where,*args):
		return db.select_int('select count(`%s`) from `%s` %s'% (cls.__primary_key__.name,cls.__table__,where),*args)

	def update(self):
		self.pre_update and self.pre_update()
		L=[]
		args=[]
		for k,v in self.__mapings__.iteritems():
			if v.updatable:
				if hasattr(self,k):
					arg=getattr(self,k)
				else:
					arg = v.default
					setattr(self,k,arg)
				L.append('`%s`=?'%k)
				args.append(arg)
		pk = self.__primary_key__.name
		args.append(getattr(self,pk))
		db.update('update `%s` set %s where %s = ?' % (self.__table__, ','join(L),pk),*args)
		return self
	def delete(self):
		self.pre_delete and self.pre_delete()
		pk = self.__primary_key__.name
		args = (getattr(self,pk),)
		db.update('delete from `%s` where `%s`= ?' % (self.__table__,pk),*args)
		return self
	def insert(self):
		self.pre_insert and self.pre_insert()
		params ={}
		for k,v in self.__mapings__.iteritems():
			if v.insertable:
				if not hasattr(self,k):
					setattr(self,k,v.default)
				params[v.name] = getattr(self,k)
		db.insert('%s' % self.__table__,**params)
		return self


if __name__ == '__main__':
	logging.basicConfig(lecel=logging.DEBUG)
	db.create_engine('root','password','mypython','127.0.0.1')
	db.update('drop table if exists user')
	db.update('create table user (id int primary key,name text,email text,passwd text,last_modified real)')
	import doctest
	doctest.testmod()