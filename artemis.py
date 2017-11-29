#!/usr/bin/env python
import feedpuller
from datetime import datetime
from ConfigParser import ConfigParser
import os
import sys
import shutil
import hpfeeds
import gevent
import json
import logging
import MySQLdb

from daemon import runner


logger = logging.getLogger('artemis')

class Artemis(object):
    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/var/artemis-storage/logs/artemis_out.log'
        self.stderr_path = '/var/artemis-storage/logs/artemis_err.log'
        self.pidfile_path = '/var/artemis-storage/pid/artemis.pid'
        self.pidfile_timeout = 5
        self.logfile = '/var/artemis-storage/logs/artemis.log'
        self.config_file = '/var/artemis-storage/config/config.conf'

    def parse_config(self,config_file):
        if not os.path.isfile(config_file):
            logger.critical("Could not find configuration file: {0}".format(config_file))
            sys.exit("Could not find configuration file: {0}".format(config_file))

        parser = ConfigParser()
        parser.read(config_file)

        config = {}

        config['mysqlserver'] = parser.get('mysql', 'server')
        config['mysqldb'] = parser.get('mysql', 'database')
        config['mysqluser'] = parser.get('mysql', 'user')
        config['mysqlpass'] = parser.get('mysql', 'password')

        config['hpf_channels'] = parser.get('hpfeeds', 'channels').split(',')
        config['hpf_ident'] = parser.get('hpfeeds', 'ident')
        config['hpf_secret'] = parser.get('hpfeeds', 'secret')
        config['hpf_port'] = parser.getint('hpfeeds', 'port')
        config['hpf_host'] = parser.get('hpfeeds', 'host')



        return config

    def init_db(self,c):
        db_conn = MySQLdb.connect(host=c['mysqlserver'],
                                     user=c['mysqluser'],
                                     passwd=c['mysqlpass'])
        db_curr = db_conn.cursor()

        create_db = "CREATE DATABASE IF NOT EXISTS %s COLLATE=utf8mb4_unicode_ci"
        try:
            logger.debug('Initializing database {0}'.format(c['mysqldb']))
            db_curr.execute(create_db % str(c['mysqldb']))
        except MySQLdb.Error, e:
            logger.critical("Error initializing database - %d: %s" % (e.args[0], e.args[1]))


        create_t_attachments = ('CREATE TABLE IF NOT EXISTS `attachments` ('
                                '`id` BIGINT NOT NULL AUTO_INCREMENT,'
                                '`timestamp` DATETIME NOT NULL,'
                                '`spam_id` CHAR(32),'
                                '`sensor_id` VARCHAR(64) CHARACTER SET utf8 COLLATE utf8_unicode_ci,'
                                '`sender` VARCHAR(256) CHARACTER SET utf8 COLLATE utf8_unicode_ci,'
                                '`recipient` VARCHAR(256) CHARACTER SET utf8 COLLATE utf8_unicode_ci,'
                                '`source_ip` VARCHAR(16) CHARACTER SET utf8 COLLATE utf8_unicode_ci,'
                                '`file_name` VARCHAR(200) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,'
                                '`file_path` MEDIUMTEXT NOT NULL,'
                                '`file_type` VARCHAR(50) NOT NULL,'
                                '`md5` CHAR(32) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,'
                                '`sha1` CHAR(40),'
                                '`sha256` CHAR(64),'
                                '`vt_positives` SMALLINT UNSIGNED,'
                                '`vt_total` SMALLINT UNSIGNED,'
                                '`last_vt` DATETIME,'
                                'PRIMARY KEY (`id`),'
                                'KEY `spam_id` (`spam_id`),'
                                'KEY `file_name` (`file_name`),'
                                'KEY `md5` (`md5`)'
                                ') ENGINE=InnoDB DEFAULT COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1')

        create_t_thug = ('CREATE TABLE IF NOT EXISTS `thugfiles` ('
                         '`id` BIGINT NOT NULL AUTO_INCREMENT,'
                         '`timestamp` DATETIME NOT NULL,'
                         '`file_name` VARCHAR(200) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,'
                         '`file_path` MEDIUMTEXT NOT NULL,'
                         '`md5` CHAR(32) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,'
                         '`sha1` CHAR(40),'
                         '`sha256` CHAR(64),'
                         '`vt_positives` SMALLINT UNSIGNED,'
                         '`vt_total` SMALLINT UNSIGNED,'
                         '`last_vt` DATETIME,'
                         'PRIMARY KEY (`id`),'
                         'KEY `file_name` (`file_name`),'
                         'KEY `md5` (`file_name`)'
                         ') ENGINE=InnoDB DEFAULT COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1;')

        try:
            logger.debug('Initializing tables')
            db_conn.select_db(str(c['mysqldb']))
            db_curr.execute(create_t_attachments)
            db_curr.execute(create_t_thug)
        except MySQLdb.Error, e:
            logger.critical("Error initializing tables - %d: %s" % (e.args[0], e.args[1]))

        db_conn.close()

    def run(self):
        logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                            filename=self.logfile,
                            level=logging.DEBUG)

        try:
            while True:
                logger.info("Artemis Storage Server starting up...")
                c = self.parse_config(self.config_file)

                self.init_db(c)

                greenlets = {}

                puller = feedpuller.FeedPuller(c)
                greenlets['hpfeeds-puller'] = gevent.spawn(puller.start_listening)

                try:
                    gevent.joinall(greenlets.values())
                except KeyboardInterrupt as err:
                    if puller:
                        puller.stop()
                        db_conn.close()

                gevent.joinall(greenlets.values())
        except (SystemExit,KeyboardInterrupt):
            pass
        except:
            logger.exception("Exception")
        finally:
            logger.info("Artemis Storage Server shutting down...")


if __name__ == '__main__':
    template = os.path.join(os.path.dirname(os.path.abspath(__file__)),"data","prototype")
    if not os.path.exists("/var/artemis-storage"):
        shutil.copytree(template,"/var/artemis-storage")

    daemon_runner = runner.DaemonRunner(Artemis())
    daemon_runner.daemon_context.detach_process=True
    daemon_runner.do_action()
