"""Use EasyBiomes' full Broadleaf rules with Redwood added to its collections.

HP_BROADLEAF_STAGE: assets, preview, world. Vendor assets remain unchanged.
Project graph copies only adapt surface queries for baked Mesh Terrain.
"""
import unreal as u
from pathlib import Path
import json,math,sys,time,traceback

ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).parent
sys.path.insert(0,str(ROOT/'Scripts'))
import hollow_pines_layout as layout
BASE='/Game/HollowPines/Environment/PCG/Broadleaf'
VENDOR='/Game/EasyBiomes'
lib=u.EditorAssetLibrary
assets=u.AssetToolsHelpers.get_asset_tools()
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert not u.EditorLevelLibrary.get_pie_worlds(False),'Stop PIE first'
STAGE=globals().get('HP_BROADLEAF_STAGE','assets')

def save(obj):assert lib.save_loaded_asset(obj,only_if_is_dirty=False),obj
def duplicate(source,target):
    return u.load_asset(target) if lib.does_asset_exist(target) else lib.duplicate_asset(source,target)
def props(obj,values):
    for key,value in values.items():assert u.CRBlueprintTools.set_property_text(obj,key,str(value)),key
def table(source,name,rows):
    result=duplicate(source,BASE+'/'+name)
    assert u.DataTableFunctionLibrary.fill_data_table_from_json_string(result,json.dumps(rows))
    save(result);return result
def rows(path):return json.loads(u.DataTableFunctionLibrary.export_data_table_to_json_string(u.load_asset(path)))

adapted={}
def adapt_graph(source):
    key=source.get_path_name()
    if key in adapted:return adapted[key]
    graph=duplicate(key,BASE+'/Graphs/HP_'+source.get_name())
    adapted[key]=graph
    # Keep every spacing, species relationship, pruning, noise, road and coverage
    # rule. Only the surface providers and their recursive references change.
    for node in list(graph.nodes):
        settings=node.get_settings()
        if isinstance(settings,u.PCGSubgraphSettings):
            source_node=next((n for n in source.nodes if n.get_name()==node.get_name()),None)
            original=source_node.get_settings().subgraph_instance.graph if source_node else settings.subgraph_instance.graph
            if isinstance(original,u.PCGGraph) and original.get_path_name().startswith(VENDOR):
                settings.subgraph_instance.set_editor_property('graph',adapt_graph(original))
        elif isinstance(settings,u.PCGGetLandscapeSettings):
            targets=[(e.output_pin.get_outer(),e.output_pin.properties.label) for pin in node.output_pins for e in pin.edges]
            replacement,ray=graph.add_node_of_type(u.PCGWorldRayHitSettings)
            replacement.set_editor_property('node_title','Baked Mesh Terrain Surface')
            for target,pin in targets:graph.add_edge(replacement,'Out',target,pin)
            graph.remove_node(node);settings=ray
        if isinstance(settings,u.PCGWorldRayHitSettings):
            settings.set_editor_property('query_params',u.PCGWorldRayHitQueryParams())
            props(settings,{'QueryParams':'(bOverrideDefaultParams=True,RayOrigin=(X=0,Y=0,Z=40000),RayDirection=(X=0,Y=0,Z=-1),RayLength=80000,bIgnorePCGHits=True,bIgnoreSelfHits=True,bTraceComplex=True)'})
    save(graph);return graph

def child(name,parent,values):
    path=BASE+'/'+name
    if lib.does_asset_exist(path):
        bp=u.load_asset(path)
        u.BlueprintEditorLibrary.reparent_blueprint(bp,u.load_asset(parent).generated_class())
    else:
        factory=u.BlueprintFactory();factory.set_editor_property('parent_class',u.load_asset(parent).generated_class())
        bp=assets.create_asset(name,BASE,u.Blueprint,factory)
    props(u.get_default_object(bp.generated_class()),values)
    u.BlueprintEditorLibrary.compile_blueprint(bp)
    assert not u.CRBlueprintTools.has_blueprint_errors(bp),name
    save(bp);return bp

