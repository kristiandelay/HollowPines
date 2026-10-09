"""Build the reference-driven Blackwater Reach exploration prototype.

Editor bridge stages: set HP_BUILD_STAGE to terrain, dressing or pcg; then exec
this file. The default 'all' runs all stages. Existing generated map is loaded;
only actors tagged HP_Generated are replaced when a stage is rerun.
"""
import unreal as u
import math,random,json,sys,importlib
from pathlib import Path

ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).parent
if str(ROOT/'Scripts') not in sys.path:sys.path.insert(0,str(ROOT/'Scripts'))
import hollow_pines_layout as layout
importlib.reload(layout)
STAGE=globals().get('HP_BUILD_STAGE','all')
MAP='/Game/HollowPines/Maps/L_BlackwaterReach'
BASE='/Game/HollowPines/Environment'
lib=u.EditorAssetLibrary
assets=u.AssetToolsHelpers.get_asset_tools()
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert not u.EditorLevelLibrary.get_pie_worlds(False),'Stop Play before rebuilding'

def save(asset):
    assert lib.save_loaded_asset(asset,only_if_is_dirty=False),asset

def label(actor,name,stage):
    actor.set_actor_label(name)
    if stage=='Terrain' and actor.get_class().get_name()=='ModifierActor':
        for component in actor.get_components_by_class(u.ActorComponent):
            if component.get_class().get_name()=='MeshProviderModifier':
                assert u.CRBlueprintTools.set_property_text(component,'bIsDisabled','True')
    actor.tags=list(dict.fromkeys([str(t) for t in actor.tags]+['HP_Generated','HP_'+stage]))
    actor.set_folder_path('HollowPines/'+stage)
    return actor

def clear_stage(stage):
    for actor in actors.get_all_level_actors():
        if actor.actor_has_tag('HP_Generated') and actor.actor_has_tag('HP_'+stage):actors.destroy_actor(actor)

def material(name,texture,normal=None,tile=400):
    path=BASE+'/Materials/'+name
    if lib.does_asset_exist(path):return u.load_asset(path)
    mat=assets.create_asset(name,BASE+'/Materials',u.Material,u.MaterialFactoryNew())
    edit=u.MaterialEditingLibrary
    fn=edit.create_material_expression(mat,u.MaterialExpressionMaterialFunctionCall,-300,0)
    fn.set_material_function(u.load_asset('/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedTexture'))
    tex=edit.create_material_expression(mat,u.MaterialExpressionTextureObject,-600,0)
    color=u.load_asset(texture)
    if color.get_editor_property('virtual_texture_streaming'):
        regular_path=BASE+'/Materials/T_'+name+'_Color'
        color=u.load_asset(regular_path) if lib.does_asset_exist(regular_path) else lib.duplicate_asset(texture,regular_path)
        color.set_editor_property('virtual_texture_streaming',False);save(color)
    tex.texture=color
    size=edit.create_material_expression(mat,u.MaterialExpressionConstant3Vector,-600,180)
    size.constant=u.LinearColor(tile,tile,tile,1)
    assert edit.connect_material_expressions(tex,'',fn,'TextureObject')
    assert edit.connect_material_expressions(size,'',fn,'TextureSize')
    assert edit.connect_material_property(fn,'XYZ Texture',u.MaterialProperty.MP_BASE_COLOR)
    rough=edit.create_material_expression(mat,u.MaterialExpressionConstant,-100,280);rough.r=.83
    edit.connect_material_property(rough,'',u.MaterialProperty.MP_ROUGHNESS)
    mat.set_editor_property('two_sided',True)
    edit.recompile_material(mat);save(mat)
    return mat

def dynamic(vertices,triangles,uvs=None):
    mesh=u.DynamicMesh()
    buffers=u.GeometryScriptSimpleMeshBuffers()
    buffers.vertices=[u.Vector(x*100,y*100,z*100) for x,y,z in vertices]
    # Unreal's front-facing winding is the reverse of the XY grid convention.
    buffers.triangles=[u.IntVector(b,a,c) for a,b,c in triangles]
    buffers.uv0=[u.Vector2D(*(uvs[i] if uvs else (p[0]/4,p[1]/4))) for i,p in enumerate(vertices)]
    u.GeometryScript_MeshEdits.append_buffers_to_mesh(mesh,buffers)
    u.GeometryScript_Normals.recompute_normals(mesh,u.GeometryScriptCalculateNormalsOptions())
    return mesh

