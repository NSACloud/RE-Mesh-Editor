![REMeshEditorTitle](https://github.com/NSACloud/RE-Mesh-Editor/assets/46909075/156d0b53-ff4f-43db-9a3d-9e0cbd71326e)


**V0.56 (9/9/2025) | [Planned Features](https://github.com/NSACloud/RE-Mesh-Editor/milestone/1) | [Change Log](https://github.com/NSACloud/RE-Mesh-Editor?tab=readme-ov-file#change-log)**

**BETA RELEASE, THERE MAY BE BUGS**


This addon allows for importing and exporting of RE Engine mesh and mdf2 (material) files natively in Blender.
### [Download RE Mesh Editor](https://github.com/NSACloud/RE-Mesh-Editor/archive/refs/heads/main.zip)

<img width="1736" height="1019" alt="meshEditorPreview" src="https://github.com/user-attachments/assets/74e026a0-73bc-41e8-a3f6-2d931f5c7dc0" />

## Features
 - Allows for importing and exporting of RE Engine mesh files.
 - Allows for importing and exporting of RE Engine mdf2 (material) files.
 - MDF material editing from within Blender.<details>
 
    <summary>Video Preview</summary>
  
    https://github.com/user-attachments/assets/48be61bc-7c40-440f-881b-534809d3232f
   
    </details>
   
 - Preset system that allows for presets of materials to be saved and shared.
 - Supports LOD (level of detail) import and export.
 - Texture conversion tools.
 - Collection based system that allows for export with multiple mesh files in a scene.
 - RE Toolbox batch export integration. Any files exported will be added to the RE Toolbox batch export list.
 - Drag and drop dds/tex conversion. (Blender 4.1 and higher)<details>
    <summary>Video Preview</summary>
  
    https://github.com/user-attachments/assets/cf99e5f2-2aa6-4a6f-b170-1e5beb3bcec4
   
    </details>
 - Drag and drop mesh importing. (Blender 4.1 and higher)<details>
    <summary>Video Preview</summary>
  
    https://github.com/user-attachments/assets/fa1ba74e-8a57-4115-b6cd-9585a2a92a21
   
    </details>
 - Additional supported file types:
  - **.fbxskel** - (Skeleton)
 ## Supported Games
 - **Devil May Cry 5**
 - **Resident Evil 2/3 Remake (Supports both RT and Non RT Versions)**
 - **Resident Evil 4 Remake**
 - **Resident Evil 7 Ray Tracing Version**
 - **Resident Evil 8**
 - **Resident Evil Re:Verse** 
 - **Monster Hunter Rise**
 - **Street Fighter 6**
 - **Dragon's Dogma 2**
 - **Kunitsu-Gami: Path of the Goddess**
 - **Dead Rising Deluxe Remaster**
 - **Onimusha 2: Samurai's Destiny**
 - **Monster Hunter Wilds**
 
Support for more games may be added in the future.

## Requirements
* [Blender 2.93 or higher (4.3.2 or higher recommended)](https://www.blender.org/download/)

  
**Not required but strongly recommended:**
* [RE Chain Editor](https://github.com/NSACloud/RE-Chain-Editor) - Blender addon for creation of chain files. Used to add physics to models.
* [RE Asset Library (Blender 4.3.2 or higher required)](https://github.com/NSACloud/RE-Asset-Library) - Blender addon that allows for extraction and importing of RE Engine files. Reduces the need to look up file IDs to find what you're looking for.
## Installation
Download the addon from the "Download RE Mesh Editor" link at the top or click Code > Download Zip.

In Blender, go to Edit > Preferences > Addons, then click "Install" in the top right.

NOTE: If you are on Blender 4.2 or above, the install button is found by clicking the arrow in the top right of the addon menu.

![image](https://github.com/user-attachments/assets/49dd95c1-9a20-49d8-af55-7160d54836df)

Navigate to the downloaded zip file for this addon and click "Install Addon". The addon should then be usable.

To update this addon, navigate to Preferences > Add-ons > RE Mesh Editor and press the "Check for update" button.

## Change Log
### V0.56 - 9/9/2025
* Reverted triangulation changes from previous update as it caused issues in some cases.

### V0.55 - 8/27/2025
* Added partial MPLY (stage mesh) support.
Note that not all stage meshes are fully working yet.

For more info on current issues with stage meshes, see the issues page.

* The RE MDF tab has been renamed to RE Mesh.
* Tool panels have been reorganized.
* Added .fbxskel (skeleton) import/export support. This allows for proportional changes to armatures.
Note that certain animations and cutscenes can override the .fbxskel file's changes.
* Added "Link Armature Bones" button to the RE Mesh tab. This can be used to constrain bones from several armatures to an fbxskel armature. 
* Fixed issue where normals could become incorrect if a model was not triangulated prior to export.
* Added RE Mesh Tools panel.

The RE Toolbox addon is now deprecated, as it's functionality has been integrated in the RE Mesh tab.

Uninstalling is recommended.

### V0.54 - 8/17/2025
* Fixed issue where certain meshes using extra weights in MH Wilds couldn't be imported.
* Fixed detail normal map direction.

### V0.53 - 8/13/2025
* Added MDF updater buttons in the RE MDF tab under the RE Asset Extensions tab.
This allows for outdated MDF files to be updated with the click of a button.
RE Asset Library is required to use this feature.
Be sure to update to the latest version for both the addon and asset libraries themselves.

* Added extra weight support for MH Wilds.
This extends the allowed amount of weights on a vertex from 6 to 12.
This may also be usable on other games to extend the weight limit from 8 to 16, but for now the addon only allows MH Wilds to exceed the limit.

* Fixed issue where Import All LODs didn't work with MH Wilds.
* Fixed issue where MH Wilds would crash when a monster is slain if it's model was edited.
* Fixed material import error related to tiling.

### V0.52 - 7/15/2025
* Fixed issue where materials would fail to import if materials had previously been loaded in a blend file using an older addon version.
* Added RE Verse drag and drop tex conversion support.

### V0.51 - 6/30/2025
* Fixed issue where certain models could fail to import if bone names exceeded Blender's size limit.
* Fixed material loading issue on certain models in RE4.
* Fixed issue where the addon wouldn't work on versions before 4.3.2.

### V0.50 - 6/4/2025
* Fixed tex version for SF6 Elena update.

### V0.49 - 6/1/2025
* Fix skin material issue introduced by last update.
### V0.48 - 6/1/2025
* Added Onimusha 2 support.
* Fixed issue where having certain characters in a path could prevent files from being found.
* Added Clear Texture Cache button in the addon preferences.
* Fixed issue with slowdown in the addon preferences when the texture cache is very large.
* The texture cache size is no longer automatically checked due to performance reasons.
* The addon will warn if the texture cache path is too long and may cause issues with path lengths.
* UV map names are now corrected automatically when when applying an MDF to a mesh.

### V0.47 - 3/8/2025
* Added error handling for unsupported DDS formats.
* Fixed Linux support.

### V0.46 - 3/8/2025
* Fixed some issues with texture conversion.
* Fixed issue related to tangents.
* Other minor bug fixes.

### V0.45 - 3/7/2025
* Added Tex conversion support for Monster Hunter Wilds. (Thanks to Asterisk for assisting)

IMPORTANT: Converted textures will not work unless they are contained inside a patch pak.

You will get a black screen if textures are included in a loose file mod.

You can create a patch pak by using the "Create Patch Pak" button in the RE MDF tab in the properties panel (press N if you don't see it).

**RE Asset Library is required. If it is not installed, the button will not show up.**

**Patch paks can be installed using Fluffy Manager.**

**The latest version of RE Framework is required for patch paks to load.**

* Minor bug fixes.

<details>
  <summary>Older Version Change Logs</summary>

### V0.44 - 2/28/2025
* Fixed issue where an error could occur when exporting a mesh from a blend file previously used to export for the MH Wilds beta.

### V0.43 - 2/28/2025
* Support for full release of Monster Hunter Wilds.
* Minor bug fixes.

### V0.42 - 2/16/2025
* Fixed issue where adding a preset material didn't work.
* Fixed issue where DD2 textures couldn't be converted.

### V0.41 - 2/14/2025
* Improved material importing for hair, skin, faces and more for MH Wilds.
* Improved automatic MDF detection for MH Wilds, more MDF files will be found automatically now.
* Minor bug fixes.

### V0.40 - 2/9/2025
* Added Linux support for converting MH Wilds textures.
* When selecting a mesh or MDF collection to export, a warning will appear if the collection is not a mesh or MDF collection.
* The file name will automatically change when the mesh or MDF collection is changed when exporting.
* Fixed issue where the selected game version would revert upon every export. (Again)
* Fixed error related to the console window on Linux.
* Fixed issue where metallic on ALBM textures didn't work.
* Fixed issue where the buttons for removing and reordering the chunk path list didn't work correctly.
* Reverted alpha clipping changes from previous update as it caused issues.

### V0.39 - 2/7/2025
* Fixed issue where the selected game version would revert to the last imported version upon every export.
* Fixed some material loading issues for SF6.
* Fixed MH Wilds player skin tone appearence.
* Fixed bounding box related error upon import.
* Added MH Wilds benchmark version import support.
* Reduced sheen values to make them appear closer to how they appear in game.
* Fixed issue where emission values were much too bright.
* Color values can now be manually set to values above 1.0.
* Removed alpha clipping from materials due to it causing issues with certain games.
* Fixed issue where unused images weren't cleared when using the "Clear Scene" import option.

### V0.38 - 1/18/2025
* Moved .mesh and .mdf2 import/export into "RE Mesh Editor" menu under File > Import/Export.
* MDF materials can now be renamed by changing the material name inside the parentheses. (The material name in the mdf settings will be updated upon export or reindexing). 
* When "Load MDF Material Data" is checked, the mesh and MDF collection will be grouped together in a collection.
* Only mesh or mdf collections will show when choosing a collection in the RE MDF tab.
* The mod directory in the RE MDF tab is now set automatically when exporting a mesh or mdf file.
* Fixed some issues with loading certain MH Wilds materials.
* Fixed issue where streaming textures would not be loaded when importing an RE7 RT mesh.

### V0.37 - 12/2/2024
* Added mesh import support for RE:Verse. 

### V0.36 - 11/28/2024
* Fixed issue with importing materials on Blender 4.3.

### V0.35 - 11/17/2024
* Default mesh import and export settings can now be configured in the addon preferences.
* Fixed some issues with MH Wilds color masks.
* Made adjustments to the MH Wilds skin shader mapping node. It's now easier to set specific skin tones.
* DD2 Shapekey vertex groups are no longer locked upon import.
* Fixed an export error that occurred when the exported armature was not inside the mesh collection.
* If an error occurs during material importing, it will notify you an error occurred.

### V0.34 - 11/14/2024
* Fixed issue that caused materials to fail to import when Blender's language was not set to English.

NOTE: For Monster Hunter Wilds, be sure to extract re_chunk_000.pak.sub_000.pak and merge it's contents with the extracted re_chunk_000.pak.

Textures will not be imported if the extracted chunk files are not merged.

### V0.33 - 11/13/2024
* Added support for Monster Hunter Wilds textures. (Thanks Ando)
NOTE: Conversion from DDS back to MH Wilds tex is not implemented yet.

UPDATE 3/7/2025: Tex conversion for MH Wilds is now supported.

### V0.32 - 11/12/2024
* Added support for secondary weights used by Dragon's Dogma 2. These weights are labeled with "SHAPEKEY_" and control the scaling of armor meshes.
* Fixed third person animation issue in Resident Evil 8 caused by incorrect symmetry indices.

### V0.31 - 11/6/2024
* Added support for Dragon's Dogma 2's new mesh version.
* Added streaming mesh support for DD2 and Street Fighter 6.
* Refactored streaming mesh implementation to fix some importing issues.

### V0.30 - 11/4/2024
* Added error messages for streaming file related issues.

### V0.29 - 11/3/2024
* Added Monster Hunter Wilds support.
  
~~MH Wilds textures are not supported yet due to file format changes. See the [issues page](https://github.com/NSACloud/RE-Mesh-Editor/issues/4) for details.~~

UPDATE: MH Wilds Textures are now supported.

* Added support for streamed meshes.
* Chunk paths are now saved automatically when importing meshes. This can be disabled in the addon preferences.
* Textures that were not imported appear red now instead of pink. This is for differentiating between textures that were once present but later moved.
* Added "Merge All New Armatures" import option. When multiple meshes are selected during import, using this option will merge all newly imported armatures into one.
* Minor bug fixes.

### V0.28 - 9/19/2024
* Fixed issue that caused Blender to crash when importing certain Dead Rising meshes.
* Minor bug fixes.
* Added license.

### V0.27 - 9/18/2024
* Added Dead Rising support.
* RE Toolbox is no longer a requirement.
* Disabled translucency shader temporarily since it doesn't work correctly.

### V0.26 - 9/14/2024
* Material importing has been improved. Imported materials now more closely resemble how they appear in game.
* MDF files will now be imported along with the mesh file, this can be disabled by unchecking "Load MDF Material Data" in the import options.
* Added drag and drop mesh importing - drag and drop a .mesh or .mdf2 file into the 3D view to import it. (Blender 4.1 and higher only)
  
https://github.com/user-attachments/assets/fa1ba74e-8a57-4115-b6cd-9585a2a92a21

* Added drag and drop tex conversion - drag and drop a .tex or .dds file into the 3D view to convert it. (Blender 4.1 and higher only)


https://github.com/user-attachments/assets/cf99e5f2-2aa6-4a6f-b170-1e5beb3bcec4

* Changes made to certain MDF material properties now reflect in Blender. MDF properties that have a wrench icon next to them are previewable.

https://github.com/user-attachments/assets/48be61bc-7c40-440f-881b-534809d3232f

* Blender 4.2 and above now cache textures as DDS files instead of TIF. This massively decreases material importing time. (Approximately 6x faster)
* Extended max vertex limit per sub mesh from 65535 to 4294967295.

* Added support for conversion of array textures. (Tex files that have multiple images inside them)
* The console is now opened when importing or exporting mesh files. This can be disabled in the addon preferences.
* When an exported mesh has errors that prevent export, a window will pop up explaining what's wrong with the mesh and how to fix it.
* NRRT/NRRC normal maps are now displayed correctly.
* Fixed issue where certain textures didn't convert correctly.
* Many minor bug fixes


### V0.25 - 7/26/2024
* Fixed issue where Blender could give out of bound vertex group indices and cause an error.

### V0.24 - 7/26/2024
* Fixed issue where BaseTwoSideEnable was missing in the UI for MDF flags.

### V0.23 - 7/22/2024
* Fixed mesh triangulation being disabled after previous update.

### V0.22 - 7/21/2024
* Fixed mesh export issue where if vertex weights were below a certain amount, the vertices would snap to the world origin in game.

### V0.21 - 7/12/2024
* Exported meshes are triangulated automatically. This does not alter meshes in the scene, it only affects the exported mesh file.

### V0.20 - 7/11/2024
* Fixed issue where MDFs using render targets (rtex) didn't export correctly.
* Fixed issue with mesh export that caused an error on specific system configurations. 

### V0.19 - 7/6/2024
* Fixed error with "Apply Active MDF" button.

### V0.18 - 7/5/2024
* Added support for Dragon's Dogma 2, Devil May Cry 5, Kunitsu-Gami, Resident Evil 2/3 Non RT, and Resident Evil 7 RT.
* Added support for GPU Buffer data used in DD2 MDF files.
* LOD collections are no longer created upon import if "Import All LODs" is unchecked.
* Fixed issue where the exported local bone matrix was incorrect.

### V0.17 - 6/16/2024
* Fixed issue where the preserve bone matrices export option didn't work. 

### V0.16 - 6/14/2024
* Fixed issue where low influence weights would be weighted incorrectly upon export.
* Fixed issue where some single weight meshes wouldn't import with weights

### V0.15 - 6/5/2024
* Fixed issue where exported mesh weights would be incorrect due to rounding issues.

### V0.14 - 5/28/2024
* Fixed issue with importing armatures from mesh files exported with Noesis.

### V0.13 - 5/27/2024
* Bone length of imported armatures is now determined by the area of bone weights. This makes areas with closely grouped bones such as faces look less cluttered. This is purely visual and does not affect export.
* Fixed issue where MDF exporting didn't work correctly for Street Fighter 6.
* Fixed issue where exporting an MDF for SF6 didn't check for material mismatches with the mesh.
* Added MMTRS data importing for MDF files. This is only used with SF6.
* Added more unknown values to the flags section of the MDF material flags.
* Fixed issue where texture files in the addon folder will be backed up when the addon is updated.

### V0.12 - 5/21/2024

* Fixed issue with importing SF6 meshes from the latest update.

### V0.11 - 5/20/2024

* Auto Solve Repeated UVs and Split Sharp Edges no longer modifies the meshes in the scene. The changes will only be applied on the exported mesh.
* Split Sharp Edges export option now requires RE Toolbox.
* Fixed issue where merging armatures didn't work correctly.
* Fixed issue where exporting an MDF with more than one mesh collection in a scene could cause warnings about mismatched materials.
* Fixed issue causing some meshes in RE3 to not be importable.


## V0.10 - 5/4/2024

* Fixed issue where exported tangents were incorrect.
* Fixed issue where an error message didn't show for having no meshes in the exported collection.

### V0.9 - 5/3/2024

* Fixed error that could occur when loose geometry was present when exporting.
* Rotation is now applied on imported objects when Y to Z up is enabled (Rotation is now (0,0,0) instead of (0,90,0). Previously imported meshes will still work correctly on export.
* Textures will no longer be repeatedly try to be loaded if an error occurs during attempting to import them.

### V0.8 - 4/29/2024

* Fixed issue causing UV2 to not export correctly.
* Fixed issue where split normals didn't export correctly.
* Fixed issue where a new collection would not be created when importing a mesh with the same name as an existing mesh.
* Fixed issue where a mesh collection would be assigned in the mesh export options even if it didn't exist.
* Replaced "Add Edge Split Modifier" with "Split Sharp Edges" in the mesh export options. Now disabled by default.
* Added tool tips to the chunk path buttons in the addon preferences.

NOTE: RE Toolbox has also been updated. Be sure to update it as well as it contains important fixes to "Solve Repeated UVs".

### V0.7 - 4/28/2024

* Fixed issue where group IDs would be lost upon export if "Import All LODs" was disabled.

### V0.6 - 4/28/2024

* Beta initial release.

 </details>


## Usage Guide

Video guide coming soon. Images will be added to the text guide once the video is done.

[Written Model Importing Guide (WIP)](https://github.com/Modding-Haven/REEngine-Modding-Documentation/wiki/Custom-Model-Importing-Guide)

Click the link above for a full written walkthrough of importing a custom model into an RE Engine game.

Note that the guide is currently a work in progress and is not yet complete.

For a short version of the guide, see below.

<details>
  <summary>TLDR Model Importing Guide</summary>


1. Find the mesh you want to replace inside the extracted .pak files.
2. Create a folder for your mod, then recreate the folder structure leading to the mesh file inside your mod folder starting from the "natives" folder.
3. Import the mesh file from File > Import > RE Mesh. Use the default import settings.
4. Import the model you want to replace it with.
5. Pose your model and rig it to the armature from the imported mesh file.
6. Separate your model by material (Ctrl P > Material) so that every mesh only has one material.
7. Move your meshes into the red .mesh collection either by dragging them onto it in the outliner, or pressing M (Move To Collection).
8. Rename your meshes to the same naming format as the imported mesh. (Example: Group_0_Sub_0__**MaterialName**)
9. Import the .mdf2 file that was alongside the .mesh file.
10. Rename the mdf material objects to your new material names in Object Properties > RE MDF Material Settings > Material Name
11. Change the texture bindings in the RE MDF Material settings to new paths for any textures you want to change.
12. Duplicate or add material presets if necessary. **NOTE: The names and amount of materials in the mdf must match the mesh file or you will get either an invisible model or a checkerboard texture in game.**
13. Open your textures in Photoshop or any image editor with full .dds saving support. (Not Gimp) Install the [Intel DDS Plugin](https://www.intel.com/content/www/us/en/developer/articles/tool/intel-texture-works-plugin.html) if using Photoshop.
14. Adjust the color channels of your textures so that they match the corresponding RE Engine texture's color channel layout.
15. Save edited textures to their own folder as a .dds file. For the compression settings, use BC7 sRGB if it's an albedo/color map or BC7 Linear if it's anything else.
16. In the RE MDF tab on the sidebar, set the Mod Directory to the natives\STM\ folder inside your mod folder.
17. Set the image directory to the directory containing the .dds files you saved.
18. Press "Convert Directory to Tex", then press "Copy Converted Tex Files". The tex files will be placed at whatever path you set them to be in the MDF material.
19. To test the textures, press "Apply Active MDF". Check the console (Window > Toggle System Console) and make sure that there's no warnings about the textures that you created.
20. (Optional) Add bones to the armature to be used as physics bones. Create chains using RE Chain Editor.
21. Export from File > Export > RE Mesh/MDF and put them in the mod folder at their original chunk path.
22. Install the mod folder using Fluffy Manager or use FirstNatives.

 </details>

## FAQ / Troubleshooting
* **The model has a checkerboard texture or is invisible in game.**

The material names or amount of materials in the mesh and MDF file do not match.
* **The game infinitely loads when the model is loaded.**
  
A texture is not at the path set in the MDF. Or you may be using an outdated .mdf2, .pfb, or .user file in your mod. Make sure that you extracted from the most recent patch pak file.
* **The model is stuck in a T pose**
  
The mesh is not rigged to the armature correctly. Check the the mesh moves along with the armature in pose mode. Also check that the armature is inside the mesh collection.
* **The material looks bugged in game**
  
You may be using an outdated .mdf2 file, be sure to extract from the latest patch pak as materials can change upon updates.

**For additional help, go here:**

[Monster Hunter Modding Discord](https://discord.gg/gJwMdhK)

[Modding Haven Discord](https://discord.gg/modding-haven-718224210270617702)

## Credits

- [Ando](https://github.com/Andoryuuta) - Solving the compression format for MH Wilds textures.
- [AsteriskAmpersand](https://github.com/AsteriskAmpersand) - Mesh format research and tex conversion code
- [AlphaZomega](https://github.com/alphazolam/) - RE Mesh 010 Template and Noesis plugin
- [CG Cookie](https://github.com/CGCookie) - Addon updater module
- [matyalatte](https://github.com/matyalatte/Texconv-Custom-DLL) - DirectX Texconv DLL library
- [PittRBM](https://x.com/wDnrbm) - NRRT texture node setup
