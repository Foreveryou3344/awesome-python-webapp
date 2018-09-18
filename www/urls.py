#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'ForYou'

from transwarp.web import get, view, post, ctx, interceptor, seeother
from models import User, Blog
from apis import api, APIValueError, APIError, APIPermissionError, Page
import re
import time
import hashlib
import logging
from config import configs


_COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.session.secret


def _get_page_index():
	page_index = 1
	try:
		page_index = int(ctx.request.get('page', '1'))  # 取url后接的参数
	except ValueError:
		pass
	return page_index


def make_signed_cookie(id, password, max_age):  # 加密cookie
	expires = str(int(time.time() + (max_age or 86400)))
	L = [id, expires, hashlib.md5('%s-%s-%s-%s' % (id, password, expires, _COOKIE_KEY)).hexdigest()]
	return '-'.join(L)


def parse_signed_cookie(cookie_str):  # 解密cookie
	try:
		L = cookie_str.split('-')
		if len(L) != 3:
			return None
		id, expires, md5 = L
		if int(expires) < time.time():
			return None
		user = User.get(id)
		if user is None:
			return None
		if md5 != hashlib.md5('%s-%s-%s-%s' % (id, user.password, expires, _COOKIE_KEY)).hexdigest():
			return None
		return user
	except:
		return None


def check_admin():  # 检查管理员权限
	user = ctx.request.user
	if user and user.admin:
		return
	raise APIPermissionError('No permission')


@interceptor('/')  # 添加url以/开头的必经拦截器
def user_interceptor(next):
	logging.info('try to bind user from session cookie')
	user = None
	cookie = ctx.request.cookies.get(_COOKIE_NAME)
	if cookie:
		user = parse_signed_cookie(cookie)
		if user:
			logging.info('bind user<%s> to session' % user.email)
	ctx.request.user = user
	return next()


@interceptor('/manage/')
def manage_interceptor(next):
	user = ctx.request.user
	if user and user.admin:
		return next()
	raise seeother('/signin')


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
def register():  # 注册模板中使用了vue.js,并在提示时调用$.ajax 使用register_user进行注册
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


@view('signin.html')
@get('/signin')
def signin():
	return dict()


def _get_blogs_by_page():
	total = Blog.count_all()
	page = Page(total, _get_page_index())
	blogs = Blog.find_by('order by created_at desc limit ?,?', page.offset, page.limit)
	return blogs, page


@api
@get('/api/blogs')
def api_get_blogs():
	blogs, page = _get_blogs_by_page()
	return dict(blogs=blogs, page=page)


@api
@post('/api/authenticate')
def authenticate():  # 登陆
	i = ctx.request.input()
	email = i.email.strip().lower()
	password = i.password
	user = User.find_first('where email=?', email)
	if user is None:
		raise APIError('auth:failed', 'email', 'Invalid email')
	elif user.password != password:
		raise APIError('auth:failed', 'password', 'Invalid password')
	max_age = 604800
	cookie = make_signed_cookie(user.id, user.password, max_age)
	ctx.response.set_cookie(_COOKIE_NAME, cookie, max_age=max_age)
	user.password = '******'
	return user


@view('manage_blog_list.html')
@get('/manage/blogs')
def manage_blogs():
	return dict(page_index=_get_page_index(), user=ctx.request.user)


@view('manage_blog_edit.html')  # blog编辑页
@get('/manage/blogs/create')
def manage_blogs_create():
	return dict(id=None, action='/api/blogs', redirect='/manage/blogs', user=ctx.request.user)

@api
@post('/api/blogs')  # blog录入
def api_create_blog():
	check_admin()
	i = ctx.request.input(name='', summary='', content='')
	name = i.name.strip()
	summary = i.summary.strip()
	content = i.content.strip()
	if not name:
		raise APIValueError('name', 'name cannot be empty')
	if not summary:
		raise APIValueError('summary', 'summary cannot be empty')
	if not content:
		raise APIValueError('content', 'content cannot be empty')
	user = ctx.request.user
	blog = Blog(user_id=user.id, user_name=user.name, name=name, summary=summary, content=content)
	blog.insert()
	return blog
