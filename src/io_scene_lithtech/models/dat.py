from mathutils import Vector, Quaternion


class DAT:
    version = 0
    object_data_pos = -1
    render_data_pos = -1
    world_info_string = ""
    lightmap_grid_size = 20
    boundary_min = Vector()
    boundary_max = Vector()

    quad_tree = None
    world_models: list["WorldModel"] = []
    world_objects: list["WorldObject"] = []


class QuadTree:
    box_min = Vector()
    box_max = Vector()
    node_count = 0
    dummy_terrain_depth = 0
    tree_data = []


class Vertex:
    count = 0
    extra = 0

class LeafData:
    portal_id = 0
    contents = []

class Leaf:
    leaf_data = []
    polygons = []

class Plane:
    normal = Vector()
    distance = 0


class Surface:
    uv_list = [Vector(), Vector(), Vector()]
    texture_index = 0
    flags = 0
    use_effects = False
    effect = ""
    effect_param = ""
    texture_flags = 0

    @property
    def is_solid(self):
        """Surface is solid"""
        return self.flags & (1<<0)

    @property
    def is_non_existent(self):
        """Gets removed by preprocessor"""
        return self.flags & (1<<1)

    @property
    def is_invisible(self):
        """Don't draw"""
        return self.flags & (1<<2)

    @property
    def is_sky(self):
        """Sky portal"""
        return self.flags & (1<<4)

    @property
    def is_bright(self):
        """Full bright"""
        return self.flags & (1<<5)

    @property
    def is_flat_shaded(self):
        """Flat shaded"""
        return self.flags & (1<<6)

    @property
    def is_lightmap(self):
        """Has a lightmap"""
        return self.flags & (1<<7)

    @property
    def is_no_sub_div(self):
        """Don't subdivide this surface"""
        return self.flags & (1<<8)

    @property
    def is_hull_maker(self):
        """Adds hulls for PVS"""
        return self.flags & (1<<9)

    @property
    def is_directional_light(self):
        """Only lit by GlobalDirLight"""
        return self.flags & (1<<11)

    @property
    def is_gouraud_shaded(self):
        """Gouraud shade this surface"""
        return self.flags & (1<<12)

    @property
    def is_portal(self):
        """This surface is a portal that can be opened/closed"""
        return self.flags & (1<<13)

    @property
    def is_panning_sky(self):
        """This surface has a panning sky on it"""
        return self.flags & (1<<15)

    @property
    def is_physics_blocker(self):
        """Blocks player"""
        return self.flags & (1<<17)

    @property
    def is_terrain_occluder(self):
        """Used for visibility calculations on terrain"""
        return self.flags & (1<<18)

    @property
    def is_additive(self):
        """Add source and destination colours"""
        return self.flags & (1<<19)

    @property
    def is_vis_blocker(self):
        """Blocks off the visibility tree"""
        return self.flags & (1<<21)

    @property
    def is_not_a_step(self):
        """No steppy on this surface"""
        return self.flags & (1<<22)

    @property
    def is_mirror(self):
        """A mirror, plane/portal based reflections"""
        return self.flags & (1<<23)

class Poly:
    center = Vector()
    lightmap_width = 0
    lightmap_height = 0
    surface_index = 0
    plane_index = 0
    disk_vertices = []


class Point:
    data = Vector()
    normals = Vector()


class Node:
    poly_index = 0
    leaf_index = 0
    node_indices = []

class UserPortal:
    name = ""
    center = Vector()
    dims = Vector()


class WorldModel:
    index = 0
    name = ""
    root_node_index = -1
    sections = 0

    info_flags = 0
    point_count = 0
    plane_count = 0
    surface_count = 0
    user_portal_count = 0
    poly_count = 0
    leaf_count = 0
    vertex_count = 0
    total_vis_list_size = 0
    leaf_list_count = 0
    node_count = 0
    min_box: Vector
    max_box: Vector
    world_offset: Vector
    texture_list: list[str]

    vertices: list[Vertex]
    leafs: list[Leaf]
    planes: list[Plane]
    surfaces: list[Surface]
    polies: list[Poly]
    nodes: list[Node]
    user_portals: list[UserPortal]
    points: list[Point]
    block_table: list

    def __init__(self):
        self.index = 0
        self.name = ''
        self.root_node_index = -1
        self.sections = 0

        self.info_flags = 0
        self.point_count = 0
        self.plane_count = 0
        self.surface_count = 0
        self.user_portal_count = 0
        self.poly_count = 0
        self.leaf_count = 0
        self.vertex_count = 0
        self.total_vis_list_size = 0
        self.leaf_list_count = 0
        self.node_count = 0
        self.min_box = Vector()
        self.max_box = Vector()
        self.world_offset = Vector()
        self.texture_list: list[str] = []

        self.vertices: list[Vertex] = []
        self.leafs: list[Leaf] = []
        self.planes: list[Plane] = []
        self.surfaces: list[Surface] = []
        self.polies: list[Poly] = []
        self.nodes: list[Node] = []
        self.user_portals: list[UserPortal] = []
        self.points: list[Point] = []
        self.block_table = []  # Physics?

    @property
    def is_movable(self):
        return self.info_flags & (1 << 1)

    @property
    def is_main_world(self):
        return self.info_flags & (1 << 2)

    @property
    def is_physics_bsp(self):
        return self.info_flags & (1 << 4)

    @property
    def is_vis_bsp(self):
        return self.info_flags & (1 << 5)


class WorldProperty:
    name = ""
    property_type = 0
    flags = 0


class WorldPropertyString(WorldProperty):
    value = ""


class WorldPropertyVector(WorldProperty):
    value = Vector()


class WorldPropertyFloat(WorldProperty):
    value = 0.0


class WorldPropertyBool(WorldProperty):
    value = False


class WorldPropertyInt(WorldProperty):
    value = 0


class WorldPropertyRotation(WorldProperty):
    value = Quaternion()


class WorldObject:
    type = ""
    property_count = 0
    properties: list[WorldProperty] = []
