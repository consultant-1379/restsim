#!/usr/bin/python

import logging
from datetime import datetime


class LoggerUtilities(object):
    logger = None
    is_debug = False

    def set_time_based_logger_object(self, log_name, file_path):
        from logging.handlers import TimedRotatingFileHandler
        self.logger = logging.getLogger(log_name)
        self.logger.setLevel(logging.INFO)
        handler = TimedRotatingFileHandler(file_path, 'MIDNIGHT', 1, 10)
        self.logger.addHandler(handler)

    def get_formatted_local_date_time(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def print_info(self, msg):
        print(self.get_formatted_local_date_time() + ' ' + 'INFO : ' + msg)

    def print_warn(self, msg):
        print(self.get_formatted_local_date_time() + ' ' + 'WARNING : ' + msg)

    def print_error(self, msg):
        print(self.get_formatted_local_date_time() + ' ' + 'ERROR : ' + msg)

    def log_info(self, msg, console_print=False):
        self.logger.info(msg)
        if console_print:
            self.print_info(msg)

    def log_error(self, msg, console_print=False):
        self.logger.error(msg)
        if console_print:
            self.print_error(msg)

    def log_warning(self, msg, console_print=False):
        self.logger.warning(msg)
        if console_print:
            self.print_warn(msg)

    def set_is_debug_value(self, value):
        if value:
            self.is_debug = True
        else:
            self.is_debug = False

    def log_debug(self, msg):
        if self.is_debug:
            print(self.get_formatted_local_date_time() + ' ' + 'DEBUG : ' + msg)
