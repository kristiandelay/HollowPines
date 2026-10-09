# HollowPines

Unreal Engine **5.8.3** project built on Lyra and the Game Animation Sample's CMC locomotion and traversal. The starting map is `/Game/Maps/L_TraversalGym`.

## Get started

Install Unreal Engine 5.8.3, the Visual Studio C++ tools required by Unreal, Git, and Git LFS. The project and source art are stored in Git LFS; run `git lfs pull` before opening either Unreal or Blender.

```powershell
git lfs install
git clone git@github.com:kristiandelay/HollowPines.git
cd HollowPines
git lfs pull
powershell -ExecutionPolicy Bypass -File Scripts/Build-Editor.ps1
```

Open `Open-Traversal.cmd`, then press Play. If Unreal is installed elsewhere, pass `-EngineRoot` to the build/open PowerShell scripts.

The Unreal project is `src/HollowPines.uproject`. Build targets are `HollowPines`, `HollowPinesEditor`, `HollowPinesClient`, and `HollowPinesServer`, with EOS/Steam variants for the game and server. Native `LyraGame` and `LyraEditor` module names and asset paths are retained to preserve serialized Blueprint references.

## Repository layout

- `src/`: Unreal project, source, plugins, assets, and build configuration.
- `Scripts/`: Build, launch, authoring, and validation tools.
- `docs/`: Controls and integration notes.
- `resources/`: Asset manifests and validation records.
- `Mockups/`: Project mockup assets.
- `Art/Characters/`: Preserved source models/textures, editable Blender rigs, FBX exports, and posed review images.

Unreal assets and binary art/audio files use Git LFS, as configured in `.gitattributes`. Generated binaries, caches, IDE files, local editor data, and `Artifacts/` reports are excluded by `.gitignore`.

## Included gameplay

- Motion-matched movement, sliding, jumping, vaulting, mantling, and climbing.
- Inventory, rifle/pistol/shotgun pickups, firing, reloading, and combat death/respawn.
- Aim offsets, shooting while sliding, and shoulder switching with mirrored weapon poses and hand transfer.
- Physics Control, passive ragdolls, pose-matched recovery, and paired shove/tackle/takedown interactions.
- Automatic server-assigned character visuals: teammates receive distinct characters and keep them after respawn.
- Standalone and two-player PIE validation scripts.

See [BaselineTemplate.txt](docs/BaselineTemplate.txt) for controls and maintenance, and [TraversalSetup.txt](docs/TraversalSetup.txt) for integration details. Original sample documentation and notices remain under `src/`.

Older imported `resources/*Validation.json` files record checks of the original baseline; their historical paths and hashes do not certify the renamed project. `MonsterNPCValidation.json`, `PlayerGoreValidation.json`, `BlackwaterWeatherValidation.json`, `BlackwaterReachValidation.json`, and `BlackwaterTraversalValidation.json` record the current project integration checks. Running the validation scripts generates current reports under `Artifacts/`. Packaged builds and networking under latency/loss require project-specific validation.

## Hollow Pines characters

Maya Cross, Mudbound Survivor, Wasteland Hero, Wasteland Sentinel, and Wasteland Vanguard appear in the Game Animation Widget's visual override list. Their assets are under `/Game/HollowPines/Players`. Auto-Rig Pro fits include both hands and all five fingers, UE5 spine/neck/twist bones, and Manny-to-character IK retargeters. Each character has its own fitted skeleton, preserving the existing Manny skeleton and animations.

The server assigns these five survivors first, then the six sample characters if more players join. Assignments replicate to every client, survive death/respawn, and become available when a player disconnects. The current eleven-model roster supports eleven distinct appearances; larger sessions reuse the least-used characters until more models are added. For manual art previews only, enter `hp.UniquePlayerVisuals 0` in the console before selecting a character in the Game Animation Widget. The default is `1`.

`Scripts/Test-TeamVisuals.py` checks four-player identity replication and combat respawn. `Scripts/Test-ClimbGravity.py` checks completed/interrupted climbs, mantles, hurdles and vaults on the host and client, plus gravity and movement correction after the action ends. Traversal cleanup also handles a failed animation and no longer replays predicted climbs on their owning player.

Cave Stalker, Hollow Stalker, Hollow Root Revenant, and Hag are under `/Game/HollowPines/Monsters`. Each folder includes a custom skeleton, skeletal mesh, materials, an `IK_` chain asset, and a placeable `BP_` preview actor. Cave Stalker uses four limbs plus the source model's central tail appendage; the root creature is 5.5 m tall. The Hag has separate sleeve and robe chains. Each creature now has a custom locomotion blend space and 13 first-pass clips: idle, walk, run, jump start/loop/landing, three melee attacks, three directional hit reactions, and death. These are motion-blocking animations ready for review; cloth simulation and animation polish remain.

Open `Art/Characters/<Name>/<Name>.blend` for editing. Player control rigs require Auto-Rig Pro (prepared with Blender 5.2.2 and ARP 3.78.57); creature rigs use Blender FK chains with optional IK targets. Normalized textures use relative `Source/` paths. Originals remain unchanged in `Source/` and the renamed ZIP archives; their hashes and original filenames are recorded in `SourceManifest.json`.

