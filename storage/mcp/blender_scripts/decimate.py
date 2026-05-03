import bpy

ratio = 0.3

for obj in bpy.context.selected_objects:
    if obj.type == 'MESH':
        before = len(obj.data.polygons)
        mod = obj.modifiers.new('Decimate', 'DECIMATE')
        mod.ratio = ratio
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier='Decimate')
        after = len(obj.data.polygons)
        print(f"{obj.name}: {before} → {after} faces ({after/before*100:.0f}%)")
