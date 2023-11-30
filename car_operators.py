import bpy
import os
import math
from mathutils import Vector, Matrix


def is_scene_reset(context):
    scene = context.scene
    my_settings = scene.my_settings
    scene_reset = False
    if hasattr(scene, "test"):
        if scene.test != my_settings.test:
            scene_reset = True
    else:
        if my_settings.test:
            scene_reset = True
    return scene_reset


def get_raycast_param(view_layer):
    if bpy.app.version >= (2, 91, 0):
        return view_layer.depsgraph
    else:
        return view_layer


class SnapToGroundOperator(bpy.types.Operator):
    bl_idname = "view3d.snap_to_ground"
    bl_label = "Snap to ground operator"
    bl_description = "Snap active object to ground"

    def execute(self, context):
        selection = context.selected_objects
        for obj in context.selected_objects:
            # obj: bpy.types.Object = bpy.context.active_object
            obj.hide_set(True)
            ray_cast_param = get_raycast_param(bpy.context.window.view_layer)
            result = bpy.context.scene.ray_cast(
                ray_cast_param,
                obj.location,
                [0, 0, -1])
            obj.hide_set(False)
            obj.select_set(True)
            if result[0]:
                face_normal = Vector(result[2])
                z = Vector(obj.matrix_world.col[2][:3])
                axis = z.cross(face_normal)
                angle_cos = z.dot(face_normal)
                angle_cos = max(min(angle_cos, 1.0), -1.0)
                angle = math.acos(angle_cos)
                m = Matrix.Rotation(angle, 4, axis)
                obj.matrix_world = m @ obj.matrix_world
                obj.location = result[1]
        return {"FINISHED"}


def find_blend_file(folder):
    files = os.listdir(folder)
    files = list(filter(lambda x: x.endswith(".blend"), files))
    if not files:
        return "", False
    return os.path.join(folder, files[0]), True

def find_blend_file_lowpoly(folder, use_lowpoly):
    files = os.listdir(folder)
    files = list(filter(lambda x: x.endswith(".blend"), files))
    num_blend_files = len(files)
    if num_blend_files == 0:
        return "", False
    if num_blend_files == 1:
        return os.path.join(folder, files[0]), True
    if num_blend_files > 2:
        return "", False

    lowpoly_file = ""
    lowpoly_file_list = list(filter(lambda x:"lowpoly" in x, files))
    if len(lowpoly_file_list) > 0 :
        lowpoly_file = list(filter(lambda x:"lowpoly" in x, files))[0]
    else:
        lowpoly_file = files[0]
    hd_file = list(filter(lambda x:"lowpoly" not in x, files))[0]
    file = lowpoly_file if use_lowpoly else hd_file

    return os.path.join(folder, file), True


class AddVehicleOperator(bpy.types.Operator):
    bl_idname = "view3d.add_vehicle"
    bl_label = "Add vehicle operator"
    bl_description = "Add selected vehicle to scene"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        my_settings = scene.my_settings
        scene_reset = is_scene_reset(context)

        use_cursor = my_settings.spawn_location == "CURSOR"
        location = scene.cursor.location if use_cursor else Vector((0, 0, 0))

        car_folder = os.path.dirname(os.path.normpath(__file__))\
            + "/data/vehicles/" + my_settings.car_type

        first_car_in_category = os.listdir(car_folder)[0]
        car = first_car_in_category if scene_reset else scene.car_previews
        car_folder = car_folder + "/" + car

        use_lowpoly = my_settings.high_low_poly == "Lowpoly"
        car_blend, found = find_blend_file_lowpoly(car_folder, use_lowpoly)
        if not found:
            return {"FINISHED"}

        with bpy.data.libraries.load(car_blend, link=False) as (data_src, data_dst):
            data_dst.collections = data_src.collections
        
        if data_dst.collections is not None:
            collection = data_dst.collections[0]
            instance = bpy.data.objects.new(name=collection.name, object_data=None)
            instance.instance_collection = collection
            instance.instance_type = 'COLLECTION'
            instance.location = location
            scene.collection.objects.link(instance)
            instance.select_set(True)
            context.view_layer.objects.active = instance
            instance['TP_car_file_path'] = car_blend
        return {"FINISHED"}


def find_car_paint_materials(objects):
    car_paint_materials = []
    car_paint_objects = []
    for obj in objects:
        instance = obj.instance_collection
        instance_objects = objects if instance is None else instance.all_objects
        for instance_object in instance_objects:
            material = instance_object.active_material
            if material is None:
                continue
            name = material.name.lower()
            if "car" in name and "paint" in name:
                car_paint_materials.append(material)
                car_paint_objects.append(instance_object)
    return car_paint_materials, car_paint_objects


