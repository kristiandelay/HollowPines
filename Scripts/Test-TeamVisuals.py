"""Four-player PIE: all views agree, preview CVars cannot homogenize the team, death retains identity."""
import json
import time
import traceback
from pathlib import Path
import unreal as u

team_out = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).parent / 'Artifacts/TeamVisuals.json'
team_test = {'phase': 'initial', 'next': 0, 'busy': False, 'results': [], 'deadline': time.monotonic()+150}
team_test['old_preview'] = u.SystemLibrary.get_console_variable_int_value('DDCvar.VisualOverride')


def team_views(count=4):
    worlds = u.EditorLevelLibrary.get_pie_worlds(False)
    assert len(worlds) == 4, f'Expected four PIE worlds, got {len(worlds)}'
    snapshots = []
    for world in worlds:
        states = [s for s in u.GameplayStatics.get_all_actors_of_class(world, u.HollowPinesPlayerState)
                  if s.get_pawn() and isinstance(s.get_pawn(), u.CRTraversalCharacter)
                  and 'TrainingPartner' not in s.get_pawn().get_class().get_name()]
        assert len(states) == count, f'{world.get_name()}: {len(states)} players'
        mapping = {}
        for state in states:
            pawn = state.get_pawn()
            visual = pawn.selected_visual_override.get_editor_property('child_actor')
            assert visual, f'{pawn.get_name()} has no visible character'
            assigned = str(state.get_editor_property('assigned_visual_override'))
            cls = visual.get_class().get_path_name()
            assert cls in assigned, f'Replicated assignment {assigned} != {cls}'
            mesh = pawn.baseline_equipment.get_presentation_mesh()
            driver = pawn.baseline_equipment.get_weapon_animation_mesh()
            assert mesh != driver and mesh.is_visible() and not driver.is_visible()
            assert mesh.get_anim_instance(), 'Missing retarget animation'
            if '/Game/HollowPines/Players/' in cls:
                assert all(mesh.get_material(i) for i in range(mesh.get_num_materials())), cls+' has an unassigned material'
            mapping[str(state.player_id)] = cls
        assert len(set(mapping.values())) == count, mapping
        snapshots.append(mapping)
    assert all(s == snapshots[0] for s in snapshots), snapshots
    return snapshots[0]


def team_finish(error=None):
    u.unregister_slate_post_tick_callback(team_test['handle'])
    u.SystemLibrary.execute_console_command(None, 'DDCvar.VisualOverride '+str(team_test['old_preview']))
    team_test.update(finished=True, error=error)
    team_out.write_text(json.dumps({'passed': error is None, 'error': error, 'results': team_test['results']}, indent=2))
    print('TEAM_VISUALS_COMPLETE', error)


def team_tick(dt):
    if team_test['busy']: return
    team_test['busy'] = True
    try:
        now = time.monotonic()
        assert now < team_test['deadline'], 'Team visuals timed out: '+str(team_test.get('pending'))
        if now < team_test['next']: return
        worlds = u.EditorLevelLibrary.get_pie_worlds(False)
        host = next((w for w in worlds if u.GameplayStatics.get_game_mode(w)), None)
        if not host: return
        try: roster = team_views()
        except AssertionError as e:
            team_test['pending'] = str(e)
            return
        phase = team_test['phase']
        if phase == 'initial':
            assert all('/Game/HollowPines/Players/' in v for v in roster.values())
            team_test['roster'] = roster
            team_test['results'].append({'case': 'four_distinct_survivors_in_all_four_worlds', 'views': 16, 'roster': roster})
            u.SystemLibrary.execute_console_command(host, 'DDCvar.VisualOverride 0')
            team_test.update(phase='preview', next=now+2)
        elif phase == 'preview':
            assert roster == team_test['roster'], 'Global preview changed team assignments'
            team_test['results'].append({'case': 'global_preview_preserves_team', 'views': 16})
            states = u.GameplayStatics.get_all_actors_of_class(host, u.HollowPinesPlayerState)
            target = next(s for s in states if s.get_pawn() and not s.get_pawn().is_locally_controlled()
                          and 'TrainingPartner' not in s.get_pawn().get_class().get_name())
            pawn = target.get_pawn()
            team_test.update(target_id=str(target.player_id), old_pawns={})
            for world in worlds:
                old_state = next(s for s in u.GameplayStatics.get_all_actors_of_class(world, u.HollowPinesPlayerState)
                                 if s.player_id == target.player_id)
                team_test['old_pawns'][world.get_path_name()] = old_state.get_pawn().get_path_name()
            asc = u.AbilitySystemLibrary.get_ability_system_component(pawn)
            damage = u.load_asset('/Game/GameplayEffects/Damage/GE_Damage_Basic_SetByCaller').generated_class()
            spec = asc.make_outgoing_spec(damage, 1, asc.make_effect_context())
            tag = u.GameplayTag(); tag.import_text('(TagName="SetByCaller.Damage")')
            spec = u.AbilitySystemLibrary.assign_tag_set_by_caller_magnitude(spec, tag, 1000)
            asc.apply_gameplay_effect_spec_to_self(spec)
            team_test.update(phase='respawn', next=now+5)
        elif phase == 'respawn':
            assert roster == team_test['roster'], 'Death reshuffled characters'
            for world in worlds:
                state = next(s for s in u.GameplayStatics.get_all_actors_of_class(world, u.HollowPinesPlayerState)
                             if str(s.player_id) == team_test['target_id'])
                if state.get_pawn().get_path_name() == team_test['old_pawns'][world.get_path_name()]: return
                if state.get_pawn().get_component_by_class(u.LyraHealthComponent).get_health() != 100: return
            team_test['results'].append({'case': 'remote_player_death_and_respawn_keeps_character', 'views': 16})
            team_finish()
    except Exception: team_finish(traceback.format_exc())
    finally: team_test['busy'] = False


team_test['handle'] = u.register_slate_post_tick_callback(team_tick)
print('Started four-player visual identity checks')
