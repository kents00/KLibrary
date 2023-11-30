import bpy
import bpy.utils.previews
import os
from .hdri_operators import set_power, set_height, set_rotation, set_saturation


categories_loaded: bool = False
hdri_categories_loaded: bool = False
vehicle_categories: list = []
hdri_categories: list = []
preview_collections = {}
hdri_previews = {}
car_previews = {}
metallic_previews = []
metallic_previews_loaded = False
matt_previews = []
matt_previews_loaded = False
shiny_previews = []
shiny_previews_loaded = False


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


def find_preview_file(folder):
    img_extensions = ['.jpg', '.jpeg', '.png']
    files = os.listdir(folder)
    files = list(filter(lambda x: x.startswith("preview"), files))
    if not files:
        return "", False
    for file in files:
        filename, extension = os.path.splitext(file)
        if extension in img_extensions:
            file = os.path.join(folder, file)
            return file, True
    return "", False


def get_folders_in(folder):
    folders = os.listdir(folder)
    folders = list(map(lambda x: os.path.join(folder, x), folders))
    folders = list(filter(lambda x: os.path.isdir(x), folders))
    return folders


def get_previews_from_folders(folders, preview_collection):
    previews = []
    i = 0
    for folder in folders:
        preview_file, found = find_preview_file(folder)
        if not found:
            continue
        image_name = os.path.basename(os.path.normpath(folder))
        image_path = os.path.join(folder, preview_file)
        image = preview_collection.load(image_name, image_path, 'IMAGE')
        previews.append((image_name, image_name, image_name, image.icon_id, i))
        i += 1
    return previews


def generate_previews(pcoll):
    folder = pcoll.images_dir
    vehicles = get_folders_in(folder)
    items = get_previews_from_folders(vehicles, pcoll)
    return items


def generate_hdri_previews2(pcoll):
    folder = pcoll.images_dir
    hdris = get_folders_in(folder)
    items = get_previews_from_folders(hdris, pcoll)
    return items


def generate_metallic_previews():
    global metallic_previews_loaded, metallic_previews
    if not metallic_previews_loaded:
        pcoll = bpy.utils.previews.new()
        pcoll.images_dir = os.path.dirname(os.path.normpath(__file__)) + "/data/materials/metallic"
        preview_collections["metallic"] = pcoll
        materials = get_folders_in(pcoll.images_dir)
        metallic_previews = get_previews_from_folders(materials, pcoll)
        metallic_previews_loaded = True
        return metallic_previews


def generate_matt_previews():
    global matt_previews_loaded, matt_previews
    if not matt_previews_loaded:
        pcoll = bpy.utils.previews.new()
        pcoll.images_dir = os.path.dirname(os.path.normpath(__file__)) + "/data/materials/matt"
        preview_collections["matt"] = pcoll
        materials = get_folders_in(pcoll.images_dir)
        matt_previews = get_previews_from_folders(materials, pcoll)
        matt_previews_loaded = True
        return matt_previews


def generate_shiny_previews():
    global shiny_previews_loaded, shiny_previews
    if not shiny_previews_loaded:
        pcoll = bpy.utils.previews.new()
        pcoll.images_dir = os.path.dirname(os.path.normpath(__file__)) + "/data/materials/glossy"
        preview_collections["shiny"] = pcoll
        materials = get_folders_in(pcoll.images_dir)
        shiny_previews = get_previews_from_folders(materials, pcoll)
        shiny_previews_loaded = True
        return shiny_previews


def on_car_icon_clicked(self, context):
    scene = context.scene
    my_settings = scene.my_settings
    scene.selected_car = scene.car_previews


def on_hdri_icon_clicked(self, context):
    scene = context.scene
    my_settings = scene.my_settings
    scene.selected_hdri = scene.hdri_previews


def on_material_icon_clicked(self, context):
    scene = context.scene
    my_settings = scene.my_settings
    scene.selected_material = scene.material_previews


