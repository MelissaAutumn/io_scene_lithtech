import bpy
import bpy_extras
import bmesh
import os
import math
from math import ceil
from mathutils import Vector, Matrix
from bpy.props import StringProperty, BoolProperty, FloatProperty
from .dtx import DTX
from .utils import get_framerate

# Format imports
from .reader_abc_v6_pc import ABCV6ModelReader
from .reader_abc_pc import ABCModelReader
from .reader_ltb_pc import PCLTBModelReader
from .reader_ltb_ps2 import PS2LTBModelReader

from . import utils


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

    # This seems to be the rage these days
    Context = bpy.context
    Data = bpy.data
    Ops = bpy.ops
    Types = bpy.types

    # Create our new collection. This will help us later on..
    collection = Data.collections.new(model.name)
    # Add our collection to the scene
    Context.scene.collection.children.link(collection)

    # TODO: clear the orphan list for ultra name purity
    sun = Data.lights.new(name="Sun", type='SUN')
    sun_object = Data.objects.new("Sun", sun)
    collection.objects.link(sun_object)

    # Create the armature
    armature = bpy.data.armatures.new(model.name)
    armature_object = bpy.data.objects.new(model.name, armature)
    armature_object.data.display_type = 'STICK'
    armature_object.show_in_front = True

    collection.objects.link(armature_object)
    armature_object.select_set(True)
    # armature_object.edit_bones()

    Context.view_layer.objects.active = armature_object
    Ops.object.mode_set(mode='EDIT')

    for node in model.nodes:
        bone = armature.edit_bones.new(node.name)
        '''
        We can be assured that the parent will always be found because
        the node list is in the same order as a depth-first traversal of the
        node hierarchy.
        '''
        bone.parent = armature.edit_bones[node.parent.name] if node.parent else None

        # Apply our bind matrix with proper tail and roll.
        tail, roll = Types.Bone.AxisRollFromMatrix(node.bind_matrix.to_3x3())
        bone.head = node.bind_matrix.to_translation()
        bone.tail = tail + bone.head
        bone.roll = roll

        if bone.parent is not None:
            bone.use_connect = bone.parent.tail == bone.head
        # End If
    # End For

    # FIXME: Make bones touch their parents.
    # This however breaks the animations.
    #
    # I think I need to offset this in the animation processing,
    # and animations might be a touch broken right now but it's not noticable...just ugly in blender.
    # ----------------------------
    # for node in model.nodes:
    #     bone = armature.edit_bones[node.name]

    #     if len(bone.children) == 0:
    #         continue
    #     # End If

    #     for child in bone.children:
    #         bone.tail = child.head
    # # End For

    Ops.object.mode_set(mode='OBJECT')

    ''' Add sockets as empties with a child-of constraint to the appropriate bone. '''
    if options.should_import_sockets:
        for socket in model.sockets:
            empty_object = Data.objects.new("s_" + socket.name, None)
            empty_object.location = socket.location
            empty_object.rotation_quaternion = socket.rotation
            empty_object.empty_display_type = 'PLAIN_AXES'
            child_of_constraint = empty_object.constraints.new('CHILD_OF')
            child_of_constraint.target = armature_object
            child_of_constraint.subtarget = model.nodes[socket.node_index].name
            empty_object.parent = armature_object
            collection.objects.link(empty_object)

    ''' Determine the amount of LODs to import. '''
    lod_import_count = model.lod_count if options.should_import_lods else 1

    ''' Create materials. '''
    materials = []

    for i, piece in enumerate(model.pieces):
        while len(materials) <= piece.material_index:
            ''' Create a material for the new piece. '''
            material = Data.materials.new(piece.name)
            material.specular_intensity = piece.specular_power / 100

            material.use_nodes = True

            # TODO: maybe put something in here for the specular scale?
            materials.append(material)

            ''' Create texture. '''

            # Swapped over to nodes
            bsdf = material.node_tree.nodes["Principled BSDF"]
            texImage = material.node_tree.nodes.new('ShaderNodeTexImage')
            material.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])

            texture = Data.textures.new(piece.name, type='IMAGE')

            # Note: Texture image names are stored in ModelButes.txt
            if options.image is not None:
                texture.image = bpy.data.images.new(piece.name, width=options.image.width, height=options.image.height, alpha=True)  # TODO: get real name
                texture.image.pixels[:] = options.image.pixels[:]

            texImage.image = texture.image

    ''' Create a mesh for each piece of each LOD level that we are importing. '''
    for lod_index in range(lod_import_count):
        for piece_index, piece in enumerate(model.pieces):
            lod = piece.lods[lod_index]

            ''' Create the object and mesh. '''
            mesh_name = piece.name
            if options.should_import_lods:
                mesh_name += '.LOD{0!s}'.format(lod_index)
            mesh = Data.meshes.new(model.name)
            mesh_object = Data.objects.new(mesh_name, mesh)

            ''' Add materials to mesh. '''
            for material in materials:
                ''' Create UV map. '''
                '''
                uv_texture = mesh.uv_textures.new()
                mesh.materials.append(material)
                material.texture_slots[0].uv_layer = uv_texture.name
                '''
                uv_texture = mesh.uv_layers.new()
                mesh.materials.append(material)
                # material.uv_layers[0].name = uv_texture.name

            ''' Create a vertex group for each node. '''
            for node in model.nodes:
                mesh_object.vertex_groups.new(name=node.name)

            # TODO: these need to be reset for each mesh
            vertex_offset = 0
            face_offset = 0

            ''' Populate the actual mesh data. '''
            bm = bmesh.new()
            bm.from_mesh(mesh)

            for vertex in lod.vertices:
                bm.verts.new(vertex.location)

            bm.verts.ensure_lookup_table()
            duplicate_face_indices = []
            for face_index, face in enumerate(lod.faces):
                face = [bm.verts[vertex_offset + vertex.vertex_index] for vertex in face.vertices]
                try:
                    bmface = bm.faces.new(face)
                except ValueError:
                    '''
                    This face is a duplicate of another face, which is disallowed by Blender.
                    Mark this face for deletion after iteration.
                    '''
                    duplicate_face_indices.append(face_index)
                    continue
                '''
                Assign the material index of face based on the piece's material index.
                '''
                bmface.material_index = model.pieces[piece_index].material_index
                bmface.smooth = True

            bm.faces.ensure_lookup_table()

            '''
            Warn the user of the number of duplicate faces detected, if any.
            '''
            if len(duplicate_face_indices) > 0:
                print('WARNING: {} duplicate faces detected.'.format(len(duplicate_face_indices)))

            '''
            Delete any of the duplicate faces from the mesh.
            '''
            for face_index in reversed(sorted(duplicate_face_indices)):
                del lod.faces[face_index]

            vertex_offset += len(lod.vertices)
            face_offset += len(lod.faces)

            bm.to_mesh(mesh)
            bm.free()

            '''
            Assign texture coordinates.
            '''
            material_face_offsets = [0] * len(mesh.materials)
            uv_texture = mesh.uv_layers[piece.material_index]

            # Set the correct UV as active
            uv_texture.active = True
            uv_texture.active_render = True

            for face_index, face in enumerate(lod.faces):
                material_face_offset = material_face_offsets[0]  # TODO: is this right?
                texcoords = [vertex.texcoord for vertex in face.vertices]
                for i in range(3):
                    uv = texcoords[i][0], 1.0 - texcoords[i][1]
                    uv_texture.data[(material_face_offset + face_index) * 3 + i].uv = uv
            material_face_offsets[0] += len(lod.faces)

            ''' Assign normals '''
            normals = []
            for polygon in mesh.polygons:
                for loop_index in polygon.loop_indices:
                    vertex_index = mesh.loops[loop_index].vertex_index
                    normal = Vector(lod.vertices[vertex_index].normal)
                    normals.append(normal)
            mesh.normals_split_custom_set(normals)

            mesh.validate(clean_customdata=False)
            mesh.update(calc_edges=False)

            # add it to our collection c:
            collection.objects.link(mesh_object)

            if Ops.object.mode_set.poll():
                Ops.object.mode_set(mode='OBJECT')
            Ops.object.select_all(action='DESELECT')

            ''' Add an armature modifier. '''
            armature_modifier = mesh_object.modifiers.new(name='Armature', type='ARMATURE')
            armature_modifier.object = armature_object
            # TODO: remove if we fix mesh neutral pose bug?
            armature_modifier.show_in_editmode = True
            armature_modifier.show_on_cage = True

            ''' Assign vertex weighting. '''
            vertex_offset = 0
            for (vertex_index, vertex) in enumerate(lod.vertices):
                for weight in vertex.weights:
                    vertex_group_name = model.nodes[weight.node_index].name
                    vertex_group = mesh_object.vertex_groups[vertex_group_name]
                    vertex_group.add([vertex_offset + vertex_index], weight.bias, 'REPLACE')
            vertex_offset += len(lod.vertices)

            # Work-around for PC LTB meshes having overlapping but not connected vertices...
            if options.should_merge_duplicate_verts:
                # Merge duplicates
                bm = bmesh.new()
                bm.from_mesh(mesh)
                bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
                bm.to_mesh(mesh)
                bm.free()

            ''' Parent the mesh to the armature. '''
            mesh_object.parent = armature_object

    ''' Animations '''
    if options.should_import_animations:
        for ob in bpy.context.scene.objects:
            ob.animation_data_clear()

        assert (len(armature.bones) == len(model.nodes))

        armature_object.animation_data_create()

        if options.should_import_vertex_animations:
            for obj in armature_object.children:
                obj.shape_key_add(name="neutral_pose", from_mix=False)
                # we'll animate using mesh.shape_keys.eval_time
                mesh.shape_keys.animation_data_create()
                mesh.shape_keys.use_relative = False

        actions = []
        md_actions = []

        index = 0
        processed_frame_count = 1  # 1 for neutral_pose
        for animation in model.animations:
            print("Processing", animation.name)

            index = index + 1
            # Create a new action with the animation name
            action = bpy.data.actions.new(name=animation.name)

            # Temp set
            armature_object.animation_data.action = action

            if options.should_import_vertex_animations:
                # Create a new shape key action with d_ prefixed animation name
                md_action = Data.actions.new(name="d_%s" % (animation.name))
                mesh.shape_keys.animation_data.action = md_action

            # For every keyframe
            for keyframe_index, keyframe in enumerate(animation.keyframes):
                # Set keyframe time - Scale it down to the default blender animation framerate (25fps)
                subframe_time = keyframe.time * get_framerate()

                # Apply transforms with respect to their parent's transforms
                transform_stack = [None]
                current_index = 0
                while len(transform_stack) > 0:
                    node_index = current_index
                    parent_matrix = transform_stack.pop()

                    node = model.nodes[node_index]
                    pose_bone = armature_object.pose.bones[node_index]

                    # Get the current transform
                    transform = animation.node_keyframe_transforms[node_index][keyframe_index]

                    mat_scale = Matrix()

                    if model.version == 6 and model.flip_anim:
                        transform.rotation.conjugate()
                    # End

                    # Form our animation matrix
                    mat_rot = transform.rotation.to_matrix()
                    mat_loc = Matrix.Translation(transform.location)
                    matrix = mat_loc @ mat_rot.to_4x4() @ mat_scale

                    # If we have a parent, make sure to apply their matrix with ours to get position relative to our parent
                    # otherwise just use our matrix
                    if parent_matrix is not None:
                        matrix = parent_matrix @ matrix

                    pose_bone.matrix = matrix

                    for _ in range(0, node.child_count):
                        transform_stack.append(pose_bone.matrix)

                    current_index += 1

                # For every bone
                for bone, node in zip(armature_object.pose.bones, model.nodes):
                    bone.keyframe_insert('location', frame=subframe_time)
                    bone.keyframe_insert('rotation_quaternion', frame=subframe_time)
                # End For

                if options.should_import_vertex_animations:
                    # shape keys, here I go!
                    for obj in armature_object.children:
                        # create our shape key
                        shape_key = obj.shape_key_add(name="%s_%d" % (animation.name, keyframe_index), from_mix=False)

                        for vert_index, vert in enumerate(obj.data.vertices):
                            our_vert_index = vert_index
                            node_index = model.pieces[0].lods[0].vertices[our_vert_index].weights[0].node_index
                            node = model.nodes[node_index]

                            if node.md_vert_count > 0:
                                md_vert = node.md_vert_list.index(our_vert_index) + (keyframe_index * node.md_vert_count)

                                vertex_transform = animation.vertex_deformations[node_index][md_vert].location
                                shape_key.data[vert_index].co = node.bind_matrix @ vertex_transform
                            # End If
                        # End For
                    # End For

                    mesh.shape_keys.eval_time = shape_key.frame
                    mesh.shape_keys.keyframe_insert("eval_time", frame=subframe_time)
                # End For

            processed_frame_count += len(animation.keyframes)

            # Add to actions array
            actions.append(action)
            if options.should_import_vertex_animations:
                md_actions.append(md_action)

        # Add our actions to animation data
        if actions:
            armature_object.animation_data.action = actions[0]
        if md_actions:
            mesh.shape_keys.animation_data.action = md_actions[0]

    # Set almost sane defaults
    Context.scene.frame_start = 0
    Context.scene.frame_end = ceil(max([animation.keyframes[-1].time * get_framerate() for animation in model.animations]))
    # Set our keyframe time to 0
    Context.scene.frame_set(0)
    # Set this because almost 100% chance you're importing keyframes that aren't aligned to 25fps
    Context.scene.show_subframe = True

    # TODO: make an option to convert to blender coordinate system
    armature_object.rotation_euler.x = math.radians(90)
    armature_object.scale.x = -1.0

    # Apply the geometry flip in armature space
    # This may not be the best place to do it, but it works for now!
    if model.version == 6 or model.flip_geom:
        armature_object.scale.z = -1.0

    return {'FINISHED'}


