#!/usr/bin/env python

import os
import sys
import logging
import MySQLdb as mdb
import base64
import json
import datetime

logger = logging.getLogger('artemis')

class ThugFiles(object):

    def __init__(self,db_cursor,config):
        self.db_cursor = db_cursor
        self.ident = None
        self.payload = None
        self.config = config

    def save_file(self,payload):
        try:
            decoded = json.loads(str(payload))
            logger.debug('Decoded file payload')
        except:
            decoded = {'raw': payload}
            logger.debug('Saving file payload as raw data')

        if not 'md5' in decoded or not 'data' in decoded:
            logger.error('Received file does not contain hash or data - Ignoring it')
            return

        logger.debug("Checking if file already exists: %s" % str(decoded['md5']))
        md5 = (str(decoded['md5']),)
        checkFile = "SELECT COUNT(1) FROM `thugfiles` WHERE `md5` = %s"
        try:
            self.db_cursor.execute(checkFile, md5)
            if (self.db_cursor.fetchone()[0]):
                logger.info("File already exists, skipping")
                return
        except mdb.Error, e:
            logger.critical("Error checking attachment database - %d: %s" % (e.args[0], e.args[1]))


        filedata = decoded['data'].decode('base64')
        path = "/var/artemis-storage/files/thug/" + decoded['md5']
        logger.debug('Saving Thug file')
        fd = open(path, 'wb')
        fd.write(filedata)
        logger.debug('Thug file saved')

        now = datetime.datetime.now()
        f = '%Y-%m-%d %H:%M:%S'

        values = str(now.strftime(f)), str(decoded['md5']), str(mdb.escape_string(path)), str(decoded['md5']), '0', '0'
        insertFile = "INSERT INTO `thugfiles`(`timestamp`, `file_name`, `file_path`, `md5`, `vt_positives`, `vt_total`) VALUES(%s, %s, %s, %s, %s, %s)"

        try:
            logger.debug('Saving thug file info to database')
            self.db_cursor.execute(insertFile, values)
        except mdb.Error, e:
            logger.critical("Error inserting file info into MySQL - %d: %s" % (e.args[0], e.args[1]))

    def handle_payload(self,ident,payload):
        self.ident = ident
        self.payload = payload

        self.save_file(payload)

