"""Check player grounding, airborne gravity and passive forest encounters."""
import unreal as u
from pathlib import Path
import sys,time,json,traceback

assert not u.EditorLevelLibrary.get_pie_worlds(False),'Stop PIE first'
forest_root=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).parent
sys.path.insert(0,str(forest_root/'Scripts'))
import hollow_pines_layout as forest_layout
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert levels.load_level('/Game/HollowPines/Maps/L_BlackwaterReach')
settings=u.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings')
for key,value in [('PlayNetMode','PIE_ListenServer'),('PlayNumberOfClients','2'),('RunUnderOneProcess','True'),('bLaunchSeparateServer','False')]:
    assert u.CRBlueprintTools.set_property_text(settings,key,value)
forest_test={'phase':'ready','next':0,'busy':False,'deadline':time.monotonic()+240,'results':[]}

def forest_finish(error=None):
    u.unregister_slate_post_tick_callback(forest_test['handle'])
    forest_test.update(finished=True,error=error)
    (forest_root/'Artifacts/BlackwaterTraversalValidation.json').write_text(json.dumps({'passed':error is None,
        'error':error,'results':forest_test['results']},indent=2)+'\n')
    print('BLACKWATER_TRAVERSAL_TEST_COMPLETE',error)

def forest_tick(dt):
    if forest_test['busy']:return
    forest_test['busy']=True
    try:
        now=time.monotonic()
        assert now<forest_test['deadline'],'Timeout at '+forest_test['phase']
        if now<forest_test['next']:return
        worlds=u.EditorLevelLibrary.get_pie_worlds(False)
        if len(worlds)!=2:return
        host=next(w for w in worlds if u.GameplayStatics.get_game_mode(w))
        players=[s.get_pawn() for s in u.GameplayStatics.get_all_actors_of_class(host,u.HollowPinesPlayerState)]
        if len(players)!=2 or not all(players):return
        phase=forest_test['phase']
        if phase=='ready':
            # A dense map can finish loading on the host before the client's
            # replicated pawns arrive. Begin movement checks after both views
            # are ready, rather than timing readiness from the host alone.
            for w in worlds:
                pawns=[s.get_pawn() for s in u.GameplayStatics.get_all_actors_of_class(w,u.HollowPinesPlayerState)]
                if len(pawns)!=2 or not all(pawns):return
            forest_test.update(phase='camp',next=now+4)
        elif phase in ['camp','cave','bridge']:
            views=[]
            for w in worlds:
                pawns=[s.get_pawn() for s in u.GameplayStatics.get_all_actors_of_class(w,u.HollowPinesPlayerState)]
                assert len(pawns)==2 and all(pawns),(phase,w.get_path_name(),'Player pawns not ready',pawns)
                for pawn in pawns:
                    movement=pawn.character_movement
                    assert movement.movement_mode==u.MovementMode.MOVE_WALKING,(phase,pawn.get_name(),str(movement.movement_mode))
                    assert movement.gravity_scale>0
                    assert pawn.get_component_by_class(u.LyraHealthComponent).get_health()==100
                    if phase=='cave':assert 4700<pawn.get_actor_location().z<5200,pawn.get_actor_location()
                    views.append({'player':pawn.get_name(),'z_cm':pawn.get_actor_location().z})
            forest_test['results'].append({'case':phase+'_grounding','views':views})
            if phase=='camp':
                forest_test['homes']=[p.get_actor_location() for p in players]
                for i,p in enumerate(players):
                    p.character_movement.stop_movement_immediately()
                    p.set_actor_location(u.Vector(33000,1800+i*180,(forest_layout.MINE_Z-40)*100+250),False,True)
                    p.character_movement.set_movement_mode(u.MovementMode.MOVE_FALLING)
                forest_test.update(phase='cave',next=now+3)
            elif phase=='cave':
                # A server-side Jump input is not authoritative for a remote
                # player's input stream. Launch tests gravity on both pawns.
                for p in players:p.launch_character(u.Vector(0,0,450),False,True)
                forest_test.update(phase='airborne',next=now+.2)
            else:
                monsters=u.GameplayStatics.get_all_actors_of_class(host,u.HollowPinesMonster)
                assert len(monsters)==4 and all(not a.rehearse_attacks for a in monsters)
                forest_test['results'].append({'case':'all_encounters_remain_passive','count':len(monsters)})
                for p,home in zip(players,forest_test['homes']):p.set_actor_location(home,False,True)
                forest_finish()
        elif phase=='airborne':
            assert all(p.character_movement.is_falling() for p in players),[(p.get_name(),str(p.character_movement.movement_mode)) for p in players]
            forest_test.update(phase='land',next=now+2)
        elif phase=='land':
            assert all(p.character_movement.movement_mode==u.MovementMode.MOVE_WALKING for p in players)
            forest_test['results'].append({'case':'cave_airborne_returns_to_walking'})
            for i,p in enumerate(players):
                p.character_movement.stop_movement_immediately()
                p.set_actor_location(u.Vector(forest_layout.river_x(-230)*100,-23000+i*160,forest_layout.POI_HEIGHTS['River Crossing']*100+220),False,True)
                p.character_movement.set_movement_mode(u.MovementMode.MOVE_FALLING)
            forest_test.update(phase='bridge',next=now+3)
    except Exception:forest_finish(traceback.format_exc())
    finally:forest_test['busy']=False

forest_test['handle']=u.register_slate_post_tick_callback(forest_tick)
u.SystemLibrary.execute_console_command(None,'t.IdleWhenNotForeground 0')
levels.editor_request_begin_play()
print('BLACKWATER_TRAVERSAL_TEST_STARTED')