def apply_base_color_to_materials(materials, base_color):
    for mat in materials:
        nodes = mat.node_tree.nodes
        for node in nodes:
            if node.bl_static_type == "BSDF_PRINCIPLED":
                i = node.inputs["Base Color"]
                i.default_value = base_color


def apply_custom_color_material(objects, material, color):
    nodes = material.node_tree.nodes
    material.diffuse_color = color
    for node in nodes:
        if node.label == "custom_color":
            node.outputs[0].default_value = color
    for obj in objects:
        obj.active_material = material


class ApplyCustomCarPaintColor(bpy.types.Operator):
    bl_idname = "view3d.apply_custom_car_color"
    bl_label = "Add Custom color"
    bl_description = "Add Custom color"

    def execute(self, context):
        scene = context.scene
        my_settings = scene.my_settings
        custom_color = my_settings.custom_car_paint_color
        material_types = {
            "METALLIC": "Metalic_carpaint.blend",
            "MATT": "Matt_carpaint.blend",
            "SHINY": "Shiny_carpaint.blend"
        }
        # paint_type = my_settings.custom_car_paint_type.pop()
        paint_type = my_settings.custom_car_paint_type
        material_blend = os.path.dirname(os.path.normpath(__file__)) \
            + "/data/" + material_types[paint_type]
        with bpy.data.libraries.load(material_blend, link=False) as (data_src, data_dst):
            data_dst.materials = data_src.materials
        material = data_dst.materials[0]
        _, car_paint_objects = find_car_paint_materials(context.selected_objects)
        apply_custom_color_material(car_paint_objects, material, custom_color)
        return {"FINISHED"}


class ApplyCustomCarPaintMaterial(bpy.types.Operator):
    bl_idname = "view3d.apply_custom_car_material"
    bl_label = "Apply Custom material"
    bl_description = "Apply Custom material"

    def execute(self, context):
        scene = context.scene
        my_settings = scene.my_settings
        material_name = scene.selected_material

        material_types = {
            "METALLIC": "metallic",
            "MATT": "matt",
            "SHINY": "glossy"
        }
        material_category = material_types[my_settings.car_paint_type]

        material_folder = os.path.dirname(os.path.normpath(__file__)) \
            + "/data/materials/" + material_category + "/" \
            + material_name

        material_blend, found = find_blend_file(material_folder)
        if not found:
            return {"FINISHED"}

        with bpy.data.libraries.load(material_blend, link=False) as (data_src, data_dst):
            data_dst.materials = data_src.materials

        material = data_dst.materials[0]
        _, car_paint_objects = find_car_paint_materials(context.selected_objects)
        for obj in car_paint_objects:
            obj.active_material = material
        return {"FINISHED"}


class MakeEditableOperator(bpy.types.Operator):
    bl_idname = "view3d.make_editable"
    bl_label = "Make editable operator"
    bl_description = "Make editable"

    def execute(self, context):
        scene = context.scene
        my_settings = scene.my_settings

        # bpy.ops.object.duplicates_make_real(use_base_parent=False, use_hierarchy=True)
        obj = context.active_object
        if obj is None:
            return {"CANCELLED"}
        if 'TP_car_file_path' not in context.active_object.keys():
            return {"CANCELLED"}
        
        location = obj.location
        rotation = obj.rotation_euler
        scale = obj.scale
        path = obj['TP_car_file_path']
        materials, _ = find_car_paint_materials([obj])
        material = None
        if materials is not None:
            material = materials[0]

        with bpy.data.libraries.load(path, link=False) as (data_src, data_dst):
            data_dst.collections = data_src.collections

        collection = data_dst.collections[0]
        scene.collection.children.link(collection)

        for object in context.selected_objects:
            object.select_set(False)
        obj.select_set(True)
        bpy.ops.object.delete()

        # reset location rotation scale
        car_rig_found = False
        car_rig = None
        for o in collection.objects:
            if "Car Rig" in o.name:
                car_rig = o
                car_rig_found = True
                break
        if not car_rig_found:
            return {"CANCELLED"}
        car_rig.location = location
        car_rig.rotation_euler = rotation
        car_rig.scale = scale

        # reset material
        _, car_paint_objects = find_car_paint_materials(collection.objects)
        for obj in car_paint_objects:
            obj.active_material = material

        # print(obj['TP_car_file_path'])
        return {"FINISHED"}
