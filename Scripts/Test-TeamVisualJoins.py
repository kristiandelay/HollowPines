"""Run after Test-TeamVisuals.py in the same four-player listen session."""
join_test = {'phase':'join_fifth', 'next':0, 'busy':False, 'count':4, 'results':[], 'deadline':time.monotonic()+100}


def join_finish(error=None):
    u.unregister_slate_post_tick_callback(join_test['handle'])
    for key in ['fifth','sixth','replacement']:
        controller = join_test.pop(key,None)
        if controller:
            try: u.GameplayStatics.remove_player(controller,True)
            except Exception: pass
    join_test.update(finished=True,error=error)
    team_out.with_name('TeamVisualJoins.json').write_text(json.dumps({'passed':error is None,'error':error,'results':join_test['results']},indent=2))
    print('TEAM_VISUAL_JOINS_COMPLETE',error)


def join_tick(dt):
    if join_test['busy']: return
    join_test['busy']=True
    try:
        now=time.monotonic()
        assert now<join_test['deadline'], str(join_test.get('pending','Join timeout'))
        if now<join_test['next']:return
        host=next(w for w in u.EditorLevelLibrary.get_pie_worlds(False) if u.GameplayStatics.get_game_mode(w))
        try: roster=team_views(join_test['count'])
        except AssertionError as e:
            join_test['pending']=str(e)
            return
        phase=join_test['phase']
        if phase=='join_fifth':
            join_test['original']=roster
            join_test['fifth']=u.GameplayStatics.create_player(host,-1,True)
            assert join_test['fifth']
            join_test.update(phase='fifth',count=5,next=now+2)
        elif phase=='fifth':
            assert all(roster[k]==v for k,v in join_test['original'].items())
            join_test['fifth_id']=str(join_test['fifth'].player_state.player_id)
            join_test['fifth_visual']=roster[join_test['fifth_id']]
            assert 'WastelandVanguard' in join_test['fifth_visual']
            join_test['results'].append({'case':'late_fifth_player_gets_unused_survivor','views':20})
            join_test['sixth']=u.GameplayStatics.create_player(host,-1,True)
            assert join_test['sixth']
            join_test.update(phase='sixth',count=6,next=now+2)
        elif phase=='sixth':
            sixth=roster[str(join_test['sixth'].player_state.player_id)]
            assert '/Game/HollowPines/Players/' not in sixth
            join_test['results'].append({'case':'sixth_player_gets_distinct_sample_character','views':24,'visual':sixth})
            u.GameplayStatics.remove_player(join_test.pop('fifth'),True)
            join_test.update(phase='disconnected',count=5,next=now+2)
        elif phase=='disconnected':
            assert join_test['fifth_id'] not in roster
            join_test['replacement']=u.GameplayStatics.create_player(host,-1,True)
            assert join_test['replacement']
            join_test.update(phase='reused',count=6,next=now+2)
        elif phase=='reused':
            assert roster[str(join_test['replacement'].player_state.player_id)]==join_test['fifth_visual']
            assert all(roster[k]==v for k,v in join_test['original'].items())
            join_test['results'].append({'case':'disconnect_releases_character_without_reshuffling_team','views':24})
            join_finish()
    except Exception:join_finish(traceback.format_exc())
    finally:join_test['busy']=False


join_test['handle']=u.register_slate_post_tick_callback(join_tick)
print('Started join and disconnect character checks')
