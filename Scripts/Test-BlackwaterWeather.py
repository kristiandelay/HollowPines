"""Two-player PIE checks for the forest clock, weather blends and rain blockers."""
import unreal as u
from pathlib import Path
import json,time,traceback

assert not u.EditorLevelLibrary.get_pie_worlds(False), 'Stop PIE first'
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert levels.load_level('/Game/HollowPines/Maps/L_BlackwaterReach')
settings=u.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings')
for key,value in [('PlayNetMode','PIE_ListenServer'),('PlayNumberOfClients','2'),('RunUnderOneProcess','True'),('bLaunchSeparateServer','False')]:
    assert u.CRBlueprintTools.set_property_text(settings,key,value)
weather_test={'phase':'ready','next':0,'busy':False,'deadline':time.monotonic()+160,'results':[]}
weather_root=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).parent

def weather_finish(error=None):
    u.unregister_slate_post_tick_callback(weather_test['handle'])
    weather_test.update(finished=True,error=error)
    (weather_root/'Artifacts/BlackwaterWeatherValidation.json').write_text(json.dumps({
        'passed':error is None,'error':error,'results':weather_test['results']},indent=2)+'\n')
    print('BLACKWATER_WEATHER_TEST_COMPLETE',error)

def weather_tick(dt):
    if weather_test['busy']:return
    weather_test['busy']=True
    try:
        now=time.monotonic()
        assert now<weather_test['deadline'],'Timeout at '+weather_test['phase']
        if now<weather_test['next']:return
        worlds=u.EditorLevelLibrary.get_pie_worlds(False)
        if len(worlds)!=2:return
        skies=[next((a for a in u.GameplayStatics.get_all_actors_of_class(w,u.Actor)
            if 'HollowPinesSky' in a.get_class().get_name()),None) for w in worlds]
        if not all(skies):return
        host=next(a for w,a in zip(worlds,skies) if u.GameplayStatics.get_game_mode(w))
        phase=weather_test['phase']
        if phase=='ready':
            weather_test['start']=host.get_editor_property('CurrentTime')
            weather_test.update(phase='clock',next=now+5)
        elif phase=='clock':
            clocks=[a.get_editor_property('CurrentTime') for a in skies]
            assert clocks[0]>weather_test['start']+40,clocks
            assert abs(clocks[0]-clocks[1])<20,clocks
            weather_test['results'].append({'case':'clock_advances_and_stays_synchronized','clocks':clocks})
            # Keep automatic selection out of this short deterministic blend check.
            u.CRBlueprintTools.set_property_text(host,'bManuallyChangeWeatherScenarios','True')
            host.call_method('SetNewWeatherScenario',args=(host.get_editor_property('HeavyRain'),u.Vector2D(1,1)))
            weather_test.update(phase='rain',next=now+7)
        elif phase=='rain':
            captures=[]
            for a in skies:
                assert a.get_editor_property('RainAmountInternal')>.99
                assert a.get_editor_property('IsRaining')
                capture=a.get_component_by_class(u.SceneCaptureComponent2D)
                blockers=[x for x in capture.show_only_actors if x]
                terrain=sum(x.actor_has_tag('HP_BakedTerrain') for x in blockers)
                roofs=[x.get_actor_label() for x in blockers if 'Camp Shelter' in x.get_actor_label()]
                assert terrain>0 and len(roofs)==3,(terrain,roofs)
                assert capture.texture_target and capture.ortho_width>10000
                captures.append({'terrain_sections':terrain,'shelters':roofs})
            weather_test['results'].append({'case':'rain_replicates_and_capture_contains_camp_roofs','captures':captures})
            host.call_method('SetNewWeatherScenario',args=(host.get_editor_property('ClearSky'),u.Vector2D(1,1)))
            weather_test.update(phase='clear',next=now+7)
        elif phase=='clear':
            assert all(a.get_editor_property('RainAmountInternal')<.01 for a in skies)
            weather_test['results'].append({'case':'rain_blends_back_to_clear_on_both_clients'})
            # Direct clock jumps are presentation tests. Natural replication was
            # measured above; the vendor intentionally interpolates large jumps.
            for a in skies:
                u.CRBlueprintTools.set_property_text(a,'CurrentTime','22000')
                u.CRBlueprintTools.set_property_text(a,'TargetTime','22000')
            weather_test.update(phase='night',next=now+3)
        elif phase=='night':
            weights=[a.get_editor_property('SunWeight') for a in skies]
            assert all(x<0 for x in weights),weights
            weather_test['results'].append({'case':'night_lighting','sun_weights':weights})
            for a in skies:
                u.CRBlueprintTools.set_property_text(a,'CurrentTime','12000')
                u.CRBlueprintTools.set_property_text(a,'TargetTime','12000')
            weather_test.update(phase='day',next=now+3)
        elif phase=='day':
            weights=[a.get_editor_property('SunWeight') for a in skies]
            assert all(x>.9 for x in weights),weights
            weather_test['results'].append({'case':'day_lighting','sun_weights':weights})
            weather_finish()
    except Exception:weather_finish(traceback.format_exc())
    finally:weather_test['busy']=False

weather_test['handle']=u.register_slate_post_tick_callback(weather_tick)
u.SystemLibrary.execute_console_command(None,'t.IdleWhenNotForeground 0')
levels.editor_request_begin_play()
print('BLACKWATER_WEATHER_TEST_STARTED')
