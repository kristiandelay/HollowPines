"""Keep UE 5.8 source modifiers stored, but use baked geometry for editing/play.

The installed Mesh Partition preview/compiler asserts in AppendDynamicMesh.
Disabling its modifiers avoids that engine path without discarding source meshes.
"""
import unreal as u
l=u.get_editor_subsystem(u.LevelEditorSubsystem)
a=u.get_editor_subsystem(u.EditorActorSubsystem)
assert l.load_level('/Game/HollowPines/Maps/L_BlackwaterReach')
count=0
for actor in a.get_all_level_actors():
    if actor.get_class().get_name()=='ModifierActor' and actor.actor_has_tag('HP_Terrain'):
        for component in actor.get_components_by_class(u.ActorComponent):
            if component.get_class().get_name()=='MeshProviderModifier':
                assert u.CRBlueprintTools.set_property_text(component,'bIsDisabled','True')
                count+=1
    if actor.actor_has_tag('HP_BakedTerrain'):
        assert u.CRBlueprintTools.set_property_text(actor,'bHiddenEd','False')
        actor.set_is_temporarily_hidden_in_editor(False)
        actor.set_actor_hidden_in_game(False)
assert count==66,count
assert l.save_current_level()
print('STABLE_BAKED_TERRAIN',count)
