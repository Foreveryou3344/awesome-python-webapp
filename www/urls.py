#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'ForYou'

import logging
from transwarp.web import get, view
from models import User,Blog,Comment


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
