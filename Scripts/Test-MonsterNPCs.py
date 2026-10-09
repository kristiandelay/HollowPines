"""Two-world PIE checks for custom animation, jumps, passive AI and fair dummy turns."""
import unreal as u
import time,json,traceback,math
from pathlib import Path

assert not u.EditorLevelLibrary.get_pie_worlds(False), 'Stop PIE first'
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert levels.load_level('/Game/HollowPines/Maps/L_MonsterAnimationGym')
settings=u.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings')
for key,value in [('PlayNetMode','PIE_ListenServer'),('PlayNumberOfClients','2'),('RunUnderOneProcess','True'),('bLaunchSeparateServer','False')]:
    assert u.CRBlueprintTools.set_property_text(settings,key,value)

monster_test={'phase':'ready','next':0,'busy':False,'deadline':time.monotonic()+180,'results':[]}
monster_report=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).parent/'Artifacts/MonsterNPCValidation.json'

def monster_finish(error=None):
    u.unregister_slate_post_tick_callback(monster_test['handle'])
    monster_test.update(finished=True,error=error)
    monster_report.write_text(json.dumps({'passed':error is None,'error':error,'results':monster_test['results']},indent=2))
    print('MONSTER_TEST_COMPLETE',error)

def monster_tick(dt):
    if monster_test['busy']:return
    monster_test['busy']=True
    try:
        now=time.monotonic()
        assert now<monster_test['deadline'],'Timeout at '+monster_test['phase']
        if now<monster_test['next']:return
        worlds=u.EditorLevelLibrary.get_pie_worlds(False)
        if len(worlds)!=2:return
        host=next((w for w in worlds if u.GameplayStatics.get_game_mode(w)),None)
        if not host:return
        actors=u.GameplayStatics.get_all_actors_of_class(host,u.HollowPinesMonster)
        phase=monster_test['phase']
        if phase=='ready':
            if len(actors)!=4 or not u.GameplayStatics.get_player_pawn(host,0):return
            if len(u.GameplayStatics.get_all_actors_of_class(host,u.CRTraversalCharacter))!=2:return
            assert all(not a.rehearse_attacks for a in actors)
            for i,a in enumerate(actors):
                a.set_paused(False)
                a.set_actor_location(u.Vector(-2700+i*1800,400,a.profile.capsule_half_height+5),False,True)
            monster_test['starts']={a.get_name():a.get_actor_location() for a in actors}
            monster_test['health']={p.get_name():p.get_component_by_class(u.LyraHealthComponent).get_health() for p in u.GameplayStatics.get_all_actors_of_class(host,u.CRTraversalCharacter)}
            monster_test.update(phase='passive',next=now+6)
        elif phase=='passive':
            moved=[]
            for a in actors:
                assert a.action_state.action==u.HPMonsterAction.NONE
                assert a.health.get_health()==100
                assert a.mesh.get_anim_instance()
                moved.append((a.get_actor_location()-monster_test['starts'][a.get_name()]).length())
                a.set_paused(True)
            assert max(moved)>20,moved
            for i,a in enumerate(actors):
                for b in actors[i+1:]:assert (a.get_actor_location()-b.get_actor_location()).length()>a.profile.capsule_radius+b.profile.capsule_radius
            monster_test['results'].append({'case':'passive_ai_moves_with_spacing','movement_cm':moved})
            monster_test['actions']=[u.HPMonsterAction.ATTACK1,u.HPMonsterAction.ATTACK2,u.HPMonsterAction.ATTACK3,u.HPMonsterAction.HIT_FRONT,u.HPMonsterAction.HIT_LEFT,u.HPMonsterAction.HIT_RIGHT]
            monster_test.update(phase='action_start',index=0)
        elif phase=='action_start':
            action=monster_test['actions'][monster_test['index']]
            for a in actors:a.preview_action(action)
            monster_test.update(phase='action_check',next=now+.3)
        elif phase=='action_check':
            action=monster_test['actions'][monster_test['index']]
            for w in worlds:
                peers=u.GameplayStatics.get_all_actors_of_class(w,u.HollowPinesMonster)
                assert len(peers)==4
                for a in peers:
                    assert a.action_state.action==action,(w.get_name(),a.get_name(),a.action_state.action,action)
                    anim=a.mesh.get_anim_instance()
                    assert anim.action_weight>.8
                    assert anim.action_sequence==a.get_action_sequence()
                    assert anim.action_time>0
            monster_test['results'].append({'case':'replicated_'+str(action),'views':8})
            monster_test['index']+=1
            monster_test.update(phase='action_start' if monster_test['index']<6 else 'jump_start',next=now+2.2)
        elif phase=='jump_start':
            monster_test['ground']={a.get_name():a.get_actor_location().z for a in actors}
            for a in actors:a.preview_action(u.HPMonsterAction.JUMP_START)
            monster_test.update(phase='jump_air',next=now+.65)
        elif phase=='jump_air':
            for a in actors:
                assert a.character_movement.is_falling(),a.get_name()
                assert a.get_actor_location().z>monster_test['ground'][a.get_name()]+15
            monster_test.update(phase='jump_land',next=now+2)
        elif phase=='jump_land':
            for w in worlds:
                for a in u.GameplayStatics.get_all_actors_of_class(w,u.HollowPinesMonster):
                    assert a.character_movement.movement_mode==u.MovementMode.MOVE_WALKING
                    assert a.action_state.action==u.HPMonsterAction.NONE
                    if a.profile.hover:assert a.mesh.get_socket_location('root').z > a.get_actor_location().z-a.profile.capsule_half_height+30
            monster_test['results'].append({'case':'jump_land_and_hag_hover','views':8})
            dummy=actors[0].practice_target
            center=dummy.get_actor_location()
            for i,a in enumerate(actors):
                angle=math.tau*i/4
                a.set_actor_location(u.Vector(center.x+1100*math.cos(angle),center.y+1100*math.sin(angle),a.profile.capsule_half_height+4),False,True)
                a.rehearse_attacks=True;a.set_paused(False)
            monster_test.update(phase='turns',turns={},last=None,turn_deadline=now+65,next=now+.1)
        elif phase=='turns':
            attacks=[a for a in actors if a.action_state.action in [u.HPMonsterAction.ATTACK1,u.HPMonsterAction.ATTACK2,u.HPMonsterAction.ATTACK3]]
            assert len(attacks)<=1,'Two simultaneous melee turns'
            for a in attacks:
                assert a.get_observed_target()==a.practice_target
                name=a.get_name()
                if monster_test['last']!=name:
                    monster_test['turns'][name]=monster_test['turns'].get(name,0)+1
                    monster_test['last']=name
            if len(monster_test['turns'])==4:
                monster_test['results'].append({'case':'fair_single_attacker_dummy_rehearsal','turns':monster_test['turns']})
                for a in actors:a.rehearse_attacks=False;a.set_paused(True);a.preview_action(u.HPMonsterAction.DEATH)
                monster_test.update(phase='death',next=now+3)
            else:
                assert now<monster_test['turn_deadline'],'Not all monsters received a turn: '+str(monster_test['turns'])
                monster_test['next']=now+.1
        elif phase=='death':
            for w in worlds:
                for a in u.GameplayStatics.get_all_actors_of_class(w,u.HollowPinesMonster):
                    assert a.dead and a.action_state.action==u.HPMonsterAction.DEATH
                    assert abs(a.mesh.get_anim_instance().action_time-a.get_action_sequence().get_play_length())<.05
            for p in u.GameplayStatics.get_all_actors_of_class(host,u.CRTraversalCharacter):
                assert p.get_component_by_class(u.LyraHealthComponent).get_health()==monster_test['health'][p.get_name()]
            monster_test['results'].append({'case':'death_holds_final_pose_and_no_player_damage','views':8})
            monster_finish()
    except Exception:monster_finish(traceback.format_exc())
    finally:monster_test['busy']=False

monster_test['handle']=u.register_slate_post_tick_callback(monster_tick)
print('MONSTER_TEST_STARTED')
