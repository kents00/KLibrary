import bpy
import bpy.utils.previews
import os

bl_info = {
    "name": "KLibrary",
    "blender": (3, 4, 1),
    "version": (1, 0),
    "category": "3D View",
    "author": "Kent Edoloverio",
    "location": "3D View > UI Templates",
    "description": "Collection of Shaders in one single click",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
}


class ShaderLibrary:
    def __init__(self):
        self.previews = []
        self.previews_loaded = False

    def find_preview_file(self, folder):
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

    def get_folders_in(self, folder):
        folders = os.listdir(folder)
        folders = [os.path.join(folder, x) for x in folders]
        folders = list(filter(lambda x: os.path.isdir(x), folders))
        return folders

    def get_previews_from_folders(self, folders, preview_collection):
        previews = []
        i = 0
        for folder in folders:
            preview_file, found = self.find_preview_file(folder)
            if not found:
                continue
            image_name = os.path.basename(os.path.normpath(folder))
            image_path = os.path.join(folder, preview_file)
            image = preview_collection.load(image_name, image_path, 'IMAGE')
            previews.append(
                (image_name, image_name, image_name, image.icon_id, i))
            i += 1
        return previews

    def generate_previews(self, pcoll):
        folder = pcoll.images_dir
        vehicles = self.get_folders_in(folder)
        items = self.get_previews_from_folders(vehicles, pcoll)
        return items

    def generate_shader_previews(self):
        if not self.previews_loaded:
            pcoll = bpy.utils.previews.new()
            pcoll.images_dir = os.path.dirname(
                os.path.normpath(__file__)) + "/data/shaders"
            materials = self.get_folders_in(pcoll.images_dir)
            self.previews = self.get_previews_from_folders(materials, pcoll)
            self.previews_loaded = True
            return self.previews


def find_blend_file(folder):
    files = os.listdir(folder)
    files = list(filter(lambda x: x.endswith(".blend"), files))
    if not files:
        return "", False
    return os.path.join(folder, files[0]), True


def on_material_icon_clicked(self, context):
    scene = context.scene
    tool_settings = scene.tool_settings
    scene.selected_material = scene.material_previews


class KLibrarySettings(bpy.types.PropertyGroup):
    shader_library = ShaderLibrary()

    bpy.types.Scene.material_previews = bpy.props.EnumProperty(
        items=shader_library.generate_shader_previews(),
        update=on_material_icon_clicked
    )
    bpy.types.Scene.selected_material = bpy.props.StringProperty(
        default=shader_library.previews[0][0]
    )


class KLIBRARY_OT_import_material(bpy.types.Operator):
    bl_idname = "klibrary.import_material"
    bl_label = "Import Material"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        shader_library = ShaderLibrary()
        scene = context.scene
        tool_settings = scene.tool_settings
        material_name = scene.selected_material

        material_folder = os.path.dirname(os.path.normpath(
            __file__)) + "/data/shaders/" + material_name

        material_blend, found = find_blend_file(material_folder)
        if not found:
            return {"CANCELLED"}

        with bpy.data.libraries.load(material_blend, link=False) as (data_src, data_dst):
            data_dst.materials = data_src.materials

        # Assign the imported material to the active object's material slot
        active_obj = context.active_object
        if active_obj and active_obj.type == 'MESH':
            material = bpy.data.materials.get(material_name)
            if material and material_name not in active_obj.data.materials:
                active_obj.data.materials.append(material)
            return {'FINISHED'}
        else:
            self.report(
                {'ERROR'}, "Select a mesh object to apply the material.")
            return {'CANCELLED'}


class KLibraryPanel(bpy.types.Panel):
    bl_idname = "KLibrary_PL_Shaders"
    bl_label = "KLibrary"
    bl_category = "KLibrary"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        pcoll = KLibrary_Layers_Preview["main"]
        kofi = pcoll["kofi"]
        deviant = pcoll["deviant"]
        github = pcoll["github"]

        scene = context.scene
        layout = self.layout

        box = layout.box()
        row = box.row()
        row.label(text="Shaders")
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
        box = layout.box()
        box.scale_y = 1.5
        box.scale_x = 1.5
        kofi = box.operator(
            'wm.url_open',
            text='KO-FI',
            icon_value=kofi.icon_id,
            emboss=False
        )
        kofi.url = 'https://ko-fi.com/kents_workof_art'

        box = layout.box()
        box.scale_y = 1.5
        box.scale_x = 1.5
        deviant = box.operator(
            'wm.url_open',
            text='DEVIANT ART',
            icon_value=deviant.icon_id,
            emboss=False
        )
        deviant.url = 'https://www.deviantart.com/kents001'

        box = layout.box()
        box.scale_y = 1.5
        box.scale_x = 1.5
        github = box.operator(
            'wm.url_open',
            text='GITHUB',
            icon_value=github.icon_id,
            emboss=False
        )
        github.url = 'https://github.com/kents00'


KLibrary_Layers_Preview = {}

classes = (
    KLibrarySettings,
    KLibraryPanel,
    KLIBRARY_OT_import_material
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    pcoll = bpy.utils.previews.new()

    absolute_path = os.path.join(os.path.dirname(__file__), 'data/')
    relative_path = "icons"
    path = os.path.join(absolute_path, relative_path)
    pcoll.load("kofi", os.path.join(path, "kofi.png"), 'IMAGE')
    pcoll.load("deviant", os.path.join(path, "deviantart.png"), 'IMAGE')
    pcoll.load("github", os.path.join(path, "github.png"), 'IMAGE')
    KLibrary_Layers_Preview["main"] = pcoll


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    for pcoll in KLibrary_Layers_Preview.values():
        bpy.utils.previews.remove(pcoll)
    KLibrary_Layers_Preview.clear()

if __name__ == "__main__":
    register()