import bpy
import bpy.utils.previews
import os
import math
from mathutils import Vector, Matrix
from .car_operators import find_blend_file

preview_collections = {}
backplate_previews = {}
shadow_catcher_material = None


def get_z_min(obj):
    bounding_box_points = list()
    for i in range(8):
        bounding_box_points.append(obj.bound_box[i][2])
    return min(bounding_box_points)


def get_children(obj):
    return [ob for ob in bpy.data.objects if ob.parent == obj]


def find_custom_hdri_in_world(context):
    if context.scene.world is None:
        bpy.ops.world.new()
        context.scene.world = bpy.data.worlds[-1]
    nodes = context.scene.world.node_tree.nodes
    for node in nodes:
        if node.label == "transportation_hdri":
            return node
    return None


def find_backplate_in_compositor(context):
    nodes = context.scene.node_tree.nodes
    for node in nodes:
        if node.label == "transportation_backplate":
            return node
    return None


def find_custom_hdri_in_node_groups():
    node_groups = bpy.data.node_groups
    for node_group in node_groups:
        if node_group.name == "transportation_hdri":
            return node_group
    return None


def find_backplate_in_node_groups():
    node_groups = bpy.data.node_groups
    for node_group in node_groups:
        if node_group.name == "transportation_backplate":
            return node_group
    return None


def load_custom_hdri():
    hdri_blend = os.path.dirname(os.path.normpath(__file__)) \
        + "/data/hdri.blend"
    with bpy.data.libraries.load(hdri_blend, link=False) as (data_src, data_dst):
        data_dst.node_groups = data_src.node_groups
    hdri_group = data_dst.node_groups[0]
    hdri_group.name = "transportation_hdri"
    return hdri_group


def load_custom_backplate():
    backplate_blend = os.path.dirname(os.path.normpath(__file__)) \
        + "/data/backplate.blend"
    with bpy.data.libraries.load(backplate_blend, link=False) as (data_src, data_dst):
        data_dst.node_groups = data_src.node_groups
    backplate_group = data_dst.node_groups[0]
    backplate_group.name = "transportation_backplate"
    return backplate_group


def get_world_output_node(context):
    world_nodes = context.scene.world.node_tree.nodes
    for node in world_nodes:
        if node.bl_idname == "ShaderNodeOutputWorld":
            return node
    return None


def find_hdr_file(folder):
    img_extensions = ['.hdr', '.exr']
    files = os.listdir(folder)
    if not files:
        return None
    for file in files:
        filename, extension = os.path.splitext(file)
        if extension in img_extensions:
            file = os.path.join(folder, file)
            return file
    return None


def set_power(self, context):
    node = find_custom_hdri_in_world(context)
    node.inputs[0].default_value = self.hdri_power


def set_saturation(self, context):
    node = find_custom_hdri_in_world(context)
    node.inputs[1].default_value = self.hdri_saturation


def set_height(self, context):
    node = find_custom_hdri_in_world(context)
    node.inputs[3].default_value = self.hdri_height


def set_rotation(self, context):
    node = find_custom_hdri_in_world(context)
    node.inputs[2].default_value = self.hdri_rotation * 3.14 / 180.0


def load_images_in_folder(folder, context):
    images = []
    previews = []
    scene = context.scene
    my_settings = scene.my_settings
    img_extensions = ['.jpg', '.jpeg', '.png']
    files = os.listdir(folder)
    for file in files:
        filename, extension = os.path.splitext(file)
        if extension in img_extensions:
            file = os.path.join(folder, file)
            images.append(file)

    backplate, _ = os.path.split(folder)
    _, backplate = os.path.split(backplate)
    backplate_pcoll = "backplates_" + backplate
    if backplate_pcoll in preview_collections:
        pcoll = preview_collections[backplate_pcoll]
        previews = backplate_previews[backplate_pcoll]
    else:
        pcoll = bpy.utils.previews.new()
        pcoll.images_dir = os.path.dirname(os.path.normpath(__file__)) + \
            "/data/HDRI/" + my_settings.hdri_type + "/" + \
            scene.selected_hdri + "/backplates"
        preview_collections[backplate_pcoll] = pcoll
        for i, image in enumerate(images):
            preview = pcoll.load(image, image, 'IMAGE')
            previews.append((image, image, image, preview.icon_id, i))
        backplate_previews[backplate_pcoll] = previews

    return previews


def find_render_layers_node(nodes):
    for node in nodes:
        if node.bl_idname == 'CompositorNodeRLayers':
            return node
    return None


def find_composite_node(nodes):
    for node in nodes:
        if node.bl_idname == 'CompositorNodeComposite':
            return node
    return None


def is_material_valid(material):
    is_valid = False
    try:
        tree = material.node_tree
        is_valid = True
    except:
        is_valid = False
    return is_valid


def get_shadow_catcher_material():
    global shadow_catcher_material
    if shadow_catcher_material:
        if is_material_valid(shadow_catcher_material):
            return shadow_catcher_material
    hdri_blend = os.path.dirname(os.path.normpath(__file__)) \
        + "/data/hdri.blend"
    with bpy.data.libraries.load(hdri_blend, link=False) as (data_src, data_dst):
        data_dst.materials = data_src.materials
    shadow_catcher_material = data_dst.materials[0]
    return shadow_catcher_material


