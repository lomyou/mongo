#!/usr/bin/env python
#
# Copyright (c) 2008-2012 WiredTiger, Inc.
#	All rights reserved.
#
# See the file LICENSE for redistribution information.
#
# test_config01.py
# 	The home directory for wiredtiger_open
#

import unittest
import wiredtiger
from wiredtiger import WiredTigerError
import wttest
import os

class test_config02(wttest.WiredTigerTestCase):
    table_name1 = 'test_config02'
    nentries = 100

    # Each test needs to set up its connection in its own way,
    # so override these methods to do nothing
    def setUpConnectionOpen(self, dir):
        return None

    def setUpSessionOpen(self, conn):
        return None

    def populate_and_check(self):
        """
        Create entries, and read back in a cursor: key=string, value=string
        """
        create_args = 'key_format=S,value_format=S'
        self.session.create("table:" + self.table_name1, create_args)
        cursor = self.session.open_cursor('table:' + self.table_name1, None, None)
        for i in range(0, self.nentries):
            cursor.set_key(str(1000000 + i))
            cursor.set_value('value' + str(i))
            cursor.insert()
        i = 0
        cursor.reset()
        for key, value in cursor:
            self.assertEqual(key, str(1000000 + i))
            self.assertEqual(value, ('value' + str(i)))
            i += 1
        self.assertEqual(i, self.nentries)
        cursor.close(None)

    def checkfiles(self, dirname):
        self.assertTrue(os.path.exists(dirname + os.sep + self.table_name1 + ".wt"))

    def checknofiles(self, dirname):
        self.assertEqual(len(os.listdir(dirname)), 0)

    def common_test(self, homearg, homeenv, configextra):
        """
        Call wiredtiger_open and run a simple test.
        homearg is the first arg to wiredtiger_open, it may be null.
        WIREDTIGER_HOME is set to homeenv, if it is not null.
        configextra are any extra configuration strings needed on the open.
        """
        configarg = 'create'
        if configextra != None:
            configarg += ',' + configextra
        if homeenv == None:
            os.unsetenv('WIREDTIGER_HOME')
	else:
            os.putenv('WIREDTIGER_HOME', homeenv)
        self.conn = wiredtiger.wiredtiger_open(homearg, configarg)
        self.session = self.conn.open_session(None)
        self.populate_and_check()

    def test_home_nohome(self):
        self.common_test(None, None, None)
        self.checkfiles(".")

    def test_home_rel(self):
        dir = 'subdir'
        os.mkdir(dir)
        self.common_test(dir, None, None)
        self.checkfiles(dir)

    def test_home_abs(self):
        dir = os.path.realpath('.') + os.sep + 'subdir'
        os.mkdir(dir)
        self.common_test(dir, None, None)
        self.checkfiles(dir)

    def test_home_and_env(self):
        hdir = 'homedir'
        edir = 'envdir'
        os.mkdir(hdir)
        os.mkdir(edir)
        self.common_test(hdir, edir, None)
        self.checkfiles(hdir)
        self.checknofiles(edir)

    def test_home_and_env_conf(self):
        # If homedir is set, the environment is ignored
        hdir = 'homedir'
        edir = 'envdir'
        os.mkdir(hdir)
        os.mkdir(edir)
        self.common_test(hdir, edir, 'home_environment=true')
        self.checkfiles(hdir)
        self.checknofiles(edir)

    def test_home_and_missing_env(self):
        # If homedir is set, it is used no matter what
        hdir = 'homedir'
        os.mkdir(hdir)
        self.common_test(hdir, None, 'home_environment=true')
        self.checkfiles(hdir)

    def test_env_conf(self):
        edir = 'envdir'
        os.mkdir(edir)
        self.common_test(None, edir, 'home_environment=true')
        self.checkfiles(edir)

    def test_env_conf_without_env_var(self):
        # no env var set, so should use current directory
        self.common_test(None, None, 'home_environment=true')
        self.checkfiles(".")

    def test_env_no_conf(self):
	# env var, but no open configuration string, should fail
        edir = 'envdir'
        os.mkdir(edir)
        self.assertRaises(WiredTigerError,
                          lambda: self.common_test(None, edir, None))

    def test_home_does_not_exist(self):
        dir = 'nondir'
        self.assertRaises(WiredTigerError,
                          lambda: wiredtiger.wiredtiger_open(dir, 'create'))

    def test_home_not_writeable(self):
        dir = 'subdir'
        os.mkdir(dir)
        os.chmod(dir, 0555)
        self.assertRaises(WiredTigerError,
                          lambda: wiredtiger.wiredtiger_open(dir, 'create'))

if __name__ == '__main__':
    wttest.run()
