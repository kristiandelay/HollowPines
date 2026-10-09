"""Real mapped traversal input, all network views, and gravity after leaving the ledge."""
import json
import time
import traceback
from pathlib import Path
import unreal as u

climb_out = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).parent / 'Artifacts/ClimbGravity.json'
climb_test = {'phase': 'place', 'index': 0, 'next': 0, 'busy': False, 'results': [], 'deadline': time.monotonic()+300}
climb_test['locked_controllers'] = []
climb_cases = [
    ('climb', [2700,-1770,94], 90, False),
    ('interrupted_climb', [2700,-1770,94], 90, True),
    ('mantle', [4300,-970,94], 90, False),
    ('hurdle', [2730,-800,94], 0, False),
    ('vault', [4810,-800,444], 0, False),
]


def climb_pawns():
    pawns = [p for w in u.EditorLevelLibrary.get_pie_worlds(False)
             for p in u.GameplayStatics.get_all_actors_of_class(w, u.CRTraversalCharacter)
             if isinstance(p.player_state, u.HollowPinesPlayerState) and 'TrainingPartner' not in p.get_class().get_name()]
    local = sorted([p for p in pawns if p.is_locally_controlled()], key=lambda p: (not p.has_authority(), p.player_state.player_id))
    # Test a listen host and one remote client; standalone has only the host.
    subject = local[min(climb_test['index']//len(climb_cases), len(local)-1)]
    views = [p for p in pawns if p.player_state.player_id == subject.player_state.player_id]
    return subject, views


def climb_logic(p):
    return next(c for c in p.get_components_by_class(u.ActorComponent) if c.get_name() == 'AC_TraversalLogic')


def climb_input(p, pressed):
    sub = next(s for s in u.ObjectIterator(u.EnhancedInputLocalPlayerSubsystem)
               if isinstance(s.get_outer(),u.LocalPlayer) and u.GameplayStatics.get_player_controller(s,0) == p.get_controller())
    sub.inject_input_vector_for_action(u.load_asset('/Game/Input/IA_Jump'), u.Vector(1 if pressed else 0,0,0), [], [])


def climb_finish(error=None):
    u.unregister_slate_post_tick_callback(climb_test['handle'])
    for controller in climb_test.pop('locked_controllers', []):
        controller.set_ignore_move_input(False)
        controller.set_ignore_look_input(False)
    climb_test.update(finished=True, error=error)
    climb_out.write_text(json.dumps({'passed':error is None, 'error':error, 'results':climb_test['results']}, indent=2))
    print('CLIMB_GRAVITY_COMPLETE', error)


def climb_tick(dt):
    if climb_test['busy']: return
    climb_test['busy'] = True
    try:
        assert time.monotonic() < climb_test['deadline'], 'Climb test timed out'
        pawn, views = climb_pawns()
        now = u.GameplayStatics.get_time_seconds(pawn)
        if now < climb_test['next']: return
        if not all(p.physical_interaction.controls_created for p in views): return
        name, start, yaw, interrupt = climb_cases[climb_test['index'] % len(climb_cases)]
        phase = climb_test['phase']
        if phase == 'place':
            controller = pawn.get_controller()
            if controller not in climb_test['locked_controllers']:
                controller.set_ignore_move_input(True)
                controller.set_ignore_look_input(True)
                climb_test['locked_controllers'].append(controller)
            climb_input(pawn, False)
            for p in views:
                if p.has_authority() or p == pawn:
                    p.character_movement.stop_movement_immediately()
                    p.set_actor_location(u.Vector(*start), False, True)
                    p.set_actor_rotation(u.Rotator(yaw=yaw), True)
                    p.force_net_update()
            pawn.get_controller().set_control_rotation(u.Rotator(yaw=yaw))
            climb_test.update(phase='start', next=now+1, placed=now)
        elif phase == 'start':
            if pawn.character_movement.movement_mode != u.MovementMode.MOVE_WALKING:
                assert now-climb_test['placed'] < 4, 'No starting floor: '+name+' '+str(pawn.get_actor_location())
                return
            climb_input(pawn, True)
            climb_test.update(phase='active', started=now, saw_montage=False, interrupted=False, montage=None)
        elif phase == 'active':
            elapsed = now-climb_test['started']
            climb_input(pawn, elapsed < .12)
            montage = pawn.mesh.get_anim_instance().get_current_active_montage()
            if montage:
                climb_test.update(saw_montage=True, montage=montage.get_path_name())
                if interrupt and elapsed > .35 and not climb_test['interrupted']:
                    # Interrupt both prediction and authority, as a replicated action would.
                    for p in views: p.mesh.get_anim_instance().montage_stop(.1)
                    climb_test['interrupted'] = True
            assert elapsed < 14, name+' did not restore movement: '+str([(p.get_local_role(), str(p.character_movement.movement_mode), climb_logic(p).get_editor_property('DoingTraversalAction')) for p in views])
            if elapsed > 1 and climb_test['saw_montage'] and all(
                not climb_logic(p).get_editor_property('DoingTraversalAction')
                and p.character_movement.movement_mode in [u.MovementMode.MOVE_WALKING, u.MovementMode.MOVE_FALLING]
                for p in views):
                location = pawn.get_actor_location()
                climb_test['ledge_exit'] = [location.x, location.y, location.z]
                if not interrupt:
                    axis, edge = {'climb':('y',-1680), 'mantle':('y',-880), 'hurdle':('x',2820), 'vault':('x',4900)}[name]
                    assert getattr(location,axis) > edge, name+' failed to cross the ledge: '+str(location)
                climb_test.update(phase='drop', next=now+.5)
        elif phase == 'drop':
            for p in views:
                movement = p.character_movement
                desc = u.CRBlueprintTools.describe_object(movement)
                assert 'bIgnoreClientMovementErrorChecksAndCorrection = False' in desc
                assert 'bServerAcceptClientAuthoritativePosition = False' in desc
                if p.has_authority() or p == pawn:
                    # A short fall isolates CMC gravity without triggering the
                    # separate high-speed impact ragdoll mechanic.
                    movement.stop_movement_immediately()
                    p.set_actor_location(u.Vector(-1400,-3200,300), False, True)
                    p.force_net_update()
            climb_test.update(phase='fallen', next=now+1.5)
        elif phase == 'fallen':
            assert all(p.get_actor_location().z < 200 for p in views), 'Gravity stayed disabled after '+name
            assert all(p.character_movement.movement_mode == u.MovementMode.MOVE_WALKING for p in views), 'Did not land after '+name
            assert all(not p.physical_interaction.is_busy() for p in views), 'Drop accidentally tested ragdoll instead of CMC gravity'
            climb_test['results'].append({'case':name, 'owner':'host' if pawn.has_authority() else 'client',
                'views':len(views), 'montage':climb_test['montage'], 'ledge_exit':climb_test['ledge_exit'],
                'z_after_drop':[p.get_actor_location().z for p in views]})
            climb_test['index'] += 1
            count = 10 if len(u.EditorLevelLibrary.get_pie_worlds(False)) > 1 else 5
            if climb_test['index'] == count:
                # Reproduce the original failed-playback defect directly, with no montage.
                authority = next(p for p in views if p.has_authority())
                logic = climb_logic(authority)
                text = u.CRBlueprintTools.describe_object(logic)
                import re
                value = next(line.split(' = ',1)[1] for line in text.splitlines() if line.startswith('TraversalResult = '))
                value = re.sub(r'ChosenMontage_[^=]+=\"?[^,]*', lambda m:m.group(0).split('=')[0]+'=None', value)
                assert u.CRBlueprintTools.set_property_text(logic,'TraversalResult',value)
                logic.call_method('PerformTraversalAction_CMC')
                assert not logic.get_editor_property('DoingTraversalAction')
                assert authority.character_movement.movement_mode != u.MovementMode.MOVE_FLYING
                climb_test['results'].append({'case':'failed_montage_restores_gravity_immediately'})
                climb_finish()
            else: climb_test.update(phase='place', next=now+.3)
    except Exception: climb_finish(traceback.format_exc())
    finally: climb_test['busy'] = False


climb_test['handle'] = u.register_slate_post_tick_callback(climb_tick)
print('Started climb exit and gravity checks')
