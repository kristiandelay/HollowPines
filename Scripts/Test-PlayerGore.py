"""Exercise real Lyra damage, replicated wounds, protected torso and limb debris."""
import unreal as u
from pathlib import Path
import time,json,traceback
assert not u.EditorLevelLibrary.get_pie_worlds(False), 'Stop PIE before running this test'
assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level('/Game/HollowPines/Maps/L_MonsterAnimationGym')
settings=u.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings')
for key,value in [('PlayNetMode','PIE_ListenServer'),('PlayNumberOfClients','2'),('RunUnderOneProcess','True'),('bLaunchSeparateServer','False')]:
    assert u.CRBlueprintTools.set_property_text(settings,key,value),key

gore_test={'phase':'ready','next':0,'busy':False,'deadline':time.monotonic()+180,'results':[]}
gore_root=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).parent
gore_test_profile=u.load_asset('/Game/HollowPines/Gore/DA_PlayerGore')
gore_test['original_drop_chance']=gore_test_profile.get_editor_property('organ_drop_chance')
def gore_tag(name):
    tag=u.GameplayTag();tag.import_text('(TagName="'+name+'")');return tag
def gore_hit(pawn,bone):
    mesh=pawn.baseline_equipment.get_presentation_mesh()
    point=mesh.get_socket_location(bone)+pawn.get_actor_forward_vector()*8
    return u.HitResult(blocking_hit=True,hit_actor=pawn,hit_component=mesh,hit_bone_name=bone,
        impact_point=point,location=point,normal=pawn.get_actor_forward_vector(),impact_normal=pawn.get_actor_forward_vector())
def gore_damage(pawn,amount,bone=None,slash=False):
    asc=u.AbilitySystemLibrary.get_ability_system_component(pawn)
    context=asc.make_effect_context()
    if bone:u.AbilitySystemLibrary.effect_context_add_hit_result(context,gore_hit(pawn,bone),True)
    spec=asc.make_outgoing_spec(u.load_asset('/Game/GameplayEffects/Damage/GE_Damage_Basic_SetByCaller').generated_class(),1,context)
    spec=u.AbilitySystemLibrary.assign_tag_set_by_caller_magnitude(spec,gore_tag('SetByCaller.Damage'),amount)
    if slash:spec=u.AbilitySystemLibrary.add_asset_tag(spec,gore_tag('HollowPines.Damage.Slash'))
    asc.apply_gameplay_effect_spec_to_self(spec)
def gore_players(world):
    return [s.get_pawn() for s in u.GameplayStatics.get_all_actors_of_class(world,u.HollowPinesPlayerState) if s.get_pawn()]
def gore_finish(error=None):
    u.unregister_slate_post_tick_callback(gore_test['handle'])
    u.CRBlueprintTools.set_property_text(gore_test_profile,'OrganDropChance',str(gore_test['original_drop_chance']))
    gore_test.update(finished=True,error=error)
    (gore_root/'Artifacts/PlayerGoreValidation.json').write_text(json.dumps({'passed':error is None,'error':error,'results':gore_test['results']},indent=2)+'\n')
    print('PLAYER_GORE_TEST_COMPLETE',error)
