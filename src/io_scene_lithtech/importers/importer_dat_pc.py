import logging

import bpy
import bmesh
from mathutils import Vector, Quaternion

from ..defines import WORLD_CAMERA_CLIP_END, LOGGER_NAME, WORLD_CAMERA_CLIP_START
from ..models.dat import DAT

# Format imports

from .. import utils

logger = logging.getLogger(LOGGER_NAME)

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

    world_mdls_collection = Data.collections.new("world_models")
    world_objs_collection = Data.collections.new("world_objects")
    collection.children.link(world_mdls_collection)
    collection.children.link(world_objs_collection)

    # Update the viewport's camera clip end so we can see things
    for a in bpy.context.screen.areas:
        if a.type == 'VIEW_3D':
            for s in a.spaces:
                if s.type == 'VIEW_3D':
                    s.clip_start = WORLD_CAMERA_CLIP_START
                    s.clip_end = WORLD_CAMERA_CLIP_END

    # Load in the world objects
    for obj in model.world_objects:
        name = obj.name or '__unnamed_prop__'
        bl_obj = bpy.data.objects.new(name, object_data=None)
        # Space conversion
        bl_obj.location = Vector((-obj.pos.x, -obj.pos.z, obj.pos.y)) or Vector()
        bl_obj.rotation_quaternion = obj.rotation or Quaternion()
        bl_obj.empty_display_type = 'SPHERE'

        font_curve = bpy.data.curves.new(type='FONT', name=f'{name}_txt_curve')
        font_curve.body = name
        font_curve.align_x = 'CENTER'
        font_obj = bpy.data.objects.new(name=f'{name}_txt', object_data=font_curve)
        font_obj.parent = bl_obj

        world_objs_collection.objects.link(bl_obj)
        world_objs_collection.objects.link(font_obj)

    for mdl in model.world_models:
        mesh = Data.meshes.new(mdl.name)
        mesh_object = Data.objects.new(mdl.name, mesh)

        bm = bmesh.new()
        bm.from_mesh(mesh)

        normals = []

        tri_fans = []
        bm_vert_size = 0
        for idx, poly in enumerate(mdl.polies):
            tri_fan = []
            for disk in poly.disk_vertices:
                # TODO: Clean this up
                vert_idx = disk.vert_idx
                _vert_colour = disk.vert_colour

                point = mdl.points[vert_idx]
                vert = point.data
                normal = point.normals

                # axis conversion
                vert = Vector((-vert.x, -vert.z, vert.y))

                bm.verts.new(vert)
                normals.append(normal)
                tri_fan.append(bm_vert_size)
                bm_vert_size += 1
            tri_fans.append(tri_fan)

        # Ensure the lookup table is all correct and nice
        bm.verts.ensure_lookup_table()

        # These are triangle fans
        for tri_fan in tri_fans:
            for idx in range(0, len(tri_fan)-2):
                face = [
                    bm.verts[tri_fan[0]],
                    bm.verts[tri_fan[idx + 1]],
                    bm.verts[tri_fan[idx + 2]],
                ]

                try:
                    _bmface = bm.faces.new(face)
                except ValueError:
                    # I don't think this will ever happen, but we should cover it...
                    logger.debug("Ignoring duplicate face")
                    continue

        bm.faces.ensure_lookup_table()
        #mesh.normals_split_custom_set(normals)

        bm.to_mesh(mesh)
        bm.free()

        # Validate and update the mesh
        mesh.validate(clean_customdata=False)
        mesh.update(calc_edges=False)

        # add it to our collection c:
        world_mdls_collection.objects.link(mesh_object)

        pass

    return {'FINISHED'}

