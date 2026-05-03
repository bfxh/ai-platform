bl_info = {
    "name": "AI Builder",
    "author": "Your Name",
    "version": (0, 1),
    "blender": (4, 4, 0),
    "location": "View3D > Sidebar > AI Builder",
    "description": "Generate objects from text instructions",
    "category": "Object",
}

import bpy

# ---------- Operator ----------

class OBJECT_OT_ai_builder(bpy.types.Operator):
    """Parses text input and creates objects"""
    bl_idname = "object.ai_builder"
    bl_label = "AI Build"

    def execute(self, context):
        prompt = context.scene.ai_builder_prompt.lower()

        # Keyword-based parsing
        if "room" in prompt:
            self.create_room()
        if "desk" in prompt:
            self.create_desk()
        if "lamp" in prompt:
            self.create_lamp()

        self.report({'INFO'}, "AI Build completed.")
        return {'FINISHED'}

    def create_room(self):
        # Create floor
        bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
        floor = bpy.context.active_object
        floor.name = "Floor"

        # Create four walls (simple cubes scaled)
        wall_thickness = 0.1
        wall_height = 3

        # Back wall
        bpy.ops.mesh.primitive_cube_add(location=(0, -5, wall_height/2))
        back_wall = bpy.context.active_object
        back_wall.scale = (5, wall_thickness, wall_height/2)
        back_wall.name = "Back Wall"

        # Front wall
        bpy.ops.mesh.primitive_cube_add(location=(0, 5, wall_height/2))
        front_wall = bpy.context.active_object
        front_wall.scale = (5, wall_thickness, wall_height/2)
        front_wall.name = "Front Wall"

        # Left wall
        bpy.ops.mesh.primitive_cube_add(location=(-5, 0, wall_height/2))
        left_wall = bpy.context.active_object
        left_wall.scale = (wall_thickness, 5, wall_height/2)
        left_wall.name = "Left Wall"

        # Right wall
        bpy.ops.mesh.primitive_cube_add(location=(5, 0, wall_height/2))
        right_wall = bpy.context.active_object
        right_wall.scale = (wall_thickness, 5, wall_height/2)
        right_wall.name = "Right Wall"

    def create_desk(self):
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 1))
        desk = bpy.context.active_object
        desk.scale = (1, 0.5, 0.05)
        desk.name = "Desk"

    def create_lamp(self):
        # Lamp stand
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1, location=(0.5, 0, 1.5))
        stand = bpy.context.active_object
        stand.name = "Lamp Stand"

        # Lamp head
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(0.5, 0, 2))
        head = bpy.context.active_object
        head.name = "Lamp Head"

# ---------- Panel ----------

class VIEW3D_PT_ai_builder_panel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "AI Builder"
    bl_idname = "VIEW3D_PT_ai_builder_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AI Builder'

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "ai_builder_prompt")
        layout.operator("object.ai_builder", text="Generate Objects")

# ---------- Register ----------

classes = (
    OBJECT_OT_ai_builder,
    VIEW3D_PT_ai_builder_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.ai_builder_prompt = bpy.props.StringProperty(
        name="Prompt",
        description="Describe your scene",
        default=""
    )

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.ai_builder_prompt

if __name__ == "__main__":
    register()
