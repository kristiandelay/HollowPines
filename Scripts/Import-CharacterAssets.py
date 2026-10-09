"""Import Hollow Pines rig exports and PBR materials into the running editor."""
import unreal as u
import json
from pathlib import Path

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).parent
lib = u.EditorAssetLibrary
tools = u.AssetToolsHelpers.get_asset_tools()
assert not u.EditorLevelLibrary.get_pie_worlds(False)

def save(asset):
    assert lib.save_loaded_asset(asset, only_if_is_dirty=False)

u.SystemLibrary.execute_console_command(None, 'Interchange.FeatureFlags.Import.FBX 0')
for record in json.loads((ROOT/'resources/CharacterSources.json').read_text())['characters']:
    name = record['name']
    if name not in globals().get('CHARACTER_IMPORT_NAMES', [r['name'] for r in json.loads((ROOT/'resources/CharacterSources.json').read_text())['characters']]):
        continue
    source = ROOT/'Art/Characters'/name
    assert json.loads((source/'RigValidation.json').read_text())['passed']
    destination = '/Game/HollowPines/'+record['category']+'/'+name
    textures = {}
    for kind in ['BaseColor','Normal','Metallic','Roughness']:
        asset_name = name+'_'+kind
        task = u.AssetImportTask()
        task.filename = str(source/'Source'/(asset_name+'.png'))
        task.destination_path = destination+'/Textures'
        task.destination_name = asset_name
        task.automated = True
        task.replace_existing = True
        task.save = True
        tools.import_asset_tasks([task])
        texture = u.load_asset(destination+'/Textures/'+asset_name)
        assert texture, asset_name
        texture.set_editor_property('srgb', kind == 'BaseColor')
        if kind == 'Normal':
            texture.set_editor_property('compression_settings', u.TextureCompressionSettings.TC_NORMALMAP)
            texture.set_editor_property('flip_green_channel', True)
        elif kind != 'BaseColor':
            texture.set_editor_property('compression_settings', u.TextureCompressionSettings.TC_MASKS)
        save(texture)
        textures[kind] = texture
    material_path = destination+'/M_'+name
    material = u.load_asset(material_path) if lib.does_asset_exist(material_path) else tools.create_asset('M_'+name,destination,u.Material,u.MaterialFactoryNew())
    u.MaterialEditingLibrary.delete_all_material_expressions(material)
    for i,(kind,prop) in enumerate([('BaseColor',u.MaterialProperty.MP_BASE_COLOR),('Normal',u.MaterialProperty.MP_NORMAL),('Metallic',u.MaterialProperty.MP_METALLIC),('Roughness',u.MaterialProperty.MP_ROUGHNESS)]):
        expression = u.MaterialEditingLibrary.create_material_expression(material,u.MaterialExpressionTextureSample,-400,i*220)
        expression.texture = textures[kind]
        if kind == 'Normal': expression.sampler_type = u.MaterialSamplerType.SAMPLERTYPE_NORMAL
        elif kind != 'BaseColor': expression.sampler_type = u.MaterialSamplerType.SAMPLERTYPE_MASKS
        assert u.MaterialEditingLibrary.connect_material_property(expression,'RGB' if kind in ['BaseColor','Normal'] else 'R',prop)
    u.MaterialEditingLibrary.recompile_material(material)
    save(material)
    options = u.FbxImportUI()
    for key,value in {'import_mesh':True,'import_as_skeletal':True,
            'mesh_type_to_import':u.FBXImportType.FBXIT_SKELETAL_MESH,
            'original_import_type':u.FBXImportType.FBXIT_SKELETAL_MESH,
            'automated_import_should_detect_type':False,'import_animations':False,
            'import_materials':False,'import_textures':False,'create_physics_asset':True}.items():
        options.set_editor_property(key,value)
    options.skeletal_mesh_import_data.set_editor_property('normal_import_method',u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
    options.skeletal_mesh_import_data.set_editor_property('update_skeleton_reference_pose',False)
    if lib.does_asset_exist(destination+'/'+name+'_Skeleton'):
        options.set_editor_property('skeleton',u.load_asset(destination+'/'+name+'_Skeleton'))
    task = u.AssetImportTask()
    task.filename = str(source/'Export'/(name+'.fbx'))
    task.destination_path = destination
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.save = True
    task.options = options
    tools.import_asset_tasks([task])
    mesh = u.load_asset(destination+'/'+name)
    assert isinstance(mesh,u.SkeletalMesh),str(task.imported_object_paths)
    materials = list(mesh.get_editor_property('materials'))
    for slot in materials: slot.set_editor_property('material_interface',material)
    mesh.set_editor_property('materials',materials)
    editor = u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem)
    assert editor.regenerate_lod(mesh,3,False,False)
    save(mesh)
    save(mesh.get_editor_property('skeleton'))
    physics = mesh.get_editor_property('physics_asset')
    assert physics, 'Physics asset creation failed: '+name
    save(physics)
    print('CHARACTER_IMPORTED',mesh.get_path_name(),mesh.get_editor_property('skeleton').get_path_name())
print('CHARACTER_IMPORT_COMPLETE')
