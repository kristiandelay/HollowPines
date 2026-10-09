"""Adapt the licensed wound painter to each Hollow Pines survivor material."""
import unreal as u
import json
from pathlib import Path
ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).parent
BASE='/Game/HollowPines/Gore'
VENDOR='/Game/ThatIndividual_GoreSystem'
lib=u.EditorAssetLibrary
assets=u.AssetToolsHelpers.get_asset_tools()
edit=u.MaterialEditingLibrary
assert not u.EditorLevelLibrary.get_pie_worlds(False)
def save(a):
    assert lib.save_loaded_asset(a,only_if_is_dirty=False)
def duplicate(source,target):
    return u.load_asset(target) if lib.does_asset_exist(target) else lib.duplicate_asset(source,target)

painter=duplicate(VENDOR+'/Blueprints/BP_GoreSystem_hit_sender',BASE+'/BP_PlayerGorePainter')
assert u.HPWorldTools.configure_gore_painter(painter)
defaults=u.get_default_object(painter.generated_class())
for key,value in {'- Preset Set':'True','- GoreSystemON -':'True','Use Gore Deep Wounds':'True',
    'Use Bleed Soaking':'True','Use Bleeding':'True','Use Mesh Decal Slices':'True',
    'No Torso Dismemberment':'True','Drop Random Organs':'True','Use Dismemberment':'False',
    'Use Multiplayer Replication':'False','bReplicates':'False'}.items():
    assert u.CRBlueprintTools.set_property_text(defaults,key,value),key
save(painter)

master=duplicate(VENDOR+'/Materials/M_GoreSystemMaterial',BASE+'/M_PlayerGore')
master.set_editor_property('used_with_skeletal_mesh',True)
expressions=list(edit.get_material_expressions(master))
by_name={e.get_name():e for e in expressions}
# The source players use separate roughness and metallic maps. Preserve those
# channels while retaining the package's wound blending and depth functions.
for kind,node_name,y in [('Roughness','MaterialExpressionLinearInterpolate_5',1600),('Metallic','MaterialExpressionLinearInterpolate_6',1800)]:
    e=next((x for x in expressions if isinstance(x,u.MaterialExpressionTextureSampleParameter2D) and str(x.get_editor_property('parameter_name'))=='Player '+kind),None)
    if not e:e=edit.create_material_expression(master,u.MaterialExpressionTextureSampleParameter2D,-1100,y)
    e.set_editor_property('parameter_name','Player '+kind)
    e.texture=u.load_asset('/Game/HollowPines/Players/MayaCross/Textures/MayaCross_'+kind)
    e.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_MASKS
    assert edit.connect_material_expressions(e,'R',by_name[node_name],'A')
ao=next((e for e in expressions if isinstance(e,u.MaterialExpressionScalarParameter) and str(e.get_editor_property('parameter_name'))=='Player AO'),None)
if not ao:ao=edit.create_material_expression(master,u.MaterialExpressionScalarParameter,-1100,2000)
ao.set_editor_property('parameter_name','Player AO');ao.set_editor_property('default_value',1)
assert edit.connect_material_expressions(ao,'',by_name['MaterialExpressionLinearInterpolate_3'],'A')
# A shared render-target asset may contain demo paint. New characters start clean.
empty_mask=duplicate(VENDOR+'/Textures/T_black',BASE+'/T_EmptyWoundMask')
empty_mask.set_editor_property('srgb',False)
save(empty_mask)
for e in expressions:
    if isinstance(e,u.MaterialExpressionTextureSampleParameter2D) and str(e.get_editor_property('parameter_name'))=='MaskMapTexture':
        e.texture=empty_mask
        e.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR
