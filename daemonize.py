#!/usr/bin/env python
from grizzled.os import daemonize
from os import environ, execve, getcwd, chdir
from sys import argv
from paste import run

PYTHON_EXECUTABLE = 'python2'

# daemonize sets the cwd to /, so keep a track of the current cwd...
cwd = getcwd()
daemonize(no_close=True, pidfile=cwd+'/paste.pid')
# ... and we go back in this directory
chdir(cwd)

run()
