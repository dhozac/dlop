#!/usr/bin/python -tt

import os
import shutil
import subprocess
import unittest

import dlop.database
import dlop.cliui

class TestCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gpg = dlop.cliui.find_gpg_program()
        cls.gpgdir = os.path.join(os.curdir, "testgpg")
        shutil.rmtree(cls.gpgdir, ignore_errors=True)
        os.mkdir(cls.gpgdir, 0700)
        subprocess.check_call([cls.gpg, "--homedir", cls.gpgdir, "--batch", "--gen-key", os.path.join(os.curdir, "genkey")])
        cls.passphrase = ''
        cls.user_id = dlop.cliui.find_user_id(cls.gpg, gpg_home=cls.gpgdir)
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.gpgdir, ignore_errors=True)
    def setUp(self):
        self.dir = os.path.join(os.curdir, "testdb")
        self.database = dlop.database.DLOPDB(self.dir, self.gpg, self.user_id, gpg_home=self.gpgdir)
    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)
        del self.database

    def test_add_1(self):
        self.database.add("test1", "qwerty")
        self.assertEqual(len(os.listdir(self.dir)), 1)

    def test_get_1(self):
        entry = self.database.get(self.passphrase, "test1")
        self.assertIs(entry, None)

    def test_add_1_get_1(self):
        self.database.add("test1", "qwerty")
        entry = self.database.get(self.passphrase, 'test1')
        self.assertIsNot(entry, None)
        self.assertEqual(entry['password'], "qwerty")

    def test_add_2_get_merge(self):
        self.database.add("test1", "qwerty")
        self.database.add("test2", "dvorak")
        self.assertEqual(len(os.listdir(self.dir)), 2)
        entry = self.database.get(self.passphrase, 'test1', merge=True)
        self.assertEqual(os.listdir(self.dir), ["0003.json.gpg"])
        self.assertIsNot(entry, None)
        self.assertEqual(entry['password'], "qwerty")
        entry = self.database.get(self.passphrase, 'test2')
        self.assertIsNot(entry, None)
        self.assertEqual(entry['password'], "dvorak")

    def test_addnget_1_addnget_1(self):
        self.database.add("test1", "qwerty")
        entry = self.database.get(self.passphrase, 'test1')
        self.assertIsNot(entry, None)
        self.assertEqual(entry['password'], "qwerty")

        self.database.add("test2", "dvorak")
        entry = self.database.get(self.passphrase, 'test2')
        self.assertEqual(len(os.listdir(self.dir)), 1)
        self.assertIsNot(entry, None)
        self.assertEqual(entry['password'], "dvorak")

    def test_remove(self):
        self.database.add("test1", "qwerty")
        self.database.add("test2", "dvorak")
        self.database.remove(self.passphrase, "test1")
        self.assertEqual(os.listdir(self.dir), ["0003.json.gpg"])
        entry = self.database.get(self.passphrase, "test2")
        self.assertIsNot(entry, None)
        self.assertIs(self.database.get(self.passphrase, "test1"), None)

    def test_add_3_get_1_from_new_db(self):
        self.database.add("test1", "qwerty")
        self.database.add("test2", "dvorak")
        self.database.add("test3", "foobar")
        self.database = dlop.database.DLOPDB(self.dir, self.gpg, self.user_id, gpg_home=self.gpgdir)
        entry = self.database.get(self.passphrase, "test1")
        self.assertEqual(os.listdir(self.dir), ["0004.json.gpg"])
        self.assertIsNot(entry, None)

if __name__ == "__main__":
    unittest.main()
