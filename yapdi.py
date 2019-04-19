# !/usr/bin/env python
''' 
#
# YapDi - Yet another python Daemon implementation <https://github.com/kasun/YapDi>
# Author Kasun Herath <kasunh01@gmail.com> 
#
# Python 3 compatibility by Anton Osten <anton@ostensible.me>
'''

from signal import SIGTERM
import sys, atexit, os, pwd
import time
from warnings import warn

OPERATION_SUCCESSFUL = 0
OPERATION_FAILED = 1
INSTANCE_ALREADY_RUNNING = 2
INSTANCE_NOT_RUNNING = 3
SET_USER_FAILED = 4

# python 2 and 3 compatibility
pyversion = sys.version_info[0]

if pyversion is 2:
    no_file_error = IOError
    no_process_error = OSError
else:
    no_file_error = FileNotFoundError
    no_process_error = ProcessLookupError

class Daemon:
    def __init__(self, pidfile=None, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr

        # If pidfile is not specified derive it by supplying scriptname
        if not pidfile:
            self.pidfile = self.get_pidfile(sys.argv[0])
        else:
            self.pidfile = pidfile

        # user to run under
        self.daemon_user = None

    def daemonize(self):
        ''' Daemonize the current process and return '''
        if self.status():
            warn('YapDi: instance is already running', RuntimeWarning)
            return INSTANCE_ALREADY_RUNNING
        try: 
            pid = os.fork() 
            if pid > 0:
                # exit first parent
                sys.exit(0) 
        except OSError as e: 
            return OPERATION_FAILED

        # decouple from parent environment
        os.setsid() 
        os.umask(0)

        # do second fork
        try: 
            pid = os.fork() 
            if pid > 0:
                # exit from second parent
                sys.exit(0) 
        except OSError as e: 
            return OPERATION_FAILED

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(self.stdin)
        so = open(self.stdout, 'a+')
        se = open(self.stderr, 'a+')
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        
        with open(self.pidfile, 'w+') as file:      
            file.write("%s\n" % pid)
    
        # If daemon user is set change current user to self.daemon_user
        if self.daemon_user:
            try:
                uid = pwd.getpwnam(self.daemon_user)[2]
                os.setuid(uid)
            except NameError as e:
                return SET_USER_FAILED
            except OSError as e:
                return SET_USER_FAILED
        return OPERATION_SUCCESSFUL

    def delpid(self):
        os.remove(self.pidfile)

    def kill(self):
        ''' kill any running instance '''
        # check if an instance is not running
        pid = self.status()
        if not pid:
            return INSTANCE_NOT_RUNNING

        # Try killing the daemon process    
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except no_process_error as err:
            err = str(err)
            if "No such process" in err:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                return OPERATION_FAILED
        return OPERATION_SUCCESSFUL

    def restart(self):
        ''' Restart an instance; If an instance is already running kill it and start else just start '''
        if self.status():
            kill_status = self.kill()
            if kill_status == OPERATION_FAILED:
                return kill_status
        return self.daemonize()

    def status(self):
        ''' check whether an instance is already running. If running return pid or else False '''
        try:
            pf = open(self.pidfile)
            pid = int(pf.read().strip())

            # check if it is actually running or even exists
            try:
                os.kill(pid, 0)
            except no_process_error:
                os.remove(self.pidfile)
                pid = None

        except no_file_error:
            pid = None
        return pid

    def set_user(self, username):
        ''' Set user under which the daemonized process should be run '''
        if not isinstance(username, str):
            raise TypeError('username should be of type str')
        self.daemon_user = username

    def get_pidfile(self, scriptname):
        ''' Return file name to save pid given original script name '''
        pidpath_components = scriptname.split('/')[0:-1]
        pidpath_components.append('.yapdi.pid')
        return '/'.join(pidpath_components)