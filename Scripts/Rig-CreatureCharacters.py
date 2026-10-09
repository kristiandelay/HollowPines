"""Build anatomy-specific creature rigs; no Unreal humanoid skeleton is imposed.

Joint coordinates are in the delivered 1.8 m source space. Sources stay untouched.
The editable Blender rigs contain FK deform chains and optional two-bone IK controls.
"""
import bpy
import json
import math
import sys
import traceback
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parents[1]
NAME = sys.argv[sys.argv.index('--')+1]
ASSET = ROOT/'Art/Characters'/NAME
OUT = ROOT/'Artifacts/CharacterPrep'/NAME
bpy.context.preferences.use_preferences_save = False
bones = []
limbs = []

def bone(name, head, tail, parent=None, deform=True):
    bones.append((name,Vector(head),Vector(tail),parent,deform))
    return name

def chain(prefix, points, parent, side=None):
    names = []
    for i in range(len(points)-1):
        name = prefix+'_'+str(i+1)+(('_'+side) if side else '')
        parent = bone(name,points[i],points[i+1],parent)
        names.append(name)
    return names

def mirrored(points, sign):
    return [(p[0]*sign,p[1],p[2]) for p in points]

def digits(wrist, spread, parent, side, sign, direction='OUT'):
    # Creature digits retain their own naming and independent three-joint chains.
    for i in range(4):
        x,y,z = wrist
        offset = (i-1.5)*spread
        if direction == 'FORWARD':
            points=[(x+offset,y,z), (x+offset*1.2,y-.10,z-.025),
                    (x+offset*1.35,y-.19,z-.055),(x+offset*1.40,y-.24,z-.10)]
        else:
            points=[(x,y+offset,z), (x+.075,y+offset*1.2,z-.015),
                    (x+.14,y+offset*1.4,z-.045),(x+.17,y+offset*1.5,z-.085)]
        chain('claw'+str(i+1),mirrored(points,sign),parent,side)

bone('root',(0,0,0),(0,0,.15),deform=False)
if NAME == 'CaveStalker':
    scale = 2.5/4.366084098815918
    description = 'Quadruped with long forelimbs, folded hindlegs, jaw and the supplied central tail appendage.'
    chain('spine',[(0,.65,1.28),(0,.12,1.24),(0,-.45,1.36),(0,-.86,1.46)],'root')
    bone('neck',(0,-.86,1.46),(0,-1.08,1.45),'spine_3')
    bone('head',(0,-1.08,1.45),(0,-1.34,1.36),'neck')
    bone('jaw',(0,-1.02,1.26),(0,-1.32,.77),'head')
    chain('tail',[(0,.70,1.27),(0,1.15,.69),(0,1.94,.25),(0,2.17,.10)],'spine_1')
    for side,sign in [('l',1),('r',-1)]:
        front=mirrored([(.30,-.54,1.35),(.61,-.58,1.19),(.92,-.68,.64),(1.00,-1.64,.32),(1.04,-1.88,.19)],sign)
        names=chain('forelimb',front,'spine_3',side)
        limbs.append((names[1],names[2],front[3],side+'Fore'))
        digits((1.04,-1.89,.18),.075,names[-1],side,sign,'FORWARD')
        hind=mirrored([(.27,.58,1.29),(.49,.36,.56),(.58,.98,.46),(.57,1.10,.13),(.57,.78,.055)],sign)
        names=chain('hindlimb',hind,'spine_1',side)
        limbs.append((names[0],names[1],hind[2],side+'Hind'))
elif NAME == 'HollowStalker':
    scale = 2.4/1.8
    description = 'Hunched biped with elongated arms, independent claws, digitigrade legs and an opening jaw.'
    chain('spine',[(0,.27,1.02),(0,.20,1.20),(0,.025,1.44),(0,-.17,1.58)],'root')
    bone('neck',(0,-.17,1.58),(0,-.31,1.61),'spine_3')
    bone('head',(0,-.31,1.61),(0,-.46,1.50),'neck')
    bone('jaw',(0,-.31,1.45),(0,-.39,1.27),'head')
    for side,sign in [('l',1),('r',-1)]:
        arm=mirrored([(.10,.02,1.47),(.28,.02,1.49),(.66,-.035,1.27),(1.02,-.16,.98),(1.10,-.24,.82)],sign)
        names=chain('arm',arm,'spine_3',side)
        limbs.append((names[1],names[2],arm[3],side+'Arm'))
        # Long descending claws, fitted to the hanging hand rather than a human palm.
        for i in range(4):
            y=-.30+i*.065
            x=1.06+(i%3)*.045
            chain('claw'+str(i+1),mirrored([(x,y,.83),(x+.055,y-.025,.73),(x+.065,y-.04,.65),(x+.035,y-.05,.57)],sign),names[-1],side)
        leg=mirrored([(.15,.27,1.02),(.21,-.04,.67),(.16,.43,.28),(.18,.19,.11),(.24,-.09,.045)],sign)
        names=chain('leg',leg,'spine_1',side)
        limbs.append((names[0],names[1],leg[2],side+'Leg'))
