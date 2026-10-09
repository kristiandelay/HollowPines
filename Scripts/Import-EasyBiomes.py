"""Merge the supplied local EasyBiomes packs without replacing existing project assets.

River provides the shared framework (including water components); Broadleaf contributes its additional assets.
Every collision and chosen source is recorded, and source projects stay untouched.
"""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [ROOT.parent / 'RiverGeneratorPCGBiome', ROOT.parent / 'BroadleafPCG']
DEST = ROOT / 'Src/Content/EasyBiomes'

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def main():
    chosen, records = {}, []
    report_path=ROOT/'resources/EasyBiomesImport.json'
    previous=json.loads(report_path.read_text()).get('assets',{}) if report_path.exists() else {}
    for project in SOURCES:
        source = project / 'Content/EasyBiomes'
        assert source.is_dir(), source
        for src in sorted(source.rglob('*')):
            if not src.is_file():
                continue
            relative = src.relative_to(source).as_posix()
            digest = sha(src)
            if relative in chosen:
                if digest != chosen[relative]['sha256']:
                    records.append({'path': relative, 'kept': chosen[relative]['source'],
                                    'alternate': project.name, 'alternate_sha256': digest})
                continue
            target = DEST / relative
            if target.exists():
                existing=sha(target)
                assert existing in [digest,previous.get(relative,{}).get('sha256')], f'Locally edited project asset differs: {target}'
                if existing!=digest:shutil.copy2(src,target)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, target)
            chosen[relative] = {'source': project.name, 'sha256': digest, 'bytes': src.stat().st_size}
    report = {'shared_framework': 'RiverGeneratorPCGBiome', 'assets': chosen, 'different_shared_assets': records}
    (ROOT / 'resources/EasyBiomesImport.json').write_text(json.dumps(report, indent=2) + '\n')
    project_file = ROOT / 'Src/HollowPines.uproject'
    descriptor = json.loads(project_file.read_text(encoding='utf-8-sig'))
    for name in ['PCG', 'PCGGeometryScriptInterop', 'GeometryScripting', 'ModelingToolsEditorMode', 'MeshTerrainMode', 'MeshPartition']:
        plugin = next((p for p in descriptor['Plugins'] if p['Name'] == name), None)
        if plugin is None:
            descriptor['Plugins'].append({'Name': name, 'Enabled': True})
        else:
            plugin['Enabled'] = True
    project_file.write_text(json.dumps(descriptor, indent=2) + '\n')
    print(f'Imported {len(chosen)} assets; recorded {len(records)} alternate shared versions.', flush=True)

if __name__ == '__main__':
    main()
