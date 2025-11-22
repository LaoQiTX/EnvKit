import logging
import sys
import os

_logger = None

def get_logger(name: str) -> logging.Logger:
    global _logger
    if _logger is None:
        logger = logging.getLogger(name)
        logger.propagate = False
        if getattr(sys, 'frozen', False):
            logger.setLevel(logging.CRITICAL)
            logger.addHandler(logging.NullHandler())
        else:
            level = os.getenv('ENVKIT_LOG_LEVEL', 'INFO').upper()
            logger.setLevel(getattr(logging, level, logging.INFO))
            ch = logging.StreamHandler(sys.stdout)
            ch.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
            logger.addHandler(ch)
        _logger = logger
    return _logger
