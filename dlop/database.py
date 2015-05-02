#!/usr/bin/python -tt

import os
import sys
import re
import subprocess
import json
import traceback
import errno

class DLOPException(Exception):
    pass

class DLOPGPGDecryptException(DLOPException):
    pass

class DLOPGPGEncryptException(DLOPException):
    pass

class DLOPJSONException(DLOPException):
    def __init__(self, filename, exc_info):
        super(DLOPJSONException, self).__init__(filename)
        self.filename = filename
        self.exc_info = exc_info

class DLOPFindNextException(DLOPException):
    pass

class DLOPDB(object):
    def __init__(self, directory, gpg_program, user_id, extension=".json.gpg", gpg_home=None):
        self.directory = directory
        self.gpg_program = gpg_program
        self.user_id = user_id
        self.extension = extension
        self.gpg_home = gpg_home
        self.files = None
        self.database = None

    def load_file_list(self):
        if self.files is not None:
            return self.files

        try:
            self.files = map(lambda x: os.path.join(self.directory, x), filter(lambda x: x.endswith(self.extension), os.listdir(self.directory)))
            self.files.sort()
        except OSError as e:
            if e.errno == errno.ENOENT:
                self.files = []
            else:
                raise

        return self.files

    def find_next_name(self):
        self.load_file_list()

        if len(self.files) == 0:
            return os.path.join(self.directory, "0001%s" % self.extension)

        m = re.search(r'%s([0-9]+)%s$' % (os.sep, re.escape(self.extension)), self.files[-1])
        if not m:
            raise DLOPFindNextException(self.files[-1])
        new_name = "%s%s%04d%s" % (self.files[-1][:m.start()], os.sep, (int(m.group(1)) + 1), self.extension)
        return new_name

    def _decrypt(self, passphrase, filename):
        homedir = []
        if self.gpg_home:
            homedir = ["--homedir", self.gpg_home]
        p = subprocess.Popen([self.gpg_program] + homedir + ["--batch", "--no-greeting", "--no-tty", "--passphrase-fd", "0", "--decrypt", filename], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate(passphrase + "\n")
        if p.returncode != 0:
            raise DLOPGPGDecryptException(stderr)
        return stdout

    def _encrypt(self, data, filename):
        homedir = []
        if self.gpg_home:
            homedir = ["--homedir", self.gpg_home]
        try:
            os.mkdir(self.directory, 0700)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        p = subprocess.Popen([self.gpg_program] + homedir + ["--batch", "--no-greeting", "--no-tty", "--encrypt", "-r", self.user_id, "-o", filename], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        json.dump(data, p.stdin)
        stdout, stderr = p.communicate("\n")
        if p.returncode != 0:
            raise DLOPGPGEncryptException(stderr)

    def load(self, passphrase, merge=True):
        if self.database is None:
            self.load_file_list()

            self.database = []
            for filename in self.files:
                data = self._decrypt(passphrase, filename)
                try:
                    data = json.loads(data)
                except:
                    raise DLOPJSONException(filename, sys.exc_info())

                self.database.extend(data)

        if merge:
            self.merge()

        return self.database

    def save(self):
        if self.database is None:
            raise DLOPException()

        new_name = self.find_next_name()
        self._encrypt(self.database, new_name)
        for filename in self.files:
            os.unlink(filename)
        self.files = [new_name]

    def merge(self):
        if len(self.files) > 1:
            self.save()
            return True
        return False

    def add(self, name, password, data={}):
        d = data.copy()
        d['name'] = name
        d['password'] = password
        new_name = self.find_next_name()
        self._encrypt([d], new_name)
        self.files.append(new_name)
        if self.database is not None:
            self.database.append(d)

    def remove(self, passphrase, name, save=True):
        self.load(passphrase, merge=False)

        self.database = filter(lambda x: x['name'] != name, self.database)

        if save:
            self.save()

    def get(self, passphrase, name, merge=True):
        database = self.load(passphrase, merge=merge)
        for entry in database:
            if entry['name'] == name:
                return entry
        return None
