import logging
import traceback

from mathutils import Vector, Matrix, Quaternion
from typing import BinaryIO

from ..defines import LOGGER_NAME
from ..io import unpack
from ..models.dat import (
    DAT,
    QuadTree,
    WorldModel,
    Vertex,
    Plane,
    Surface,
    Poly,
    Leaf,
    LeafData,
    Node,
    UserPortal,
    WorldObject,
    WorldPropertyString,
    WorldPropertyVector,
    WorldPropertyFloat,
    WorldPropertyBool,
    WorldPropertyInt,
    WorldPropertyRotation,
    Point,
    DiskVert,
)

logger = logging.getLogger(LOGGER_NAME)


class DATModelReader:
    """Reader class for DATv66 files
    You'll probably want to call from_file with a file path to the DAT file you want to read in."""

    def _read_matrix(self, f: BinaryIO) -> Matrix:
        data = unpack('16f', f)
        rows = [data[0:4], data[4:8], data[8:12], data[12:16]]
        return Matrix(rows)

    def _read_vector(self, f: BinaryIO) -> Vector:
        return Vector(unpack('3f', f))

    def _read_quaternion(self, f: BinaryIO) -> Quaternion:
        x, y, z, w = unpack('4f', f)
        return Quaternion((w, x, y, z))

    def _read_string(self, f: BinaryIO, long_string=False) -> str:
        return f.read(unpack('H' if long_string is False else 'I', f)[0]).decode(
            'ascii'
        )

    def _read_header(self, f: BinaryIO) -> DAT:
        """Read in the DAT header including info block up until the quadtree."""
        dat = DAT()
        # Header
        dat.version = unpack('I', f)[0]
        dat.object_data_pos = unpack('I', f)[0]
        dat.render_data_pos = unpack('I', f)[0]
        _padding = unpack('8I', f)
        # Info block
        dat.world_info_string = self._read_string(f, long_string=True)
        dat.lightmap_grid_size = unpack('f', f)[0]
        dat.boundary_min = self._read_vector(f)
        dat.boundary_max = self._read_vector(f)
        return dat

    def _read_quadtree(self, f: BinaryIO) -> QuadTree:
        """Read what I assume is a quadtree, we don't really use this data, but we need to read it."""
        quadtree = QuadTree()
        quadtree.box_min = self._read_vector(f)
        quadtree.box_max = self._read_vector(f)
        quadtree.node_count = unpack('i', f)[0]
        quadtree.dummy_terrain_depth = unpack('i', f)[0]

        tree_stack = [(8, 0)]  # (bit, byte)
        current_byte = 0
        current_bit = 8
        while len(tree_stack) > 0:
            _ = tree_stack.pop()

            if current_bit == 8:
                current_byte = unpack('B', f)[0]
                current_bit = 0

            subdivide = (current_byte & (1 << current_bit)) > 0

            current_bit += 1

            if subdivide:
                # TODO: Put this data somewhere...
                quadtree.tree_data.append(current_byte)

                layouts = [(current_bit, current_byte)] * 4
                tree_stack += layouts

        return quadtree

    def _read_vertex(self, f: BinaryIO) -> Vertex:
        vertex = Vertex()
        vertex.count = unpack('B', f)[0]
        vertex.extra = unpack('B', f)[0]
        return vertex

    def _read_leaf(self, f: BinaryIO) -> Leaf:
        leaf = Leaf()
        data_count = unpack('H', f)[0]
        if data_count == 0xFFFF:
            # Dummy I think
            _unk = unpack('H', f)[0]
        else:
            for _ in range(0, data_count):
                leaf_data = LeafData()
                leaf_data.portal_id = unpack('H', f)[0]
                count = unpack('H', f)[0]
                leaf_data.contents = list(unpack(f'{count}B', f))
                leaf.leaf_data.append(leaf_data)

        polygon_count = unpack('I', f)[0]
        leaf.polygons = list(unpack(f'{polygon_count * 4}B', f))
        _unk2 = unpack('I', f)[0]
        return leaf

    def _read_plane(self, f: BinaryIO) -> Plane:
        plane = Plane()
        plane.normal = self._read_vector(f)
        plane.distance = unpack('f', f)[0]
        return plane

    def _read_surface(self, f: BinaryIO) -> Surface:
        surface = Surface()
        # One for each vertex on this surface
        surface.uv_list[0] = self._read_vector(f)
        surface.uv_list[1] = self._read_vector(f)
        surface.uv_list[2] = self._read_vector(f)

        surface.texture_index = unpack('H', f)[0]
        surface.plane_index = unpack('I', f)[0]
        surface.flags = unpack('I', f)[0]
        _unk2 = unpack('I', f)[0]
        surface.use_effects = unpack('B', f)[0]
        if surface.use_effects:
            surface.effect = self._read_string(f)
            surface.effect_param = self._read_string(f)
        surface.texture_flags = unpack('H', f)[0]
        return surface

    def _read_poly(self, f: BinaryIO, vertex: Vertex) -> Poly:
        poly = Poly()
        poly.center = self._read_vector(f)
        poly.lightmap_width = unpack('H', f)[0]
        poly.lightmap_height = unpack('H', f)[0]

        # ?
        unk = unpack('H', f)[0]
        if unk > 0:
            _unk_list = unpack(f'{unk * 2}H', f)

        poly.surface_index = unpack('H', f)[0]
        poly.plane_index = unpack('H', f)[0]

        for _ in range(0, vertex.count + vertex.extra):
            disk_vert = DiskVert()
            disk_vert.vert_idx = unpack('H', f)[0]
            disk_vert.vert_colour = unpack('3B', f)

            poly.disk_vertices.append(disk_vert)

        return poly

    def _read_node(self, f: BinaryIO) -> Node:
        node = Node()
        node.poly_index = unpack('I', f)[0]
        node.leaf_index = unpack('H', f)[0]
        node.node_indices = list(unpack('2I', f))
        return node

    def _read_user_portal(self, f: BinaryIO) -> UserPortal:
        user_portal = UserPortal()
        user_portal.name = self._read_string(f)
        _unk = unpack('I', f)[0]
        _unk2 = unpack('I', f)[0]
        _unk3 = unpack('H', f)[0]
        user_portal.center = self._read_vector(f)
        #user_portal.dims = self._read_vector(f)
        _unk4 = unpack('2f', f)
        return user_portal

    def _read_point(self, f: BinaryIO) -> Point:
        point = Point()
        point.data = self._read_vector(f)
        point.normals = self._read_vector(f)
        return point

    def _read_pblock_table(self, f: BinaryIO):
        """Read what I assume is a physics block table, we just skip it for now..."""
        x, y, z = unpack('3I', f)
        size = x * y * z

        # I assume?
        _min_box = self._read_vector(f)
        _max_box = self._read_vector(f)

        data = []

        for _ in range(0, size):
            pblock_size = unpack('H', f)[0]
            pblock_unk1 = unpack('H', f)[0]
            pblock_contents = []

            for _ in range(0, pblock_size):
                vert_idx = unpack('H', f)[0]
                quat = unpack('4B', f)
                pblock_contents.append((vert_idx, quat))
            data.append((pblock_size, pblock_unk1, pblock_contents))

    def _read_world_model(self, f: BinaryIO) -> WorldModel:
        logger.debug(f'Reading world model @ {f.tell()}')
        world_model = WorldModel()
        world_model.info_flags = unpack('I', f)[0]
        _unk = unpack('I', f)[0]
        world_model.name = self._read_string(f)
        world_model.point_count = unpack('I', f)[0]
        world_model.plane_count = unpack('I', f)[0]
        world_model.surface_count = unpack('I', f)[0]
        world_model.user_portal_count = unpack('I', f)[0]
        world_model.poly_count = unpack('I', f)[0]
        world_model.leaf_count = unpack('I', f)[0]
        world_model.vertex_count = unpack('I', f)[0]
        world_model.total_vis_list_size = unpack('I', f)[0]
        world_model.leaf_list_count = unpack('I', f)[0]
        world_model.node_count = unpack('I', f)[0]
        _unk2 = unpack('I', f)[0]
        _unk3 = unpack('I', f)[0]
        world_model.min_box = self._read_vector(f)
        world_model.max_box = self._read_vector(f)
        world_model.world_offset = self._read_vector(f)

        texture_name_len = unpack('I', f)[0]
        texture_count = unpack('I', f)[0]
        textures = list(unpack(f'{texture_name_len}c', f))
        tmp = b''
        for char in textures:
            if char == b'\0':
                world_model.texture_list.append(tmp.decode())
                tmp = b''
                continue
            tmp += char
        assert len(world_model.texture_list) == texture_count

        world_model.vertices = [
            self._read_vertex(f)
            for _ in range(0, world_model.poly_count)  # Yes polycount
        ]
        world_model.leafs = [
            self._read_leaf(f) for _ in range(0, world_model.leaf_count)
        ]
        world_model.planes = [
            self._read_plane(f) for _ in range(0, world_model.plane_count)
        ]
        world_model.surfaces = [
            self._read_surface(f) for _ in range(0, world_model.surface_count)
        ]
        world_model.polies = [
            self._read_poly(f, world_model.vertices[i])
            for i in range(0, world_model.poly_count)
        ]

        world_model.nodes = [
            self._read_node(f) for _ in range(0, world_model.node_count)
        ]
        world_model.user_portals = [
            self._read_user_portal(f) for _ in range(0, world_model.user_portal_count)
        ]
        world_model.points = [
            self._read_point(f) for _ in range(0, world_model.point_count)
        ]
        self._read_pblock_table(f)

        world_model.root_node_index = unpack('I', f)[0]
        world_model.sections = unpack('I', f)[0]

        # Note: We don't read the terrain vis information (i.e. section)

        return world_model

    def _read_world_object(self, f: BinaryIO) -> WorldObject:
        world_object = WorldObject()
        _data_len = unpack('H', f)[0]
        world_object.type = self._read_string(f)
        world_object.property_count = unpack('I', f)[0]
        for idx in range(0, world_object.property_count):
            name = self._read_string(f)
            code = unpack('b', f)[0]
            flags = unpack('I', f)[0]
            _prop_data_len = unpack('H', f)[0]

            match code:
                case 0:
                    world_property = WorldPropertyString()
                case 1 | 2:
                    world_property = WorldPropertyVector()
                case 3:
                    world_property = WorldPropertyFloat()
                case 5:
                    world_property = WorldPropertyBool()
                case 4 | 6:
                    world_property = WorldPropertyInt()
                case 7:
                    world_property = WorldPropertyRotation()
                case _:
                    logger.error(f'Unknown world property code: {code}')
                    raise TypeError()

            world_property.name = name
            world_property.flags = flags
            world_property.property_type = code
            world_property.read_value(f)

            if name == 'Name':
                world_object.name = world_property.value
                world_object.name_prop_idx = idx
            if name == 'Pos':
                world_object.pos = world_property.value
                world_object.pos_prop_idx = idx
            if name == 'Rotation':
                world_object.rotation = world_property.value
                world_object.rotation_prop_idx = idx

            world_object.properties.append(world_property)
        return world_object

    def from_file(self, path: str):
        with open(path, 'rb') as f:
            try:
                logger.debug('Reading header')
                model = self._read_header(f)
                model.name = path.split('/')[-1]

                logger.debug('Reading quadtree')
                model.quad_tree = self._read_quadtree(f)

                logger.debug('Reading world models')
                world_model_count = unpack('I', f)[0]
                for _ in range(0, world_model_count):
                    next_world_model_pos = unpack('I', f)[0]
                    _padding = unpack('32B', f)[0]
                    model.world_models.append(self._read_world_model(f))
                    # Skip terrain vis info
                    f.seek(next_world_model_pos, 0)

                logger.debug('Reading world objects')
                world_object_count = unpack('I', f)[0]
                for _ in range(0, world_object_count):
                    model.world_objects.append(self._read_world_object(f))

                logger.debug('Skipping render data!')
            except Exception as exc:
                logger.error('EXCEPTION OCCURRED---------------------------')
                logger.error(f'Error with loading DAT = {path}')
                logger.error(f'at read position: {f.tell()}')
                logger.debug(traceback.print_tb(exc.__traceback__))
                logger.error(exc)
        return model