elif NAME == 'HollowRootRevenant':
    scale = 5.5/1.8
    description = '5.5 m forest creature with a root pelvis, tree spine, branch arms and independently curling branch digits.'
    chain('trunk',[(0,.035,1.03),(0,.025,1.20),(0,.005,1.40),(0,-.04,1.53)],'root')
    bone('neck',(0,-.04,1.53),(0,-.08,1.60),'trunk_3')
    bone('head',(0,-.08,1.60),(0,-.11,1.70),'neck')
    bone('crown',(0,-.11,1.70),(0,-.04,1.80),'head')
    for side,sign in [('l',1),('r',-1)]:
        arm=mirrored([(.06,.005,1.41),(.23,.008,1.41),(.52,.018,1.39),(.78,.01,1.385),(.86,-.015,1.375)],sign)
        names=chain('branch_arm',arm,'trunk_3',side)
        limbs.append((names[1],names[2],arm[3],side+'BranchArm'))
        digits((.86,-.015,1.375),.032,names[-1],side,sign)
        leg=mirrored([(.105,.035,1.03),(.125,.018,.59),(.16,.015,.15),(.23,-.16,.035)],sign)
        names=chain('root_leg',leg,'trunk_1',side)
        limbs.append((names[0],names[1],leg[2],side+'RootLeg'))
elif NAME == 'Hag':
    scale = 2.3/1.8
    description = 'Floating wraith rig with clawed arms, hat and face, hanging sleeves and four articulated robe panels.'
    chain('spine',[(0,.095,.73),(0,.075,.89),(0,.035,1.06),(0,-.06,1.18)],'root')
    bone('neck',(0,-.06,1.18),(0,-.13,1.26),'spine_3')
    bone('head',(0,-.13,1.26),(0,-.13,1.38),'neck')
    bone('hat',(0,-.13,1.38),(0,.025,1.78),'head')
    bone('jaw',(0,-.18,1.24),(0,-.22,1.15),'head')
    for side,sign in [('l',1),('r',-1)]:
        arm=mirrored([(.06,.015,1.13),(.18,.02,1.13),(.36,.02,1.13),(.57,-.02,1.13),(.66,-.04,1.12)],sign)
        names=chain('arm',arm,'spine_3',side)
        limbs.append((names[1],names[2],arm[3],side+'Arm'))
        digits((.66,-.04,1.12),.032,names[-1],side,sign)
        for index,x in enumerate([.29,.41]):
            chain('sleeve'+str(index+1),mirrored([(x,.045,1.11),(x,.07,.85),(x+.025,.07,.62),(x+.035,.045,.42)],sign),names[1 if index==0 else 2],side)
        for label,y in [('front',-.085),('back',.17)]:
            chain('robe_'+label,mirrored([(.09,y,.74),(.12,y,.47),(.17,y*1.4,.22),(.30,y*1.8,.035)],sign),'spine_1',side)
else:
    raise ValueError(NAME)

