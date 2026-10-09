"""Wire server player identities and bounded CMC traversal cleanup into the sample graphs."""
import unreal as u

for path, configure in [
    ('/Game/Blueprints/AC_VisualOverrideManager', u.CRBlueprintTools.configure_unique_player_visuals),
    ('/Game/Blueprints/AC_TraversalLogic', u.CRBlueprintTools.configure_traversal_cleanup),
]:
    asset = u.load_asset(path)
    assert configure(asset), path
    u.BlueprintEditorLibrary.compile_blueprint(asset)
    assert not u.CRBlueprintTools.has_blueprint_errors(asset), path
    assert u.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False), path
    print('Integrated', path)
