"""Repair skeletal-mesh shader usage for previously imported character materials."""
import unreal as u
import json
from pathlib import Path

ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).parent
assert not u.EditorLevelLibrary.get_pie_worlds(False), 'Stop PIE before repairing character assets'
records=json.loads((ROOT/'resources/CharacterSources.json').read_text())['characters']
for record in records:
    name=record['name'];folder=record['unreal_folder']
    material=u.load_asset(folder+'/M_'+name)
    assert isinstance(material,u.Material),name
    material.set_editor_property('used_with_skeletal_mesh',True)
    u.MaterialEditingLibrary.recompile_material(material)
    assert u.MaterialEditingLibrary.has_material_usage(material,u.MaterialUsage.MATUSAGE_SKELETAL_MESH),name
    assert u.EditorAssetLibrary.save_loaded_asset(material,only_if_is_dirty=False)
    mesh=u.load_asset(folder+'/'+name)
    slots=mesh.get_editor_property('materials')
    assert slots and all(slot.material_interface==material for slot in slots),name
    print('CHARACTER_MATERIAL_FIXED',name)
