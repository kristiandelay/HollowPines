"""Render neutral and posed exported meshes for deformation review."""
import bpy
import sys
import math
from pathlib import Path
from mathutils import Vector, Quaternion

ROOT=Path(__file__).resolve().parents[1]
NAME=sys.argv[sys.argv.index('--')+1]
ASSET=ROOT/'Art/Characters'/NAME
OUT=ASSET/'Review'
OUT.mkdir(exist_ok=True)
bpy.context.preferences.use_preferences_save=False
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=str(ASSET/'Export'/(NAME+'.fbx')))
mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH')
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
material=bpy.data.materials.new(NAME+'_Review');material.use_nodes=True
tex=material.node_tree.nodes.new('ShaderNodeTexImage')
tex.image=bpy.data.images.load(str(ASSET/'Source'/(NAME+'_BaseColor.png')))
material.node_tree.links.new(tex.outputs['Color'],material.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
material.node_tree.nodes.active=tex
mesh.data.materials.clear();mesh.data.materials.append(material)
scene=bpy.context.scene
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO';scene.display.shading.color_type='TEXTURE'
scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
scene.display.shading.background_type='WORLD';scene.world.color=(.075,.075,.075)
scene.render.resolution_x=900;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
camera_data=bpy.data.cameras.new('ReviewCamera');camera=bpy.data.objects.new('ReviewCamera',camera_data)
scene.collection.objects.link(camera);scene.camera=camera;camera_data.type='ORTHO'
points=[mesh.matrix_world@Vector(p) for p in mesh.bound_box]
low=Vector(tuple(min(p[i] for p in points) for i in range(3)))
high=Vector(tuple(max(p[i] for p in points) for i in range(3)))
center=(low+high)*.5;size=max(high-low)

def render(label,direction,target=center,zoom=None):
    camera.location=target+Vector(direction).normalized()*size*4
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    camera_data.ortho_scale=zoom or size*1.4
    scene.render.filepath=str(OUT/(label+'.png'))
    bpy.ops.render.render(write_still=True)

render('NeutralFront',(0,-1,0))
render('NeutralSide',(1,0,0))
if 'pelvis' in rig.data.bones:
    for side in ['l','r']:
        curl_axis=(rig.data.bones['pinky_01_'+side].head_local-rig.data.bones['index_01_'+side].head_local).normalized()
        for finger in ['thumb','index','middle','ring','pinky']:
            for i,angle in enumerate([35,50,25],1):
                pb=rig.pose.bones[f'{finger}_{i:02}_{side}'];pb.rotation_mode='QUATERNION'
                pb.rotation_quaternion=Quaternion(pb.bone.matrix_local.to_quaternion().inverted()@curl_axis,math.radians(angle if side=='l' else -angle))
        pb=rig.pose.bones['lowerarm_'+side]
        axis=(rig.data.bones['hand_'+side].head_local-pb.bone.head_local).cross(Vector((0,-1,0))).normalized()
        pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion(pb.bone.matrix_local.to_quaternion().inverted()@axis,math.radians(55))
    bpy.context.view_layer.update()
    render('PoseReview',(0,-1,.1))
    for side in ['l','r']:
        target=rig.matrix_world@((rig.pose.bones['hand_'+side].head+rig.pose.bones['middle_03_'+side].head)*.5)
        render('FingerCurl_'+side,(.3,-1,.4),target,.38)
else:
    for pb in rig.pose.bones:
        angle=0
        if pb.name in ['forelimb_3_l','arm_3_l','branch_arm_3_l']:angle=30
        if pb.name in ['forelimb_3_r','arm_3_r','branch_arm_3_r']:angle=-20
        if pb.name in ['hindlimb_1_l','leg_1_l','root_leg_1_l']:angle=15
        if pb.name.startswith(('robe_front_1','sleeve1_1','tail_2')):angle=18
        if pb.name=='head':angle=-12
        if pb.name=='jaw':angle=15
        if angle:pb.rotation_mode='XYZ';pb.rotation_euler.x=math.radians(angle)
    bpy.context.view_layer.update()
    render('PoseFront',(0,-1,.1))
    render('PoseSide',(1,-.15,.1))
print('RIG_REVIEW_RENDERED',NAME,flush=True)
