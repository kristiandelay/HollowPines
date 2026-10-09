"""Wait for PCG, rebuild navigation, and save generated World Partition actors."""
import unreal as u
import time,json,traceback
from pathlib import Path

assert not u.EditorLevelLibrary.get_pie_worlds(False),'Stop PIE first'
blackwater_finalize={'phase':'pcg','next':0,'busy':False,'deadline':time.monotonic()+240}

def blackwater_finalize_tick(dt):
    if blackwater_finalize['busy']:return
    blackwater_finalize['busy']=True
    try:
        now=time.monotonic()
        assert now<blackwater_finalize['deadline'],'PCG/navigation finalization timed out'
        if now<blackwater_finalize['next']:return
        actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
        world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
        assert world.get_path_name().startswith('/Game/HollowPines/Maps/L_BlackwaterReach.')
        if blackwater_finalize['phase']=='pcg':
            components=[]
            for actor in actors:
                if 'River Generator' in actor.get_actor_label():components.append(actor.get_editor_property('PCG_Biome'))
                elif actor.get_actor_label().startswith('PCG Redwood Forest'):components.append(actor.pcg_component)
            assert len(components)==3,len(components)
            if not all(c.generated for c in components):return
            print(u.HPWorldTools.build_navigation(world))
            blackwater_finalize.update(phase='nav',next=now+3)
        elif not u.NavigationSystemV1.is_navigation_being_built(world):
            assert u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
            counts={}
            for actor in actors:
                for component in actor.get_components_by_class(u.InstancedStaticMeshComponent):
                    if component.static_mesh and not component.static_mesh.get_name().startswith('SM_Flag'):
                        name=component.static_mesh.get_name()
                        counts[name]=counts.get(name,0)+component.get_instance_count()
            root=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).parent
            (root/'resources/BlackwaterBuild.json').write_text(json.dumps({'map':'/Game/HollowPines/Maps/L_BlackwaterReach',
                'instances':sum(counts.values()),'instances_by_mesh':counts,'navigation_built':True},indent=2)+'\n')
            u.unregister_slate_post_tick_callback(blackwater_finalize['handle'])
            blackwater_finalize['finished']=True
            print('BLACKWATER_FINALIZED',sum(counts.values()))
    except Exception:
        blackwater_finalize['error']=traceback.format_exc()
        u.unregister_slate_post_tick_callback(blackwater_finalize['handle'])
        print('BLACKWATER_FINALIZE_FAILED',blackwater_finalize['error'])
    finally:blackwater_finalize['busy']=False

blackwater_finalize['handle']=u.register_slate_post_tick_callback(blackwater_finalize_tick)
print('BLACKWATER_FINALIZATION_STARTED')
