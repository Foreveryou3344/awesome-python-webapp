#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'ForYou'

from models import User
from transwarp import db
db.create_engine(user='pythonuser', password='pythonuser', database='mypython')

u = User(name='test', email='test@example.com', password='123456', image='about:blank')
u.insert()
print 'new user id', u.id
u1 = User.find_first('where email=?', 'test@example.com')
print 'find user\'s name:', u1.name

u1.delete()
u2 = User.find_first('where email=?', 'test@example.com')
print 'find user', u2
