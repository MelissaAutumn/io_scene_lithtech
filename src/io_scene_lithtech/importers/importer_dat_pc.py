import logging
import os

import bpy
import bmesh
from mathutils import Vector, Quaternion, Color

from ..defines import WORLD_CAMERA_CLIP_END, LOGGER_NAME, WORLD_CAMERA_CLIP_START
from ..dtx import DTX
from ..models.dat import DAT

# Format imports

from .. import utils
from ..utils import get_prefs

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

"""
# TODO: Also need to handle shifting? https://github.com/Shfty/libmap/blob/6e4160924cf5373e67e8f35422b196e6e0eaa52c/src/c/geo_generator.c
func opq_to_uv(vertex : Vector3, o : Vector3, p : Vector3, q : Vector3, tex_width = 128.0, tex_height = 128.0):
	# Origin
	var point = vertex - o
	
	var u = point.dot(p) / tex_width
	var v = point.dot(q) / tex_height
	
	return Vector2(u, v)
# End Func
"""

def opq_to_uv(vertex: Vector, o: Vector, p: Vector, q: Vector, tex_width = 128.0, tex_height = 128.0):
    """Converts the three opq vectors into standard uvs"""
    origin = vertex - o

    u = origin.dot(p) / tex_width
    v = origin.dot(q) / tex_height
    return Vector((u, v))


def _import_world_objects(model: DAT, world_objs_collection):
    """Reads and creates blender objects (lights or empty so far) per each world object in the world"""
    # Load in the world objects
    for obj in model.world_objects:
        name = obj.name or '__unnamed_prop__'

        if obj.type == 'StaticSunLight':
            light_data = bpy.data.lights.new(name=f'{name}_sun', type='SUN')
            light_data.use_shadow = True

            for prop in obj.properties:
                if prop.name == 'InnerColor':
                    light_data.color = Color((prop.value.x, prop.value.y, prop.value.z))
                elif prop.name == 'BrightScale':
                    # TODO: Figure out scale, blender is in watts this is just scale
                    light_data.energy = prop.value * 0.01 # FIXME: This is just broken?

            # Create new object, pass the light data
            light_object = bpy.data.objects.new(name=name, object_data=light_data)
            light_object.location = Vector((-obj.pos.x, -obj.pos.z, obj.pos.y)) or Vector()
            light_object.rotation_quaternion = obj.rotation or Quaternion()

            world_objs_collection.objects.link(light_object)
            continue
        elif obj.type == 'ObjectLight' or obj.type == 'Light':
            light_data = bpy.data.lights.new(name=f'{name}_light', type='POINT')
            light_data.use_shadow = False

            for prop in obj.properties:
                if prop.name == 'LightRadius':
                    # TODO: Figure out scale, blender is a fall off while it seems LT is absolute distance
                    light_data.shadow_soft_size = prop.value
                elif prop.name == 'LightColor':
                    light_data.color = Color((prop.value.x, prop.value.y, prop.value.z))
                elif prop.name == 'BrightScale':
                    # TODO: Figure out scale, blender is in watts this is just scale
                    light_data.energy = prop.value * 1000

            # Create new object, pass the light data
            light_object = bpy.data.objects.new(name=name, object_data=light_data)
            light_object.location = Vector((-obj.pos.x, -obj.pos.z, obj.pos.y)) or Vector()
            light_object.rotation_quaternion = obj.rotation or Quaternion()

            world_objs_collection.objects.link(light_object)
            continue

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

