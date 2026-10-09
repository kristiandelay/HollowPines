"""Project-owned water tuning and a rock/soil slope blend for the blockout."""
import unreal as u

lib=u.EditorAssetLibrary
edit=u.MaterialEditingLibrary
base='/Game/HollowPines/Environment/Materials'
path=base+'/MI_BlackwaterWater'
water=u.load_asset(path) if lib.does_asset_exist(path) else lib.duplicate_asset('/Game/EasyBiomes/Materials/Environment/Water/MI_RiverMuddy',path)
for name,value in [('NormalIntencity',.35),('Wobble',.12),('Refraction',.2),('Specular',.35),('PixelDepthOffset',0),('ScatteringCoefficientF',.0012)]:
    edit.set_material_instance_scalar_parameter_value(water,name,value)
edit.set_material_instance_vector_parameter_value(water,'BaseColor',u.LinearColor(.08,.16,.14,1))
edit.set_material_instance_vector_parameter_value(water,'AbsorbtionColor',u.LinearColor(.16,.08,.04,.108))
lib.save_loaded_asset(water,only_if_is_dirty=False)
for name in ['NorthLakeWater','SwampWater','DescendingRiver','UndergroundLake']:
    mesh=u.load_asset('/Game/HollowPines/Environment/Geometry/SM_'+name)
    if mesh:mesh.set_material(0,water);lib.save_loaded_asset(mesh)

ground=u.load_asset(base+'/M_ForestFloor')
expressions=edit.get_material_expressions(ground)
if not any(str(x.get_editor_property('desc'))=='HP_SlopeBlend' for x in expressions):
    soil=next(x for x in expressions if isinstance(x,u.MaterialExpressionMaterialFunctionCall))
    rock=edit.create_material_expression(ground,u.MaterialExpressionMaterialFunctionCall,-200,-300)
    rock.set_material_function(u.load_asset('/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedTexture'))
    texture=edit.create_material_expression(ground,u.MaterialExpressionTextureObject,-650,-300)
    texture.texture=u.load_asset('/Game/Redwood/Textures/T_Rock_Tile_01')
    size=edit.create_material_expression(ground,u.MaterialExpressionConstant3Vector,-650,-450)
    size.constant=u.LinearColor(400,400,400,1)
    edit.connect_material_expressions(texture,'',rock,'TextureObject')
    edit.connect_material_expressions(size,'',rock,'TextureSize')
    normal=edit.create_material_expression(ground,u.MaterialExpressionVertexNormalWS,-650,500)
    z=edit.create_material_expression(ground,u.MaterialExpressionComponentMask,-450,500)
    for channel,value in [('r',False),('g',False),('b',True),('a',False)]:z.set_editor_property(channel,value)
    absolute=edit.create_material_expression(ground,u.MaterialExpressionAbs,-250,500)
    power=edit.create_material_expression(ground,u.MaterialExpressionPower,-50,500)
    power.set_editor_property('const_exponent',4.0)
    blend=edit.create_material_expression(ground,u.MaterialExpressionLinearInterpolate,200,0)
    blend.set_editor_property('desc','HP_SlopeBlend')
    assert edit.connect_material_expressions(normal,'',z,'')
    assert edit.connect_material_expressions(z,'',absolute,'')
    edit.connect_material_expressions(absolute,'',power,'Base')
    edit.connect_material_expressions(rock,'XYZ Texture',blend,'A')
    edit.connect_material_expressions(soil,'XYZ Texture',blend,'B')
    edit.connect_material_expressions(power,'',blend,'Alpha')
    edit.connect_material_property(blend,'',u.MaterialProperty.MP_BASE_COLOR)
    edit.recompile_material(ground);lib.save_loaded_asset(ground)
# Repair existing authored graphs too; these unary inputs have no display name.
expressions=edit.get_material_expressions(ground)
normal=next(x for x in expressions if isinstance(x,u.MaterialExpressionVertexNormalWS))
z=next(x for x in expressions if isinstance(x,u.MaterialExpressionComponentMask))
absolute=next(x for x in expressions if isinstance(x,u.MaterialExpressionAbs))
assert edit.connect_material_expressions(normal,'',z,'')
assert edit.connect_material_expressions(z,'',absolute,'')
edit.recompile_material(ground);lib.save_loaded_asset(ground)
print('BLACKWATER_MATERIALS_TUNED')
