"""Audit saved character assets and the visual catalog after PIE has stopped."""
import unreal as u
import json
from pathlib import Path

ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).parent
assert not u.EditorLevelLibrary.get_pie_worlds(False)
lib=u.EditorAssetLibrary
editor=u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem)
records=json.loads((ROOT/'resources/CharacterSources.json').read_text())['characters']
catalog=u.get_default_object(u.load_asset('/Game/Blueprints/GM_Sandbox').generated_class()).get_editor_property('VisualOverrides_Soft')
assert len(catalog)==11,len(catalog)
result={'passed':False,'catalog_entries':[c.get_path_name() for c in catalog],'characters':[]}
for record in records:
    name=record['name'];folder=record['unreal_folder']
    mesh=u.load_asset(folder+'/'+name)
    assert isinstance(mesh,u.SkeletalMesh),name
    assert editor.get_lod_count(mesh)==3,name
    expected_material=u.load_asset(folder+'/M_'+name)
    assert expected_material,name
    assert u.MaterialEditingLibrary.has_material_usage(expected_material,u.MaterialUsage.MATUSAGE_SKELETAL_MESH), 'Missing skeletal-mesh material usage: '+name
    material_slots=mesh.get_editor_property('materials')
    assert material_slots and all(slot.material_interface==expected_material for slot in material_slots), 'Unexpected mesh materials: '+name
    physics=mesh.get_editor_property('physics_asset')
    assert physics,name
    physics_package=physics.get_path_name().split('.')[0].removeprefix('/Game/')
    assert (ROOT/'src/Content'/(physics_package+'.uasset')).is_file(), 'Physics asset was not saved: '+name
    assert editor.is_physics_asset_compatible(mesh,physics),name
    skeleton=mesh.get_editor_property('skeleton')
    assert skeleton and lib.does_asset_exist(skeleton.get_path_name())
    component=u.new_object(u.SkeletalMeshComponent)
    component.set_skeletal_mesh_asset(mesh)
    bones=[str(component.get_bone_name(i)) for i in range(component.get_num_bones())]
    assert 'root' in bones,name
    for i in range(len(bones)):
        scale=component.get_ref_pose_transform(i).scale3d
        assert max(abs(scale.x-1),abs(scale.y-1),abs(scale.z-1))<.001,(name,bones[i],scale)
    ik=u.load_asset(folder+'/IK_'+name)
    assert isinstance(ik,u.IKRigDefinition),name
    chain_count=len(u.IKRigController.get_controller(ik).get_retarget_chains())
    actor=u.load_asset(folder+'/BP_'+name)
    assert isinstance(actor,u.Blueprint),name
    assert not u.CRBlueprintTools.has_blueprint_errors(actor),name
    if record['category']=='Players':
        assert any(c.get_path_name()==actor.generated_class().get_path_name() for c in catalog),name
        for side in ['l','r']:
            for finger in ['thumb','index','middle','ring','pinky']:
                for index in [1,2,3]:assert f'{finger}_{index:02}_{side}' in bones,(name,finger,side,index)
        retarget=u.load_asset(folder+'/RTG_Manny_to_'+name)
        assert isinstance(retarget,u.IKRetargeter)
    else:
        assert 'pelvis' not in bones,'A creature was forced onto a human skeleton'
    for kind in ['BaseColor','Normal','Metallic','Roughness']:
        texture=u.load_asset(folder+'/Textures/'+name+'_'+kind)
        assert texture and texture.get_editor_property('srgb')==(kind=='BaseColor')
    bounds=mesh.get_bounds()
    result['characters'].append({'name':name,'skeletal_mesh':mesh.get_path_name(),'skeleton':skeleton.get_path_name(),
        'bones':len(bones),'lods':editor.get_lod_count(mesh),'ik_chains':chain_count,'physics':physics.get_path_name(),
        'root_motion_bone':bones[0],
        'bounds_cm':{'origin':[bounds.origin.x,bounds.origin.y,bounds.origin.z],
                     'extent':[bounds.box_extent.x,bounds.box_extent.y,bounds.box_extent.z]}})
result['passed']=True
(ROOT/'resources/CharacterAssetValidation.json').write_text(json.dumps(result,indent=2)+'\n')
print('UNREAL_CHARACTER_VALIDATION_PASSED',len(records))
