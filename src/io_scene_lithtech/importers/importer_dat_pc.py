
import bpy
import bmesh
import math
from math import ceil
from mathutils import Vector, Matrix
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


def import_model(model, options: ModelImportOptions):
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



    return {'FINISHED'}

