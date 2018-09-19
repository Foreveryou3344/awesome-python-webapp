#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'ForYou'

from transwarp.web import get, view, post, ctx, interceptor, seeother, notfound
from models import User, Blog, Comment
from apis import api, APIValueError, APIError, APIPermissionError, Page, APIResourceNotFoundError
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


def _get_blogs_by_page():
	total = Blog.count_all()
	page = Page(total, _get_page_index())
	blogs = Blog.find_by('order by created_at desc limit ?,?', page.offset, page.limit)
	return blogs, page


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


@view('blogs.html')  # 和manage_blog_list不同的事，管理页需要删除编辑等交互操作，所以我们把分页的内容交给vue渲染，这里面只需要渲染一次所以就用jinja渲染就行
@get('/')
def index():
	blogs, page = _get_blogs_by_page()
	return dict(page=page, blogs=blogs, user=ctx.request.user)


@view('blog.html')
@get('/blog/:blog_id')
def blog(blog_id):
	blog = Blog.get(blog_id)
	if blog is None:
		raise notfound()
	comments = Comment.find_by('where blog_id=? order by created_at desc limit 1000', blog_id)
	return dict(blog=blog, comments=comments, user=ctx.request.user)


@api
@post('/api/blogs/:blog_id/comments')  # 添加评论api
def api_create_blog_comment(blog_id):
	user = ctx.request.user
	if user is None:
		raise APIPermissionError('need signin')
	blog = Blog.get(blog_id)
	if blog is None:
		raise APIResourceNotFoundError('Blog')
	content = ctx.request.input(content='').content.strip()
	if not content:
		raise APIValueError('content')
	c = Comment(blog_id=blog_id, user_id=user.id, user_name=user.name, user_image=user.image, content=content)
	c.insert()
	return dict(comment=c)


@view('register.html')
@get('/register')
def register():  # 注册模板中使用了vue.js,并在提交时调用$.ajax 使用register_user进行注册
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
	max_age = 604800
	cookie = make_signed_cookie(user.id, user.password, max_age)
	ctx.response.set_cookie(_COOKIE_NAME, cookie, max_age=max_age)  # 注册后直接完成登陆
	return user


@view('signin.html')
@get('/signin')
def signin():
	return dict()


@get('/signout')
def signout():
	ctx.response.delete_cookie(_COOKIE_NAME)
	raise seeother('/')


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


@get('/manage/')  # 管理界面初始页
def manage_index():
	raise seeother('/manage/comments')


@view('manage_comment_list.html')  # 评论管理列表
@get('/manage/comments')
def manage_comments():
	return dict(page_index=_get_page_index(), user=ctx.request.user)


@api
@get('/api/comments')  # 获取评论api
def api_get_comments():
	total = Comment.count_all()
	page = Page(total, _get_page_index())
	comments = Comment.find_by('order by created_at desc limit ?,?', page.offset, page.limit)
	return dict(comments=comments, page=page)


@api
@post('/api/comments/:comment_id/delete')  # 删除评论
def api_delete_comment(comment_id):
	check_admin()
	comment = Comment.get(comment_id)
	if comment is None:
		raise APIResourceNotFoundError('Comment')
	comment.delete()
	return dict(id=comment_id)


@view('manage_user_list.html')  # 用户列表管理
@get('/manage/users')
def manage_users():
	return dict(page_index=_get_page_index(), user=ctx.request.user)


@api
@get('/api/users')  # 获取用户列表api
def api_get_users():
	total = User.count_all()
	page = Page(total, _get_page_index())
	users = User.find_by('order by created_at desc limit ?,?', page.offset, page.limit)
	for u in users:
		u.password = '******'
	return dict(page=page, users=users)


@api
@post('/api/users/:user_id/delete')  # 用户 删除
def api_delete_user(user_id):
	check_admin()
	user = User.get(user_id)
	if user is None:
		raise APIResourceNotFoundError('user')
	user.delete()
	Blog.delete_by('where user_id = ?', user_id)
	Comment.delete_by('where user_id = ?', user_id)
	return dict(id=user_id)


@view('manage_blog_list.html')  # blog管理列表页
@get('/manage/blogs')
def manage_blogs():
	return dict(page_index=_get_page_index(), user=ctx.request.user)


@view('manage_blog_edit.html')  # blog新增编辑页
@get('/manage/blogs/create')
def manage_blogs_create():
	return dict(id=None, action='/api/blogs', redirect='/manage/blogs', user=ctx.request.user)


@view('manage_blog_edit.html')  # blog编辑
@get('/manage/blogs/edit/:blog_id')
def manage_blogs_edit(blog_id):
	blog = Blog.get(blog_id)
	if blog is None:
		raise notfound()
	return dict(id=blog.id, name=blog.name, summary=blog.summary, content=blog.content, action='/api/blogs/%s' % blog_id, redirect='/manage/blogs', user=ctx.request.user)


@api
@get('/api/blogs')  # blog列表api
def api_get_blogs():
	blogs, page = _get_blogs_by_page()
	return dict(blogs=blogs, page=page)


@api
@get('/api/blogs/:blog_id')  # 获取blog api
def api_get_blog(blog_id):
	blog = Blog.get(blog_id)
	if blog:
		return blog
	raise APIResourceNotFoundError('Blog')


@api
@post('/api/blogs')  # blog新增录入
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


@api
@post('/api/blogs/:blog_id')  # blog修改录入
def api_update_blog(blog_id):
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
	blog = Blog.get(blog_id)
	if blog is None:
		raise APIResourceNotFoundError('Blog')
	blog.name = name
	blog.summary = summary
	blog.content = content
	blog.update()
	return blog


@api
@post('/api/blogs/:blog_id/delete')  # blog 删除
def api_delete_blog(blog_id):
	check_admin()
	blog = Blog.get(blog_id)
	if blog is None:
		raise APIResourceNotFoundError('blog')
	blog.delete()
	Comment.delete_by('where blog_id = ?', blog_id)
	return dict(id=blog_id)
