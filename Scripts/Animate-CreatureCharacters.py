"""Author editable, anatomy-specific blocking animation and baked FBX clips.

Run with Blender --background --python this_file -- CreatureName.
The delivered rig is preserved. These are first-pass animation review clips.
"""
import bpy
import math
import json
import sys
from pathlib import Path
from mathutils import Vector, Quaternion

ROOT = Path(__file__).resolve().parents[1]
NAME = sys.argv[sys.argv.index('--') + 1]
ASSET = ROOT / 'Art/Characters' / NAME
OUT = ASSET / 'Animations'
OUT.mkdir(exist_ok=True)
bpy.context.preferences.use_preferences_save = False
bpy.ops.wm.open_mainfile(filepath=str(ASSET / (NAME + '.blend')))
rig = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
mesh = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
scene = bpy.context.scene
scene.render.fps = 30
rig.animation_data_clear()
rig.animation_data_create()
PB = rig.pose.bones
HAG = NAME == 'Hag'
CAVE = NAME == 'CaveStalker'
ROOTLING = NAME == 'HollowRootRevenant'
SIZE = {'CaveStalker': 103, 'HollowStalker': 240, 'HollowRootRevenant': 550, 'Hag': 230}[NAME]
SPINE = 'trunk' if ROOTLING else 'spine'
ARM = 'branch_arm' if ROOTLING else ('forelimb' if CAVE else 'arm')
LEG = 'root_leg' if ROOTLING else ('hindlimb' if CAVE else 'leg')
TAU = math.tau

def smooth(x):
    x = max(0.0, min(1.0, x))
    return x*x*(3-2*x)

def pulse(t, a, peak, end):
    return smooth((t-a)/(peak-a)) if t < peak else 1-smooth((t-peak)/(end-peak))

def rotate(name, x=0, y=0, z=0):
    if name not in PB:
        return
    p = PB[name]
    basis = p.bone.matrix_local.to_quaternion().inverted()
    for axis, angle in [((1,0,0),x), ((0,1,0),y), ((0,0,1),z)]:
        if angle:
            p.rotation_quaternion @= Quaternion(basis @ Vector(axis), math.radians(angle))

def move(name, xyz):
    PB[name].location += PB[name].bone.matrix_local.to_quaternion().inverted() @ Vector(xyz)

def reset():
    for p in PB:
        p.rotation_mode = 'QUATERNION'
        p.rotation_quaternion = Quaternion()
        p.location = (0,0,0)
        p.scale = (1,1,1)
        for c in p.constraints:
            if c.type == 'IK':
                c.influence = 0

def idle(t, cycle=3.2):
    w = TAU*t/cycle
    move('root', (0, 0, (42 + 6*math.sin(w)) if HAG else SIZE*.004*math.sin(w)))
    rotate(SPINE+'_1', x=1.1*math.sin(w), z=.8*math.sin(w))
    rotate(SPINE+'_2', x=1.5*math.sin(w+.3))
    rotate('head', x=-1.4*math.sin(w+.3), z=2*math.sin(w*.999))
    rotate('jaw', x=2+1.5*math.sin(w))
    for side, sign in [('l',1),('r',-1)]:
        lower = 50 if (HAG or ROOTLING) else (12 if not CAVE else 0)
        rotate(f'{ARM}_2_{side}', y=sign*(lower+1.8*math.sin(w+.6)), z=sign*4)
        rotate(f'{ARM}_3_{side}', z=-sign*(12 if HAG else 5))
        for i in range(1,5):
            for j in range(1,4):
                rotate(f'claw{i}_{j}_{side}', y=sign*(12+4*math.sin(w+i*.35)))
        if HAG:
            # Counter the lowered shoulder on the long hanging fabric.
            for sleeve in [1,2]:
                rotate(f'sleeve{sleeve}_1_{side}', y=-sign*(lower*.85), x=4*math.sin(w+.7))
                for j in [2,3]:
                    rotate(f'sleeve{sleeve}_{j}_{side}', x=5*math.sin(w+.7+j*.45), y=sign*2)
            for panel in ['front','back']:
                for j in [1,2,3]:
                    rotate(f'robe_{panel}_{j}_{side}', x=4*math.sin(w+j*.5+sign*.4), y=sign*3)
    if HAG:
        rotate('hat', x=2*math.sin(w+.8), z=2*math.sin(w+.4))
    if CAVE:
        for i in range(1,4):
            rotate(f'tail_{i}', z=5*math.sin(w+i*.6))

def foot_target(label, phase, stride, lift, body_z):
    control = PB.get('CTRL_'+label)
    if not control:
        return
    phase %= 1
    stance = .6
    if phase < stance:
        y = -stride*.5 + stride*(phase/stance)
        z = 0
    else:
        swing = (phase-stance)/(1-stance)
        y = stride*.5 - stride*smooth(swing)
        z = lift*math.sin(math.pi*swing)
    move(control.name, (0,y,z-body_z))
    for p in PB:
        for c in p.constraints:
            if c.type == 'IK' and c.subtarget == control.name:
                c.influence = 1

