#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 提供字典转json服务 以及错误定义
__author__ = 'ForYou'

import json
import functools
from transwarp.web import ctx


# 通过传入总明细数 当前页 每页明细数 来计算 总页数 当前页首条明细的位置 查询时限制条数 是否有上一页下一页
class Page(object):
	def __init__(self, item_count, page_index=1, page_size=10):
		self.item_count = item_count
		self.page_size = page_size
		self.page_count = item_count // page_size + (1 if item_count % page_size > 0 else 0)
		if (item_count == 0) or (page_index < 1) or (page_index > self.page_count):
			self.offset = 0
			self.limit = 0
			self.page_index = 1
		else:
			self.page_index = page_index
			self.offset = self.page_size * (page_index - 1)
			self.limit = self.page_size
		self.has_next = self.page_index < self.page_count
		self.has_previous = self.page_index > 1

	def __str__(self):
		return 'item_count: %s,page_count: %s,page_index: %s,offset: %s,limit: %s' % \
			(self.item_count, self.page_count, self.page_index, self.offset, self.limit)

	__repr__ = __str__


def _dump(obj):  # Page实例转换成json返回
	if isinstance(obj, Page):
		return {
			'page_index': obj.page_index,
			'page_count': obj.page_count,
			'item_count': obj.item_count,
			'has_next': obj.has_next,
			'has_previous': obj.has_previous
		}
	raise TypeError('%s is not JSON serializable' % obj)


def dumps(obj):
	return json.dumps(obj, default=_dump)


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
			r = dumps(func(*args, **kw))
		except APIError, e:
			r = json.dumps(dict(error=e.error, data=e.data, message=e.message))
		except Exception, e:
			r = json.dumps(dict(error='internalerror', data=e.__class__.__name__, message=e.message))
		ctx.response.content_type = 'application/json'
		return r
	return _wrapper
