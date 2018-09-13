#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'ForYou'

from models import User, Blog
from transwarp import db
db.create_engine(user='pythonuser', password='pythonuser', database='mypython')

# u = User(name='test3', email='test3@example.com', password='123456', image='about:blank')
# u.insert()
# print 'new user id', u.id
# u1 = User.find_first('where email=?', 'test@example.com')
# print 'find user\'s name:', u1.name

# u1.delete()
u2 = User.find_first('where email=?', 'test@example.com')
uid = u2.id

b1 = Blog(user_id=uid, user_name=u2.name, user_image=u2.image, name='日志1', summary='日志1', content='日志1详情')
b2 = Blog(user_id=uid, user_name=u2.name, user_image=u2.image, name='日志2', summary='日志2', content='日志2详情')
b3 = Blog(user_id=uid, user_name=u2.name, user_image=u2.image, name='日志3', summary='日志3', content='日志3详情')
b1.insert()
b2.insert()
b3.insert()
