#!/usr/bin/python -tt

import os
import sys
import stat
import optparse
import getpass
import fnmatch
import subprocess
import json
import pyperclip
from dlop.database import DLOPDB

def prompt(message, secure=False):
    if not secure:
        print message
        return sys.stdin.readline()
    else:
        return getpass.getpass(message)

def inform(message):
    print message

error = inform

def find_gpg_program():
    paths = os.environ.get('PATH', '').split(os.pathsep)
    for path in paths:
        for bin_name in ["gpg2", "gpg"]:
            name = os.path.join(path, bin_name)
            if os.name == 'nt':
                name = name + ".exe"
            if os.path.exists(name) and (stat.S_IXOTH & os.stat(name)[stat.ST_MODE]) != 0:
                return name
    return None

def find_user_id(gpg_program, gpg_home=None):
    # FIXME: Ugly hack, at least use regexp
    homedir = []
    if gpg_home:
        homedir = ["--homedir", gpg_home]
    p = subprocess.Popen([gpg_program, "--list-secret-keys"] + homedir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    return map(lambda x: x[12:20], filter(lambda x: x.startswith("sec "), stdout.splitlines()))[0]

def main(args):
    parser = optparse.OptionParser()
    parser.add_option("-a", "--add", dest="add", action="store_true", help="Add a new password")
    parser.add_option("-g", "--get", dest="get", action="store_true", help="Get a password")
    parser.add_option("-r", "--replace", dest="replace", action="store_true", help="Replace a password")
    parser.add_option("-R", "--remove", dest="remove", action="store_true", help="Remove a password")
    parser.add_option("--gpg-program", dest="gpg_program", action="store", help="GPG program to use")
    parser.add_option("-d", "--directory", dest="directory", action="store", help="Directory to use", default=os.path.join(os.path.expanduser("~"), ".dlop"))
    parser.add_option("-u", "--user-id", dest="user_id", action="store", help="User ID to encrypt for")
    parser.add_option("-E", "--extra-data", dest="extra", action="store", help="JSON extra data to store with password")
    options, args = parser.parse_args(args)

    if not options.add and not options.get and not options.remove and not options.replace:
        options.get = True

    if not options.gpg_program:
        options.gpg_program = find_gpg_program()

    if not options.user_id:
        options.user_id = find_user_id(options.gpg_program)

    dlopdb = DLOPDB(options.directory, options.gpg_program, options.user_id)
    if options.get:
        passphrase = prompt("GPG passphrase? ", secure=True)
        database = dlopdb.load(passphrase)
        if len(args) > 0:
            matches = []
            for entry in database:
                for arg in args:
                    if fnmatch.fnmatch(entry['name'], arg) or len(fnmatch.filter(entry.get('aliases', []), arg)) > 0:
                        matches.append(entry)

            if len(matches) == 1:
                pyperclip.copy(matches[0]['password'])
            elif len(matches) == 0:
                inform("No matching password was found")
                sys.exit(1)
            else:
                print "Several matches found, which one do you want? "
                for num, match in enumerate(matches):
                    print "%-3d. %s" % (num + 1, match['name'])
                choice = int(sys.stdin.readline().strip())
                pyperclip.copy(matches[choice - 1]['password'])
        else:
            for entry in database:
                print "%s: %s %s" % (entry['name'], entry['password'], " ".join(["%s=%s" % (key, val) for key, val in entry.iteritems() if key not in ("name", "password", "aliases")]))

    elif options.add or options.replace:
        if options.replace:
            passphrase = prompt("GPG passphrase? ", secure=True)
        if len(args) == 0:
            name = prompt("Name? ").strip()
        else:
            name = args[0]
        if len(args) <= 1:
            password = prompt("Password: ", secure=True)
        else:
            password = args[1]
        if options.extra:
            data = json.loads(options.extra)
        else:
            data = {}
        if name != name.lower():
            data['aliases'] = [name.lower()]
        if options.replace:
            dlopdb.remove(passphrase, name)
        dlopdb.add(name, password, data)

    elif options.remove:
        passphrase = prompt("GPG passphrase? ", secure=True)
        if len(args) == 0:
            name = prompt("Name? ").strip()
        else:
            name = args[0]
        dlopdb.remove(passphrase, name)

if __name__ == "__main__":
    main(sys.argv[1:])