#
# Real rough, but here's the importer classes
# They're connected in __init__
# These can definitely be combined at some point...
#


class ImportOperatorABC(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = 'io_scene_abc.abc_import'  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = 'Import Lithtech ABC'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    # ImportHelper mixin class uses this
    filepath = ""
    filename_ext = ".abc"

    filter_glob: StringProperty(
        default="*.abc",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    bone_length_min: FloatProperty(
        name='Bone Length',
        default=0.1,
        description='The minimum bone length',
        min=0.01
    )

    should_import_lods: BoolProperty(
        name="Import LODs (Not implemented)",
        description="When checked, LOD meshes will be imported (suffixed with .LOD0, .LOD1 etc.)",
        default=False,
    )

    should_import_animations: BoolProperty(
        name="Import Animations (Experimental)",
        description="When checked, animations will be imported as actions.",
        default=True,
    )

    should_import_vertex_animations: BoolProperty(
        name="Import Vertex Animations (Experimental)",
        description="When checked, vertex animations will be imported. (Requires Import Animations.)",
        default=False,
    )

    should_import_sockets: BoolProperty(
        name="Import Sockets",
        description="When checked, sockets will be imported as Empty objects.",
        default=False,
    )

    should_merge_pieces: BoolProperty(
        name="Merge Pieces (Not implemented)",
        description="When checked, pieces that share a material index will be merged.",
        default=False,
    )

    should_import_textures: BoolProperty(
        name="Import Textures (WIP)",
        description="When checked, pieces that share a material index will be merged.",
        default=False,
    )

    should_clear_scene: BoolProperty(
        name="Clear Scene",
        description="When checked, the scene will be cleared before the model is imported.",
        default=False,
    )

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text='Nodes')
        box.row().prop(self, 'bone_length_min')
        box.row().prop(self, 'should_import_sockets')

        box = layout.box()
        box.label(text='Meshes')
        box.row().prop(self, 'should_import_lods')
        box.row().prop(self, 'should_merge_pieces')

        box = layout.box()
        box.label(text='Materials')
        box.row().prop(self, 'should_import_textures')
        # box.row().prop(self, 'should_assign_materials')

        box = layout.box()
        box.label(text='Animations')
        box.row().prop(self, 'should_import_animations')
        box.row().prop(self, 'should_import_vertex_animations')

        box = layout.box()
        box.label(text='Misc')
        box.row().prop(self, 'should_clear_scene')

    def execute(self, context):
        # Load the model
        try:
            model = ABCModelReader().from_file(self.filepath)
        except Exception:
            model = ABCV6ModelReader().from_file(self.filepath)

        model.name = os.path.splitext(os.path.basename(self.filepath))[0]
        image = None
        if self.should_import_textures:
            filename = os.path.splitext(os.path.basename(self.filepath))[0]
            skins_directory = os.path.join(os.path.dirname(self.filepath), '..', 'SKINS')
            texture = os.path.join(skins_directory, filename + '.DTX')
            try:
                image = DTX(texture)
            except IOError:
                pass
        options = ModelImportOptions()
        options.bone_length_min = self.bone_length_min
        options.should_import_lods = self.should_import_lods
        options.should_import_animations = self.should_import_animations
        options.should_import_vertex_animations = self.should_import_vertex_animations
        options.should_import_sockets = self.should_import_sockets
        options.should_merge_pieces = self.should_merge_pieces
        options.should_clear_scene = self.should_clear_scene
        options.image = image
        import_model(model, options)
        return {'FINISHED'}

    @staticmethod
    def menu_func_import(self, context):
        self.layout.operator(ImportOperatorABC.bl_idname, text='Lithtech ABC (.abc)')


class ImportOperatorLTB(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = 'io_scene_lithtech.ltb_import'  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = 'Import Lithtech LTB'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    # ImportHelper mixin class uses this
    filename_ext = ".ltb"

    filter_glob: StringProperty(
        default="*.ltb",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    bone_length_min: FloatProperty(
        name='Bone Length',
        default=0.1,
        description='The minimum bone length',
        min=0.01
    )

    should_import_lods: BoolProperty(
        name="Import LODs",
        description="When checked, LOD meshes will be imported (suffixed with .LOD0, .LOD1 etc.)",
        default=False,
    )

    should_import_animations: BoolProperty(
        name="Import Animations",
        description="When checked, animations will be imported as actions.",
        default=True,
    )

    should_import_sockets: BoolProperty(
        name="Import Sockets",
        description="When checked, sockets will be imported as Empty objects.",
        default=False,
    )

    should_merge_pieces: BoolProperty(
        name="Merge Pieces (not yet working)",
        description="When checked, pieces that share a material index will be merged.",
        default=False,
    )

    should_import_textures: BoolProperty(
        name="Import Textures (WIP)",
        description="When checked, pieces that share a material index will be merged.",
        default=False,
    )

    should_clear_scene: BoolProperty(
        name="Clear Scene",
        description="When checked, the scene will be cleared before the model is imported.",
        default=True,
    )

    should_merge_duplicate_verts: BoolProperty(
        name="Merge Duplicate Vertices",
        description="When checked, any overlapping but non-connected vertices will be merged. (Recommended  for PC LTB files.)",
        default=True,
    )

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text='Nodes')
        # box.row().prop(self, 'bone_length_min')
        box.row().prop(self, 'should_import_sockets')

        box = layout.box()
        box.label(text='Meshes')
        box.row().prop(self, 'should_merge_duplicate_verts')
        # box.row().prop(self, 'should_import_lods')
        # box.row().prop(self, 'should_merge_pieces')

        # box = layout.box()
        # box.label(text='Materials')
        # box.row().prop(self, 'should_import_textures')
        # # box.row().prop(self, 'should_assign_materials')

        box = layout.box()
        box.label(text='Animations')
        box.row().prop(self, 'should_import_animations')

        box = layout.box()
        box.label(text='Misc')
        box.row().prop(self, 'should_clear_scene')

    def execute(self, context):

        # Load the model
        try:
            model = PCLTBModelReader().from_file(self.filepath)
        except Exception:
            model = PS2LTBModelReader().from_file(self.filepath)

        model.name = os.path.splitext(os.path.basename(self.filepath))[0]
        image = None
        if self.should_import_textures:
            filename = os.path.splitext(os.path.basename(self.filepath))[0]
            skins_directory = os.path.join(os.path.dirname(self.filepath), '..', 'SKINS')
            texture = os.path.join(skins_directory, filename + '.DTX')
            try:
                image = DTX(texture)
            except IOError:
                pass
        options = ModelImportOptions()
        options.bone_length_min = self.bone_length_min
        options.should_import_lods = self.should_import_lods
        options.should_import_animations = self.should_import_animations
        options.should_import_vertex_animations = False
        options.should_import_sockets = self.should_import_sockets
        options.should_merge_pieces = self.should_merge_pieces
        options.should_clear_scene = self.should_clear_scene
        options.should_merge_duplicate_verts = self.should_merge_duplicate_verts
        options.image = image
        import_model(model, options)

        return {'FINISHED'}

    @staticmethod
    def menu_func_import(self, context):
        self.layout.operator(ImportOperatorLTB.bl_idname, text='Lithtech LTB (.ltb)')
