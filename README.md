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
- `resources/`: Imported baseline validation records.
- `Mockups/`: Project mockup assets.
- `Art/Characters/`: Preserved source models/textures, editable Blender rigs, FBX exports, and posed review images.

Unreal assets and binary art/audio files use Git LFS, as configured in `.gitattributes`. Generated binaries, caches, IDE files, local editor data, and `Artifacts/` reports are excluded by `.gitignore`.

## Included gameplay

- Motion-matched movement, sliding, jumping, vaulting, mantling, and climbing.
- Inventory, rifle/pistol/shotgun pickups, firing, reloading, and combat death/respawn.
- Aim offsets, shooting while sliding, and shoulder switching with mirrored weapon poses and hand transfer.
- Physics Control, passive ragdolls, pose-matched recovery, and paired shove/tackle/takedown interactions.
- Eleven character visual overrides through the Game Animation Widget, including five Hollow Pines survivors.
- Standalone and two-player PIE validation scripts.

See [BaselineTemplate.txt](docs/BaselineTemplate.txt) for controls and maintenance, and [TraversalSetup.txt](docs/TraversalSetup.txt) for integration details. Original sample documentation and notices remain under `src/`.

The imported `resources/*Validation.json` files record checks of the original baseline; their historical paths and hashes do not certify the renamed project. Running the validation scripts generates current reports under `Artifacts/`. Packaged builds and networking under latency/loss require project-specific validation.

## Hollow Pines characters

Maya Cross, Mudbound Survivor, Wasteland Hero, Wasteland Sentinel, and Wasteland Vanguard appear in the Game Animation Widget's visual override list. Their assets are under `/Game/HollowPines/Players`. Auto-Rig Pro fits include both hands and all five fingers, UE5 spine/neck/twist bones, and Manny-to-character IK retargeters. Each character has its own fitted skeleton, preserving the existing Manny skeleton and animations.

Cave Stalker, Hollow Stalker, Hollow Root Revenant, and Hag are under `/Game/HollowPines/Monsters`. Each folder includes a custom skeleton, skeletal mesh, materials, an `IK_` chain asset, and a placeable `BP_` preview actor. Cave Stalker uses four limbs plus the source model's central tail appendage; the root creature is 5.5 m tall. The Hag has separate sleeve and robe chains. These are rigged creature assets; creature locomotion, attacks, AI, and cloth simulation still need their gameplay/animation work.

Open `Art/Characters/<Name>/<Name>.blend` for editing. Player control rigs require Auto-Rig Pro (prepared with Blender 5.2.2 and ARP 3.78.57); creature rigs use Blender FK chains with optional IK targets. Normalized textures use relative `Source/` paths. Originals remain unchanged in `Source/` and the renamed ZIP archives; their hashes and original filenames are recorded in `SourceManifest.json`.

The Meshy convention is `Name.fbx`, `Name_BaseColor.png`, `Name_Normal.png`, `Name_Metallic.png`, and `Name_Roughness.png`. `Scripts/Prepare-MeshySource.py` performs collision-checked normalization. The fitting, skinning, import, integration, and validation scripts are in `Scripts/`; `resources/CharacterSources.json` records all nine assets. Player LOD0 meshes are about 90k triangles and creature LOD0 meshes about 100k, with two reduced Unreal LODs. These Meshy sculpts remain prototype art and may need topology and weight refinement for extreme poses or close-up cinematics.