def load_first_car_category():
    found = False
    script_file = os.path.realpath(__file__)
    vehicles_dir = os.path.dirname(script_file) + "/data/vehicles"
    dirs = os.listdir(vehicles_dir)
    category = ""
    for d in dirs:
        if os.path.isdir(os.path.join(vehicles_dir, d)):
            category = d
            found = True
            break

    if not found:
        return

    car_pcoll = "cars_" + category
    if car_pcoll in preview_collections:
        pcoll = preview_collections[car_pcoll]
        items = car_previews[car_pcoll]
    else:
        pcoll = bpy.utils.previews.new()
        pcoll.images_dir = os.path.dirname(os.path.normpath(__file__)) + \
        "/data/vehicles/" + category
        preview_collections[car_pcoll] = pcoll
        items = generate_previews(pcoll)
        car_previews[car_pcoll] = items

    bpy.types.Scene.car_previews = bpy.props.EnumProperty(
        name="",
        description="",
        items=items,
        update=on_car_icon_clicked
    )
    bpy.types.Scene.car_previews_first = bpy.props.EnumProperty(
        name="",
        description="",
        items=items,
        update=on_car_icon_clicked
    )
    bpy.types.Scene.selected_car = bpy.props.StringProperty(
        default=items[0][0]
    )


def category_load(self, context):
    # global preview_collections
    scene = context.scene
    my_settings = scene.my_settings
    category = my_settings.car_type

    car_pcoll = "cars_" + category
    if car_pcoll in preview_collections:
        pcoll = preview_collections[car_pcoll]
        items = car_previews[car_pcoll]
    else:
        pcoll = bpy.utils.previews.new()
        pcoll.images_dir = os.path.dirname(os.path.normpath(__file__)) + \
        "/data/vehicles/" + category
        preview_collections[car_pcoll] = pcoll
        items = generate_previews(pcoll)
        car_previews[car_pcoll] = items

    bpy.types.Scene.car_previews = bpy.props.EnumProperty(
        name="",
        description="",
        items=items,
        update=on_car_icon_clicked
    )
    scene.selected_car = scene.car_previews
    bpy.types.Scene.test = bpy.props.BoolProperty(
        name="test property",
        default=True
    )
    my_settings.test = True


def load_first_hdri_category():
    found = False
    script_file = os.path.realpath(__file__)
    hdri_dir = os.path.dirname(script_file) + "/data/HDRI"
    dirs = os.listdir(hdri_dir)
    category = ''
    for d in dirs:
        if os.path.isdir(os.path.join(hdri_dir, d)):
            category = d
            found = True
            break

    if not found:
        return

    hdri_pcoll = "hdri_" + category
    if hdri_pcoll in preview_collections:
        pcoll = preview_collections[hdri_pcoll]
        items = hdri_previews[hdri_pcoll]
    else:
        pcoll = bpy.utils.previews.new()
        pcoll.images_dir = os.path.dirname(os.path.normpath(__file__)) + \
        "/data/HDRI/" + category
        preview_collections[hdri_pcoll] = pcoll
        items = generate_hdri_previews2(pcoll)
        hdri_previews[hdri_pcoll] = items

    bpy.types.Scene.hdri_previews = bpy.props.EnumProperty(
        name="",
        description="",
        items=items,
        update=on_hdri_icon_clicked
    )
    bpy.types.Scene.selected_hdri = bpy.props.StringProperty(
        default=items[0][0]
    )


def hdri_category_load(self, context):
    scene = context.scene
    my_settings = scene.my_settings
    category = my_settings.hdri_type

    hdri_pcoll = "hdri_" + category
    if hdri_pcoll in preview_collections:
        pcoll = preview_collections[hdri_pcoll]
        items = hdri_previews[hdri_pcoll]
    else:
        pcoll = bpy.utils.previews.new()
        pcoll.images_dir = os.path.dirname(os.path.normpath(__file__)) + \
        "/data/HDRI/" + category
        preview_collections[hdri_pcoll] = pcoll
        items = generate_hdri_previews2(pcoll)
        hdri_previews[hdri_pcoll] = items

    bpy.types.Scene.hdri_previews = bpy.props.EnumProperty(
        name="",
        description="",
        items=items,
        update=on_hdri_icon_clicked,
    )
    scene.selected_hdri = scene.hdri_previews


