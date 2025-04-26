import importlib
import os

LOGGER_NAME = 'io_scene_lithtech'
LOGGER_FORMAT = '%(asctime)s %(levelname)s %(message)s'

# Pydev defines
PYDEV_ENABLED = False
PYDEV_SOURCE_DIR = None
PYDEV_HOST = 'localhost'
PYDEV_PORT = 5678

# Pull a django and try to import a local defines file
try:
    from .local_defines import *
except ImportError:
    pass