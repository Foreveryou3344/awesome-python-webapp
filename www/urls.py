#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'fangyu'

import logging
from transwarp.web import get, view
from models import User,Blog,Comment


@view('test_user.html')
@get('/')
def test_users():
	users = User.find_all()
	return dict(users=users)