def static_mesh(name,vertices,triangles,mat,collision=True):
    path=BASE+'/Geometry/'+name
    if lib.does_asset_exist(path):
        mesh=u.load_asset(path)
        options=u.GeometryScriptCopyMeshToAssetOptions()
        options.enable_recompute_normals=True;options.enable_recompute_tangents=True
        u.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(dynamic(vertices,triangles),mesh,options,u.GeometryScriptMeshWriteLOD())
        mesh.set_material(0,mat);save(mesh);return mesh
    options=u.GeometryScriptCreateNewStaticMeshAssetOptions()
    options.enable_recompute_normals=True;options.enable_recompute_tangents=True
    options.enable_collision=collision;options.collision_mode=u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
    mesh,outcome=u.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dynamic(vertices,triangles),path,options)
    assert mesh,(name,outcome)
    mesh.set_material(0,mat);save(mesh);return mesh

def prop(path,name,x,y,z=None,yaw=0,scale=1,stage='Dressing',ground=True):
    mesh=u.load_asset(path)
    assert isinstance(mesh,u.StaticMesh),path
    pos=u.Vector(x*100,y*100,(layout.height(x,y) if z is None else z)*100)
    sx,sy,sz=(scale,scale,scale) if isinstance(scale,(int,float)) else scale
    if ground:
        bounds=mesh.get_bounds();pos.z-=(bounds.origin.z-bounds.box_extent.z)*sz
    actor=label(actors.spawn_actor_from_class(u.StaticMeshActor,pos,u.Rotator(pitch=0,yaw=yaw,roll=0)),name,stage)
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.set_actor_scale3d(u.Vector(sx,sy,sz))
    actor.static_mesh_component.set_collision_profile_name('BlockAll')
    return actor

def light(name,x,y,z,power=450,radius=1400,color=(1,.53,.2)):
    a=label(actors.spawn_actor_from_class(u.PointLight,u.Vector(x*100,y*100,z*100)),name,'Dressing')
    c=a.light_component;c.set_editor_property('intensity',power);c.set_editor_property('attenuation_radius',radius)
    c.set_light_color(u.LinearColor(*color,1));c.set_editor_property('cast_shadows',True)
    return a

def text_actor(text,x,y,z,yaw=180,size=30):
    a=label(actors.spawn_actor_from_class(u.TextRenderActor,u.Vector(x*100,y*100,z*100),u.Rotator(pitch=0,yaw=yaw,roll=0)),text,'Dressing')
    a.text_render.set_text(text);a.text_render.set_world_size(size)
    a.text_render.set_text_render_color(u.Color(210,199,157,255));return a

def partition(name,mat):
    path=BASE+'/Terrain/MPD_'+name.replace(' ','')
    definition=u.load_asset(path) if lib.does_asset_exist(path) else lib.duplicate_asset('/MeshPartition/DataAssets/MPD_Default',path)
    assert definition
    assert u.CRBlueprintTools.set_property_text(definition,'ChannelMap','(ChannelDescs=((Name="Red"),(Name="Green"),(Name="Blue"),(Name="Yellow")))')
    definition.set_editor_property('material',mat);save(definition)
    terrain=u.HPWorldTools.create_mesh_terrain(world,definition)
    assert terrain
    label(terrain,name,'Terrain')
    return terrain

