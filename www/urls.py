#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'ForYou'

from transwarp.web import get, view
from models import User, Blog
from apis import api


@view('test_user.html')
@get('/test')
def test_users():
	users = User.find_all()
	return dict(users=users)


@view('blogs.html')
@get('/')
def index():
	blogs = Blog.find_all()
	user = User.find_first('where email=?', 'test@example.com')
	return dict(blogs=blogs, user=user)


@api
@get('/api/users')
def api_get_users():
	users = User.find_all('order by created_at desc')
	return dict(users=users)
