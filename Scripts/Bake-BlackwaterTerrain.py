"""Bake editable Mesh Terrain providers to ordinary play meshes (UE 5.8 fallback).

The stock compiled-section builder currently asserts in FMeshData::AppendDynamicMesh
on these imported providers. Sources remain editable in Mesh Terrain mode. Re-run
this bake after sculpting; visible baked play meshes supply collision and PIE art.
"""
import unreal as u
import json,re
from pathlib import Path

ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).parent
lib=u.EditorAssetLibrary
assets=u.AssetToolsHelpers.get_asset_tools()
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
assert not u.EditorLevelLibrary.get_pie_worlds(False)
BASE='/Game/HollowPines/Environment'

# Restore the declared channels before loading the providers. Their stored weight
# attributes require the same names even though this first material pass is unpainted.
for name in ['BlackwaterSurface','BlackwaterCaves']:
    definition=u.load_asset(BASE+'/Terrain/MPD_'+name)
    assert u.CRBlueprintTools.set_property_text(definition,'ChannelMap','(ChannelDescs=((Name="Red"),(Name="Green"),(Name="Blue"),(Name="Yellow")))')
    lib.save_loaded_asset(definition)

# WorldAlignedTexture expects a regular texture object, not a virtual texture.
texture_path=BASE+'/Materials/T_ForestFloor_Color'
texture=u.load_asset(texture_path) if lib.does_asset_exist(texture_path) else lib.duplicate_asset('/Game/EasyBiomes/Textures/Terrain/CheapVersion/T_ForestGround_10_BC',texture_path)
texture.set_editor_property('virtual_texture_streaming',False)
lib.save_loaded_asset(texture)
ground=u.load_asset(BASE+'/Materials/M_ForestFloor')
for expression in u.MaterialEditingLibrary.get_material_expressions(ground):
    if isinstance(expression,u.MaterialExpressionTextureObject):expression.texture=texture
u.MaterialEditingLibrary.recompile_material(ground);lib.save_loaded_asset(ground)

assert levels.load_level('/Game/HollowPines/Maps/L_BlackwaterReach')
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
u.SystemLibrary.execute_console_command(world,'MeshPartition.PIE.CreateMissingSections 0')
existing={a.get_actor_label():a for a in actors.get_all_level_actors() if a.actor_has_tag('HP_BakedTerrain')}
sections=[a for a in actors.get_all_level_actors() if a.get_class().get_name()=='ModifierActor' and a.actor_has_tag('HP_Terrain')]
assert len(sections)==66,('Load all authored World Partition cells before baking',len(sections))
report=[]
for section in sections:
    name=section.get_actor_label()
    mesh=u.HPWorldTools.get_mesh_terrain_section(section)
    assert mesh,name
    path=BASE+'/Geometry/SM_Terrain_'+re.sub(r'[^A-Za-z0-9_]+','_',name)
    material=ground if name.startswith('Surface ') else u.load_asset(BASE+'/Materials/M_CaveRock')
    if lib.does_asset_exist(path):
        static=u.load_asset(path)
        options=u.GeometryScriptCopyMeshToAssetOptions()
        options.enable_recompute_normals=True
        options.enable_recompute_tangents=True
        u.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(mesh,static,options,u.GeometryScriptMeshWriteLOD())
    else:
        options=u.GeometryScriptCreateNewStaticMeshAssetOptions()
        options.enable_recompute_normals=True;options.enable_recompute_tangents=True
        options.enable_collision=True;options.collision_mode=u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
        static,result=u.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(mesh,path,options)
        assert static,(name,result)
    static.set_material(0,material)
    lib.save_loaded_asset(static)
    actor=existing.get('Play Mesh - '+name)
    if not actor:actor=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector())
    actor.set_actor_label('Play Mesh - '+name)
    actor.tags=['HP_Generated','HP_BakedTerrain']
    actor.set_folder_path('HollowPines/BakedTerrain')
    actor.static_mesh_component.set_static_mesh(static)
    actor.static_mesh_component.set_collision_profile_name('BlockAll')
    # UE 5.8 preview currently asserts. Keep sources stored but disabled, and use
    # the same baked render/collision meshes in the editor and in play.
    for component in section.get_components_by_class(u.ActorComponent):
        if component.get_class().get_name()=='MeshProviderModifier':
            assert u.CRBlueprintTools.set_property_text(component,'bIsDisabled','True')
    u.CRBlueprintTools.set_property_text(actor,'bHiddenEd','False')
    actor.set_is_temporarily_hidden_in_editor(False)
    actor.set_actor_hidden_in_game(False)
    report.append({'source':name,'asset':path,'triangles':mesh.get_triangle_count()})
    print('BAKED',name,flush=True)
assert levels.save_current_level()
(ROOT/'resources/BlackwaterTerrainBake.json').write_text(json.dumps({'method':'Mesh Terrain source providers -> static render/collision meshes','native_compiler_status':'UE5.8.3 AppendDynamicMesh assertion; bake fallback active','sections':report},indent=2)+'\n')
print('BLACKWATER_BAKE_COMPLETE',len(report),flush=True)