The Meshy convention is `Name.fbx`, `Name_BaseColor.png`, `Name_Normal.png`, `Name_Metallic.png`, and `Name_Roughness.png`. `Scripts/Prepare-MeshySource.py` performs collision-checked normalization. The fitting, skinning, import, integration, and validation scripts are in `Scripts/`; `resources/CharacterSources.json` records all nine assets. Player LOD0 meshes are about 90k triangles and creature LOD0 meshes about 100k, with two reduced Unreal LODs. These Meshy sculpts remain prototype art and may need topology and weight refinement for extreme poses or close-up cinematics.

## Monster animation review

Open the isolated review map:

```powershell
powershell -ExecutionPolicy Bypass -File Scripts/Open-Traversal.ps1 -Map /Game/HollowPines/Maps/L_MonsterAnimationGym
```

The four `BP_NPC_` characters patrol with crowd avoidance and personal spacing. The Hag's animations hover above her movement capsule. NPCs cannot damage players. Rehearsal targets must be non-pawn practice dummies; a shared queue grants one melee animation turn at a time.

In the review map: **F1** selects a creature, **F2** pauses patrol, **F3** toggles coordinated dummy rehearsal, **1/2/3** play attacks, **J** jumps, **H** cycles hit reactions, **X** plays death, and **Backspace** resets the selected creature. Editable animation sources are `Art/Characters/<Name>/<Name>_Animations.blend`; the original rig files remain separate.

## Player gore

The five Hollow Pines survivors use project-owned Gore Systems materials under `/Game/HollowPines/Gore`. Real Lyra damage with an impact hit paints localized wounds and spawns blood/bleeding effects. Damage tagged `HollowPines.Damage.Slash` paints a cut; fatal slashes may detach an arm, leg or head at a supported joint. **Root, pelvis and spine/torso bones are excluded from dismemberment.** The torso remains a single mesh.

Fatal torso hits and strong torso slashes have a 35% chance to drop one or two random organs. Wounds and deterministic drop decisions replicate; debris physics are local cosmetics with a 30-second lifetime. Bleeding effects last eight seconds and do not add gameplay damage. Respawn restores the complete, clean character. Tune probabilities and effects in `DA_PlayerGore`; this is joint-based slicing, not arbitrary torso-plane cutting.

## Blackwater Reach exploration prototype

```powershell
powershell -ExecutionPolicy Bypass -File Scripts/Open-Traversal.ps1 -Map /Game/HollowPines/Maps/L_BlackwaterReach
```

The 1 km square forest follows `Mockups/Level/map.png`: a Survivor Basecamp start, cabin, river crossing, logging site, radio tower, old mine, north lake, cliff lookout, swamp and south exit. Paths connect the landmarks and reserve clear space in the seeded Redwood PCG forest. The mine contains a descending cave route, underground lake, collapsed branch and swamp exit. Landmarks and cave surfaces are blockouts for traversal/layout testing, not finished environment art.

EasySky V2 is included as a project plugin. The project sky starts at 16:30, runs a 30-minute full day/night cycle, favors overcast/fog/rain, and changes weather every 3?7 real minutes with 30?90 second blends. Dynamic rain-depth capture includes camp shelters and terrain. Settings live in `BP_HollowPinesSky` and `resources/BlackwaterWeather.json`.

Unreal 5.8's experimental Mesh Terrain compiled-section builder asserts on the imported providers in this engine install. The map therefore retains editable Mesh Terrain source sections with their providers disabled and uses baked static meshes for rendering/collision. Keep providers disabled until that compiler issue is resolved. `Scripts/Bake-BlackwaterTerrain.py` refreshes the play meshes after source changes; `Scripts/Stabilize-BlackwaterTerrain.py` restores the safe state. The baked geometry is the current tested runtime path.

The axe animation pack is available under `/Game/MeleeComboFullSet/Animations/Axe`; axe combat/equipment binding is not yet implemented. Asset import source choices are recorded in `resources/EasyBiomesImport.json` and `resources/EasySkyImport.json`.

## Authoring and validation

Launch with `-Automation` to enable the local editor bridge, then use `python Scripts/Send-Editor.py <script>`. Scripts require a running editor and report results under ignored `Artifacts/`.

- `Animate-CreatureCharacters.py` authors the source animation clips in Blender; `Import-MonsterAnimations.py` imports their Unreal animation assets.
- `Build-MonsterAnimationGym.py` rebuilds the isolated review map. It does not edit `L_TraversalGym`.
- `Build-BlackwaterReach.py` builds the layout, dressing and PCG. Set `HP_BUILD_STAGE` inside the editor Python environment to `terrain`, `dressing`, `pcg`, or `all`; terrain is baked before generating vegetation, and finalization waits for PCG/navigation before saving. Layout, paths and seed are in `hollow_pines_layout.py`.
- `Finalize-BlackwaterReach.py` waits for PCG and navigation before saving; `Tune-BlackwaterMaterials.py` maintains the project water and slope materials.
- `Validate-BlackwaterReach.py` checks saved PCG output, landmark collision and underground floors/ceilings. `Test-BlackwaterTraversal.py` checks multiplayer grounding and gravity at the camp, cave and bridge.
- `Integrate-PlayerGore.py` creates the character materials, painter and organ meshes. `Integrate-BlackwaterWeather.py` installs the forest sky preset.
- `Test-MonsterNPCs.py`, `Test-PlayerGore.py` and `Test-BlackwaterWeather.py` exercise multiplayer behavior. Stop PIE between tests. The gore test includes repeated combat death/respawn.

Packaged builds, performance at target hardware settings, late joining and adverse-network testing remain separate release checks.
