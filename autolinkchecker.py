#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Francois Boulogne
# License: GPLv3

import os
import shutil
import subprocess
# To get UID/GID
import pwd
import grp

import argparse
import logging

import configparser


def _demote(user_uid, user_gid):
    """
    Pass the function 'set_ids' to preexec_fn, rather than just calling
    setuid and setgid. This will change the ids for that subprocess only
    """

    def set_ids():
        os.setgid(user_gid)
        os.setuid(user_uid)

    return set_ids


class Job():
    """
    A class to store and run a job
    """

    def __init__(self, config, url):
        self.config = config
        self.url = url

        configfile = configparser.ConfigParser()
        configfile.read(self.config)
        # TODO: handle other formats as well.
        self.output = configfile['html']['filename']

        destination = '/var/www/linkchecker'
        self.file_on_server = os.path.join(destination, os.path.split(self.output)[1])

    def run(self):
        """
        Run the job
        """
        command = []
        command.append('/usr/bin/linkchecker')
        command.append('-f')
        command.append(self.config)
        command.append(self.url)

        # Linkchecker drops priviledges as a grand child
        process = subprocess.Popen(command, bufsize=4096, stdout=subprocess.PIPE, preexec_fn=_demote(1000, 1000))
        logger.debug('Command: %s' % command)
        stdout, stderr = process.communicate()
        logger.debug(stdout.decode('utf8'))
        if stderr is not None:
            logger.warning(stderr.decode('utf8'))

        # Move and set the correct UID/GID
        logger.debug('Move %s to %s' % (self.output, self.file_on_server))
        shutil.move(self.output, self.file_on_server)
        uid = pwd.getpwnam("www-data").pw_uid
        gid = grp.getgrnam("www-data").gr_gid
        os.chown(self.file_on_server, uid, gid)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='', epilog='')
    parser.add_argument('-d', '--debug', action='store_true',
                        default=False, help='Run in debug mode')

    args = parser.parse_args()

    if args.debug:
        llevel = logging.DEBUG
    else:
        llevel = logging.INFO
    logger = logging.getLogger()
    logger.setLevel(llevel)

    steam_handler = logging.StreamHandler()
    steam_handler.setLevel(llevel)
    logger.addHandler(steam_handler)

    # Run a job
    job = Job('/tmp/www.sciunto.org', 'http://www.sciunto.org')
    job.run()