def terrain_stage():
    clear_stage('Terrain')
    forest_mat=material('M_ForestFloor','/Game/EasyBiomes/Textures/Terrain/CheapVersion/T_ForestGround_10_BC',tile=500)
    rock_mat=material('M_CaveRock','/Game/Redwood/Textures/T_Rock_Tile_01',tile=400)
    surface=partition('Blackwater Surface',forest_mat)
    caves=partition('Blackwater Caves',rock_mat)
    # 64 editable mesh sections, 2 m grid, with open portals cut into the surface.
    for tx in range(8):
        for ty in range(8):
            x0=-500+tx*125;y0=-500+ty*125;count=64
            vertices=[(x0+i*125/count,y0+j*125/count,layout.height(x0+i*125/count,y0+j*125/count)) for j in range(count+1) for i in range(count+1)]
            triangles=[]
            for j in range(count):
                for i in range(count):
                    a=j*(count+1)+i;b=a+1;c=a+count+1;d=c+1
                    center=tuple(sum(vertices[k][v] for k in [a,b,c,d])/4 for v in range(3))
                    if layout.near_cave_opening(*center):continue
                    triangles.extend([(a,b,d),(a,d,c)])
            section=u.HPWorldTools.add_mesh_terrain_section(surface,dynamic(vertices,triangles),f'Surface {tx:02}_{ty:02}')
            assert section;label(section,f'Surface {tx:02}_{ty:02}','Terrain')
    # A continuous open-ended tunnel avoids internal end caps between cave sections.
    points=[]
    for _,path,_,_ in layout.CAVES[:3]:points.extend(path if not points else path[1:])
    build_tunnel(caves,'Mine - Cavern - Underground Lake - Swamp',points,5.5,7,True)
    build_tunnel(caves,'Collapsed Side Passage',layout.CAVES[3][1],4,5.5,False)
    # Keep a geometry manifest for collision and route checks.
    manifest={'map':MAP,'seed':layout.SEED,'size_m':[1000,1000],'surface_sections':64,
              'pois':layout.POIS,'paths':layout.TRAILS,'caves':layout.CAVES,'stage':'Exploration prototype'}
    (ROOT/'resources/BlackwaterReachLayout.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('BLACKWATER_TERRAIN_CREATED',flush=True)

def build_tunnel(terrain,name,control,width,roof,main):
    centers=[]
    # Linear resampling keeps the authored grades exact. Averaged ring tangents soften joints.
    for a,b in zip(control,control[1:]):
        steps=max(2,round(math.dist(a,b)/2))
        for i in range(steps):centers.append(tuple(a[k]+(b[k]-a[k])*i/steps for k in range(3)))
    centers.append(control[-1])
    profile=[(math.cos(math.pi*i/16),math.sin(math.pi*i/16)) for i in range(17)]
    profile += [(-1+2*i/8,0) for i in range(1,8)]
    ring=len(profile);vertices=[]
    for i,(x,y,z) in enumerate(centers):
        before=centers[max(0,i-1)];after=centers[min(len(centers)-1,i+1)]
        dx=after[0]-before[0];dy=after[1]-before[1];length=max(.01,math.hypot(dx,dy))
        broad=1
        if main:
            broad+=1.7*math.exp(-((x-330)**2+(y-18)**2)/24**2)
            broad+=1.4*math.exp(-((x-310)**2+(y+90)**2)/24**2)
        for j,(px,pz) in enumerate(profile):
            irregular=(.15*math.sin(i*.83+j*2.4)+.12*math.sin(i*.29+j)) if pz>.05 else 0
            floor_offset=0
            if main and pz==0:
                floor_offset=-2.3*math.exp(-((x-310)**2+(y+90)**2)/13**2)*(1-px*px)
            vx=x-dy/length*(width*broad+irregular)*px
            vy=y+dx/length*(width*broad+irregular)*px
            # Keep enlarged chambers under the surface. Portal rings deliberately
            # remain open where the tunnel meets the surface at either end.
            ceiling=roof*broad+irregular
            if 15<i<len(centers)-16:ceiling=min(ceiling,max(4.5,layout.height(vx,vy)-z-2))
            vertices.append((vx,vy,z+ceiling*pz+floor_offset))
    triangles=[]
    for i in range(len(centers)-1):
        for j in range(ring):
            a=i*ring+j;b=i*ring+(j+1)%ring;c=(i+1)*ring+j;d=(i+1)*ring+(j+1)%ring
            center=tuple(sum(vertices[k][v] for k in [a,b,c,d])/4 for v in range(3))
            # Join the side passage through an opening in the main tunnel's east wall.
            if main and j<16 and center[0]>311 and math.hypot(center[0]-318,center[1]+35)<8:continue
            triangles.extend([(a,c,d),(a,d,b)])
    section=u.HPWorldTools.add_mesh_terrain_section(terrain,dynamic(vertices,triangles),name)
    assert section;label(section,name,'Terrain')

def dressing_stage():
    clear_stage('Dressing')
    S='/Game/SurvivorBase/Meshes/'
    x,y,_=layout.POIS['Start Camp'];z=layout.POI_HEIGHTS['Start Camp']
    prop(S+'Generic/SM_Campfire_A','Campfire',x,y,z)
    light('Campfire Glow',x,y,z+1,160,1800)
    for i,(dx,dy,yaw) in enumerate([(-12,8,0),(12,9,180),(-12,-13,20)]):
        prop(S+'Generic/SM_Canopy_A','Camp Shelter '+str(i),x+dx,y+dy,z,yaw)
        prop(S+'Table/SM_Table_01','Supplies Table '+str(i),x+dx,y+dy-2,z,yaw)
        prop(S+'Chairs/SM_CampingChair','Camp Chair '+str(i),x+dx+2,y+dy-3,z,yaw+90)
        prop(S+'Generic/SM_Ammo_Canopy','Supply Stash '+str(i),x+dx-2,y+dy,z,yaw)
        prop(S+'Lamps/SM_Lantern_01','Camp Lantern '+str(i),x+dx,y+dy-2,z+1)
        light('Shelter Light '+str(i),x+dx,y+dy,z+2.5,50,950)
    prop(S+'Electric/SM_Generator_A','Camp Generator',x+18,y+5,z)
    prop(S+'Electric/SM_Radio_A','Camp Radio',x-12,y+6,z+1)
    for i in range(5):
        prop(S+'Boxes/SM_Cargo_WoodBox-A','Camp Gear Crate '+str(i),x-6+i*1.3,y+16,z,15*i)
    for i in range(4):
        start=label(actors.spawn_actor_from_class(u.PlayerStart,u.Vector((x-4+i*2)*100,(y-8)*100,z*100+115),u.Rotator(pitch=0,yaw=90,roll=0)),'Camp Player Start '+str(i),'Dressing')
    text_actor('HOLLOW PINES\nSTART CAMP',x-7,y-17,z+2,180,42)
    text_actor('NORTH LAKE  ^\nOLD MINE  >',x+13,y+13,z+2.5,180,28)
    # Identifiable landmark props from the supplied kit, grouped for later art passes.
    for name in ['Abandoned Cabin','Logging Site','Radio Tower','Old Mine','North Lake','Cliff Lookout','South Exit']:
        px,py,_=layout.POIS[name];pz=layout.POI_HEIGHTS[name]
        text_actor(name.upper(),px,py-9,pz+2,180,42)
        light(name+' Warm Landmark',px,py,pz+3,140,1800)
        if name in ['Radio Tower','Cliff Lookout']:
            prop(S+'Generic/SM_Tower_A',name+' Tower',px,py,pz,90)
            prop(S+'Electric/SM_Radio_A',name+' Radio',px+3,py,pz+1)
        elif name=='Logging Site':
            prop(S+'Wood/SM_Sawmill_A','Abandoned Sawmill',px,py,pz)
            for i in range(5):prop(S+'Wood/SM_WoodPiles_A','Log Stack '+str(i),px-12+i*5,py+11,pz,90)
        elif name in ['Abandoned Cabin','Old Mine']:
            prop(S+'Containers/SM_Container_A_Inside',name+' Shelter Blockout',px-8,py+5,pz,0)
            prop(S+'Generic/SM_Storage_Canopy_A',name+' Porch',px-8,py-1,pz,0)
        else:prop(S+'Generic/SM_Canopy_A',name+' Shelter',px,py,pz)
    # Bridge and west ford use continuous walkable decks with kit planks and railings.
    wood=material('M_BridgeWood','/Game/Redwood/Textures/T_Trunk_Long_01',tile=300)
    for tag,cy,width,z in [('River Crossing',-230,64,layout.POI_HEIGHTS['River Crossing']),('West Ford',-65,42,layout.river_water_z(-65)+.45)]:
        cx=layout.river_x(cy)
        verts=[(cx-width/2,cy-2.5,z),(cx+width/2,cy-2.5,z),(cx+width/2,cy+2.5,z),(cx-width/2,cy+2.5,z)]
        mesh=static_mesh('SM_'+tag.replace(' ','')+'Deck',verts,[(0,1,2),(0,2,3)],wood)
        a=label(actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector()),tag+' Deck','Dressing');a.static_mesh_component.set_static_mesh(mesh)
        for side in [-1,1]:
            # Begin on the deck before the bank and follow the ground to avoid
            # metre-high steps where the flat deck meets the sculpted riverbank.
            vertices=[];triangles=[]
            for i in range(22):
                dx=side*(width/2-8+i)
                height=z if i==0 else max(z,layout.height(cx+dx,cy)+.06)
                vertices.extend([(cx+dx,cy-2.5,height),(cx+dx,cy+2.5,height)])
                if i:
                    pair=[(2*i-2,2*i,2*i+1),(2*i-2,2*i+1,2*i-1)]
                    triangles.extend(pair if side>0 else [(c,b,a) for a,b,c in pair])
            ramp=static_mesh('SM_'+tag.replace(' ','')+'Approach'+str(side),vertices,triangles,wood)
            a=label(actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector()),tag+' Bank Approach '+str(side),'Dressing')
            a.static_mesh_component.set_static_mesh(ramp)
        for dx in range(-int(width/2),int(width/2)+1,4):
            for dy in [-2.5,2.5]:
                prop('/Game/EasyBiomes/StaticMeshes/Environment/Outdoor/WoodConstructions/SM_WoodenPillar_01',tag+' Post',cx+dx,cy+dy,z,0,.7)
    # Mine support frames follow the first descent; lights also mark the return route.
    for i,p in enumerate(layout.CAVES[0][1][:3]):
        px,py,pz=p
        for dx in [-4.4,4.4]:
            prop('/Game/EasyBiomes/StaticMeshes/Environment/Outdoor/WoodConstructions/SM_WoodenPillar_01','Mine Support',px+dx,py,pz,0,2)
        light('Mine Lamp '+str(i),px+3,py,pz+3,65,1200)
    for i,p in enumerate([p for _,pts,_,_ in layout.CAVES[:3] for p in pts][3:]):
        light('Cave Route Light '+str(i),p[0],p[1],p[2]+3,45,1400,(.3,.57,.72) if i%3 else (1,.52,.17))
    px,py,pz=layout.CAVES[3][1][-1]
    for i in range(4):prop('/Game/Redwood/Models/Debris/SM_Rock_Small_01','Collapsed Tunnel Rubble',px+(i-1.5)*2,py,pz,50*i,4)
    # Water along the descending channel is an authored ribbon; flat basins use River Generator.
    water=u.load_asset('/Game/EasyBiomes/Materials/Environment/Water/MI_RiverMuddy')
    for water_name,x,y,rx,ry,z in [('NorthLake',0,348,84,67,layout.river_water_z(320)),('Swamp',275,-325,65,75,19)]:
        vertices=[(x,y,z)]+[(x+rx*1.4*math.cos(math.tau*i/128),y+ry*1.4*math.sin(math.tau*i/128),z) for i in range(128)]
        mesh=static_mesh('SM_'+water_name+'Water',vertices,[(0,i+1,(i+1)%128+1) for i in range(128)],water,False)
        actor=label(actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector()),water_name+' Water Surface','Dressing')
        component=actor.static_mesh_component;component.set_static_mesh(mesh)
        component.set_collision_profile_name('NoCollision');u.CRBlueprintTools.set_property_text(component,'bUseDefaultCollision','False')
    lx,ly,lz=310,-90,layout.MINE_Z-70-.65
    lake_vertices=[(lx,ly,lz)]+[(lx+8*math.cos(math.tau*i/32),ly+10*math.sin(math.tau*i/32),lz) for i in range(32)]
    lake_mesh=static_mesh('SM_UndergroundLake',lake_vertices,[(0,i+1,(i+1)%32+1) for i in range(32)],water,False)
    lake=label(actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector()),'Underground Lake','Dressing')
    lake.static_mesh_component.set_static_mesh(lake_mesh);lake.static_mesh_component.set_collision_profile_name('NoCollision');u.CRBlueprintTools.set_property_text(lake.static_mesh_component,'bUseDefaultCollision','False')
    vertices=[];triangles=[]
    for i in range(165):
        ry=-500+i*5;rx=layout.river_x(ry);rz=layout.river_water_z(ry)
        vertices.extend([(rx-10,ry,rz),(rx+10,ry,rz)])
        if i:triangles.extend([(2*i-2,2*i-1,2*i+1),(2*i-2,2*i+1,2*i)])
    mesh=static_mesh('SM_DescendingRiver',vertices,triangles,water,False)
    river=label(actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector()),'Descending River','Dressing')
    river.static_mesh_component.set_static_mesh(mesh);river.static_mesh_component.set_collision_profile_name('NoCollision');u.CRBlueprintTools.set_property_text(river.static_mesh_component,'bUseDefaultCollision','False')
    # Creature encounters stay away from the camp clearing and remain passive.
    for name,px,py in [('HollowStalker',115,80),('HollowRootRevenant',-250,120),('Hag',310,-260),('CaveStalker',325,72)]:
        cls=u.load_class(None,f'/Game/HollowPines/Monsters/{name}/BP_NPC_{name}.BP_NPC_{name}_C')
        profile=u.get_default_object(cls).profile
        pz=layout.MINE_Z-23 if name=='CaveStalker' else layout.height(px,py)
        npc=label(actors.spawn_actor_from_class(cls,u.Vector(px*100,py*100,pz*100+profile.capsule_half_height+5)),name+' Passive Patrol','Dressing')
        npc.set_editor_property('rehearse_attacks',False);npc.set_editor_property('patrol_radius',1800 if name!='CaveStalker' else 650)
    bounds=u.HPWorldTools.add_navigation_bounds(world,u.Vector(0,0,5000),u.Vector(98000,98000,20000))
    label(bounds,'Blackwater Navigation','Dressing')
    print('BLACKWATER_CAMP_AND_LANDMARKS_CREATED',flush=True)

