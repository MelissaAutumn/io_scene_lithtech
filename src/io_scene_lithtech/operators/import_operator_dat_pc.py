import bpy
from bpy.props import StringProperty
import bpy_extras

from ..readers.reader_dat_pc import DATModelReader
from ..importers.importer_dat_pc import import_model, ModelImportOptions

class ImportOperatorDATPC(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""

    bl_idname = 'io_scene_lithtech.dat_import'  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = 'Import Lithtech DAT'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    # ImportHelper mixin class uses this
    filepath = ''
    filename_ext = '.dat'

    filter_glob: StringProperty(
        default='*.dat',
        options={'HIDDEN'},
        maxlen=255,
    )

    def draw(self, context):
        _layout = self.layout


    def execute(self, context):
        # Load the model
        print('Loading dat!', self.filepath)

        model = DATModelReader().from_file(self.filepath)

        import_model(model, options=ModelImportOptions())

        return {'FINISHED'}

    @staticmethod
    def menu_func_import(self, context):
        self.layout.operator(ImportOperatorDATPC.bl_idname, text='Lithtech DAT (.dat)')
