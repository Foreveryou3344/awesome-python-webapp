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
RE_FILES = re.compile('\r?\n')


def _current_path():
	return os.path.abspath('.')


def _now():
	return datetime.now().strftime('%y-%m-%d_%H.%M.%S')


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
	with settings(warn_only=True):
		run('supervisorctl -c /etc/supervisor/supervisord.conf stop awesome')
		run('supervisorctl -c /etc/supervisor/supervisord.conf start awesome')
		run('/etc/init.d/nginx reload')


def backup():  # backup mysql to localhost
	dt = _now()
	f = 'backup-awesome-%s.sql' % dt
	with cd('/tmp'):
		run('mysqldump --user=%s --password=%s --skip-opt --add-drop-table --default-character-set=utf8 --quick mypython > %s' % (db_user, db_password, f))
		run('tar -czvf %s.tar.gz %s' % (f, f))
		get('%s.tar.gz' % f, '%s/backup/' % _current_path())
		run('rm -f %s' % f)
		run('rm -f %s.tar.gz' % f)


def rollback():
	with cd(_REMOTE_BASE_DIR):
		r = run('ls -p -1')
		files = [s[:-1] for s in RE_FILES.split(r) if s.startswith('www-') and s.endswith('/')]
		files.sort(cmp=lambda s1, s2: 1 if s1 < s2 else -1)
		print files
		r = run('ls -l www')
		ss = r.split(' -> ')
		if len(ss) != 2:
			print ('ERROR:\'www\' is not a symbol link ')
			return
		current = ss[1]
		print ('found current symbol link points to: %s\n' % current)
		try:
			index = files.index(current)
		except ValueError, e:
			print ('ERROR: symbol link is invalid')
			return
		if len(files) == index + 1:
			print('ERROR: already the oldest version')
		old = files[index + 1]
		print ('===============')
		for f in files:
			if f ==current:
				print ('      current--->%s' % current)
			elif f == old:
				print ('  rollback to--->%s' % old)
			else:
				print ('                 %s' % f)
		print ('==============')
		print ('')
		yn = raw_input('continue?y/n')
		if yn != 'y' and yn != 'Y':
			print ('canceled')
			return
		print ('start rollback')
		run('rm -f www')
		run('ln -s %s www' % old)
		with settings(warn_only=True):
			run('supervisorctl -c /etc/supervisor/supervisord.conf stop awesome')
			run('supervisorctl -c /etc/supervisor/supervisord.conf start awesome')
			run('/etc/init.d/nginx reload')
		print ('rollback ok')