class Transportation_OT_AddHDRI(bpy.types.Operator):
    bl_idname = "transportation.add_hdri"
    bl_label = "Add HDRI operator"
    bl_description = "Add selected HDRI to scene"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        my_settings = scene.my_settings

        hdri_node_group = find_custom_hdri_in_world(context)
        if not hdri_node_group:
            group = find_custom_hdri_in_node_groups()
            if not group:
                group = load_custom_hdri()
            hdri_node_group = context.scene.world.node_tree.nodes.new(
                "ShaderNodeGroup")
            hdri_node_group.node_tree = group
            hdri_node_group.label = "transportation_hdri"
        world_output = get_world_output_node(context)
        links = context.scene.world.node_tree.links
        links.new(hdri_node_group.outputs[0], world_output.inputs[0])

        script_file = os.path.realpath(__file__)
        hdri = context.scene.hdri_previews
        hdri_dir = os.path.dirname(script_file) + "/data/HDRI"
        hdri_type = my_settings.hdri_type
        hdri_dir = os.path.join(hdri_dir, hdri_type)
        hdri_dir = os.path.join(hdri_dir, hdri)
        hdri_file = find_hdr_file(hdri_dir)

        env_texture_node = hdri_node_group.node_tree.nodes["Environment Texture"]
        img = bpy.data.images.load(hdri_file)
        env_texture_node.image = img

        backplates_dir = hdri_dir + "/backplates"
        items = load_images_in_folder(backplates_dir, context)

        bpy.types.Scene.backplate_previews = bpy.props.EnumProperty(
            name="",
            description="",
            items=items,
            update=None
        )
        my_settings.hdri_added = True

        return {"FINISHED"}


class Transportation_OT_AddBackplate(bpy.types.Operator):
    bl_idname = "transportation.add_backplate"
    bl_label = "Add backplate operator"
    bl_description = "Add selected background"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        if not context.scene.node_tree:
            return {"FINISHED"}
        scene = context.scene
        my_settings = scene.my_settings
        if not my_settings.hdri_added:
            return {"FINISHED"}
        if not hasattr(context.scene, "backplate_previews"):
            return {"FINISHED"}

        camera = scene.camera
        if not camera:
            msg = "you need a camera to add a backplate"
            self.report({'INFO'}, msg)
            return {"FINISHED"}

        my_settings.use_backplate
        name = camera.data.name
        if not bpy.data.cameras[name].show_background_images and my_settings.use_backplate:
            bpy.data.cameras[name].show_background_images = True

        backplate_node_group = find_backplate_in_compositor(context)
        if not backplate_node_group:
            group = find_backplate_in_node_groups()
            if not group:
                group = load_custom_backplate()
            backplate_node_group = context.scene.node_tree.nodes.new(
                "CompositorNodeGroup")
            backplate_node_group.node_tree = group
            backplate_node_group.label = "transportation_backplate"
        scene_nodes = context.scene.node_tree.nodes

        render_layers = find_render_layers_node(scene_nodes)
        composite = find_composite_node(scene_nodes)

        links = context.scene.node_tree.links
        links.new(render_layers.outputs[0], backplate_node_group.inputs[0])
        links.new(backplate_node_group.outputs[0], composite.inputs[0])

        script_file = os.path.realpath(__file__)
        backplate = context.scene.backplate_previews
        backplate_dir = os.path.dirname(script_file) + "/data/HDRI"
        hdri_type = my_settings.hdri_type
        hdri = context.scene.hdri_previews
        backplate_dir = os.path.join(backplate_dir, hdri_type)
        backplate_dir = os.path.join(backplate_dir, hdri)
        backplate_dir = os.path.join(backplate_dir, 'backplates')
        backplate_file = os.path.join(backplate_dir, backplate)

        nodes = backplate_node_group.node_tree.nodes
        image_node = nodes['Image']
        img = bpy.data.images.load(backplate_file)
        image_node.image = img

        nb_bg_imgs = len(camera.data.background_images)
        bg = camera.data.background_images.new(
        ) if nb_bg_imgs == 0 else camera.data.background_images[0]
        bg.image = img
        bg.frame_method = 'CROP'
        bg.alpha = 1.0

        my_settings.backplate_x = img.size[0]
        my_settings.backplate_y = img.size[1]

        return {"FINISHED"}


class Transportation_OT_AddShadowCatcher(bpy.types.Operator):
    bl_idname = "transportation.add_shadow_catcher"
    bl_label = "Add shadow catcher"
    bl_description = "Add shadow catcher"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        # my_settings = scene.my_settings

        global shadow_catcher_material
        shadow_catcher_material = get_shadow_catcher_material()

        for obj in context.selected_objects:
            children = get_children(obj)
            shadow_catchers = [
                s for s in children if "transportation_shadow_catcher" in s]
            if shadow_catchers:
                continue
            z = get_z_min(obj)
            x = max(obj.dimensions.x, 1.0)
            y = max(obj.dimensions.y, 1.0)
            if obj.instance_collection:
                inst = obj.instance_collection
                x = max(
                    [objects.dimensions.x for objects in obj.instance_collection.all_objects])
                y = max(
                    [objects.dimensions.y for objects in obj.instance_collection.all_objects])
            location = Vector((0, 0, z))
            size = max(x, y) * 5
            bpy.ops.mesh.primitive_plane_add(size=size, location=location)
            plane = context.selected_objects[0]
            plane.name = "shadow catcher"
            plane.parent = obj
            plane["transportation_shadow_catcher"] = True
            if bpy.app.version >= (3, 0, 0):
                plane.is_shadow_catcher = True
            else:
                plane.cycles.is_shadow_catcher = True
            plane.data.materials.append(shadow_catcher_material)
        return {"FINISHED"}