def pcg_graph():
    folder=BASE+'/PCG';path=folder+'/PCG_BlackwaterForest'
    graph=u.load_asset(path) if lib.does_asset_exist(path) else assets.create_asset('PCG_BlackwaterForest',folder,u.PCGGraph,u.PCGGraphFactory())
    for node in list(graph.nodes):graph.remove_node(node)
    graph.set_editor_property('description','Hollow Pines forest. Authored exclusion points -> terrain projection -> seeded transforms -> weighted Redwood and understory instances. Rebuild layout points with Build-BlackwaterReach.py after changing paths.')
    layers=[('Redwood',16,5,[f'/Game/Redwood/Models/Trees/SM_Redwood_{s}' for s in ['Large_01','Large_02','Large_03','Medium_01','Medium_02','Small_01','Small_02']],True,100000),
            ('Ferns',5.5,.5,[f'/Game/Redwood/Models/Plants/SM_Fern_0{i}_A' for i in [1,2,3,5,6]],False,15000),
            ('Forest Floor',8,.5,['/Game/Redwood/Models/Plants/SM_Grass_01','/Game/Redwood/Models/Plants/SM_Grass_02','/Game/Redwood/Models/Debris/SM_Debris_01','/Game/Redwood/Models/Debris/SM_Debris_04'],False,11000)]
    report=[]
    for index,(name,spacing,clearance,meshes,collision,cull) in enumerate(layers):
        points=layout.scatter(spacing,clearance,layout.SEED+index)
        source,settings=graph.add_node_of_type(u.PCGCreatePointsSettings)
        settings.points_to_create=[u.PCGPoint(transform=u.Transform(location=u.Vector(x*100,y*100,z*100),rotation=u.Rotator(pitch=0,yaw=0,roll=0),scale=u.Vector(1,1,1)),density=1,seed=i+layout.SEED) for i,(x,y,z,_,_) in enumerate(points)]
        settings.cull_points_outside_volume=False
        ray,ray_settings=graph.add_node_of_type(u.PCGWorldRayHitSettings)
        assert u.CRBlueprintTools.set_property_text(ray_settings,'QueryParams','(bOverrideDefaultParams=True,RayOrigin=(X=0,Y=0,Z=40000),RayDirection=(X=0,Y=0,Z=-1),RayLength=80000,bIgnorePCGHits=True,bIgnoreSelfHits=True,bTraceComplex=True)')
        projection,ps=graph.add_node_of_type(u.PCGProjectionSettings)
        pp=ps.projection_params;pp.project_rotations=False;ps.projection_params=pp
        transform,ts=graph.add_node_of_type(u.PCGTransformPointsSettings)
        ts.rotation_min=u.Rotator(pitch=0,yaw=-180,roll=0);ts.rotation_max=u.Rotator(pitch=0,yaw=180,roll=0)
        ts.scale_min=u.Vector(.8,.8,.8);ts.scale_max=u.Vector(1.2,1.2,1.2);ts.seed=layout.SEED+index
        spawn,ss=graph.add_node_of_type(u.PCGStaticMeshSpawnerSettings)
        entries=[]
        for mesh_path in meshes:
            entry=u.PCGMeshSelectorWeightedEntry()
            collision_text='QueryAndPhysics' if collision else 'NoCollision';profile='BlockAll' if collision else 'NoCollision'
            assert entry.import_text(f'(Descriptor=(StaticMesh="{mesh_path}.{mesh_path.rsplit("/",1)[-1]}",ComponentClass="/Script/Engine.HierarchicalInstancedStaticMeshComponent",BodyInstance=(CollisionEnabled={collision_text},CollisionProfileName="{profile}"),InstanceEndCullDistance={cull},InstanceStartCullDistance={int(cull*.8)},bCanEverAffectNavigation={str(collision)},WorldPositionOffsetDisableDistance=18000),Weight=1)')
            entries.append(entry)
        ss.mesh_selector_parameters.set_editor_property('mesh_entries',entries)
        graph.add_edge(source,'Out',projection,'In');graph.add_edge(ray,'Out',projection,'Projection Target')
        graph.add_edge(projection,'Out',transform,'In');graph.add_edge(transform,'Out',spawn,'In')
        graph.add_edge(spawn,'Out',graph.get_output_node(),'Out')
        for col,node in enumerate([source,ray,projection,transform,spawn]):
            node.set_node_position(col*340,index*400+(120 if node==ray else 0))
            node.set_editor_property('node_title',name+' '+node.get_settings().get_class().get_name().replace('PCG','').replace('Settings',''))
        report.append({'layer':name,'points':len(points),'meshes':meshes,'collision':collision})
    save(graph)
    (ROOT/'resources/BlackwaterForestPCG.json').write_text(json.dumps({'seed':layout.SEED,'graph':graph.get_path_name(),'layers':report},indent=2)+'\n')
    return graph

