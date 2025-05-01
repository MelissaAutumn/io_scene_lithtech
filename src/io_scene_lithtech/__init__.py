"""
Init for io_scene_lithtech

The try/except pass allows us to use dtx without needing blender (like with the convert_tex.py script.)
"""

try:
    import logging
    import sys

    import bpy
    from bpy.utils import register_class, unregister_class

    from . import hash_ps2
    from . import s3tc
    from . import dtx
    from . import abc
    from . import builder
    from . import reader_abc_pc
    from . import reader_ltb_ps2
    from . import writer_abc_pc
    from . import writer_lta_pc
    from . import importer
    from . import exporter
    from . import converter

    from .readers import reader_dat_pc
    from .operators import import_operator_dat_pc
    from .importers import importer_dat_pc
    from .models import dat
    from .defines import (
        LOGGER_NAME,
        LOGGER_FORMAT,
        PYDEV_ENABLED,
        PYDEV_HOST,
        PYDEV_PORT,
    )
    from .settings import AddonPrefs, GameData, AddGameDataFolder, RemoveGameDataFolder

    if 'bpy' in locals():
        import importlib
        print('>', locals())

        if 'hash_ps2' in locals():
            importlib.reload(hash_ps2)
        if 's3tc' in locals():
            importlib.reload(s3tc)
        if 'dxt' in locals():
            importlib.reload(dtx)
        if 'abc' in locals():
            importlib.reload(abc)
        if 'builder' in locals():
            importlib.reload(builder)
        if 'reader_abc_pc' in locals():
            importlib.reload(reader_abc_pc)
        if 'reader_dat_pc' in locals():
            importlib.reload(reader_dat_pc)
        if 'reader_ltb_ps2' in locals():
            importlib.reload(reader_ltb_ps2)
        if 'writer_abc_pc' in locals():
            importlib.reload(writer_abc_pc)
        if 'writer_lta_pc' in locals():
            importlib.reload(writer_lta_pc)
        if 'importer' in locals():
            importlib.reload(importer)
        if 'exporter' in locals():
            importlib.reload(exporter)
        if 'converter' in locals():
            importlib.reload(converter)
        if 'import_operator_dat_pc' in locals():
            importlib.reload(import_operator_dat_pc)
        if 'importer_dat_pc' in locals():
            importlib.reload(importer_dat_pc)
        if 'dat' in locals():
            importlib.reload(dat)


    classes = (
        GameData,
        AddonPrefs,
        AddGameDataFolder,
        RemoveGameDataFolder,
        importer.ImportOperatorABC,
        importer.ImportOperatorLTB,
        import_operator_dat_pc.ImportOperatorDATPC,
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
        except Exception:
            logging.debug('Please run the debug server before trying to connect to it.')


    def register():
        for cls in classes:
            register_class(cls)

        # Import options
        bpy.types.TOPBAR_MT_file_import.append(importer.ImportOperatorABC.menu_func_import)
        bpy.types.TOPBAR_MT_file_import.append(importer.ImportOperatorLTB.menu_func_import)
        bpy.types.TOPBAR_MT_file_import.append(
            import_operator_dat_pc.ImportOperatorDATPC.menu_func_import
        )

        # Export options
        bpy.types.TOPBAR_MT_file_export.append(exporter.ExportOperatorABC.menu_func_export)
        bpy.types.TOPBAR_MT_file_export.append(exporter.ExportOperatorLTA.menu_func_export)

        # Converters
        bpy.types.TOPBAR_MT_file_import.append(converter.ConvertPCLTBToLTA.menu_func_import)
        bpy.types.TOPBAR_MT_file_import.append(
            converter.ConvertPS2LTBToLTA.menu_func_import
        )

        # If we don't have an entry then add one by default
        prefs = bpy.context.preferences.addons[__package__].preferences
        if not prefs.game_data_list:
            prefs.game_data_list.add()

        setup_debugger()


    def unregister():
        for cls in reversed(classes):
            unregister_class(cls)

        # Import options
        bpy.types.TOPBAR_MT_file_import.remove(importer.ImportOperatorABC.menu_func_import)
        bpy.types.TOPBAR_MT_file_import.remove(importer.ImportOperatorLTB.menu_func_import)
        bpy.types.TOPBAR_MT_file_import.remove(
            import_operator_dat_pc.ImportOperatorDATPC.menu_func_import
        )

        # Export options
        bpy.types.TOPBAR_MT_file_export.remove(exporter.ExportOperatorABC.menu_func_export)
        bpy.types.TOPBAR_MT_file_export.remove(exporter.ExportOperatorLTA.menu_func_export)

        # Converters
        bpy.types.TOPBAR_MT_file_import.remove(converter.ConvertPCLTBToLTA.menu_func_import)
        bpy.types.TOPBAR_MT_file_import.remove(
            converter.ConvertPS2LTBToLTA.menu_func_import
        )

except Exception as e:  # noqa: E722
    print(f'ERR: {e}')
    print('^ Ignore if this is running outside of blender!')