def custom_material_category_load(self, context):
    scene = context.scene
    my_settings = scene.my_settings
    category = my_settings.car_paint_type
    previews = {
        "METALLIC": metallic_previews,
        "MATT": matt_previews,
        "SHINY": shiny_previews
    }
    items = previews[category]

    bpy.types.Scene.material_previews = bpy.props.EnumProperty(
        items=items,
        update=on_material_icon_clicked
    )
    scene.selected_material = scene.material_previews


def on_use_backplates(self, context):
    scene = context.scene
    my_settings = scene.my_settings
    use_nodes = my_settings.use_backplate
    context.scene.use_nodes = use_nodes
    context.scene.render.film_transparent = use_nodes
    camera = context.scene.camera
    name = camera.data.name
    bpy.data.cameras[name].show_background_images = use_nodes


class TransportationSettings(bpy.types.PropertyGroup):
    def get_car_types(self, context):
        global vehicle_categories, categories_loaded
        if not categories_loaded:
            script_file = os.path.realpath(__file__)
            vehicles_dir = os.path.dirname(script_file) + "/data/vehicles"
            dirs = os.listdir(vehicles_dir)
            for d in dirs:
                if os.path.isdir(os.path.join(vehicles_dir, d)):
                    vehicle_categories.append((d, d, ""))
                    # vehicle_categories_folders.append(os.path.join(vehicles_dir, d))
            categories_loaded = True
        return vehicle_categories

    def get_hdri_types(self, context):
        global hdri_categories, hdri_categories_loaded
        if not hdri_categories_loaded:
            hdri_categories = []
            script_file = os.path.realpath(__file__)
            hdri_dir = os.path.dirname(script_file) + "/data/HDRI"
            dirs = os.listdir(hdri_dir)
            for d in dirs:
                if os.path.isdir(os.path.join(hdri_dir, d)):
                    hdri_categories.append((d, d, ""))
            hdri_categories_loaded = True
        return hdri_categories

    generate_metallic_previews()
    generate_matt_previews()
    generate_shiny_previews()
    bpy.types.Scene.material_previews = bpy.props.EnumProperty(
        items=metallic_previews,
        update=on_material_icon_clicked
    )
    bpy.types.Scene.selected_material = bpy.props.StringProperty(
        default=metallic_previews[0][0]
    )

    car_type: bpy.props.EnumProperty(
        default=None,
        name="",
        description="car category",
        items=get_car_types,
        update=category_load,
        options={'ANIMATABLE'}
    )
    hdri_type: bpy.props.EnumProperty(
        description="hdri category",
        items=get_hdri_types,
        update=hdri_category_load,
        options={'ANIMATABLE'}
    )
    spawn_location: bpy.props.EnumProperty(
        name="spawn_location_enum",
        description="choose where to spawn cars",
        items=[
            ("CENTER", "Center", "Spawn at world origin"),
            ("CURSOR", "Cursor", "Spawn at cursor")
        ],
        default="CENTER"
    )
    high_low_poly: bpy.props.EnumProperty(
        name="high_low_poly_enum",
        description="choose to load HD or lowpoly model",
        items=[
            ("HD", "HD", "High definition mesh"),
            ("Lowpoly", "Low Poly", "Low poly mesh")
        ],
        default="HD"
    )
    
    car_paint_type: bpy.props.EnumProperty(
        name="car paint type",
        description="type of car paint",
        items=[
            ("METALLIC", "Metallic", "metallic materials"),
            ("MATT", "Matt", "matt materials"),
            ("SHINY", "Shiny", "shiny materials")
        ],
        update=custom_material_category_load,
        default="METALLIC",
    )
    custom_car_paint_type: bpy.props.EnumProperty(
        name="car paint type",
        description="type of car paint",
        items=[
            ("METALLIC", "Metallic", "metallic materials"),
            ("MATT", "Matt", "matt materials"),
            ("SHINY", "Shiny", "glossy materials")
        ],
        default="METALLIC"
    )
    custom_car_paint_color: bpy.props.FloatVectorProperty(
        name="Choose color",
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
        default=(0.109, 0.1, 0.107, 1.0)
    )
    hdri_power: bpy.props.FloatProperty(
        name="Power",
        description="power of hdri",
        min=0.0,
        soft_min=0.0,
        default=1.0,
        update=set_power
    )
    hdri_saturation: bpy.props.FloatProperty(
        name="Saturation",
        description="saturation of hdri",
        min=0.0,
        soft_min=0.0,
        default=1.0,
        update=set_saturation
    )
    hdri_rotation: bpy.props.FloatProperty(
        name="Rotation",
        description="rotation of hdri",
        min=0.0,
        soft_min=0.0,
        update=set_rotation
    )
    hdri_height: bpy.props.FloatProperty(
        name="Height",
        description="height of hdri",
        soft_min=-2.0,
        soft_max=2.0,
        default=0.0,
        update=set_height
    )
    use_backplate: bpy.props.BoolProperty(
        name="Backplates",
        description="use backplate",
        default=False,
        update=on_use_backplates
    )
    hdri_added: bpy.props.BoolProperty(
        name="hdri added",
        description="hdri added",
        default=False
    )
    backplate_x: bpy.props.IntProperty(
        name="backplate x resolution",
        description="backplate x resolution",
        default=0
    )
    backplate_y: bpy.props.IntProperty(
        name="backplate y resolution",
        description="backplate y resolution",
        default=0
    )
    test: bpy.props.BoolProperty(
        name="test property",
        default=False
    )


