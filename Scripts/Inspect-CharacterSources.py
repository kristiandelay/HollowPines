"""Blender: inspect normalized character sources and render front/side views."""
import bpy
import json
from pathlib import Path
from mathutils import Vector
import sys

ROOT = Path(__file__).resolve().parents[1]
records = json.loads((ROOT / 'resources/CharacterSources.json').read_text())['characters']
names = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
for record in records:
    name = record['name']
    if names and name not in names:
        continue
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    folder = ROOT / 'Artifacts/CharacterPrep' / name
    folder.mkdir(parents=True, exist_ok=True)
    bpy.ops.import_scene.fbx(filepath=str(ROOT / record['source_fbx']))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    points = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    low = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    high = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    center = (low + high) / 2
    report = {'name': name, 'bounds_min': list(low), 'bounds_max': list(high),
              'dimensions_m': list(high-low), 'meshes': []}
    for obj in meshes:
        obj.data.calc_loop_triangles()
        report['meshes'].append({'name': obj.name, 'vertices': len(obj.data.vertices),
                                'triangles': len(obj.data.loop_triangles),
                                'uv_layers': [u.name for u in obj.data.uv_layers],
                                'vertex_groups': len(obj.vertex_groups)})
        material = bpy.data.materials.new(name + '_Inspection')
        material.use_nodes = True
        tex = material.node_tree.nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(str(ROOT / 'Art/Characters' / name / 'Source' / (name + '_BaseColor.png')), check_existing=True)
        material.node_tree.links.new(tex.outputs['Color'], material.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
        material.node_tree.nodes.active = tex
        obj.data.materials.clear()
        obj.data.materials.append(material)
        for face in obj.data.polygons:
            face.material_index = 0
    (folder / 'source-inspection.json').write_text(json.dumps(report, indent=2))
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'TEXTURE'
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.background_type = 'WORLD'
    scene.world.color = (.08, .08, .08)
    scene.render.resolution_x = 720
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    camera_data = bpy.data.cameras.new('InspectionCamera')
    camera = bpy.data.objects.new('InspectionCamera', camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type = 'ORTHO'
    size = max(high-low)
    for view, direction in [('front', Vector((0,-1,0))), ('side', Vector((1,0,0)))]:
        camera.location = center + direction * size * 3
        camera.rotation_euler = (center-camera.location).to_track_quat('-Z','Y').to_euler()
        camera_data.ortho_scale = max((high-low).z, ((high-low).x if view=='front' else (high-low).y) / .8) * 1.15
        scene.render.filepath = str(folder / (view + '.png'))
        bpy.ops.render.render(write_still=True)
    print('SOURCE_INSPECTED', name, json.dumps(report), flush=True)