def prepare_assets():
    sets=[]
    for name,variants,group in [('TreesHuge',['Large_01','Large_02','Large_03'],0),('TreesBig',['Medium_01','Medium_02'],1),('TreesMedium',['Small_01','Small_02'],2)]:
        sets.append({'SetName':name,'Meshes':[f"/Script/Engine.StaticMesh'/Game/Redwood/Models/Trees/SM_Redwood_{v}.SM_Redwood_{v}'" for v in variants],'CullingGroup':group})
    redwoods=table(VENDOR+'/Foliage/Trees/Poplar/DT_Poplar_Collection','DT_Redwood_BroadleafCollection',[{'Name':'NewRow','Sets':sets}])
    dense=next(r for r in rows(VENDOR+'/PCG/BiomePresets/DT_Biome_Poplar') if r['Name']=='Forest_Dense')
    dense['Name']='HollowPines_LushRedwood';dense['MeshCollections'].append(redwoods.get_path_name())
    dense['BiomeCoverage']=1.;dense['BiomeDensity']=1.;dense['BiomeSeason']=1.
    for key,name in [('BiomeGraph','PCG_Biome_Poplar'),('CoverageGraph','PCG_Biome_PoplarCover'),('TerrainGraph','PCG_Biome_PoplarTerrain')]:
        dense[key]=adapt_graph(u.load_asset(VENDOR+'/PCG/Graph/Biomes/Poplar/'+name)).get_path_name()
    preset=table(VENDOR+'/PCG/BiomePresets/DT_Biome_Poplar','DT_HollowPines_Broadleaf',[dense])
    child('BP_HollowPinesBroadleaf',VENDOR+'/PCG/Blueprints/BP_Biome',{
        'BiomePreset':f'(DataTable="{preset.get_path_name()}",RowName="HollowPines_LushRedwood")',
        'SpawnOnMeshes':True,'GroundCover':True,'TerrainElements':True,'LargeVegetation':True,
        'FillLandscape':False,'WaterBiome':False,'RuntimeGeneration':False,'Debug':False,'HideVisuals':True})
    road_rows=rows(VENDOR+'/PCG/BiomePresets/DT_SubBiome_RoadPoplar')
    for row in road_rows:
        if row.get('BiomeGraph') and row['BiomeGraph']!='None':
            source=row['BiomeGraph'].split("'")[1] if "'" in row['BiomeGraph'] else row['BiomeGraph']
            row['BiomeGraph']=adapt_graph(u.load_asset(source)).get_path_name()
    table(VENDOR+'/PCG/BiomePresets/DT_SubBiome_RoadPoplar','DT_HollowPines_ForestRoads',road_rows)
    road_base=duplicate(VENDOR+'/PCG/Blueprints/BP_SubBiome',BASE+'/BP_HollowPinesSubBiome')
    assert u.HPWorldTools.configure_biome_mesh_bounds(road_base)
    save(road_base)
    child('BP_HollowPinesForestRoad',BASE+'/BP_HollowPinesSubBiome',{
        'BiomePreset':f'(DataTable="{BASE}/DT_HollowPines_ForestRoads.DT_HollowPines_ForestRoads",RowName="Path")',
        'IsRoad':True,'SpawnOnMeshes':True,'HideVisuals':True,'RuntimeGeneration':False})
    (ROOT/'resources/BlackwaterBroadleaf.json').write_text(json.dumps({
        'source_listing':'https://www.fab.com/listings/61f2b0fc-5656-46b7-86ef-3c2100cebcb4','source_preset':'Forest_Dense',
        'preset':preset.get_path_name(),'redwood_collection':redwoods.get_path_name(),
        'coverage':1,'density':1,'season':1,'ground_cover':True,'terrain_elements':True,
        'road_blueprint':BASE+'/BP_HollowPinesForestRoad',
        'adaptations':'Surface queries project to baked Mesh Terrain; sub-biome bounds honor SpawnOnMeshes. Original Broadleaf placement rules retained.',
        'graphs':{k:v.get_path_name() for k,v in adapted.items()}},indent=2)+'\n')
    print('BROADLEAF_ASSETS_READY',len(adapted),flush=True)

def mark(actor,name):
    actor.set_actor_label(name);actor.set_folder_path('HollowPines/Broadleaf')
    actor.tags=list(dict.fromkeys([str(t) for t in actor.tags]+['HP_Broadleaf']))
    return actor
