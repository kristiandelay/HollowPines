"""Finalize a Broadleaf forest rebuild after PCG and navigation finish."""
import unreal as u
from pathlib import Path
root=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).parent
namespace={'HP_BROADLEAF_STAGE':'definitions'}
script=root/'Scripts/Integrate-BlackwaterBroadleaf.py'
exec(compile(script.read_text(),str(script),'exec'),namespace)
actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
forest=next(a for a in actors if a.get_actor_label().startswith('Broadleaf Forest -'))
roads=[a for a in actors if a.get_actor_label().startswith('Broadleaf Path -')]
assert len(roads)==12,len(roads)
blackwater_finalize=namespace['finalize'](forest,roads)
print('BLACKWATER_FINALIZATION_STARTED')
