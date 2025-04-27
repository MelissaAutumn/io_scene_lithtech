
import bpy
import bmesh
import math
from math import ceil
from mathutils import Vector, Matrix, Quaternion

from ..defines import WORLD_CAMERA_CLIP_END
from ..models.dat import DAT
from ..utils import get_framerate

# Format imports

from .. import utils


class ModelImportOptions(object):
    should_merge_duplicate_verts = False
    should_import_animations = False
    should_import_sockets = False
    should_import_lods = False
    should_merge_pieces = False
    should_clear_scene = False

    bone_length_min = 0.1
    image = None


def import_model(model: DAT, options: ModelImportOptions):
    if options.should_clear_scene:
        utils.clear_scene()

    Context = bpy.context
    Data = bpy.data
    Ops = bpy.ops
    Types = bpy.types

    # Create our new collection. This will help us later on..
    collection = Data.collections.new(model.name)
    # Add our collection to the scene
    Context.scene.collection.children.link(collection)

    world_objs_collection = Data.collections.new("world_objects")
    Context.scene.collection.children.link(world_objs_collection)

    # Update the viewport's camera clip end so we can see things
    for a in bpy.context.screen.areas:
        if a.type == 'VIEW_3D':
            for s in a.spaces:
                if s.type == 'VIEW_3D':
                    s.clip_end = WORLD_CAMERA_CLIP_END

    for obj in model.world_objects:
        name = obj.name or '__unnamed_prop__'
        bl_obj = bpy.data.objects.new(name, object_data=None)
        # Space conversion
        bl_obj.location = Vector((-obj.pos.x, -obj.pos.z, obj.pos.y)) or Vector()
        bl_obj.rotation_quaternion = obj.rotation or Quaternion()
        bl_obj.rotation_euler.x = math.radians(90)
        bl_obj.empty_display_type = 'SPHERE'

        font_curve = bpy.data.curves.new(type='FONT', name=f'{name}_txt_curve')
        font_curve.body = name
        font_curve.align_x = 'CENTER'
        font_obj = bpy.data.objects.new(name=f'{name}_txt', object_data=font_curve)
        font_obj.parent = bl_obj

        world_objs_collection.objects.link(bl_obj)
        world_objs_collection.objects.link(font_obj)

    return {'FINISHED'}

