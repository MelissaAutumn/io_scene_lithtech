import logging
import sys

import bpy
from . import hash_ps2
from . import s3tc
from . import dtx
from . import abc
from . import builder
from . import reader_abc_pc
from . import reader_dat_pc
from . import reader_ltb_ps2
from . import writer_abc_pc
from . import writer_lta_pc
from . import importer
from . import exporter
from . import converter
from .defines import (
    LOGGER_NAME,
    LOGGER_FORMAT,
    PYDEV_SOURCE_DIR,
    PYDEV_ENABLED,
    PYDEV_HOST,
    PYDEV_PORT,
)

if "bpy" in locals():
    import importlib

    if "hash_ps2" in locals():
        importlib.reload(hash_ps2)
    if "s3tc" in locals():
        importlib.reload(s3tc)
    if "dxt" in locals():
        importlib.reload(dtx)
    if "abc" in locals():
        importlib.reload(abc)
    if "builder" in locals():
        importlib.reload(builder)
    if "reader_abc_pc" in locals():
        importlib.reload(reader_abc_pc)
    if "reader_dat_pc" in locals():
        importlib.reload(reader_dat_pc)
    if "reader_ltb_ps2" in locals():
        importlib.reload(reader_ltb_ps2)
    if "writer_abc_pc" in locals():
        importlib.reload(writer_abc_pc)
    if "writer_lta_pc" in locals():
        importlib.reload(writer_lta_pc)
    if "importer" in locals():
        importlib.reload(importer)
    if "exporter" in locals():
        importlib.reload(exporter)
    if "converter" in locals():
        importlib.reload(converter)

from bpy.utils import register_class, unregister_class

classes = (
    importer.ImportOperatorABC,
    importer.ImportOperatorLTB,
    importer.ImportOperatorDAT,
    exporter.ExportOperatorABC,
    exporter.ExportOperatorLTA,
    converter.ConvertPCLTBToLTA,
    converter.ConvertPS2LTBToLTA,
)

# Setup our logger! We don't to register it multiple times, just on the first module load
logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(logging.DEBUG)
if not logger.hasHandlers():
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(LOGGER_FORMAT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def setup_debugger():
    if not PYDEV_ENABLED:
        return

    try:
        # import pydevd module
        import pydevd

        # set debugging enabled
        pydevd.settrace(PYDEV_HOST, True, True, PYDEV_PORT, False, False)
    except:
        logging.debug('Please run the debug server before trying to connect to it.')


def register():
    for cls in classes:
        register_class(cls)

    # Import options
    bpy.types.TOPBAR_MT_file_import.append(importer.ImportOperatorABC.menu_func_import)
    bpy.types.TOPBAR_MT_file_import.append(importer.ImportOperatorLTB.menu_func_import)
    bpy.types.TOPBAR_MT_file_import.append(importer.ImportOperatorDAT.menu_func_import)

    # Export options
    bpy.types.TOPBAR_MT_file_export.append(exporter.ExportOperatorABC.menu_func_export)
    bpy.types.TOPBAR_MT_file_export.append(exporter.ExportOperatorLTA.menu_func_export)

    # Converters
    bpy.types.TOPBAR_MT_file_import.append(converter.ConvertPCLTBToLTA.menu_func_import)
    bpy.types.TOPBAR_MT_file_import.append(
        converter.ConvertPS2LTBToLTA.menu_func_import
    )

    setup_debugger()

def unregister():
    for cls in reversed(classes):
        unregister_class(cls)

    # Import options
    bpy.types.TOPBAR_MT_file_import.remove(importer.ImportOperatorABC.menu_func_import)
    bpy.types.TOPBAR_MT_file_import.remove(importer.ImportOperatorLTB.menu_func_import)
    bpy.types.TOPBAR_MT_file_import.remove(importer.ImportOperatorDAT.menu_func_import)

    # Export options
    bpy.types.TOPBAR_MT_file_export.remove(exporter.ExportOperatorABC.menu_func_export)
    bpy.types.TOPBAR_MT_file_export.remove(exporter.ExportOperatorLTA.menu_func_export)

    # Converters
    bpy.types.TOPBAR_MT_file_import.remove(converter.ConvertPCLTBToLTA.menu_func_import)
    bpy.types.TOPBAR_MT_file_import.remove(
        converter.ConvertPS2LTBToLTA.menu_func_import
    )