def river_preset():
    # The supplied graph samples Landscape height. Replace those three sources
    # in a project copy with complex traces against the baked Mesh Terrain.
    folder=BASE+'/PCG';path=folder+'/PCG_BlackwaterRiver'
    graph=u.load_asset(path) if lib.does_asset_exist(path) else lib.duplicate_asset('/Game/EasyBiomes/PCG/Graph/Biomes/River/PCG_Biome_River',path)
    for node in list(graph.nodes):
        if not isinstance(node.get_settings(),u.PCGGetLandscapeSettings):continue
        destinations=[(edge.output_pin.get_outer(),edge.output_pin.properties.label) for pin in node.output_pins for edge in pin.edges]
        ray,settings=graph.add_node_of_type(u.PCGWorldRayHitSettings)
        assert u.CRBlueprintTools.set_property_text(settings,'QueryParams','(bOverrideDefaultParams=True,RayOrigin=(X=0,Y=0,Z=40000),RayDirection=(X=0,Y=0,Z=-1),RayLength=80000,bIgnorePCGHits=True,bIgnoreSelfHits=True,bTraceComplex=True)')
        ray.set_editor_property('node_title','Mesh Terrain Surface')
        for destination,pin in destinations:graph.add_edge(ray,'Out',destination,pin)
        graph.remove_node(node)
    # Keep real aquatic foliage, replacing square water/duckweed proxy tiles with
    # smooth authored surfaces that intersect the curved lake and swamp shores.
    if not any(str(node.node_title)=='Replace Tiled SM_WaterPlane' for node in graph.nodes):
        spawn=next(node for node in graph.nodes if isinstance(node.get_settings(),u.PCGStaticMeshSpawnerSettings))
        pin=next(pin for pin in spawn.input_pins if str(pin.properties.label)=='In')
        edge=pin.edges[0];source_node=edge.input_pin.get_outer();source_pin=edge.input_pin.properties.label
        graph.remove_edge(source_node,source_pin,spawn,'In')
        for mesh_name in ['SM_WaterPlane','SM_ReedsPlane']:
            node,settings=graph.add_node_of_type(u.PCGAttributeFilteringSettings)
            for key,value in [('Operator','Equal'),('TargetAttribute','PCGBegin(Mesh)PCGEnd'),('bUseConstantThreshold','True'),('AttributeTypes',f'(Type=String,StringValue="/Game/EasyBiomes/StaticMeshes/Environment/Outdoor/{mesh_name}.{mesh_name}")')]:
                assert u.CRBlueprintTools.set_property_text(settings,key,value),key
            node.set_editor_property('node_title','Replace Tiled '+mesh_name)
            graph.add_edge(source_node,source_pin,node,'In');source_node=node;source_pin='OutsideFilter'
        graph.add_edge(source_node,source_pin,spawn,'In')
    save(graph)
    source=u.load_asset('/Game/EasyBiomes/PCG/BiomePresets/DT_Biome_River')
    row=next(r for r in json.loads(u.DataTableFunctionLibrary.export_data_table_to_json_string(source)) if r['Name']=='BiomeRiver')
    row.update(Name='HollowPines_River',BiomeGraph=graph.get_path_name(),BiomeDensity=.35)
    path=folder+'/DT_BlackwaterRiver'
    table=u.load_asset(path) if lib.does_asset_exist(path) else lib.duplicate_asset(source.get_path_name(),path)
    assert u.DataTableFunctionLibrary.fill_data_table_from_json_string(table,json.dumps([row]))
    save(table)
    return table


