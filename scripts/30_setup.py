#!/usr/bin/env python3
"""
Setup
-----

Create the environment, users with all the required files.
"""

__author__ = "Yoan Blanc <yoan@dosimple.ch>"
__version__ = "0.1b2"

import re
import os
import csv
import sys
import pwd
import json
import shutil
import os.path
import subprocess
import unicodedata
import multiprocessing

from jinja2 import Environment, FileSystemLoader


env = Environment(loader=FileSystemLoader("/tmp/templates"))
wwwdir = "/var/www"


def formatUserName(firstname):
    """
    Format the real name into a username

    E.g.: Juan Giovanni Di Sousa Santos -> juan
    """
    # Keep only the first firstname
    first = re.match("^(.+?)\\b", firstname, re.U).group(0).lower()

    username = unicodedata.normalize("NFD", first)
    username = username.replace(" ", "")
    # http://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string/517974#517974
    return "".join([c for c in username if not unicodedata.combining(c)])


def init_user(username, groupname, **kwargs):
    """As the user."""
    p = pwd.getpwnam(username)
    uid, gid = p.pw_uid, p.pw_gid
    homedir = p.pw_dir

    os.initgroups(groupname, gid)
    os.setgid(gid)
    os.setuid(uid)
    os.chdir(homedir)
    os.umask(0o002)  # readable by group members

    os.environ["USER"] = username
    os.environ["HOME"] = homedir
    os.environ["UID"] = str(uid)

    paths = (("bash_profile", ".bash_profile"),
             ("README.md", "README.md"))
    for tpl, dest in paths:
        if not os.path.exists(dest):
            render(tpl, dest, username=username, groupname=groupname, **kwargs)

    # link /var/www to ~/www
    os.symlink(wwwdir, "www")

    # Create .ssh/authorized_keys
    os.mkdir(".ssh")
    os.chmod(".ssh", mode=0o0700)
    authorized_keys = ".ssh/authorized_keys"
    key = "/tmp/keys/{}.key".format(kwargs.get("github", "NOKEY"))
    if os.path.exists(key):
        with open(key, "r") as f:
            with open(authorized_keys, "a+") as t:
                t.write(f.read())
        os.chmod(".ssh/authorized_keys", mode=0o0600)
    else:
        sys.stderr.write("No public key for {}!\n".format(username))

    # Laravel
    shutil.copy("/tmp/composer.phar", "composer.phar")
    shutil.copytree("/tmp/.composer", ".composer")

    # Le symlink
    os.symlink(os.path.join(homedir, ".composer/vendor/laravel/installer/laravel"),
               ".composer/vendor/bin/laravel")
    os.chmod(".composer/vendor/laravel/installer/laravel", mode=0o0755)


def create_user(username, groupname, comment):
    """
    Create a UNIX user (the group must exist beforehand)
    """
    subprocess.check_call(["useradd", username,
                           "-c", comment,
                           "--create-home",
                           "--no-user-group",
                           "--shell", "/bin/bash",
                           "--groups", "users"],
                          stderr=subprocess.PIPE,
                          stdout=subprocess.PIPE)
    subprocess.check_call(["usermod", username,
                           "--gid", groupname,
                           "--groups", "{},users".format(groupname)],
                          stderr=subprocess.PIPE,
                          stdout=subprocess.PIPE)
    proc = subprocess.Popen(["chpasswd"],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    proc.communicate("{}:{}".format(username, pwgen()).encode("utf-8"))


def init_group(groupname, **kwargs):
    """As the user representing the group."""
    p = pwd.getpwnam(groupname)
    uid, gid = p.pw_uid, p.pw_gid
    homedir = p.pw_dir

    os.initgroups(groupname, gid)
    os.setgid(gid)
    os.setuid(uid)
    os.chdir(homedir)
    os.umask(0o002)  # readable by group members

    if not os.path.exists("config"):
        os.mkdir("config")
        os.mkdir("logs")
        os.mkdir("public")

        paths = (("index.php", "public/index.php"),
                ("nginx", "config/nginx.conf"))
        for tpl, dest in paths:
            if not os.path.exists(dest):
                render(tpl, dest, groupname=groupname, **kwargs)
    return homedir, uid, gid


def create_group(groupname):
    """Create the system user named after the group."""
    subprocess.check_call(["useradd", groupname,
                           "-c", "GROUP",
                           "--no-create-home",
                           "--home-dir", wwwdir,
                           "--user-group",
                           "--system"],
                          stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE)
    subprocess.check_call(["usermod", "--lock", groupname],
                          stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE)


def render(template, path, **kwargs):
    if not os.path.exists(path):
        template = env.get_template(template)
        with open(path, "w", encoding="utf-8") as f:
            f.write(template.render(**kwargs))


def pwgen(length=128):
    """Generates a secure password."""
    proc = subprocess.Popen(["pwgen", "--secure", "{}".format(length), "1"],
                            stdout=subprocess.PIPE)
    return proc.communicate()[0].decode().strip()


def main(argv):
    # Load global conf
    conf = "/etc/container_environment.json"
    with open(conf, "r", encoding="utf-8") as f:
        environ = json.load(f)

    groupname = environ["GROUPNAME"]
    environ["MYSQL_HOST"] = environ["MYSQL_PORT_3306_TCP_ADDR"]
    environ["MYSQL_PORT"] = environ["MYSQL_PORT_3306_TCP_PORT"]

    del environ["MYSQL_PORT_3306_TCP_ADDR"]
    del environ["MYSQL_PORT_3306_TCP_PORT"]
    del environ["MYSQL_ENV_MYSQL_ROOTPASSWORD"]

    # Create the group
    try:
        p = pwd.getpwnam(groupname)
        sys.stderr.write("Setup already done!\n")
        return 1
    except KeyError:
        pass

    # Create the group
    create_group(groupname)
    p = pwd.getpwnam(groupname)
    uid, gid = p.pw_uid, p.pw_gid
    # Rights for existing files
    os.chown(wwwdir, uid, gid)
    os.chmod(wwwdir, mode=0o0775)
    for root, dirs, files in os.walk(wwwdir):
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o0775)
            os.chown(os.path.join(root, d), uid, gid)
        for f in files:
            os.chmod(os.path.join(root, f), 0o0664)
            os.chown(os.path.join(root, f), uid, gid)


    # Init the group files
    p = multiprocessing.Process(target=init_group,
                                args=(groupname,),
                                kwargs=dict(environ=environ))
    p.start()
    p.join()

    # symlink the server config
    os.symlink("/var/www/config/nginx.conf",
               "/etc/nginx/sites-enabled/{}".format(groupname))

    # Create users
    students = "/root/config/students.tsv"
    if (os.path.exists(students)):
        with open(students, encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            # skip headers
            next(reader)
            for row in reader:
                # Only pick the users of the given group
                if row[3] in (groupname, "admin"):
                    # admin become part of the group
                    username = formatUserName(row[1])
                    row[3] = groupname
                    create_user(username, groupname, row[2])  # classname
                    p = multiprocessing.Process(target=init_user,
                                                args=(username,
                                                      groupname),
                                                kwargs=dict(firstname=row[0],
                                                            lastname=row[1],
                                                            classname=row[2],
                                                            github=row[4],
                                                            environ=environ))
                    p.start()
                    p.join()
                    sys.stderr.write("{} created.\n".format(username))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
