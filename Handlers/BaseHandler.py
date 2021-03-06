#!/usr/bin/env python

import logging
from Modules.ArtemisParsed import ArtemisParsed
from Modules.ThugFiles import ThugFiles

logger = logging.getLogger('artemis')

class BaseHandler(object):

    def __init__(self,ident,db_cursor,config):
        self.ident = ident
        self.db_cursor = db_cursor
        self.config = config
        self.chan = None
        self.module = None
        self.payload = None

    def select_module(self,chan):
        self.chan = str(chan)
        if self.chan == 'artemis.parsed':
            self.module = ArtemisParsed(self.db_cursor,self.config)
            logger.info('Identified channel as {0}'.format(self.chan))
        elif self.chan == 'thug.files':
            self.module = ThugFiles(self.db_cursor,self.config)
            logger.info('Identified channel as {0}'.format(self.chan))
        else:
            logger.info('Could not identify channel {0}'.format(self.chan))


    def handle_payload(self,payload):
        logger.debug('Passing payload to handler')
        self.payload = payload
        if self.module is not None:
            self.module.handle_payload(self.ident,self.payload)
