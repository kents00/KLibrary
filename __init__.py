import bpy
import bpy.utils.previews
import os

bl_info = {
    "name": "KLibrary",
    "blender": (3, 4, 1),
    "version": (4, 5),
    "category": "3D View",
    "author": "Kent Edoloverio",
    "location": "3D View > UI Templates",
    "description": "Collection of Shaders in one single click",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
}

preview_collections = {}
shader_previews = []
shader_previews_loaded = False


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


def generate_shader_previews():
    global shader_previews_loaded, shader_previews
    if not shader_previews_loaded:
        pcoll = bpy.utils.previews.new()
        pcoll.images_dir = os.path.dirname(
            os.path.normpath(__file__)) + "/data/shaders"
        materials = get_folders_in(pcoll.images_dir)
        shader_previews = get_previews_from_folders(materials, pcoll)
        shader_previews_loaded = True
        return shader_previews


def on_material_icon_clicked(self, context):
    scene = context.scene
    tool_settings = scene.tool_settings
    scene.selected_material = scene.material_previews


def custom_material_category_load(self, context):
    scene = context.scene
    tool_settings = scene.tool_settings
    category = tool_settings.car_paint_type
    previews = {
        "METALLIC": shader_previews,
    }
    items = previews[category]

    bpy.types.Scene.material_previews = bpy.props.EnumProperty(
        items=items,
        update=on_material_icon_clicked
    )
    scene.selected_material = scene.material_previews


class KLibrarySettings(bpy.types.PropertyGroup):

    generate_shader_previews()

    bpy.types.Scene.material_previews = bpy.props.EnumProperty(
        items=shader_previews,
        update=on_material_icon_clicked
    )
    bpy.types.Scene.selected_material = bpy.props.StringProperty(
        default=shader_previews[0][0]
    )


class KLIBRARY_OT_import_material(bpy.types.Operator):
    bl_idname = "klibrary.import_material"
    bl_label = "Import Material"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Define the path to the blend file containing the custom node
        selected_material = context.scene.selected_material
        source_file = os.path.join(os.path.dirname(
            __file__), f"data\shaders\{selected_material}", f"{selected_material}.blend")

        # Check if the file exists
        if not os.path.isfile(source_file):
            self.report({'ERROR'}, "File not found: {}".format(source_file))
            return {'CANCELLED'}

        # Import the blend file
        with bpy.data.libraries.load(source_file, link=False) as (data_from, data_to):
            for node_group_name in data_from.node_groups:
                if node_group_name not in data_to.node_groups:
                    data_to.node_groups += [node_group_name]
                    # Check if the node group was successfully loaded
                    if not data_to.node_groups or not data_to.node_groups[0]:
                        self.report(
                            {'ERROR'}, "Failed to load the node group: {}".format(node_group_name))
                        return {'CANCELLED'}

                    # Report successful import
                    self.report(
                        {'INFO'}, "Successfully appended node group: {}".format(node_group_name))
        return {'FINISHED'}


class KLibraryPanel(bpy.types.Panel):
    bl_idname = "KLibrary_PL_Shaders"
    bl_label = "KLibrary"
    bl_category = "KLibrary"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        box = layout.box()
        row = box.row()
        row.label(text="KLibrary Shaders")
        row = box.row()
        row.template_icon_view(
            context.scene, "material_previews", show_labels=True)
        row = box.row()
        row.alignment = 'CENTER'
        row.label(text=scene.selected_material)
        row = box.row()
        row.scale_y = 2.0
        row.operator("klibrary.import_material",
                     text="Import Selected Material")


classes = (
    KLibrarySettings,
    KLibraryPanel,
    KLIBRARY_OT_import_material
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