try:
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.fbx(filepath=str(ASSET/'Source'/(NAME+'.fbx')))
    mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH')
    mesh.name=NAME
    bpy.context.view_layer.objects.active=mesh
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    mesh.data.calc_loop_triangles()
    source_triangles=len(mesh.data.loop_triangles)
    modifier=mesh.modifiers.new('GameMeshReduction','DECIMATE')
    modifier.ratio=min(1,100000/source_triangles)
    modifier.use_collapse_triangulate=True
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=.00001)
    bpy.ops.object.mode_set(mode='OBJECT')
    mesh.data.transform(Matrix.Scale(scale,4))
    data=bpy.data.armatures.new(NAME+'_CreatureSkeleton')
    rig=bpy.data.objects.new(NAME+'_Rig',data)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active=rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for name,head,tail,parent,deform in bones:
        b=data.edit_bones.new(name)
        b.head=head*scale
        b.tail=tail*scale
        b.use_deform=deform
        if parent:b.parent=data.edit_bones[parent]
    # Unconnected IK targets keep FK as the default and are excluded from FBX.
    for upper,lower,target,label in limbs:
        b=data.edit_bones.new('CTRL_'+label)
        b.head=Vector(target)*scale
        b.tail=b.head+Vector((0,-.12*scale,0))
        b.parent=data.edit_bones['root']
        b.use_deform=False
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    mesh.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active=rig
    print('CREATURE_HEAT_BIND',NAME,flush=True)
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    bpy.context.view_layer.objects.active=mesh
    bpy.ops.object.vertex_group_clean(group_select_mode='ALL',limit=.001,keep_single=True)
    bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL',limit=4)
    bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL',lock_active=False)
    deform={b.name for b in data.bones if b.use_deform}
    groups={g.index:g.name for g in mesh.vertex_groups}
    weighted=[];missing=[]
    for v in mesh.data.vertices:
        valid=[g for g in v.groups if groups[g.group] in deform and g.weight>1e-5]
        (weighted if valid else missing).append(v.index)
    # Only tiny detached sculpt fragments may inherit adjacent, successfully solved weights.
    assert len(missing) <= len(mesh.data.vertices)*.005, ('Heat binding failed',len(missing),len(mesh.data.vertices))
    tree=KDTree(len(weighted))
    for i in weighted:tree.insert(mesh.data.vertices[i].co,i)
    tree.balance()
    for i in missing:
        _,nearest,distance=tree.find(mesh.data.vertices[i].co)
        assert distance<.04*scale, ('Detached fragment is too far from a weighted surface',i,distance)
        for influence in mesh.data.vertices[nearest].groups:
            if groups[influence.group] in deform:
                mesh.vertex_groups[influence.group].add([i],influence.weight,'REPLACE')
    for upper,lower,target,label in limbs:
        constraint=rig.pose.bones[lower].constraints.new('IK')
        constraint.name='Optional IK '+label
        constraint.target=rig
        constraint.subtarget='CTRL_'+label
        constraint.chain_count=2
        constraint.influence=0
    rig.show_in_front=True
    material=bpy.data.materials.new('M_'+NAME)
    material.use_nodes=True
    nodes=material.node_tree.nodes;links=material.node_tree.links
    shader=nodes.get('Principled BSDF')
    for kind,socket in [('BaseColor','Base Color'),('Metallic','Metallic'),('Roughness','Roughness'),('Normal','Normal')]:
        tex=nodes.new('ShaderNodeTexImage')
        tex.label=kind
        tex.image=bpy.data.images.load(str(ASSET/'Source'/(NAME+'_'+kind+'.png')),check_existing=True)
        if kind!='BaseColor':tex.image.colorspace_settings.name='Non-Color'
        if kind=='Normal':
            normal=nodes.new('ShaderNodeNormalMap')
            links.new(tex.outputs['Color'],normal.inputs['Color'])
            links.new(normal.outputs['Normal'],shader.inputs[socket])
        else:links.new(tex.outputs['Color'],shader.inputs[socket])
        if kind=='BaseColor':nodes.active=tex
    mesh.data.materials.clear();mesh.data.materials.append(material)
    for face in mesh.data.polygons:face.use_smooth=True;face.material_index=0
    scene=bpy.context.scene
    scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.01
    # Keep data in centimetres and object transforms at identity for Unreal.
    mesh.data.transform(Matrix.Scale(100,4));rig.data.transform(Matrix.Scale(100,4))
    rig['RigDescription']=description
    rig['SourceScaleMultiplier']=scale
    rig['IKUsage']='FK is default. Enable Optional IK influence on a limb to use its CTRL target.'
    bpy.context.view_layer.objects.active=rig
    export=ASSET/'Export'/(NAME+'.fbx');export.parent.mkdir(exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(ASSET/(NAME+'.blend')))
    bpy.ops.export_scene.fbx(filepath=str(export),use_selection=True,object_types={'MESH','ARMATURE'},
        add_leaf_bones=False,use_armature_deform_only=True,bake_anim=False,axis_forward='-Y',axis_up='Z',
        apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',mesh_smooth_type='FACE',path_mode='RELATIVE')
    report={'name':NAME,'description':description,'source_triangles':source_triangles,
        'game_triangles':len(mesh.data.polygons),'vertices':len(mesh.data.vertices),'deform_bones':len(deform),
        'source_scale_multiplier':scale,'repaired_fragment_vertices':len(missing),'passed':True}
    (OUT/'creature-rig-result.json').write_text(json.dumps(report,indent=2))
    print('CREATURE_RIG_COMPLETE',json.dumps(report),flush=True)
except Exception:
    error=traceback.format_exc()
    (OUT/'creature-rig-result.json').write_text(json.dumps({'passed':False,'error':error},indent=2))
    print(error,flush=True)
    raise
