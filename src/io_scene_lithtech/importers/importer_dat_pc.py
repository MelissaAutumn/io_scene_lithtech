import logging
import os
from math import radians

import bpy
import bmesh
from mathutils import Vector, Color, Euler

from ..defines import LOGGER_NAME
from ..dtx import DTX
from ..models.dat import DAT

# Format imports

from .. import utils
from ..utils import get_prefs

logger = logging.getLogger(LOGGER_NAME)


class ModelImportOptions(object):
    clear_scene = True
    import_lights = True
    import_entities = True
    import_geometry = True
    hide_vis_by_default = True

    scale = 0.015625  # 64 units = 1 meter (it works out well enough)
    light_scale = 1.0
    sun_light_scale = 0.01  # Sun is reeeeallly bright

    bone_length_min = 0.1


def opq_to_uv(
    vertex: Vector, o: Vector, p: Vector, q: Vector, tex_width=128.0, tex_height=128.0
):
    """Converts the three opq vectors into standard uvs"""
    origin = vertex - o

    u = origin.dot(p) / tex_width
    v = origin.dot(q) / tex_height
    return Vector((u, v))


def _import_world_objects(
    model: DAT, world_objs_collection, options: ModelImportOptions
):
    """Reads and creates blender objects (lights or empty so far) per each world object in the world"""

    # Load in the world objects
    for obj in model.world_objects:
        name = obj.name or '__unnamed_prop__'

        if (
            obj.type == 'StaticSunLight'
            or obj.type == 'ObjectLight'
            or obj.type == 'DirLight'
            or obj.type == 'Light'
        ) and options.import_lights:
            is_sun = obj.type == 'StaticSunLight'
            is_point = obj.type == 'ObjectLight' or obj.type == 'Light'
            is_spot = obj.type == 'DirLight'

            if is_sun:
                light_data = bpy.data.lights.new(name=f'{name}_sun', type='SUN')
                light_data.use_shadow = True
            elif is_point:
                light_data = bpy.data.lights.new(name=f'{name}_light', type='POINT')
                light_data.use_shadow = False
            elif is_spot:
                light_data = bpy.data.lights.new(name=f'{name}_light', type='SPOT')
                light_data.use_shadow = False
            else:
                continue

            for prop in obj.properties:
                if prop.name == 'LightRadius':
                    # TODO: Figure out scale, blender is a fall off while it seems LT is absolute distance
                    light_data.shadow_soft_size = prop.value * options.scale
                elif prop.name == 'LightColor':
                    light_data.color = Color((prop.value.x, prop.value.y, prop.value.z))
                elif prop.name == 'BrightScale':
                    # TODO: Figure out scale, blender is in watts this is just scale
                    # light_data.energy = prop.value * (1000 if not is_sun else 0.01)
                    light_data.energy = (
                        prop.value * options.light_scale
                        if not is_sun
                        else prop.value * options.sun_light_scale
                    )
                elif prop.name == 'InnerColor':
                    light_data.color = Color((prop.value.x, prop.value.y, prop.value.z))
                # elif prop.name == 'CastShadows' or prop.name == 'ClipLight':
                #    light_data.use_shadow = True
                elif prop.name == 'FOV':
                    light_data.spot_size = radians(prop.value)

            # Create new object, pass the light data
            light_object = bpy.data.objects.new(name=name, object_data=light_data)
            light_object.location = (
                Vector((-obj.pos.x, -obj.pos.z, obj.pos.y)) * options.scale
                if obj.pos
                else Vector()
            )

            light_object.rotation_mode = 'XYZ'
            # Gotta rotate X by -90deg, ya just gotta.
            rot = Euler(obj.rotation, 'XYZ')
            rot.rotate(Euler((radians(-90), 0, 0)))
            light_object.rotation_euler = rot or Euler()

            world_objs_collection.objects.link(light_object)
            continue

        if options.import_entities:
            bl_obj = bpy.data.objects.new(name, object_data=None)
            # Space conversion
            bl_obj.location = (
                Vector((-obj.pos.x, -obj.pos.z, obj.pos.y)) * options.scale
                if obj.pos
                else Vector()
            )
            # bl_obj.location = obj.pos * options.scale

            bl_obj.rotation_mode = 'XYZ'
            # Gotta rotate X by -90deg, ya just gotta.
            rot = Euler(obj.rotation, 'XYZ')
            rot.rotate(Euler((radians(-90), 0, 0)))
            bl_obj.rotation_euler = rot or Euler()

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
        except (IOError, AttributeError):
            continue

        return image

    raise IOError(f'Could not find {texture_name}')


