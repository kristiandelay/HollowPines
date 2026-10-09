"""Check authored terrain collision, cave coverage, passive NPCs and PCG output."""
import unreal as u
from pathlib import Path
import json,sys,math

assert not u.EditorLevelLibrary.get_pie_worlds(False),'Stop PIE first'
root=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).parent
sys.path.insert(0,str(root/'Scripts'))
import hollow_pines_layout as layout
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert levels.load_level('/Game/HollowPines/Maps/L_BlackwaterReach')
actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
report={'passed':False,'checks':[]}

def trace(start,end):
    hit=u.SystemLibrary.line_trace_single(world,u.Vector(*start),u.Vector(*end),
        u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[a for a in actors if isinstance(a,u.Character)],u.DrawDebugTrace.NONE,True)
    assert hit,('Missing collision',start,end)
    values=hit.to_tuple()
    return values[4],values[9]

try:
    terrain=[a for a in actors if a.actor_has_tag('HP_BakedTerrain')]
    assert len(terrain)==66,len(terrain)
    assert all(a.static_mesh_component.get_collision_enabled()!=u.CollisionEnabled.NO_COLLISION for a in terrain)
    report['checks'].append({'case':'baked_terrain_sections_have_collision','count':len(terrain)})
    counts={}
    for actor in actors:
        for component in actor.get_components_by_class(u.InstancedStaticMeshComponent):
            mesh=component.static_mesh
            if mesh:counts[mesh.get_name()]=counts.get(mesh.get_name(),0)+component.get_instance_count()
    redwoods=sum(n for name,n in counts.items() if name.startswith('SM_Redwood_'))
    grass=sum(n for name,n in counts.items() if name.startswith('SM_Grass'))
    bushes=sum(n for name,n in counts.items() if 'Bush' in name and name.endswith('_Trunk'))
    cliffs=sum(n for name,n in counts.items() if name.startswith('SM_Cliff'))
    assert redwoods>=2000,redwoods
    assert grass>=100000,grass
    assert bushes>=1000,bushes
    assert cliffs>=100,cliffs
    forest=next(a for a in actors if a.get_actor_label().startswith('Broadleaf Forest -'))
    assert all(forest.get_editor_property(k).generated for k in ['PCG_Terrain','PCG_Cover','PCG_Biome'])
    roads=[a for a in actors if a.get_actor_label().startswith('Broadleaf Path -')]
    assert len(roads)==12 and all(a.get_editor_property('PCG_Biome').generated for a in roads)
    assert not any(a.get_actor_label().startswith('PCG Redwood Forest') for a in actors)
    report['checks'].append({'case':'broadleaf_output_persists_after_reload','redwoods':redwoods,
        'grass_instances':grass,'bushes':bushes,'rock_cliffs':cliffs,'road_subbiomes':len(roads),'instances_by_mesh':counts})
    npcs=[a for a in actors if isinstance(a,u.HollowPinesMonster)]
    assert len(npcs)==4 and all(not a.rehearse_attacks for a in npcs)
    report['checks'].append({'case':'four_passive_creature_encounters','actors':[a.get_actor_label() for a in npcs]})
    pois=[]
    for name,(x,y,radius) in layout.POIS.items():
        point,actor=trace((x*100,y*100,30000),(x*100,y*100,-10000))
        pois.append({'name':name,'collision_z_m':point.z/100,'actor':actor.get_actor_label()})
    report['checks'].append({'case':'landmark_ground_collision','locations':pois})
    caves=[]
    for x,y,z in [(325,72,layout.MINE_Z-23),(330,18,layout.MINE_Z-40),(310,-90,layout.MINE_Z-70),(365,-175,layout.EXIT_Z-12)]:
        floor,actor=trace((x*100,y*100,(z+2)*100),(x*100,y*100,(z-5)*100))
        ceiling,roof=trace((x*100,y*100,(z+2)*100),(x*100,y*100,(z+30)*100))
        assert actor.actor_has_tag('HP_BakedTerrain'),actor.get_actor_label()
        assert ceiling.z-floor.z>300,(floor,ceiling)
        caves.append({'xy_m':[x,y],'floor_z_m':floor.z/100,'ceiling_z_m':ceiling.z/100})
    report['checks'].append({'case':'underground_floor_and_overhead_collision','samples':caves})
    report['passed']=True
finally:
    (root/'Artifacts/BlackwaterReachValidation.json').write_text(json.dumps(report,indent=2)+'\n')
print('BLACKWATER_REACH_VALIDATED',report['passed'])
