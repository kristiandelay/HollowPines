"""Relink normalized textures using paths relative to each editable character file."""
import bpy
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
bpy.context.preferences.use_preferences_save=False
for record in json.loads((ROOT/'resources/CharacterSources.json').read_text())['characters']:
    name=record['name'];folder=ROOT/'Art/Characters'/name
    bpy.ops.wm.open_mainfile(filepath=str(folder/(name+'.blend')))
    bpy.context.preferences.use_preferences_save=False
    used=[]
    for image in list(bpy.data.images):
        if not image.users:
            bpy.data.images.remove(image)
        elif image.source=='FILE' and image.filepath:
            path=Path(bpy.path.abspath(image.filepath))
            if path.is_file():
                image.filepath=bpy.path.relpath(str(path),start=str(folder)).replace('\\','/')
                used.append(image.filepath)
    assert len([p for p in used if p.startswith('//Source/')])>=4,(name,used)
    bpy.ops.wm.save_as_mainfile(filepath=str(folder/(name+'.blend')))
    print('PORTABLE_BLEND',name,used,flush=True)