def gore_tick(dt):
    if gore_test['busy']:return
    gore_test['busy']=True
    try:
        now=time.monotonic()
        assert now<gore_test['deadline'],'Timeout at '+gore_test['phase']
        if now<gore_test['next']:return
        worlds=u.EditorLevelLibrary.get_pie_worlds(False)
        host=next((w for w in worlds if u.GameplayStatics.get_game_mode(w)),None)
        if len(worlds)!=2 or not host:return
        players=gore_players(host)
        if len(players)!=2:return
        phase=gore_test['phase']
        if phase=='ready':
            if any(not p.baseline_equipment.get_presentation_mesh() for p in players):return
            for a in u.GameplayStatics.get_all_actors_of_class(host,u.HollowPinesMonster):a.set_paused(True)
            gore_test.update(phase='damage',next=now+2)
        elif phase=='damage':
            for p in players:gore_damage(p,12,'spine_03')
            gore_test.update(phase='hit',next=now+2)
        elif phase=='hit':
            views=[]
            for w in worlds:
                for p in gore_players(w):
                    g=p.player_gore;mesh=p.baseline_equipment.get_presentation_mesh()
                    assert len(g.wounds)==1 and g.rendered_wound_count==1,(p.get_name(),len(g.wounds),g.rendered_wound_count)
                    assert p.get_component_by_class(u.LyraHealthComponent).get_health()==88
                    material=mesh.get_material(0)
                    assert isinstance(material,u.MaterialInstanceDynamic),str(material)
                    rt=material.get_texture_parameter_value('MaskMapTexture')
                    assert isinstance(rt,u.TextureRenderTarget2D),str(rt)
                    pixels=u.RenderingLibrary.read_render_target_raw(w,rt,False)
                    painted=sum(1 for pixel in pixels if pixel.r>.01)
                    assert 0<painted<len(pixels)*.1,('Wound mask is empty or covers the whole character',p.get_name(),painted)
                    views.append({'player':p.get_name(),'world':w.get_name(),'painted_pixels':painted,'target':rt.get_path_name()})
            assert len({v['target'] for v in views})==4,'Players share wound render targets'
            gore_test['results'].append({'case':'real_gas_damage_paints_independent_replicated_wounds','views':views})
            for p in players:gore_damage(p,4)
            gore_test.update(phase='environment',next=now+.8)
        elif phase=='environment':
            assert all(len(p.player_gore.wounds)==1 for p in players)
            gore_test['results'].append({'case':'nonimpact_damage_does_not_invent_wounds'})
            for p in players:gore_damage(p,15,'spine_02',True)
            gore_test.update(phase='slice',next=now+1)
        elif phase=='slice':
            for w in worlds:
                for p in gore_players(w):
                    assert len(p.player_gore.wounds)==2 and p.player_gore.wounds[-1].slice
                    assert p.player_gore.severed_limb_count==0
            gore_test['results'].append({'case':'nonfatal_slash_paints_slice_without_severing'})
            # Presentation-only fatal wound previews exercise the same server
            # routing without invoking player destruction during mesh inspection.
            # Force eligibility for this branch so probability cannot make the
            # test flaky. Mesh choice and drop counts still use wound seeds.
            u.CRBlueprintTools.set_property_text(gore_test_profile,'OrganDropChance','1.0')
            for p in players:
                for i in range(8):p.player_gore.apply_wound(gore_hit(p,'spine_03'),60,True,True)
            gore_test.update(phase='torso',next=now+2)
        elif phase=='torso':
            drops=[]
            for w in worlds:
                for p in gore_players(w):
                    g=p.player_gore
                    assert all(str(x.sever_bone)=='None' for x in g.wounds)
                    assert g.severed_limb_count==0
                    assert g.dropped_organ_count>0,('No random organs',p.get_name())
                    drops.append(g.dropped_organ_count)
            gore_test['results'].append({'case':'torso_remains_intact_and_random_organs_drop','counts':drops,'drop_chance_forced_for_test':True})
            u.CRBlueprintTools.set_property_text(gore_test_profile,'OrganDropChance',str(gore_test['original_drop_chance']))
            for p in players:p.player_gore.apply_wound(gore_hit(p,'lowerarm_l'),60,True,True)
            gore_test.update(phase='limb',next=now+2)
        elif phase=='limb':
            for w in worlds:
                for p in gore_players(w):
                    assert p.player_gore.severed_limb_count==1,(p.get_name(),p.player_gore.severed_limb_count)
                    assert p.baseline_equipment.get_presentation_mesh().is_bone_hidden_by_name('lowerarm_l')
                    assert not p.baseline_equipment.get_presentation_mesh().is_bone_hidden_by_name('spine_03')
            gore_test['results'].append({'case':'replicated_limb_cut_keeps_torso_visible','views':4})
            gore_test['old']={p.player_state.player_id:p.get_name() for p in players}
            for p in players:gore_damage(p,200)
            gore_test.update(phase='respawn',next=now+7)
        elif phase=='respawn':
            for w in worlds:
                for p in gore_players(w):
                    assert p.get_name()!=gore_test['old'][p.player_state.player_id]
                    assert len(p.player_gore.wounds)==0
                    assert p.get_component_by_class(u.LyraHealthComponent).get_health()==100
                    assert not p.baseline_equipment.get_presentation_mesh().is_bone_hidden_by_name('lowerarm_l')
            gore_test['results'].append({'case':'respawn_restores_clean_complete_character','views':4,'round':gore_test.get('death_round',1)})
            round_number=gore_test.get('death_round',1)
            if round_number<3:
                gore_test['death_round']=round_number+1
                gore_test['old']={p.player_state.player_id:p.get_name() for p in players}
                for p in players:gore_damage(p,200,'lowerarm_l',True)
                gore_test.update(next=now+7)
            else:gore_finish()
    except Exception:gore_finish(traceback.format_exc())
    finally:gore_test['busy']=False
gore_test['handle']=u.register_slate_post_tick_callback(gore_tick)
u.SystemLibrary.execute_console_command(None,'t.IdleWhenNotForeground 0')
u.get_editor_subsystem(u.LevelEditorSubsystem).editor_request_begin_play()
print('PLAYER_GORE_TEST_STARTED')