def gait(t, duration, running):
    idle(t, duration)
    w=TAU*t/duration
    if HAG:
        rotate('root', x=7 if running else 3)
        for side, sign in [('l',1),('r',-1)]:
            rotate(f'arm_2_{side}', y=-sign*(16 if running else 6), z=sign*8*math.sin(w))
            for j in range(1,4):
                rotate(f'robe_back_{j}_{side}', x=10 if running else 5)
        return
    bob = SIZE*(.012 if running else .007)*math.cos(2*w)
    move('root',(0,0,bob))
    # Keep ankle targets in world space while the torso bobs.
    body_z = PB['root'].location.dot(PB['root'].bone.matrix_local.to_quaternion().inverted() @ Vector((0,0,1)))
    stride = SIZE*(.42 if running else .24)
    lift = SIZE*(.10 if running else .055)
    for side, sign, offset in [('l',1,0),('r',-1,.5)]:
        phase=t/duration+offset
        if CAVE:
            foot_target(side+'Fore',phase,stride,lift,body_z)
            foot_target(side+'Hind',phase+(.5 if running else .28),stride*.65,lift*.8,body_z)
        else:
            foot_target(side+('RootLeg' if ROOTLING else 'Leg'),phase,stride,lift,body_z)
            rotate(f'{ARM}_2_{side}', x=(15 if running else 9)*math.sin(TAU*phase), z=sign*4*math.sin(w))
    rotate(SPINE+'_1', z=(2 if CAVE else 3)*math.sin(w), x=3 if running else 0)
    rotate(SPINE+'_3', z=-2*math.sin(w))
    rotate('head', x=-3 if running else 0)

def action_pose(kind,t,duration):
    p=t/duration
    idle(t)
    if kind.startswith('Attack'):
        attack=int(kind[-1])
        wind=pulse(p,0,.23,.48)
        strike=pulse(p,.23,.43,.82)
        rotate(SPINE+'_1', x=-10*wind+18*strike, z=(18*wind-30*strike) * (1 if attack==1 else -1) if attack<3 else 0)
        rotate('head', x=8*wind-10*strike)
        rotate('jaw', x=22*strike)
        if CAVE:
            if attack==1:
                rotate('neck',x=-18*wind+32*strike)
                move('root',(0,-18*strike,4*wind))
            elif attack==2:
                rotate('forelimb_2_l',y=-28*wind+38*strike,z=30*wind-48*strike)
                rotate('forelimb_3_l',x=-35*wind+48*strike)
            else:
                move('root',(0,-30*strike,18*pulse(p,.12,.4,.78)))
                for side in ['l','r']:
                    rotate('forelimb_2_'+side,x=-30*wind+35*strike)
                    rotate('hindlimb_1_'+side,x=22*wind-22*strike)
        else:
            for side, sign in [('l',1),('r',-1)]:
                active=attack==3 or (side=='l' if attack==1 else side=='r')
                if active:
                    rotate(f'{ARM}_2_{side}', y=-sign*(55*wind+25*strike), z=sign*(34*wind-65*strike))
                    rotate(f'{ARM}_3_{side}', z=sign*(25*wind-40*strike))
                for i in range(1,5):
                    for j in range(1,4):
                        rotate(f'claw{i}_{j}_{side}', y=sign*18*strike)
            if attack==3:
                rotate(SPINE+'_2',x=-12*wind+25*strike)
                move('root',(0,-SIZE*.05*strike,(-SIZE*.07*strike if not HAG else 35*wind-30*strike)))
                if ROOTLING:
                    rotate('root_leg_1_l',x=-22*wind+15*strike)
                    rotate('root_leg_2_l',x=32*wind)
    elif kind.startswith('Hit'):
        recoil=pulse(p,0,.17,1)
        rotate(SPINE+'_1',x=-15*recoil if kind=='HitFront' else -5*recoil,
               z=(18 if kind=='HitLeft' else -18 if kind=='HitRight' else 0)*recoil)
        rotate('head',x=-12*recoil,z=(12 if kind=='HitLeft' else -12)*recoil)
        rotate('jaw',x=14*recoil)
        for side,sign in [('l',1),('r',-1)]:
            rotate(f'{ARM}_2_{side}',y=-sign*12*recoil)
    elif kind in ['JumpStart','JumpLoop','Land']:
        amount=smooth(p) if kind=='JumpStart' else (1-smooth(p) if kind=='Land' else .8+.1*math.sin(TAU*p))
        if HAG:
            rotate(SPINE+'_1',x=-8*amount)
            for side,sign in [('l',1),('r',-1)]:
                rotate(f'arm_2_{side}',y=-sign*25*amount)
                for j in range(1,4):rotate(f'robe_back_{j}_{side}',x=12*amount)
        else:
            move('root',(0,0,-SIZE*.055*amount if kind!='JumpLoop' else SIZE*.02))
            rotate(SPINE+'_1',x=12*amount)
            for side,sign in [('l',1),('r',-1)]:
                rotate(f'{LEG}_1_{side}',x=-25*amount)
                rotate(f'{LEG}_2_{side}',x=35*amount)
                rotate(f'{ARM}_2_{side}',x=-15*amount,y=-sign*15*amount if not CAVE else 0)
    elif kind=='Death':
        sink=smooth((p-.1)/.58)
        roll=smooth((p-.2)/.62)
        if HAG:
            move('root',(0,0,-42*sink))
        rotate('root',x=(72 if CAVE else -78)*roll,y=15*roll)
        move('root',(0,SIZE*.13*sink,-SIZE*.18*sink))
        rotate(SPINE+'_1',x=25*sink)
        rotate('head',x=24*sink,z=18*roll)
        for side,sign in [('l',1),('r',-1)]:
            rotate(f'{ARM}_2_{side}',y=sign*15*sink,z=sign*30*sink)
            rotate(f'{ARM}_3_{side}',z=sign*35*sink)
            if not HAG:
                rotate(f'{LEG}_1_{side}',x=-40*sink)
                rotate(f'{LEG}_2_{side}',x=60*sink)
        # Hold a still final pose rather than continuing breathing after death.
        if p>.88:
            pass