class CarModelsPanel(bpy.types.Panel):
    bl_idname = "TRANSPORTATION_PT_car_models_panel"
    bl_label = "Car models"
    bl_category = "Transportation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        scene = context.scene
        my_settings = scene.my_settings

        layout = self.layout

        scene_reset = is_scene_reset(context)

        box = layout.box()
        row = box.row()
        row.prop(my_settings, "car_type")
        row = box.row()
        if scene_reset:
            row.template_icon_view(context.scene, "car_previews_first", show_labels=True)
        else:
            row.template_icon_view(context.scene, "car_previews", show_labels=True)
        row = box.row()
        row.alignment = 'CENTER'
        row.label(text=scene.selected_car)
        row = box.row()
        row.scale_y = 2.0
        row.operator("view3d.add_vehicle", text="Add Vehicle", icon="SCREEN_BACK")
        row = box.row()
        row.prop(my_settings, "high_low_poly", expand=True)
        row = box.row()
        row.prop(my_settings, "spawn_location", expand=True)

        box = layout.box()
        row = box.row()
        row.operator("view3d.snap_to_ground", text="snap vehicle to ground")
        row = box.row()
        row.operator("view3d.make_editable", text="Make editable for animation")

        box = layout.box()
        row = box.row()
        row.label(text="Car Paint")
        row = box.row()
        row.prop(my_settings, "car_paint_type", text="")
        row = box.row()
        row.template_icon_view(context.scene, "material_previews", show_labels=True)
        row = box.row()
        row.alignment = 'CENTER'
        row.label(text=scene.selected_material)
        row = box.row()
        row.scale_y = 2.0
        row.operator("view3d.apply_custom_car_material", text="Add carpaint to vehicle", icon="MATERIAL")

        box = layout.box()
        row = box.row()
        row.label(text="Custom carpaint color")
        col = box.column()
        col.prop(my_settings, "custom_car_paint_type", expand=True)
        row = box.row()
        row.prop(my_settings, "custom_car_paint_color")
        row = box.row()
        row.scale_y = 2.0
        row.operator("view3d.apply_custom_car_color", text="Add Custom color", icon="PROP_ON")


def register():
    load_first_car_category()
    load_first_hdri_category()
    bpy.types.Scene.backplate_dims = bpy.props.StringProperty()


def unregister():
    pass
