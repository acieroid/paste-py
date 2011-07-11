#!/usr/bin/env python
from grizzled.os import daemonize
from os import execv, getcwd, chdir

PYTHON_PATH = '/usr/local/bin/'
PYTHON2_EXECUTABLE = 'python'

# daemonize sets the cwd to /, so keep a track of the current cwd...
cwd = getcwd()
daemonize(no_close=True, pidfile=cwd+'/paste.pid')
# ... and we go back in this directory
chdir(cwd)
execv(PYTHON_PATH + PYTHON2_EXECUTABLE, [PYTHON2_EXECUTABLE, 'paste.py'])