def pcg_stage():
    clear_stage('PCG')
    if not any(a.actor_has_tag('HP_FoliageSettings') for a in actors.get_all_level_actors()):
        manager=actors.spawn_actor_from_class(u.load_asset('/Game/EasyBiomes/Blueprints/BP_FoliageManager').generated_class(),u.Vector())
        label(manager,'Blackwater Foliage Parameters','FoliageSettings')
    # The vendor's construction script replaces Actor Tags when reconstructing
    # its water plane, so also identify our two authored basin actors by label.
    for actor in actors.get_all_level_actors():
        if actor.get_actor_label() in ['North Lake - River Generator','Swamp - River Generator']:
            actors.destroy_actor(actor)
    graph=pcg_graph()
    # Custom EasyBiomes rows retain vendor presets and keep Redwood's complete meshes intact.
    folder=BASE+'/PCG'
    source=u.load_asset('/Game/EasyBiomes/Foliage/Trees/Poplar/DT_Poplar_Collection')
    path=folder+'/DT_Redwood_Collection'
    collection=u.load_asset(path) if lib.does_asset_exist(path) else lib.duplicate_asset(source.get_path_name(),path)
    sets=[]
    for set_name,files in [('TreesHuge',['Large_01','Large_02','Large_03']),('TreesBig',['Medium_01','Medium_02']),('TreesMedium',['Small_01','Small_02'])]:
        sets.append({'SetName':set_name,'Meshes':[f"/Script/Engine.StaticMesh'/Game/Redwood/Models/Trees/SM_Redwood_{f}.SM_Redwood_{f}'" for f in files],'CullingGroup':0})
    assert u.DataTableFunctionLibrary.fill_data_table_from_json_string(collection,json.dumps([{'Name':'Redwood','Sets':sets}]))
    save(collection)
    source=u.load_asset('/Game/EasyBiomes/PCG/BiomePresets/DT_Biome_Poplar')
    rows=json.loads(u.DataTableFunctionLibrary.export_data_table_to_json_string(source))
    row=next(r for r in rows if r['Name']=='Forest_Dense');row['Name']='HollowPines_Redwood'
    row['BiomeGraph']=graph.get_path_name();row['CoverageGraph']='None';row['TerrainGraph']='None'
    row['MeshCollections']=[collection.get_path_name()]
    path=folder+'/DT_Biome_HollowPines'
    table=u.load_asset(path) if lib.does_asset_exist(path) else lib.duplicate_asset(source.get_path_name(),path)
    assert u.DataTableFunctionLibrary.fill_data_table_from_json_string(table,json.dumps([row]));save(table)
    forest=label(actors.spawn_actor_from_class(u.PCGVolume,u.Vector(0,0,5000)),'PCG Redwood Forest - Seed '+str(layout.SEED),'PCG')
    forest.pcg_component.set_graph(graph);forest.pcg_component.seed=layout.SEED
    forest.pcg_component.generate(True)
    river_table=river_preset()
    basin_path=folder+'/BP_BlackwaterBasin'
    if lib.does_asset_exist(basin_path):bp=u.load_asset(basin_path)
    else:
        factory=u.BlueprintFactory();factory.set_editor_property('parent_class',u.load_asset('/Game/EasyBiomes/PCG/Blueprints/BP_Biome').generated_class())
        bp=assets.create_asset('BP_BlackwaterBasin',folder,u.Blueprint,factory)
    defaults=u.get_default_object(bp.generated_class())
    # WaterBiome must be a class default: PreConstruct removes water components
    # from dry biomes before instance properties can be assigned by Python.
    for k,v in [('WaterBiome','True'),('SpawnOnMeshes','True'),('TerrainElements','False'),('GroundCover','False'),('Debug','False')]:
        assert u.CRBlueprintTools.set_property_text(defaults,k,v),k
    u.BlueprintEditorLibrary.compile_blueprint(bp);assert not u.CRBlueprintTools.has_blueprint_errors(bp);save(bp)
    for name,cx,cy,rx,ry,z in [('North Lake',0,348,84,67,layout.river_water_z(320)),('Swamp',275,-325,65,75,19)]:
        biome=label(actors.spawn_actor_from_class(bp.generated_class(),u.Vector(cx*100,cy*100,z*100)),name+' - River Generator','PCG')
        for k,v in [('BiomePreset','(DataTable="/Game/HollowPines/Environment/PCG/DT_BlackwaterRiver.DT_BlackwaterRiver",RowName="HollowPines_River")'),('SpawnOnMeshes','True'),('Water','True'),('WaterBiome','True'),('WaterLevel',str(z*100)),('Seed',str(layout.SEED)),('BiomeDensity','0.35'),('AmbientParticles','False'),('RuntimeGeneration','False'),('GroundCover','False'),('TerrainElements','False'),('Debug','False'),('LargeVegetation','True')]:
            assert u.CRBlueprintTools.set_property_text(biome,k,v),k
        spline=biome.get_component_by_class(u.SplineComponent);assert spline
        biome.modify();spline.modify()
        assert u.CRBlueprintTools.set_property_text(spline,'bSplineHasBeenEdited','True')
        spline.clear_spline_points(False)
        for i in range(16):spline.add_spline_point(u.Vector((cx+rx*math.cos(math.tau*i/16))*100,(cy+ry*math.sin(math.tau*i/16))*100,z*100),u.SplineCoordinateSpace.WORLD,False)
        spline.set_closed_loop(True,True)
        biome.call_method('UserConstructionScript')
        spawn_name=next(line[6:] for line in u.CRBlueprintTools.describe_blueprint(u.load_asset('/Game/EasyBiomes/PCG/Blueprints/BP_Biome')).splitlines() if line.startswith('GRAPH ') and ' Spawn ' in line)
        biome.call_method(spawn_name)
        label(biome,name+' - River Generator','PCG')
        # Actor label/folder changes can invalidate generation during construction.
        biome.get_editor_property('PCG_Biome').generate(True)
    print('BLACKWATER_PCG_GENERATION_QUEUED',flush=True)

