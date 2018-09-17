#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 提供字典转json服务 以及错误定义
__author__ = 'ForYou'

import json
import functools
from transwarp.web import ctx


class APIError(StandardError):
	def __init__(self, error, data='', message=''):
		super(APIError, self).__init__(message)
		self.error = error
		self.data = data
		self.message = message


class APIValueError(APIError):  # 变量无效
	def __init__(self, field, message=''):
		super(APIValueError, self).__init__('value:invalid', field, message)


class APIPermissionError(APIError):  # 权限错误
	def __init__(self, message=''):
		super(APIPermissionError, self).__init__('permission:forbidden', 'permission', message)


def api(func):
	@functools.wraps(func)
	def _wrapper(*args, **kw):
		try:
			r = json.dumps(func(*args, **kw))
		except APIError, e:
			r = json.dumps(dict(error=e.error, data=e.data, message=e.message))
		except Exception, e:
			r = json.dumps(dict(error='internalerror', data=e.__class__.__name__, message=e.message))
		ctx.response.content_type = 'application/json'
		return r
	return _wrapper
