# HollowPines

Unreal Engine **5.8.3** project built on Lyra and the Game Animation Sample's CMC locomotion and traversal. The starting map is `/Game/Maps/L_TraversalGym`.

## Get started

Install Unreal Engine 5.8.3, the Visual Studio C++ tools required by Unreal, Git, and Git LFS. Approximately 8 GB of assets are stored in Git LFS.

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

Unreal assets and binary art/audio files use Git LFS, as configured in `.gitattributes`. Generated binaries, caches, IDE files, local editor data, and `Artifacts/` reports are excluded by `.gitignore`.

## Included gameplay

- Motion-matched movement, sliding, jumping, vaulting, mantling, and climbing.
- Inventory, rifle/pistol/shotgun pickups, firing, reloading, and combat death/respawn.
- Aim offsets, shooting while sliding, and shoulder switching with mirrored weapon poses and hand transfer.
- Physics Control, passive ragdolls, pose-matched recovery, and paired shove/tackle/takedown interactions.
- Six character visual overrides through the Game Animation Widget.
- Standalone and two-player PIE validation scripts.

See [BaselineTemplate.txt](docs/BaselineTemplate.txt) for controls and maintenance, and [TraversalSetup.txt](docs/TraversalSetup.txt) for integration details. Original sample documentation and notices remain under `src/`.

The imported `resources/*Validation.json` files record checks of the original baseline; their historical paths and hashes do not certify the renamed project. Running the validation scripts generates current reports under `Artifacts/`. Packaged builds and networking under latency/loss require project-specific validation.