def load_image(context, texture_name: str) -> DTX:
    game_data_dirs = get_prefs(context).game_data_list

    texture_name_split = texture_name.upper().split('\\')

    for item in game_data_dirs:
        game_data_dir = item.game_data_folder

        try:
            image = DTX(os.path.join(game_data_dir, *texture_name_split))
        except (IOError, AttributeError) as ex:
            continue

        return image

    raise IOError(f'Could not find {texture_name}')


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

    _import_world_objects(model, world_objs_collection)

    loaded_textures = {}
    loaded_textures_idx = 0

    for mdl in model.world_models:
        mesh = Data.meshes.new(mdl.name)
        mesh_object = Data.objects.new(mdl.name, mesh)

        # Hide the VisBSP mesh object by default
        if mdl.name == 'VisBSP':
            mesh_object.hide_viewport = True

        # Organizes things in order of appearence
        surface_indices = []
        for texture_name in mdl.texture_list:
            mesh.uv_layers.new(name=texture_name)

            texture_key = texture_name.upper()

            is_texture_loaded = texture_key in loaded_textures

            if is_texture_loaded:
                image = loaded_textures[texture_key]['image']
                texture = loaded_textures[texture_key]['tex']
            else:
                try:
                    image = load_image(Context, texture_name)
                    texture = None
                except (IOError, AttributeError):
                    logger.warning(f"Couldn't open {texture_name}")

                    # Make sure we still align with texture_index
                    material = Data.materials.new(texture_key)
                    mesh.materials.append(material)
                    surface_indices.append(None)
                    loaded_textures[texture_key] = None
                    loaded_textures_idx += 1

                    continue


            ''' Create a material for the new piece. '''
            material = Data.materials.new(texture_key)
            material.use_nodes = True
            mesh.materials.append(material)

            ''' Create texture. '''
            # Create a mix node, and mix the texture (slot A/6), and vertex colour (slot B/7)
            bsdf = material.node_tree.nodes["Principled BSDF"]
            mix = material.node_tree.nodes.new('ShaderNodeMix')
            mix.data_type = 'RGBA'
            tex_image = material.node_tree.nodes.new('ShaderNodeTexImage')
            vcol = material.node_tree.nodes.new(type='ShaderNodeVertexColor')
            vcol.layer_name = 'Col'  # the vertex color layer name

            material.node_tree.links.new(
                tex_image.outputs['Color'], mix.inputs[6]
            )
            material.node_tree.links.new(
                vcol.outputs[0], mix.inputs[7]
            )

            material.node_tree.links.new(bsdf.inputs['Base Color'], mix.outputs[2])

            material.specular_intensity = 0.0

            # TODO: Bit of a hack
            if 'SKY.DTX' in texture_key:
                material.use_transparent_shadow = True
                material.alpha_threshold = 0
                bsdf.inputs["Alpha"].default_value = 0.0

            if not texture:
                texture = Data.textures.new(texture_key, type='IMAGE')

                texture.image = bpy.data.images.new(texture_key, width=image.width, height=image.height, alpha=True, float_buffer=True)
                texture.image.pixels = [float(p) / 255.0 for p in image.pixels]

            tex_image.image = texture.image

            # Save a copy of the loaded image / texture
            if not is_texture_loaded:
                loaded_textures[texture_key] = {
                    'idx': loaded_textures_idx,
                    'tex': texture,
                    'image': image,
                    'texture_key': texture_key
                }
                loaded_textures_idx += 1

            # Append a local mesh reference
            surface_indices.append(loaded_textures[texture_key])

        bm = bmesh.new()
        bm.from_mesh(mesh)

        verts = []
        colours = []
        normals = []

        tri_fans = []
        bm_vert_size = 0
        # Add out bmesh verts, and generate our triangle fan indices
        for idx, poly in enumerate(mdl.polies):
            tri_fan = []
            for disk in poly.disk_vertices:
                vert_idx = disk.vert_idx
                vert_colour = disk.vert_colour

                point = mdl.points[vert_idx]
                vert = point.data
                normal = point.normals

                # axis conversion
                vert = Vector((-vert.x, -vert.z, vert.y))

                bm.verts.new(vert)
                verts.append(point.data)

                if vert_colour[0] > 0 and vert_colour[1] > 0 and vert_colour[2] > 0:
                    colours.append(Vector((vert_colour[0] / 255.0, vert_colour[1] / 255.0, vert_colour[2] / 255.0, 1.0)))
                else:
                    colours.append((0, 0, 0, 0))

                normals.append(normal)
                tri_fan.append(bm_vert_size)
                bm_vert_size += 1

            tri_fans.append( (poly, tri_fan) )

        # Ensure the lookup table is all correct and nice
        bm.verts.ensure_lookup_table()
        bm.verts.index_update()

        # These are triangle fans
        # FIXME: There seems to be some occasional overdraw, nothing terrible but I don't think this is quite right
        for poly, tri_fan in tri_fans:
            for idx in range(0, len(tri_fan)-2):
                face = [
                    bm.verts[tri_fan[idx + 2]],
                    bm.verts[tri_fan[idx + 1]],
                    bm.verts[tri_fan[0]],
                ]

                try:
                    bmface = bm.faces.new(face)
                except ValueError:
                    # I don't think this will ever happen, but we should cover it...
                    logger.debug("Ignoring duplicate face")
                    continue

                surface = mdl.surfaces[poly.surface_index]
                bmface.smooth = not surface.is_flat_shaded

                tex_info = surface_indices[surface.texture_index] if surface.texture_index < len(surface_indices) else None
                if not tex_info:
                    continue

                bmface.material_index = surface.texture_index

                # add uvs to the new face
                uv_layer = bm.loops.layers.uv.verify()
                colour_layer = bm.loops.layers.color.verify()
                #custom_layer = bm.loops.layers.string.verify()
                for i, loop in enumerate(bmface.loops):
                    # Need to use the original un-axis converted vert
                    vert = verts[loop.vert.index]
                    colour = colours[loop.vert.index]
                    uv = opq_to_uv(
                        vert,
                        surface.uv_list[0],
                        surface.uv_list[1],
                        surface.uv_list[2],
                        tex_info['image'].width,
                        tex_info['image'].height
                    )
                    loop[uv_layer].uv = uv
                    loop[colour_layer] = colour

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

