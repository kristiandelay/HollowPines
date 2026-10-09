"""Import baked creature clips, locomotion blends and spawnable AI archetypes."""
import unreal as u
import json
from pathlib import Path

ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).parent
lib=u.EditorAssetLibrary
tools=u.AssetToolsHelpers.get_asset_tools()
assert not u.EditorLevelLibrary.get_pie_worlds(False)
u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')

def save(asset):
    assert lib.save_loaded_asset(asset,only_if_is_dirty=False)

def asset(name,folder,cls,factory):
    return u.load_asset(folder+'/'+name) if lib.does_asset_exist(folder+'/'+name) else tools.create_asset(name,folder,cls,factory)

profiles={
    'CaveStalker':(160,370,70,70,220,230),
    'HollowStalker':(175,420,60,124,250,270),
    'HollowRootRevenant':(140,300,140,278,480,480),
    'Hag':(130,280,65,142,240,240),
}
enum={'JumpStart':u.HPMonsterAction.JUMP_START,'JumpLoop':u.HPMonsterAction.JUMP_LOOP,'Land':u.HPMonsterAction.LAND,
      'Attack1':u.HPMonsterAction.ATTACK1,'Attack2':u.HPMonsterAction.ATTACK2,'Attack3':u.HPMonsterAction.ATTACK3,
      'HitFront':u.HPMonsterAction.HIT_FRONT,'HitLeft':u.HPMonsterAction.HIT_LEFT,'HitRight':u.HPMonsterAction.HIT_RIGHT,'Death':u.HPMonsterAction.DEATH}
report=[]
for name,(walk,run,radius,half,space,reach) in profiles.items():
    folder='/Game/HollowPines/Monsters/'+name
    skeleton=u.load_asset(folder+'/'+name+'_Skeleton')
    manifest=json.loads((ROOT/'Art/Characters'/name/'Animations/AnimationManifest.json').read_text())
    clips={}
    for clip in manifest['clips']:
        label=clip['name'];asset_name=name+'_'+label
        options=u.FbxImportUI()
        for key,value in {'import_mesh':False,'import_as_skeletal':True,'import_animations':True,
            'mesh_type_to_import':u.FBXImportType.FBXIT_ANIMATION,'original_import_type':u.FBXImportType.FBXIT_ANIMATION,
            'automated_import_should_detect_type':False,'import_materials':False,'import_textures':False,'skeleton':skeleton}.items():
            options.set_editor_property(key,value)
        data=options.anim_sequence_import_data
        data.set_editor_property('animation_length',u.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
        data.set_editor_property('use_default_sample_rate',True)
        data.set_editor_property('import_bone_tracks',True)
        task=u.AssetImportTask()
        task.filename=str(ROOT/'Art/Characters'/name/'Animations'/(asset_name+'.fbx'))
        task.destination_path=folder+'/Animations';task.destination_name=asset_name
        task.automated=True;task.replace_existing=True;task.save=True;task.options=options
        tools.import_asset_tasks([task])
        sequence=u.load_asset(task.destination_path+'/'+asset_name)
        if not sequence:
            imported=[u.load_asset(p) for p in task.imported_object_paths]
            sequence=next((a for a in imported if isinstance(a,u.AnimSequence)),None)
            assert sequence,(name,label,task.imported_object_paths)
            lib.rename_asset(sequence.get_path_name(),task.destination_path+'/'+asset_name)
        assert isinstance(sequence,u.AnimSequence),(name,label)
        assert abs(sequence.get_play_length()-clip['duration'])<.06,(name,label,sequence.get_play_length())
        sequence.set_editor_property('enable_root_motion',False)
        # Preserve authored hover/death bone motion; locomotion translation comes from CharacterMovement.
        sequence.set_editor_property('force_root_lock',False)
        save(sequence);clips[label]=sequence
    factory=u.BlendSpaceFactory1D();factory.set_editor_property('target_skeleton',skeleton)
    blend=asset('BS_'+name+'_Locomotion',folder+'/Animations',u.BlendSpace1D,factory)
    assert u.HPWorldTools.configure_locomotion(blend,clips['Idle'],clips['Walk'],clips['Run'],walk,run)
    save(blend)
    factory=u.AnimBlueprintFactory();factory.set_editor_property('target_skeleton',skeleton)
    factory.set_editor_property('parent_class',u.HollowPinesMonsterAnimInstance)
    abp=asset('ABP_'+name,folder,u.AnimBlueprint,factory)
    assert u.HPWorldTools.build_creature_animation(abp,blend,clips['Idle']),name
    save(abp)
    factory=u.DataAssetFactory();factory.set_editor_property('data_asset_class',u.HollowPinesMonsterProfile)
    profile=asset('DA_'+name,folder,u.HollowPinesMonsterProfile,factory)
    profile.set_editor_properties({'mesh':u.load_asset(folder+'/'+name),'animation_class':abp.generated_class(),
        'locomotion':blend,'actions':{enum[k]:v for k,v in clips.items() if k in enum},
        'walk_speed':walk,'run_speed':run,'capsule_radius':radius,'capsule_half_height':half,
        'personal_space':space,'melee_reach':reach,'hover':name=='Hag'})
    save(profile)
    factory=u.BlueprintFactory();factory.set_editor_property('parent_class',u.HollowPinesMonster)
    bp=asset('BP_NPC_'+name,folder,u.Blueprint,factory)
    cdo=u.get_default_object(bp.generated_class());cdo.set_editor_property('profile',profile)
    cdo.set_editor_property('rehearse_attacks',False)
    u.BlueprintEditorLibrary.compile_blueprint(bp)
    assert not u.CRBlueprintTools.has_blueprint_errors(bp)
    save(bp)
    report.append({'name':name,'clips':len(clips),'blueprint':bp.get_path_name(),'player_attacks_enabled':False})
    print('MONSTER_READY',name,flush=True)
(ROOT/'resources/MonsterAnimationAssets.json').write_text(json.dumps(report,indent=2)+'\n')