def import_model(model: DAT, options: ModelImportOptions):
    if options.clear_scene:
        utils.clear_scene()

    Context = bpy.context
    Data = bpy.data
    Ops = bpy.ops
    Types = bpy.types

    # Create our new collection. This will help us later on..
    collection = Data.collections.new(model.name)
    # Add our collection to the scene
    Context.scene.collection.children.link(collection)

    world_mdls_collection = Data.collections.new('world_models')
    world_objs_collection = Data.collections.new('world_objects')
    collection.children.link(world_mdls_collection)
    collection.children.link(world_objs_collection)

    # Handle ambient light here
    ambient_light = model.world_info.get('ambientlight')
    if ambient_light and options.import_lights:
        # Ambient light contains 3 values separated by spaces
        r, g, b = ambient_light.split(' ')
        r = float(r) / 255.0
        g = float(g) / 255.0
        b = float(b) / 255.0
        bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = [r, g, b, 1.0]

    _import_world_objects(model, world_objs_collection, options)

    loaded_textures = {}
    loaded_textures_idx = 0

    if not options.import_geometry:
        return {'FINISHED'}

    for mdl in model.world_models:
        mesh = Data.meshes.new(mdl.name)
        mesh_object = Data.objects.new(mdl.name, mesh)

        # Hide the VisBSP mesh object by default
        # FIXME: Hack for now
        if (
            any(
                mdl.name == obj.name and obj.type in ['AIVolume']
                for obj in model.world_objects
            )
            or (mdl.name == 'VisBSP' and options.hide_vis_by_default)
        ):
            mesh_object.hide_viewport = True

        # Organizes things in order of appearence
        surface_indices = []
        for texture_name in mdl.texture_list:
            mesh.uv_layers.new(name=texture_name)

            texture_key = texture_name.upper()

            is_texture_loaded = texture_key in loaded_textures

            if is_texture_loaded:
                if loaded_textures[texture_key] is None:
                    continue

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

            """ Create a material for the new piece. """
            material = Data.materials.new(texture_key)
            material.use_nodes = True
            mesh.materials.append(material)

            """ Create texture. """
            # Create a mix node, and mix the texture (slot A/6), and vertex colour (slot B/7)
            bsdf = material.node_tree.nodes['Principled BSDF']
            mix = material.node_tree.nodes.new('ShaderNodeMix')
            mix.data_type = 'RGBA'
            mix.inputs[0].default_value = 0.1  # Factor
            tex_image = material.node_tree.nodes.new('ShaderNodeTexImage')
            vcol = material.node_tree.nodes.new(type='ShaderNodeVertexColor')
            vcol.layer_name = 'Col'  # the vertex color layer name

            material.node_tree.links.new(tex_image.outputs['Color'], mix.inputs[6])
            material.node_tree.links.new(vcol.outputs[0], mix.inputs[7])

            bsdf.inputs['Roughness'].default_value = 1.0
            material.node_tree.links.new(bsdf.inputs['Base Color'], mix.outputs[2])

            material.specular_intensity = 0.0

            # TODO: Bit of a hack
            if any(
                tex in texture_key
                for tex in [
                    'TEX\\SKY.DTX',
                    'TEX\\SOUND.DTX',
                    'TEX\\AI.DTX',
                    'TEX\\INVISIBLE.DTX',
                    'TEX\\NOTHING.DTX',
                    'TEX\\HULLMARKER.DTX',
                    'TEX\\OCCLUDER.TEX',
                ]
            ):
                material.use_transparent_shadow = True
                material.alpha_threshold = 0
                bsdf.inputs['Alpha'].default_value = 0.0

            if not texture:
                texture = Data.textures.new(texture_key, type='IMAGE')

                texture.image = bpy.data.images.new(
                    texture_key,
                    width=image.width,
                    height=image.height,
                    alpha=True,
                    float_buffer=True,
                )
                texture.image.pixels = [float(p) / 255.0 for p in image.pixels]

            tex_image.image = texture.image

            # Save a copy of the loaded image / texture
            if not is_texture_loaded:
                loaded_textures[texture_key] = {
                    'idx': loaded_textures_idx,
                    'tex': texture,
                    'image': image,
                    'texture_key': texture_key,
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
                vert = Vector((-vert.x, -vert.z, vert.y)) * options.scale
                # vert = vert * options.scale

                bm.verts.new(vert)
                verts.append(point.data)

                if vert_colour[0] > 0 and vert_colour[1] > 0 and vert_colour[2] > 0:
                    colours.append(
                        Vector(
                            (
                                vert_colour[0] / 255.0,
                                vert_colour[1] / 255.0,
                                vert_colour[2] / 255.0,
                                1.0,
                            )
                        )
                    )
                else:
                    colours.append((0, 0, 0, 0))

                normals.append(normal)
                tri_fan.append(bm_vert_size)
                bm_vert_size += 1

            tri_fans.append((poly, tri_fan))

        # Ensure the lookup table is all correct and nice
        bm.verts.ensure_lookup_table()
        bm.verts.index_update()

        # These are triangle fans
        # FIXME: There seems to be some occasional overdraw, nothing terrible but I don't think this is quite right
        for poly, tri_fan in tri_fans:
            for idx in range(0, len(tri_fan) - 2):
                face = [
                    bm.verts[tri_fan[idx + 2]],
                    bm.verts[tri_fan[idx + 1]],
                    bm.verts[tri_fan[0]],
                ]

                try:
                    bmface = bm.faces.new(face)
                except ValueError:
                    # I don't think this will ever happen, but we should cover it...
                    logger.debug('Ignoring duplicate face')
                    continue

                surface = mdl.surfaces[poly.surface_index]
                bmface.smooth = not surface.is_flat_shaded

                tex_info = (
                    surface_indices[surface.texture_index]
                    if surface.texture_index < len(surface_indices)
                    else None
                )
                if not tex_info:
                    continue

                bmface.material_index = surface.texture_index

                # add uvs to the new face
                uv_layer = bm.loops.layers.uv.verify()
                colour_layer = bm.loops.layers.color.verify()
                # custom_layer = bm.loops.layers.string.verify()
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
                        tex_info['image'].height,
                    )
                    loop[uv_layer].uv = uv
                    loop[colour_layer] = colour

        bm.faces.ensure_lookup_table()
        # mesh.normals_split_custom_set(normals)

        bm.to_mesh(mesh)
        bm.free()

        # Validate and update the mesh
        mesh.validate(clean_customdata=False)
        mesh.update(calc_edges=False)

        # add it to our collection c:
        world_mdls_collection.objects.link(mesh_object)

        pass

    return {'FINISHED'}