clips=[('Idle',3.2,True),('Walk',1.2 if not ROOTLING else 1.8,True),
       ('Run',.7 if not ROOTLING else 1.1,True),('JumpStart',.4,False),('JumpLoop',.8,True),
       ('Land',.55,False),('Attack1',1.4,False),('Attack2',1.6,False),('Attack3',2.0,False),
       ('HitFront',.7,False),('HitLeft',.7,False),('HitRight',.7,False),('Death',2.6,False)]
report={'creature':NAME,'stage':'Animation blocking for review','fps':30,'clips':[]}
actions={}
for kind,duration,loop in clips:
    action=bpy.data.actions.new(NAME+'_'+kind)
    action.use_fake_user=True
    rig.animation_data.action=action
    frames=round(duration*30)
    scene.frame_start=1;scene.frame_end=frames+1
    for f in range(frames+1):
        scene.frame_set(f+1)
        reset()
        t=min(f/30, duration*.88) if kind=='Death' else f/30
        if kind=='Idle':idle(t,duration)
        elif kind in ['Walk','Run']:gait(t,duration,kind=='Run')
        else:action_pose(kind,t,duration)
        if kind=='Death':
            bpy.context.view_layer.update()
            dg=bpy.context.evaluated_depsgraph_get()
            evaluated=mesh.evaluated_get(dg)
            bottom=min(v.co.z for v in evaluated.data.vertices)
            move('root',(0,0,2-bottom))
        for pb in PB:
            pb.keyframe_insert('location',frame=f+1,group=pb.name)
            pb.keyframe_insert('rotation_quaternion',frame=f+1,group=pb.name)
            for c in pb.constraints:
                if c.type=='IK':c.keyframe_insert('influence',frame=f+1)
    actions[kind]=action
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
    bpy.context.view_layer.objects.active=rig
    bpy.ops.export_scene.fbx(filepath=str(OUT/(NAME+'_'+kind+'.fbx')),
        use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,use_armature_deform_only=True,
        bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,
        bake_anim_force_startend_keying=True,bake_anim_simplify_factor=0,
        axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL')
    report['clips'].append({'name':kind,'duration':frames/30,'frames':frames+1,'loop':loop})
    print('CLIP_EXPORTED',NAME,kind,flush=True)

rig.animation_data.action=actions['Idle']
scene.frame_start=1;scene.frame_end=97;scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(ASSET/(NAME+'_Animations.blend')))
(OUT/'AnimationManifest.json').write_text(json.dumps(report,indent=2)+'\n')

# Render representative poses with the original textures for deformation review.
review=ASSET/'Review/Animation';review.mkdir(parents=True,exist_ok=True)
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO';scene.display.shading.color_type='TEXTURE'
scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
scene.display.shading.background_type='WORLD';scene.world.color=(.055,.065,.075)
scene.render.resolution_x=480;scene.render.resolution_y=560;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
camdata=bpy.data.cameras.new('AnimationReview');cam=bpy.data.objects.new('AnimationReview',camdata)
scene.collection.objects.link(cam);scene.camera=cam;camdata.type='ORTHO';camdata.clip_end=10000
target=Vector((0,0,SIZE*.5+(20 if HAG else 0)))
cam.location=target+Vector((.4,-1,.12)).normalized()*SIZE*4
cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();camdata.ortho_scale=SIZE*1.45 if not CAVE else SIZE*2.6
for kind,duration,_ in clips:
    rig.animation_data.action=actions[kind]
    scene.frame_set(round(duration*30*(.96 if kind=='Death' else .43))+1)
    scene.render.filepath=str(review/(kind+'.png'));bpy.ops.render.render(write_still=True)
print('ANIMATION_COMPLETE',NAME,flush=True)
