"""Create custom creature IK chain assets and placeable skeletal preview actors."""
import unreal as u

lib=u.EditorAssetLibrary
tools=u.AssetToolsHelpers.get_asset_tools()
assert not u.EditorLevelLibrary.get_pie_worlds(False)

def save(asset):
    if isinstance(asset,u.Blueprint):
        u.BlueprintEditorLibrary.compile_blueprint(asset)
        assert not u.CRBlueprintTools.has_blueprint_errors(asset)
    assert lib.save_loaded_asset(asset,only_if_is_dirty=False)

profiles={
    'CaveStalker': ('spine_1',[('Spine','spine_1','spine_3'),('Head','neck','head'),('Jaw','jaw','jaw'),('Tail','tail_1','tail_3')]+[(label+side,prefix+'_1_'+side,prefix+'_4_'+side) for side in ['l','r'] for label,prefix in [('Foreleg','forelimb'),('Hindleg','hindlimb')]]),
    'HollowStalker': ('spine_1',[('Spine','spine_1','spine_3'),('Head','neck','head'),('Jaw','jaw','jaw')]+[(label+side,prefix+'_1_'+side,prefix+'_4_'+side) for side in ['l','r'] for label,prefix in [('Arm','arm'),('Leg','leg')]]),
    'HollowRootRevenant': ('trunk_1',[('Trunk','trunk_1','trunk_3'),('Head','neck','crown')]+[(label+side,prefix+'_1_'+side,prefix+'_'+str(end)+'_'+side) for side in ['l','r'] for label,prefix,end in [('BranchArm','branch_arm',4),('RootLeg','root_leg',3)]]),
    'Hag': ('spine_1',[('Spine','spine_1','spine_3'),('Head','neck','hat'),('Jaw','jaw','jaw')]+[(label+side,prefix+'_1_'+side,prefix+'_'+str(end)+'_'+side) for side in ['l','r'] for label,prefix,end in [('Arm','arm',4),('SleeveInner','sleeve1',3),('SleeveOuter','sleeve2',3),('RobeFront','robe_front',3),('RobeBack','robe_back',3)]])
}
for name,(root,chains) in profiles.items():
    folder='/Game/HollowPines/Monsters/'+name
    mesh=u.load_asset(folder+'/'+name)
    assert isinstance(mesh,u.SkeletalMesh),name
    path=folder+'/IK_'+name
    ik=u.load_asset(path) if lib.does_asset_exist(path) else tools.create_asset('IK_'+name,folder,u.IKRigDefinition,u.IKRigDefinitionFactory())
    controller=u.IKRigController.get_controller(ik)
    assert controller.set_skeletal_mesh(mesh)
    controller.set_retarget_root(root)
    for old in controller.get_retarget_chains():controller.remove_retarget_chain(old.chain_name)
    for label,start,end in chains:
        assert str(controller.add_retarget_chain(label,start,end,'None'))!='None'
    for side in ['l','r']:
        for i in range(1,5):
            assert str(controller.add_retarget_chain('Claw'+str(i)+side,'claw'+str(i)+'_1_'+side,'claw'+str(i)+'_3_'+side,'None'))!='None'
    save(ik)
    path=folder+'/BP_'+name
    if lib.does_asset_exist(path):
        actor=lib.load_asset(path)
    else:
        factory=u.BlueprintFactory()
        factory.set_editor_property('parent_class',u.SkeletalMeshActor)
        actor=tools.create_asset('BP_'+name,folder,u.Blueprint,factory)
    cdo=u.get_default_object(actor.generated_class())
    component=cdo.get_editor_property('skeletal_mesh_component')
    component.set_skeletal_mesh_asset(mesh)
    component.set_editor_property('animation_mode',u.AnimationMode.ANIMATION_SINGLE_NODE)
    component.set_editor_property('component_tags',['HollowPinesCreature',name])
    save(actor)
    print('CREATURE_INTEGRATED',name,len(controller.get_retarget_chains()))
