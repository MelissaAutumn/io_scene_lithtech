from bpy.types import Operator, AddonPreferences, PropertyGroup
from bpy.props import StringProperty, CollectionProperty, BoolProperty

class GameData(PropertyGroup):
    game_data_folder: StringProperty(
        name='Game Data Folder',
        description='The folder that contains game data like the WORLDS folder, and TEXTURES. '
                    '(e.g. ~/Games/No One Lives Forever/NOLF or C:\\Games\\No One Lives Forever\\NOLF)',
        subtype='DIR_PATH',
    )

class AddGameDataFolder(Operator):
    bl_idname = 'io_scene_lithtech.add_game_data_folder'
    bl_label = "Add empty row"
    bl_options = {'REGISTER'}

    def execute(self, context): # Runs by default
        prefs = context.preferences.addons[__package__].preferences
        game_data_list = prefs.game_data_list
        game_data_list.add()

        return {'FINISHED'}

class RemoveGameDataFolder(Operator):
    bl_idname = 'io_scene_lithtech.remove_game_data_folder'
    bl_label = "Remove empty rows"
    bl_options = {'REGISTER'}

    def execute(self, context): # Runs by default
        prefs = context.preferences.addons[__package__].preferences
        game_data_list = prefs.game_data_list
        for idx, item in enumerate(game_data_list):
            if not item.game_data_folder:
                game_data_list.remove(idx)

        return {'FINISHED'}

class AddonPrefs(AddonPreferences):
    bl_idname = __package__

    game_data_list: CollectionProperty(type=GameData)

    def draw(self, context):
        layout = self.layout
        layout.label(text='List of folders this addon will use for various file searching:')
        for item in self.game_data_list:
            layout.prop(item, 'game_data_folder')
        layout.operator(AddGameDataFolder.bl_idname)
        layout.operator(RemoveGameDataFolder.bl_idname)
        layout.label(text='IMPORTANT: After making changes be sure to click on ☰ -> Save Preferences!')