if not lib.does_asset_exist(MAP):
    assert levels.new_level_from_template(MAP,'/Engine/Maps/Templates/OpenWorld')
    for a in actors.get_all_level_actors():
        if isinstance(a,(u.LandscapeProxy,u.PlayerStart)):actors.destroy_actor(a)
else:
    current=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if not current.get_path_name().startswith(MAP+'.'):assert levels.load_level(MAP)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
world.get_world_settings().set_editor_property('default_game_mode',u.CRTraversalGameMode)
if STAGE in ['all','terrain']:terrain_stage()
if STAGE in ['all','dressing']:dressing_stage()
if STAGE in ['all','terrain']:
    # Collision must match the editable source before PCG projects its points.
    assert levels.save_current_level()
    bake=ROOT/'Scripts/Bake-BlackwaterTerrain.py'
    exec(compile(bake.read_text(),str(bake),'exec'),{})
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
if STAGE in ['all','pcg']:pcg_stage()
assert levels.save_current_level()
u.EditorLevelLibrary.set_level_viewport_camera_info(u.Vector(5500,-2600,layout.POI_HEIGHTS['Start Camp']*100+500),u.Rotator(pitch=-6,yaw=90,roll=0))
tune=ROOT/'Scripts/Tune-BlackwaterMaterials.py'
exec(compile(tune.read_text(),str(tune),'exec'),{})
print('BLACKWATER_STAGE_COMPLETE',STAGE,flush=True)
if STAGE in ['all','pcg']:
    finalize=ROOT/'Scripts/Finalize-BlackwaterReach.py'
    exec(compile(finalize.read_text(),str(finalize),'exec'),globals())
