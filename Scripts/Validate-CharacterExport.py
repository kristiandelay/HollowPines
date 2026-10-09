"""Reimport FBX and check skin weights, hierarchy, scale and actual finger deformation."""
import bpy
import json
import math
import sys
import traceback
import numpy as np
from pathlib import Path
from mathutils import Vector, Quaternion

ROOT = Path(__file__).resolve().parents[1]
NAME = sys.argv[sys.argv.index('--')+1]
ASSET = ROOT / 'Art/Characters' / NAME
OUT = ROOT / 'Artifacts/CharacterPrep' / NAME
bpy.context.preferences.use_preferences_save = False

def coordinates(mesh):
    evaluated = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    temporary = evaluated.to_mesh()
    points = np.empty(len(temporary.vertices)*3, dtype=np.float32)
    temporary.vertices.foreach_get('co', points)
    evaluated.to_mesh_clear()
    return points.reshape(-1,3)

try:
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.fbx(filepath=str(ASSET / 'Export' / (NAME+'.fbx')))
    rig = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
    mesh = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    bpy.context.view_layer.objects.active = mesh
    report = {'name': NAME, 'bones': {b.name: {'parent': b.parent.name if b.parent else None,
              'head': list(rig.matrix_world @ b.head_local), 'tail': list(rig.matrix_world @ b.tail_local)} for b in rig.data.bones},
              'dimensions_m': list(mesh.dimensions), 'rig_scale': list(rig.scale)}
    # FBX stores centimetres; Blender imports a .01 conversion on the rig object.
    assert min(rig.scale) > 0 and max(rig.scale)-min(rig.scale) < .00001, list(rig.scale)
    assert all(max(abs(s-1) for s in b.matrix_local.to_scale()) < .001 for b in rig.data.bones)
    groups = {g.index: g.name for g in mesh.vertex_groups}
    bone_names = set(report['bones'])
    unweighted = 0
    max_sum_error = 0
    max_influences = 0
    for v in mesh.data.vertices:
        weights = [g.weight for g in v.groups if groups[g.group] in bone_names and g.weight > 1e-6]
        unweighted += not bool(weights)
        max_sum_error = max(max_sum_error, abs(sum(weights)-1))
        max_influences = max(max_influences, len(weights))
    assert unweighted == 0, unweighted
    assert max_sum_error < .002, max_sum_error
    assert max_influences <= 4, max_influences
    report.update(unweighted=unweighted, max_sum_error=max_sum_error, max_influences=max_influences)
    baseline = coordinates(mesh)
    report['deformation_tests'] = {}
    # Verify that major creature chains actually deform weighted geometry.
    if 'pelvis' not in bone_names:
        required = {
            'CaveStalker': ['head','jaw','forelimb_2_l','forelimb_3_l','forelimb_2_r','forelimb_3_r','hindlimb_1_l','hindlimb_1_r','tail_2'],
            'HollowStalker': ['head','jaw','arm_2_l','arm_3_l','arm_2_r','arm_3_r','leg_1_l','leg_1_r'],
            'HollowRootRevenant': ['head','branch_arm_2_l','branch_arm_3_l','branch_arm_2_r','branch_arm_3_r','root_leg_1_l','root_leg_1_r'],
            'Hag': ['head','arm_2_l','arm_3_l','arm_2_r','arm_3_r','sleeve1_1_l','sleeve1_1_r','robe_front_1_l','robe_back_1_r']
        }[NAME]
        for name in required:
            assert name in bone_names, name
            descendants = {name} | {b.name for b in rig.data.bones[name].children_recursive}
            indices = {g.index for g in mesh.vertex_groups if g.name in descendants}
            affected = [v.index for v in mesh.data.vertices if sum(g.weight for g in v.groups if g.group in indices) > .25]
            assert len(affected) >= 12, (name,len(affected))
            pb=rig.pose.bones[name]
            pb.rotation_mode='XYZ';pb.rotation_euler.x=math.radians(25)
            bpy.context.view_layer.update()
            motion=float(np.max(np.linalg.norm(coordinates(mesh)-baseline,axis=1)[affected]))*mesh.matrix_world.to_scale().x
            assert max(mesh.dimensions)*.002 < motion < max(mesh.dimensions)*.75, (name,motion)
            report['deformation_tests'][name]={'weighted_vertices':len(affected),'max_motion_m':motion}
            pb.rotation_euler=(0,0,0)
            bpy.context.view_layer.update()
    if 'pelvis' in bone_names:
        assert 1.5 < mesh.dimensions.z < 2.1, list(mesh.dimensions)
        assert 'root' in bone_names or rig.name == 'root', rig.name
        for name in ['pelvis','spine_01','spine_05','neck_01','neck_02','head','hand_l','hand_r','foot_l','foot_r']:
            assert name in bone_names, name
        report['fingers'] = {}
        for side in ['l','r']:
            for finger in ['thumb','index','middle','ring','pinky']:
                names = [f'{finger}_{i:02}_{side}' for i in range(1,4)]
                assert all(n in bone_names for n in names), names
                indices = {mesh.vertex_groups[n].index for n in names if n in mesh.vertex_groups}
                affected = [v.index for v in mesh.data.vertices if sum(g.weight for g in v.groups if g.group in indices) > .25]
                assert len(affected) >= 8, (finger,side,len(affected))
                curl_axis = (rig.data.bones['pinky_01_'+side].head_local-rig.data.bones['index_01_'+side].head_local).normalized()
                for n,angle in zip(names,[35,50,25]):
                    pb = rig.pose.bones[n]
                    pb.rotation_mode = 'QUATERNION'
                    local_axis = pb.bone.matrix_local.to_quaternion().inverted() @ curl_axis
                    pb.rotation_quaternion = Quaternion(local_axis, math.radians(angle))
                bpy.context.view_layer.update()
                distances = np.linalg.norm(coordinates(mesh)-baseline,axis=1)
                # Imported mesh coordinates are in metres with this FBX convention.
                motion = float(np.max(distances[affected])) * mesh.matrix_world.to_scale().x
                assert .008 < motion < .30, (finger,side,motion)
                report['fingers'][finger+'_'+side] = {'weighted_vertices':len(affected),'max_motion_m':motion}
                for n in names:
                    rig.pose.bones[n].rotation_quaternion = Quaternion()
                bpy.context.view_layer.update()
    report['passed'] = True
    (ASSET / 'RigValidation.json').write_text(json.dumps(report,indent=2))
    print('CHARACTER_EXPORT_VALID', NAME, len(bone_names), flush=True)
except Exception:
    error = traceback.format_exc()
    (OUT / 'export-validation-failure.txt').write_text(error)
    print(error,flush=True)
    raise
