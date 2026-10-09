"""Render all nine characters in PIE and audit their compiled skeletal materials."""
import unreal as u
import json
import time
import traceback
from pathlib import Path

material_root=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).parent
material_records=json.loads((material_root/'resources/CharacterSources.json').read_text())['characters']
material_out=material_root/'Artifacts/CharacterMaterials'
material_out.mkdir(parents=True,exist_ok=True)
material_test={'index':0,'phase':'wait','busy':False,'results':[],'deadline':time.monotonic()+180}

def material_finish(error=None):
    u.unregister_slate_post_tick_callback(material_test['handle'])
    material_test.update(finished=True,error=error)
    report={'passed':error is None,'error':error,'characters':material_test['results']}
    (material_out/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    if material_test.get('actor'):material_test['actor'].destroy_actor()
    if material_test.get('camera'):material_test['camera'].destroy_actor()
    print('CHARACTER_MATERIAL_RENDER_TEST_COMPLETE',error)

def material_tick(delta):
    if material_test['busy']:return
    material_test['busy']=True
    try:
        assert time.monotonic()<material_test['deadline'],'Material render check timed out'
        worlds=u.EditorLevelLibrary.get_pie_worlds(False)
        if not worlds:return
        world=worlds[0]
        if material_test['phase']=='wait':
            if not u.GameplayStatics.get_player_pawn(world,0):return
            material_test['camera']=u.CRBlueprintTools.spawn_pie_test_actor(world,u.SceneCapture2D,u.Transform())
            capture=material_test['camera'].get_component_by_class(u.SceneCaptureComponent2D)
            capture.set_editor_property('capture_every_frame',False)
            capture.set_editor_property('capture_on_movement',False)
            capture.set_editor_property('capture_source',u.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
            capture.set_editor_property('primitive_render_mode',u.SceneCapturePrimitiveRenderMode.PRM_USE_SHOW_ONLY_LIST)
            target=u.RenderingLibrary.create_render_target2d(world,720,900,u.TextureRenderTargetFormat.RTF_RGBA8)
            capture.set_editor_property('texture_target',target)
            material_test.update(capture=capture,target=target,phase='prepare')
        if material_test['phase']=='prepare':
            record=material_records[material_test['index']]
            name=record['name'];folder=record['unreal_folder']
            mesh=u.load_asset(folder+'/'+name)
            material=u.load_asset(folder+'/M_'+name)
            assert u.MaterialEditingLibrary.has_material_usage(material,u.MaterialUsage.MATUSAGE_SKELETAL_MESH),name
            assert all(slot.material_interface==material for slot in mesh.get_editor_property('materials')),name
            used={t.get_path_name() for t in u.MaterialEditingLibrary.get_used_textures(material)}
            for kind in ['BaseColor','Normal','Metallic','Roughness']:
                assert u.load_asset(folder+'/Textures/'+name+'_'+kind).get_path_name() in used,(name,kind)
            stats=u.MaterialEditingLibrary.get_statistics(material)
            assert stats.num_pixel_shader_instructions>0 and stats.num_pixel_texture_samples>=4,(name,stats)
            origin=u.Vector(10000,10000,1000)
            actor=u.CRBlueprintTools.spawn_pie_test_actor(world,u.SkeletalMeshActor,u.Transform(location=origin))
            actor.set_actor_enable_collision(False)
            component=actor.get_editor_property('skeletal_mesh_component')
            component.set_skeletal_mesh_asset(mesh)
            component.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
            capture=material_test['capture']
            capture.clear_show_only_components()
            capture.show_only_actor_components(actor)
            bounds=mesh.get_bounds()
            center=origin+bounds.origin
            distance=max(bounds.box_extent.x*2,bounds.box_extent.z*2)*1.7
            camera_location=center+u.Vector(0,distance,0)
            material_test['camera'].set_actor_location_and_rotation(camera_location,u.MathLibrary.find_look_at_rotation(camera_location,center),False,True)
            capture.set_editor_property('fov_angle',38)
            material_test.update(actor=actor,phase='capture',next=time.monotonic()+1.5,
                current={'name':name,'material':material.get_path_name(),'skeletal_usage':True,
                         'texture_samples':stats.num_pixel_texture_samples,'pixel_instructions':stats.num_pixel_shader_instructions})
        elif material_test['phase']=='capture' and time.monotonic()>=material_test['next']:
            material_test['capture'].capture_scene()
            material_test.update(phase='export',next=time.monotonic()+.4)
        elif material_test['phase']=='export' and time.monotonic()>=material_test['next']:
            name=material_test['current']['name']
            u.RenderingLibrary.export_render_target(world,material_test['target'],str(material_out),name+'.png')
            assert (material_out/(name+'.png')).is_file(),name
            material_test['results'].append(material_test['current'])
            material_test['actor'].destroy_actor()
            material_test['actor']=None
            material_test['index']+=1
            if material_test['index']==len(material_records):material_finish()
            else:material_test['phase']='prepare'
    except Exception:material_finish(traceback.format_exc())
    finally:material_test['busy']=False

material_test['handle']=u.register_slate_post_tick_callback(material_tick)
if not u.EditorLevelLibrary.get_pie_worlds(False):
    u.get_editor_subsystem(u.LevelEditorSubsystem).editor_request_begin_play()
print('CHARACTER_MATERIAL_RENDER_TEST_STARTED')
