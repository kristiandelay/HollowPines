"""Install a project-owned EasySky preset in the exploration map."""
import unreal as u
from pathlib import Path
import json
ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).parent
lib=u.EditorAssetLibrary
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert not u.EditorLevelLibrary.get_pie_worlds(False)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_path_name().startswith('/Game/HollowPines/Maps/L_BlackwaterReach.')
path='/Game/HollowPines/Environment/Weather/BP_HollowPinesSky'
bp=u.load_asset(path) if lib.does_asset_exist(path) else lib.duplicate_asset('/EasySkyV2/Blueprints/BP_EasySkyV2',path)
defaults=u.get_default_object(bp.generated_class())
settings={'StartTime':'16.5','CycleSpeedDay':'NewEnumerator14','CycleSpeedNight':'NewEnumerator14',
    'CustomCycleSpeedDay':'48','CustomCycleSpeedNight':'48','RandomizeStartTimeAtLoad':'False',
    'SelectedWeatherScenario':'NewEnumerator2','bUseDynamicWeather':'True',
    'MinMaxWeatherScenarioChangeDelay':'(X=40,Y=93.333333)','NetworkSyncInterval':'1',
    'UpdateRainCollisionDynamically':'True','bShowDateAndTemperatureWidget':'False',
    'NorthernLatitude':'47','SnowStartTemperature':'-20','bAlwaysRelevant':'True','bReplicates':'True'}
for key,value in settings.items():assert u.CRBlueprintTools.set_property_text(defaults,key,value),key
# Make overcast, fog and rain the common forest conditions. Preserve the package's
# parameter structs and adjust only their existing distribution weights.
import re
description=u.CRBlueprintTools.describe_object(defaults)
for name,weight in [('ClearSky',.25),('MediumClouded',1),('Clouded',3),('MediumRain',2),('HeavyRain',.6),('ThunderRain',.3),('ThunderStorm',.1),('Foggy',2)]:
    value=next(line.split(' = ',1)[1] for line in description.splitlines() if line.startswith(name+' = '))
    value=re.sub(r'(Weight_2_[A-F0-9]+=)[0-9.]+',lambda m:m[1]+str(weight),value)
    # The vendor converts this setting to sky-clock units by multiplying by 60.
    # At 48x time, 6.667..20 gives 30..90 real seconds per weather transition.
    value=re.sub(r'(MinMaxTransitionTime_6_[A-F0-9]+=)\(X=[^,]+,Y=[^)]+\)',r'\g<1>(X=6.666667,Y=20.000000)',value)
    assert u.CRBlueprintTools.set_property_text(defaults,name,value),name
u.BlueprintEditorLibrary.compile_blueprint(bp)
assert not u.CRBlueprintTools.has_blueprint_errors(bp)
assert lib.save_loaded_asset(bp,only_if_is_dirty=False)
for actor in actors.get_all_level_actors():
    if actor.actor_has_tag('HP_Weather') or isinstance(actor,(u.DirectionalLight,u.SkyLight,u.SkyAtmosphere,u.VolumetricCloud,u.ExponentialHeightFog)):
        actors.destroy_actor(actor)
sky=actors.spawn_actor_from_class(bp.generated_class(),u.Vector())
sky.set_actor_label('Hollow Pines - Day Night and Weather')
sky.tags=['HP_Generated','HP_Weather'];sky.set_folder_path('HollowPines/Weather')
assert u.CRBlueprintTools.set_property_text(sky,'bIsSpatiallyLoaded','False')
# The sky uses low-lux artistic lighting; constrain adaptation so forest paths
# remain readable at dusk while unlit caves retain deep shadows.
post=actors.spawn_actor_from_class(u.PostProcessVolume,u.Vector())
post.set_actor_label('Blackwater Exposure');post.tags=['HP_Generated','HP_Weather']
post.set_editor_property('unbound',True)
exposure=post.get_editor_property('settings')
for key,value in [('override_auto_exposure_min_brightness',True),('override_auto_exposure_max_brightness',True),('auto_exposure_min_brightness',-2.0),('auto_exposure_max_brightness',2.0)]:
    exposure.set_editor_property(key,value)
post.set_editor_property('settings',exposure)
assert u.CRBlueprintTools.set_property_text(post,'bIsSpatiallyLoaded','False')
assert levels.save_current_level()
(ROOT/'resources/BlackwaterWeather.json').write_text(json.dumps({'blueprint':path,'start_hour':16.5,'full_cycle_minutes':30,
    'weather_interval_seconds':[180,420],'weather_blend_seconds':[30,90],'source':'EasySky V2 2.5','replicated':True,'rain_occlusion':'Dynamic scene-depth capture'},indent=2)+'\n')
print('BLACKWATER_WEATHER_INSTALLED')