edit.recompile_material(master);save(master)
players=[]
sub=u.get_engine_subsystem(u.SubobjectDataSubsystem)
data=u.SubobjectDataBlueprintFunctionLibrary
for record in json.loads((ROOT/'resources/CharacterSources.json').read_text())['characters']:
    if record['category']!='Players':continue
    name=record['name'];folder='/Game/HollowPines/Players/'+name
    path=BASE+'/Materials/MI_'+name+'_Gore'
    mi=u.load_asset(path) if lib.does_asset_exist(path) else assets.create_asset(path.rsplit('/',1)[-1],BASE+'/Materials',u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
    edit.set_material_instance_parent(mi,master)
    for parameter,kind in [('Color','BaseColor'),('Normal','Normal'),('Player Roughness','Roughness'),('Player Metallic','Metallic')]:
        texture=u.load_asset(folder+'/Textures/'+name+'_'+kind)
        edit.set_material_instance_texture_parameter_value(mi,parameter,texture)
        assert edit.get_material_instance_texture_parameter_value(mi,parameter)==texture,(name,parameter)
    edit.set_material_instance_scalar_parameter_value(mi,'Gore Depth',-1.5)
    edit.update_material_instance(mi);save(mi)
    mesh=u.load_asset(folder+'/'+name)
    slots=list(mesh.get_editor_property('materials'))
    for slot in slots:slot.material_interface=mi
    mesh.set_editor_property('materials',slots)
    u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem).set_allow_cpu_access(mesh,True)
    save(mesh)
    bp=u.load_asset(folder+'/BP_'+name)
    for h in sub.k2_gather_subobject_data_for_blueprint(bp):
        c=data.get_object_for_blueprint(data.get_data(h),bp)
        if isinstance(c,u.SkeletalMeshComponent):c.set_material(0,mi)
    u.BlueprintEditorLibrary.compile_blueprint(bp);save(bp)
    players.append({'name':name,'mesh':mesh.get_path_name(),'material':mi.get_path_name()})
    print('PLAYER_GORE_MATERIAL',name,flush=True)

organs=[]
for name in ['heart','liver','kidneyL','stomach']:
    path=BASE+'/Organs/SM_'+name
    if lib.does_asset_exist(path):organ=u.load_asset(path)
    else:
        bp=u.load_asset(VENDOR+'/Blueprints/HumanBody_Blueprints/HumanOrgans_blueprints/BP_'+name)
        source=None
        for h in sub.k2_gather_subobject_data_for_blueprint(bp):
            c=data.get_object_for_blueprint(data.get_data(h),bp)
            if isinstance(c,u.SkeletalMeshComponent):source=c.skeletal_mesh_asset
        assert source,name
        dynamic,outcome=u.GeometryScript_AssetUtils.copy_mesh_from_skeletal_mesh(source,u.DynamicMesh(),u.GeometryScriptCopyMeshFromAssetOptions(),u.GeometryScriptMeshReadLOD())
        bounds=u.GeometryScript_MeshQueries.get_mesh_bounding_box(dynamic)
        u.GeometryScript_MeshTransforms.translate_mesh(dynamic,-(bounds.min+bounds.max)*.5)
        options=u.GeometryScriptCreateNewStaticMeshAssetOptions()
        options.enable_recompute_normals=True;options.enable_recompute_tangents=True
        options.enable_collision=False
        organ,outcome=u.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dynamic,path,options)
        assert organ,(name,outcome)
        for i,slot in enumerate(source.get_editor_property('materials')):organ.set_material(i,slot.material_interface)
        save(organ)
    organs.append(organ)

path=BASE+'/DA_PlayerGore'
factory=u.DataAssetFactory();factory.set_editor_property('data_asset_class',u.HollowPinesGoreProfile)
profile=u.load_asset(path) if lib.does_asset_exist(path) else assets.create_asset('DA_PlayerGore',BASE,u.HollowPinesGoreProfile,factory)
profile.set_editor_property('painter_class',painter.generated_class())
all_assets=lib.list_assets(VENDOR,recursive=True,include_folder=False)
for prop,name in [('impact_effect','FXS_BloodProcedural_Small'),('slice_effect','FXS_SlicingEffect'),('bleed_effect','FXS_DrippingBlood_Continual')]:
    path=next(p for p in all_assets if p.rsplit('.',1)[-1]==name)
    profile.set_editor_property(prop,u.load_asset(path))
profile.set_editor_property('organ_meshes',organs)
profile.set_editor_property('cut_material',u.load_asset(VENDOR+'/Materials/M_GoreMaterial'))
profile.set_editor_property('bleed_seconds',8);profile.set_editor_property('organ_drop_chance',.35)
save(profile)
(ROOT/'resources/PlayerGoreAssets.json').write_text(json.dumps({'profile':profile.get_path_name(),'players':players,
    'protected':['root','pelvis','spine','torso'],'organs':[x.get_path_name() for x in organs],
    'wounds':'Replicated from Lyra damage hit context; slash tag HollowPines.Damage.Slash',
    'cuts':'Fatal slashes only; allowed limb/head branches; protected torso remains intact'},indent=2)+'\n')
print('PLAYER_GORE_ASSETS_COMPLETE',flush=True)
