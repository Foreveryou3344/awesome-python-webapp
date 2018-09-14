#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'ForYou'

from transwarp.web import get, view, post, ctx
from models import User, Blog
from apis import api, APIValueError, APIError
import re


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


@view('register.html')
@get('/register')
def register():
	return dict()

@api
@get('/api/users')
def api_get_users():
	users = User.find_all('order by created_at desc')
	return dict(users=users)


_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_MD5 = re.compile(r'^[0-9a-f]{32}$')


@api
@post('/api/users')
def register_user():
	i = ctx.request.input(name='', email='', password='')
	name = i.name.strip()
	email = i.email.strip().lower()
	password = i.password
	if not name:
		raise APIValueError('name')
	if not email or not _RE_EMAIL.match(email):
		raise APIValueError('email')
	if not password or not _RE_MD5.match(password):
		raise APIValueError('password')
	user = User.find_first('where email=?', email)
	if user:
		raise APIError('REGISTER:failed', 'email', 'email is already in use')
	user = User(name=name, email=email, password=password, image='about:blank')
	user.insert()
	return user
