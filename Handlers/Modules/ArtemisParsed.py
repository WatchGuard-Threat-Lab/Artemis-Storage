#!/usr/bin/env python

import os
import sys
import logging
import MySQLdb as mdb
import cPickle

logger = logging.getLogger('artemis')

class ArtemisParsed(object):

    def __init__(self,db_cursor,config):
        self.db_cursor = db_cursor
        self.ident = None
        self.payload = None
        self.config = config

    def save_files(self,record,fileType):
        i = 0
        while i < len(record[fileType+'File']):
            fileName = str(record['s_id']) + "-a-" + str(record[fileType+'FileName'][i])
            path = "/var/artemis-storage/files/" + fileType + "/" + fileName

            logger.debug("Checking if file already exists: %s" % str(record[fileType+'FileMd5'][i]))
            md5 = (str(record[fileType+'FileMd5'][i]),)
            checkFile = "SELECT COUNT(1) FROM `attachments` WHERE `md5` = %s"
            try:
                self.db_cursor.execute(checkFile, md5)
                if (self.db_cursor.fetchone()[0]):
                    logger.info("File already exists, skipping")
                    i += 1
                    continue
            except mdb.Error, e:
                logger.critical("Error checking attachment database - %d: %s" % (e.args[0], e.args[1]))

            logger.debug('Saving attachment file')
            attachFile = open(path, 'wb')
            attachFile.write(record[fileType+'File'][i])
            attachFile.close()
            logger.debug('Attachment file saved to volume')

            values = str(record['date']), str(record['s_id']), str(record['sensorID']), str(record['from']), str(record['to']), str(record['sourceIP']), str(mdb.escape_string(record[fileType+'FileName'][i])), str(mdb.escape_string(path)), fileType, str(record[fileType+'FileMd5'][i]), '0', '0'

            insertFile = "INSERT INTO `attachments`(`timestamp`, `spam_id`, `sensor_id`, `sender`, `source_ip`, `file_name`, `file_path`, `file_type`, `md5`, `vt_positives`, `vt_total`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"


            try:
                logger.debug('Saving fattachment info to database')
                self.db_cursor.execute(insertFile, values)
                logger.info('Attachment info saved to database')
                i += 1
            except mdb.Error, e:
                i += 1
                logger.critical("Error inserting attachment info into MySQL - %d: %s" % (e.args[0], e.args[1]))


    def check_attachments(self,record):
        if len(record['attachmentFile']) > 0:
            logger.debug('Mail record has attachment, processing...')
            self.save_files(record,'attachment')
        else:
            logger.debug('Mail record has no attached files')

        if len(record['inlineFile']) > 0:
            logger.debug('Mail record has inline file, processing...')
            self.save_files(record,'inline')
        else:
            logger.debug('Mail record has no inline files')

    def handle_payload(self,ident,payload):
        self.ident = ident
        self.payload = str(payload)

        logger.debug("Unpacking hpfeeds payload")
        record = cPickle.loads(self.payload)

        logger.debug("Checking payload for attachments")
        self.check_attachments(record)

