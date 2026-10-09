"""Create an isolated movement/animation review map; leaves TraversalGym untouched."""
import unreal as u

assert not u.EditorLevelLibrary.get_pie_worlds(False)
MAP='/Game/HollowPines/Maps/L_MonsterAnimationGym'
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
assert levels.new_level(MAP)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
world.get_world_settings().set_editor_property('default_game_mode',u.HollowPinesMonsterReviewGameMode)

def cube(label,location,scale):
    a=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*location))
    a.set_actor_label(label);a.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cube'))
    a.set_actor_scale3d(u.Vector(*scale));a.static_mesh_component.set_collision_profile_name('BlockAll')
    return a

cube('Review Ground',(0,0,-50),(180,180,1))
for i,(x,y) in enumerate([(-1600,1400),(1600,1400),(-1600,-2000),(1600,-2000)]):
    cube('Crowd Obstacle '+str(i),(x,y,130),(3,3,2.6))
sun=actors.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,3000),u.Rotator(pitch=-45,yaw=-30,roll=0))
sun.light_component.set_mobility(u.ComponentMobility.MOVABLE)
sun.light_component.set_editor_property('intensity',3.0)
sky=actors.spawn_actor_from_class(u.SkyLight,u.Vector(0,0,2500))
sky.light_component.set_mobility(u.ComponentMobility.MOVABLE)
sky.light_component.set_editor_property('intensity',1.0)
sky.light_component.set_editor_property('real_time_capture',True)
actors.spawn_actor_from_class(u.SkyAtmosphere,u.Vector())
post=actors.spawn_actor_from_class(u.PostProcessVolume,u.Vector())
post.set_editor_property('unbound',True)
settings=post.get_editor_property('settings')
settings.set_editor_property('override_auto_exposure_min_brightness',True)
settings.set_editor_property('override_auto_exposure_max_brightness',True)
settings.set_editor_property('auto_exposure_min_brightness',0)
settings.set_editor_property('auto_exposure_max_brightness',0)
post.set_editor_property('settings',settings)
for i in range(4):actors.spawn_actor_from_class(u.PlayerStart,u.Vector(-450+i*300,-1700,110),u.Rotator(pitch=0,yaw=90,roll=0))
dummy=cube('Practice Dummy - no damage',(0,1800,130),(1,1,2.6))
dummy.tags=['HollowPinesPracticeDummy']
for i,name in enumerate(['CaveStalker','HollowStalker','HollowRootRevenant','Hag']):
    cls=u.load_class(None,'/Game/HollowPines/Monsters/'+name+'/BP_NPC_'+name+'.BP_NPC_'+name+'_C')
    half=u.get_default_object(cls).profile.capsule_half_height
    npc=actors.spawn_actor_from_class(cls,u.Vector(-2700+i*1800,400,half+10),u.Rotator(pitch=0,yaw=-90,roll=0))
    npc.set_actor_label(name+' - Motion Review');npc.set_editor_property('practice_target',dummy)
    npc.set_editor_property('patrol_radius',650.0);npc.set_editor_property('awareness_radius',3500.0)
    npc.set_editor_property('rehearse_attacks',False)
    text=actors.spawn_actor_from_class(u.TextRenderActor,u.Vector(-2700+i*1800,-300,15),u.Rotator(pitch=90,yaw=0,roll=0))
    text.text_render.set_text(name);text.text_render.set_world_size(55)
nav=u.HPWorldTools.add_navigation_bounds(world,u.Vector(0,0,1000),u.Vector(17800,17800,3000))
assert nav
for data in u.GameplayStatics.get_all_actors_of_class(world,u.RecastNavMesh):
    assert u.CRBlueprintTools.set_property_text(data,'RuntimeGeneration','Dynamic')
    assert u.CRBlueprintTools.set_property_text(data,'bForceRebuildOnLoad','True')
print(u.HPWorldTools.build_navigation(world))
# The asynchronous navigation build must finish before the final save; validation
# saves again after confirming projection and two-client movement.
assert levels.save_current_level()
u.EditorLevelLibrary.set_level_viewport_camera_info(u.Vector(-1300,-3100,850),u.Rotator(pitch=-12,yaw=65,roll=0))
print('MONSTER_REVIEW_MAP_READY',MAP)
