import sys
import os
import logging
from logging.handlers import RotatingFileHandler

class AgentLogger(object):
    def __init__(self, level=logging.ERROR, log_dir=None) -> None:
        self.logger = logging.getLogger('agent logger')
        self.level = level if not self.debugger_is_active() else logging.DEBUG

        self.logger.setLevel(self.level)
        self.set_formatter()
        self.set_log_handler(log_dir)

        pass

    def set_formatter(self):
        self.formatter = logging.Formatter(
        '[%(levelname)s]\t%(asctime)s\t%(message)s'
        )

    def set_log_handler(self, log_dir):
        if log_dir:
            fhandler = RotatingFileHandler(
                os.path.join(log_dir, 'agent.log'),
                maxBytes=4096, backupCount=10
            )
            fhandler.setFormatter(self.formatter)
            self.logger.addHandler(fhandler)
        else:
            pass
        shandler = logging.StreamHandler()
        shandler.setFormatter(self.formatter)
        self.logger.addHandler(shandler)
        
    def debugger_is_active(self) -> bool:
        gettrace = getattr(sys, 'gettrace', lambda : None) 
        return gettrace() is not None
    