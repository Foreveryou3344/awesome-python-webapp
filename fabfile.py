import os
import re
from datetime import datetime
from fabric.api import *
env.user = 'root'
env.sudo_user = 'root'
env.hosts = ['139.180.193.216']

db_user = 'pythonuser'
db_password = 'pythonuser'


_TAR_FILE = 'dist-awesome.tar.gz'
_REMOTE_TMP_TAR = '/tmp/%s' % _TAR_FILE
_REMOTE_BASE_DIR = '/srv/awesome'


def build():
	includes = ['static', 'templates', 'transwarp', 'favicon.ico', '*.py']
	excludes = ['test', '.*', '*.pyc', '*.pyo']
	local('rm -f disk/%s' % _TAR_FILE)
	with lcd(os.path.join(os.path.abspath('.'), 'www')):
		cmd = ['bsdtar', '--dereference', '-czvf', '../disk/%s' % _TAR_FILE]
		cmd.extend(['--exclude=\'%s\'' % ex for ex in excludes])
		cmd.extend(includes)
		local(' '.join(cmd))


def deploy():
	newdir = 'www-%s' % datetime.now().strftime('%y-%m-%d_%H.%M.%S')
	run('rm -f %s' % _REMOTE_TMP_TAR)
	put('disk/%s' % _TAR_FILE, _REMOTE_TMP_TAR)
	with cd(_REMOTE_BASE_DIR):
		run('mkdir %s' % newdir)
	with cd('%s/%s' % (_REMOTE_BASE_DIR, newdir)):
		run('tar -xzvf %s' % _REMOTE_TMP_TAR)
	with cd(_REMOTE_BASE_DIR):
		run('rm -f www')
		run('ln -s %s www' % newdir)
		# sudo('chown www-date:www-data www')
		# sudo('chowm -R www-date:www-data %s' % newdir)
