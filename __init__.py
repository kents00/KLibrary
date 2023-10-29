from UI import UITemplate, Materials, Models
from OP import *
import bpy
bl_info = {
    "name": "UI Templates",
    "blender": (3, 4, 1),
    "version": (4, 5),
    "category": "3D View",
    "author": "Kent Edoloverio",
    "location": "3D View > UI Templates",
    "description": "Allows you to add camera and change aspect ratios and focal lengths with a single click",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
}


classes = (
    UITemplate,
    Materials,
    Models,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