def spline(actor,points,closed=True,name='Spline'):
    component=actor.get_editor_property(name)
    actor.modify();component.modify();props(component,{'bSplineHasBeenEdited':True})
    component.clear_spline_points(False)
    for p in points:component.add_spline_point(u.Vector(*p),u.SplineCoordinateSpace.WORLD,False)
    for i in range(len(points)):component.set_spline_point_type(i,u.SplinePointType.LINEAR,False)
    component.set_closed_loop(closed,True)
    actor.call_method('UserConstructionScript')
    return component
def spawn_biome(label,bounds):
    bp=u.load_asset(BASE+'/BP_HollowPinesBroadleaf')
    actor=actors.spawn_actor_from_class(bp.generated_class(),u.Vector(0,0,5000))
    props(actor,{'Seed':layout.SEED,'BiomeDensity':1.,'BiomeCoverage':1.,'BiomeSeason':1.,'GroundCover':True,'TerrainElements':True,'LargeVegetation':True,'SpawnOnMeshes':True,'Generate':True})
    spline(actor,[(x*100,y*100,5000) for x,y in bounds])
    mark(actor,label)
    spawn_name=next(line[6:] for line in u.CRBlueprintTools.describe_blueprint(u.load_asset(VENDOR+'/PCG/Blueprints/BP_Biome')).splitlines() if line.startswith('GRAPH ') and ' Spawn ' in line)
    actor.call_method(spawn_name)
    return actor

def remover(name,points):
    bp=u.load_asset(VENDOR+'/PCG/Blueprints/BP_BiomeRemover')
    actor=actors.spawn_actor_from_class(bp.generated_class(),u.Vector())
    props(actor,{'RemoverPreset':'(DataTable="/Game/EasyBiomes/PCG/BiomePresets/DT_Remover.DT_Remover",RowName="Everything")'})
    spline(actor,[(x*100,y*100,6000) for x,y in points])
    mark(actor,'Broadleaf Clearing - '+name)
    return actor

def road(name,points):
    bp=u.load_asset(BASE+'/BP_HollowPinesForestRoad')
    actor=actors.spawn_actor_from_class(bp.generated_class(),u.Vector())
    props(actor,{'BiomePreset':f'(DataTable="{BASE}/DT_HollowPines_ForestRoads.DT_HollowPines_ForestRoads",RowName="Path")',
        'Seed':layout.SEED,'IsRoad':True,'SpawnOnMeshes':True,'Width':1,'Lift':3,'Sides':True,
        'PlantsAmount':.9,'Weed':.8,'HideVisuals':True})
    sampled=[]
    for a,b in zip(points,points[1:]):
        count=max(1,math.ceil(math.dist(a,b)/8))
        for i in range(count):
            x=a[0]+(b[0]-a[0])*i/count;y=a[1]+(b[1]-a[1])*i/count
            sampled.append((x*100,y*100,layout.height(x,y)*100+3))
    x,y=points[-1];sampled.append((x*100,y*100,layout.height(x,y)*100+3))
    spline(actor,sampled,False,'MainSpline')
    mark(actor,'Broadleaf Path - '+name)
    source=u.load_asset(VENDOR+'/PCG/Blueprints/BP_SubBiome')
    function=next(line[6:] for line in u.CRBlueprintTools.describe_blueprint(source).splitlines() if line.startswith('GRAPH ') and ' Spawn ' in line)
    actor.call_method(function)
    return actor

def build_world():
    for actor in list(actors.get_all_level_actors()):
        if actor.get_actor_label().startswith(('PCG Redwood Forest','Broadleaf Integration Preview','Broadleaf Forest','Broadleaf Clearing -','Broadleaf Path -')):
            actors.destroy_actor(actor)
    # Use the package's remover and sub-biome actors, so paths/clearings remain
    # editable through the same vendor rules as the forest.
    for name,(x,y,radius) in layout.POIS.items():
        remover(name,[(x+radius*math.cos(math.tau*i/20),y+radius*math.sin(math.tau*i/20)) for i in range(20)])
    for name,x,y,radius in [('Mine Mouth',248,114,12),('Swamp Cave Exit',305,-260,10)]:
        remover(name,[(x+radius*math.cos(math.tau*i/16),y+radius*math.sin(math.tau*i/16)) for i in range(16)])
    bank=[(layout.river_x(y)-15,y) for y in range(-500,321,10)]
    bank += [(layout.river_x(y)+15,y) for y in reversed(range(-500,321,10))]
    remover('River Channel',bank)
    for name,cx,cy,rx,ry in [('North Lake',0,348,92,74),('Swamp',275,-325,70,81)]:
        remover(name,[(cx+rx*math.cos(math.tau*i/32),cy+ry*math.sin(math.tau*i/32)) for i in range(32)])
    road_actors=[road(name,points) for name,points in layout.TRAILS]
    forest=spawn_biome('Broadleaf Forest - Lush Redwood Mix',[(-488,-488),(488,-488),(488,488),(-488,488)])
    return forest,road_actors

