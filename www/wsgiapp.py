#!/usr/bin/env python
# -*- coding :utf-8 -*-

__author__ = 'fangyu'

import logging; logging.basicConfig(level=logging.INFO)

import os

from transwarp import db
from transwarp.web import WSGIApplication, Jinja2TemplateEngine

from config import configs
db.create_engine(**configs.db)

wsgi = WSGIApplication(os.path.dirname(os.path.abspath(__file__)))  # 常用搭配返回当前脚本的绝对路径不包含文件名

template_engine = Jinja2TemplateEngine(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))

wsgi.template_engine = template_engine

import urls
wsgi.add_module(urls)

if __name__ == '__main__':
	wsgi.run(9000)
