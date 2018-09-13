#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
