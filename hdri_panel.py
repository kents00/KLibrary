import bpy
import bpy.utils.previews
import os
from.hdri_operators import load_images_in_folder

Backplates_enabled = True


def generate_backplate_items(self, context):
    scene = context.scene
    my_settings = scene.my_settings
    
    script_file = os.path.realpath(__file__)
    hdri_dir = os.path.dirname(script_file) + "/data/HDRI"
    hdri_type = my_settings.hdri_type
    hdri_dir = os.path.join(hdri_dir, hdri_type)
    hdri_dir = os.path.join(hdri_dir, scene.selected_hdri)

    backplates_dir = hdri_dir + "/backplates"
    items = load_images_in_folder(backplates_dir, context)
    return items


def load_backplate_previews():
    bpy.types.Scene.backplate_previews = bpy.props.EnumProperty(
        name="",
        description="",
        items=generate_backplate_items,
        update=None
    )


class HDRIBackplatesPanel(bpy.types.Panel):
    bl_idname = "TRANSPORTATION_PT_hdri_backplates_panel"
    bl_label = "HDRI and Backplates"
    bl_category = "Transportation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        scene = context.scene
        my_settings = scene.my_settings

        layout = self.layout

        box = layout.box()
        row = box.row()
        row.prop(my_settings, "hdri_type", text="")
        row = box.row()
        row.template_icon_view(context.scene, "hdri_previews", show_labels=True)
        row = box.row()
        row.alignment = 'CENTER'
        row.label(text=scene.selected_hdri)
        row = box.row()
        row.scale_y = 2.0
        row.operator("transportation.add_hdri", text="Add HDRI", icon="WORLD")
        row = box.row()
        row.prop(my_settings, "hdri_power")
        row = box.row()
        row.prop(my_settings, "hdri_saturation")
        row = box.row()
        row.prop(my_settings, "hdri_rotation")
        row = box.row()
        row.prop(my_settings, "hdri_height")

        box = layout.box()
        box.enabled = Backplates_enabled
        row = box.row()
        row.prop(my_settings, "use_backplate")
        row = box.row()
        if hasattr(context.scene, "backplate_previews"):
            row.template_icon_view(context.scene, "backplate_previews")
        row = box.row()
        row.scale_y = 2.0
        row.operator("transportation.add_backplate", text="Add in background", icon="IMAGE_DATA")
        row = box.row()
        row.label(text="Exif information")
        row = box.row()
        row.alignment = 'LEFT'
        row.label(text=str(my_settings.backplate_x) + "x" + str(my_settings.backplate_y) + "px")

        box = layout.box()
        row = box.row()
        row.scale_y = 2.0
        row.operator("transportation.add_shadow_catcher", text="Add transparent shadows", icon="AXIS_TOP")


def register():
    load_backplate_previews()


def unregister():
    pass