def finalize(forest,roads):
    state={'busy':False,'phase':'queue','next':time.monotonic()+1,'deadline':time.monotonic()+1200}
    performance=u.load_object(None,'/Script/UnrealEd.Default__EditorPerformanceSettings')
    throttle=performance.get_editor_property('bThrottleCPUWhenNotForeground')
    props(performance,{'bThrottleCPUWhenNotForeground':False})
    def tick(dt):
        if state['busy']:return
        state['busy']=True
        try:
            now=time.monotonic()
            if now<state['next']:return
            state['next']=now+1
            assert now<state['deadline'],'Broadleaf generation timed out'
            components=[forest.get_editor_property(k) for k in ['PCG_Terrain','PCG_Cover','PCG_Biome']]
            components += [a.get_editor_property('PCG_Biome') for a in roads]
            components += [a.get_editor_property('PCG_Biome') for a in actors.get_all_level_actors() if 'River Generator' in a.get_actor_label()]
            if state['phase']=='queue':
                # Partition mappings update on the editor tick after actors are
                # constructed. A same-frame vendor Spawn can have no cells yet.
                for c in components:
                    if c.get_graph() and not c.generated:c.generate(True)
                state['phase']='pcg'
                return
            if state['phase']=='pcg':
                if not all(c.generated for c in components):return
                u.HPWorldTools.build_navigation(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world())
                state['phase']='nav';state['next']=now+3
            else:
                world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
                if u.NavigationSystemV1.is_navigation_being_built(world):return
                assert levels.save_current_level()
                counts={}
                for actor in actors.get_all_level_actors():
                    for c in actor.get_components_by_class(u.InstancedStaticMeshComponent):
                        if c.static_mesh and not c.static_mesh.get_name().startswith('SM_Flag'):
                            n=c.static_mesh.get_name();counts[n]=counts.get(n,0)+c.get_instance_count()
                (ROOT/'resources/BlackwaterBuild.json').write_text(json.dumps({'map':'/Game/HollowPines/Maps/L_BlackwaterReach',
                    'generator':'Broadleaf Forest_Dense plus Redwood collection','instances':sum(counts.values()),
                    'instances_by_mesh':counts,'navigation_built':True,'road_subbiomes':len(roads)},indent=2)+'\n')
                state['finished']=True;u.unregister_slate_post_tick_callback(state['handle'])
                props(performance,{'bThrottleCPUWhenNotForeground':throttle})
                print('BROADLEAF_WORLD_COMPLETE',sum(counts.values()),flush=True)
        except Exception:
            state['error']=traceback.format_exc();u.unregister_slate_post_tick_callback(state['handle'])
            props(performance,{'bThrottleCPUWhenNotForeground':throttle})
            print('BROADLEAF_WORLD_FAILED',state['error'],flush=True)
        finally:state['busy']=False
    state['handle']=u.register_slate_post_tick_callback(tick)
    return state

if STAGE=='assets':prepare_assets()
elif STAGE=='preview':
    for actor in actors.get_all_level_actors():
        if actor.get_actor_label()=='Broadleaf Integration Preview':actors.destroy_actor(actor)
    broadleaf_preview=spawn_biome('Broadleaf Integration Preview',[(-430,-250),(-270,-250),(-270,-90),(-430,-90)])
    print('BROADLEAF_PREVIEW_QUEUED',flush=True)
elif STAGE=='world':
    broadleaf_forest,broadleaf_roads=build_world()
    broadleaf_build=finalize(broadleaf_forest,broadleaf_roads)
    print('BROADLEAF_WORLD_QUEUED',flush=True)
