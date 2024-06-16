#Author: NSA Cloud
bl_info = {
	"name": "RE Mesh Editor",
	"author": "NSA Cloud",
	"version": (0, 17),
	"blender": (2, 93, 0),
	"location": "File > Import-Export",
	"description": "Import and export RE Engine Mesh files natively into Blender. No Noesis required.",
	"warning": "",
	"wiki_url": "https://github.com/NSACloud/RE-Mesh-Editor",
	"tracker_url": "https://github.com/NSACloud/RE-Mesh-Editor/issues",
	"category": "Import-Export"}

import bpy
from . import addon_updater_ops

import os
from bpy_extras.io_utils import ExportHelper,ImportHelper
from bpy.props import StringProperty, BoolProperty,IntProperty, EnumProperty, CollectionProperty,PointerProperty
from bpy.types import Operator, OperatorFileListElement,AddonPreferences
from rna_prop_ui import PropertyPanel
from .modules.gen_functions import textColors,raiseWarning,getFolderSize,formatByteSize
from .modules.blender_utils import operator_exists
#mesh
from .modules.mesh.file_re_mesh import meshFileVersionToGameNameDict
from .modules.mesh.blender_re_mesh import importREMeshFile,exportREMeshFile
#mdf
from .modules.mdf.blender_re_mdf import importMDFFile,exportMDFFile
from .modules.mdf.ui_re_mdf_panels import (
	OBJECT_PT_MDFObjectModePanel,
	OBJECT_PT_MDFMaterialPanel,
	OBJECT_PT_MDFFlagsPanel,
	OBJECT_PT_MDFMaterialPropertyListPanel,
	OBJECT_PT_MDFMaterialTextureBindingListPanel,
	OBJECT_PT_MDFMaterialMMTRSIndexListPanel,
	)
from .modules.mdf.re_mdf_propertyGroups import (
	MDFToolPanelPropertyGroup,
	MDFFlagsPropertyGroup,
	MDFPropPropertyGroup,
	MDFTextureBindingPropertyGroup,
	MDFMaterialPropertyGroup,
	MDFMMTRSIndexPropertyGroup,
	
	MESH_UL_MDFPropertyList,
	MESH_UL_MDFTextureBindingList,
	MESH_UL_MDFMMTRSDataList,
	
	
	
	)

from .modules.mdf.re_mdf_operators import (
	WM_OT_NewMDFHeader,
	WM_OT_ReindexMaterials,
	WM_OT_AddPresetMaterial,
	WM_OT_SavePreset,
	WM_OT_OpenPresetFolder,
	WM_OT_ApplyMDFToMeshCollection,

)
#tex
from .modules.tex.ui_re_tex_panels import (
	OBJECT_PT_TexConversionPanel,
	)

from .modules.tex.re_tex_operators import (
	WM_OT_ConvertFolderToTex,
	WM_OT_CopyConvertedTextures,

)

os.system("color")#Enable console colors

def showMessageBox(message = "", title = "Message Box", icon = 'INFO'):

	def draw(self, context):
		self.layout.label(text = message)

	bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

class WM_OT_OpenTextureCacheFolder(Operator):
	bl_label = "Open Texture Cache Folder"
	bl_description = "Opens the texture cache folder in File Explorer"
	bl_idname = "re_mesh.open_texture_cache_folder"

	def execute(self, context):
		try:
			os.startfile(bpy.context.preferences.addons[__name__].preferences.textureCachePath)
		except:
			pass
		return {'FINISHED'}
	

class ChunkPathPropertyGroup(bpy.types.PropertyGroup):
    gameName: EnumProperty(
		name="",
		description="Set the game",
		items= [ 
        ("MHRSB", "Monster Hunter Rise", ""),
		("RE8", "Resident Evil 8", ""),
		("RERT", "Resident Evil 2 / 3 Ray Tracing", ""),
		("RE4", "Resident Evil 4", ""),
		("SF6", "Street Fighter 6", ""),
		("DD2", "Dragon's Dogma 2", ""),
		]
    )
    path: StringProperty(
        name="Path",
		subtype="DIR_PATH",
		description = "Set the path to the natives\STM folder inside the extracted chunk files\nThis determines where textures will be imported from\n"+r"Example: I:\RE4_EXTRACT\re_chunk_000\natives\STM"
    )


class AddItemOperator(bpy.types.Operator):
	bl_idname = "re_mesh.chunk_path_list_add_item"
	bl_description = "Add path to the extracted chunk's natives\STM\ folder.\n"+r"Example: I:\RE4_EXTRACT\re_chunk_000\natives\STM"
	bl_label = "Add Path"
	

	def execute(self, context):
		# Add an item to the list
		context.preferences.addons[__name__].preferences.chunkPathList_items.add()
		return {'FINISHED'}

# Operator to remove an item from the list
class RemoveItemOperator(bpy.types.Operator):
	bl_idname = "re_mesh.chunk_path_list_remove_item"
	bl_description = "Remove chunk path from the list"
	bl_label = "Remove Selected Path"

	index: bpy.props.IntProperty()

	def execute(self, context):
        # Remove the item at the specified index from the list
		context.preferences.addons[__name__].preferences.chunkPathList_items.remove(self.index)
		return {'FINISHED'}

# Operator to reorder items in the list
class ReorderItemOperator(bpy.types.Operator):
	bl_idname = "re_mesh.chunk_path_list_reorder_item"
	bl_description = "Change the order in which files will be searched"
	bl_label = "Reorder Item"

	direction: bpy.props.EnumProperty(
		items=[('UP', "Up", ""), ('DOWN', "Down", "")],
		default='UP'
	)

	index: bpy.props.IntProperty()

	def execute(self, context):
		# Reorder the item in the list
		if self.direction == 'UP':
			context.preferences.addons[__name__].preferences.chunkPathList_items.move(self.index, self.index - 1)
		elif self.direction == 'DOWN':
			context.preferences.addons[__name__].preferences.chunkPathList_items.move(self.index, self.index + 1)
		return {'FINISHED'}

class MESH_UL_ChunkPathList(bpy.types.UIList):
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
		layout.prop(item,"gameName")
		layout.prop(item,"path")
class REMeshPreferences(AddonPreferences):
	bl_idname = __name__
	textureCachePath: StringProperty(
		name="Texture Cache Path",
		subtype='DIR_PATH',
		description = "Location to save converted textures",
		default = os.path.join(os.path.dirname(os.path.realpath(__file__)),"TextureCache")
	)
	chunkPathList_items: CollectionProperty(type=ChunkPathPropertyGroup)
	chunkPathList_index: IntProperty(name="")
	# addon updater preferences
	auto_check_update: bpy.props.BoolProperty(
	    name = "Auto-check for Update",
	    description = "If enabled, auto-check for updates using an interval",
	    default = False,
	)
	
	updater_interval_months: bpy.props.IntProperty(
	    name='Months',
	    description = "Number of months between checking for updates",
	    default=0,
	    min=0
	)
	updater_interval_days: bpy.props.IntProperty(
	    name='Days',
	    description = "Number of days between checking for updates",
	    default=7,
	    min=0,
	)
	updater_interval_hours: bpy.props.IntProperty(
	    name='Hours',
	    description = "Number of hours between checking for updates",
	    default=0,
	    min=0,
	    max=23
	)
	updater_interval_minutes: bpy.props.IntProperty(
	    name='Minutes',
	    description = "Number of minutes between checking for updates",
	    default=0,
	    min=0,
	    max=59
	)
	def draw(self, context):
		layout = self.layout
		split = layout.split(factor = .3)
		col1 = split.column()
		col2 = split.column()
		col3 = split.column()
		op = col2.operator(
        'wm.url_open',
        text='Donate on Ko-fi',
        icon='FUND'
        )
		layout.prop(self, "textureCachePath")
		layout.label(text=f"Folder Size: {formatByteSize(getFolderSize(self.textureCachePath))}")
		layout.operator("re_mesh.open_texture_cache_folder")
		
		op.url = 'https://ko-fi.com/nsacloud'
		
		layout.label(text = "Chunk Path List")
		layout.template_list("MESH_UL_ChunkPathList", "", self, "chunkPathList_items", self, "chunkPathList_index",rows = 3)
		row = layout.row(align=True)
		row.operator("re_mesh.chunk_path_list_add_item")
		row.operator("re_mesh.chunk_path_list_remove_item")

        # Reorder buttons
		row = layout.row(align=True)
		row.operator("re_mesh.chunk_path_list_reorder_item", text="Move Up").direction = 'UP'
		row.operator("re_mesh.chunk_path_list_reorder_item", text="Move Down").direction = 'DOWN'
		addon_updater_ops.update_settings_ui(self,context)
class ImportREMesh(Operator, ImportHelper):
	'''Import RE Mesh File'''
	bl_idname = "re_mesh.importfile"
	bl_label = "Import RE Mesh"
	bl_options = {'PRESET', "REGISTER", "UNDO"}
	files : CollectionProperty(
			name="File Path",
			type=OperatorFileListElement,
			)
	directory : StringProperty(
			subtype='DIR_PATH',
			)
	filename_ext = ".mesh.*"
	filter_glob: StringProperty(default="*.mesh.*", options={'HIDDEN'})
	clearScene : BoolProperty(
	   name = "Clear Scene",
	   description = "Clears all objects before importing the mesh file",
	   default = False)
	loadMaterials : BoolProperty(
	   name = "Load Materials",
	   description = "Load materials from the MDF2 file. This may increase the time the mesh takes to import",
	   default = True)
	
	materialLoadLevel: EnumProperty(
		name="",
		description="Choose which textures to import. Affects how quickly the material can be imported. Load Materials must be enabled for this option to do anything",
		default = "3",
		items=[ ("1", "Albedo Only (Fast)", ""),
				("2", "Main Textures (Slower)", "Loads Albedo, Normal, Roughness, Metallic, Alpha"),
				("3", "All Textures (Slowest)", "Loads all textures from the mdf, including ones not usable by Blender"),
			  ]
		)
	reloadCachedTextures : BoolProperty(
	   name = "Reload Cached Textures",
	   description = "Convert all textures again instead of reading from already converted textures. Use this if you make changes to textures and need to reload them",
	   default = False)
	mdfPath : StringProperty(
		name = "",
		description = "Manually set the path of the mdf2 file. The MDF is found automatically if this is left blank",
		default = "",
		)
	createCollections : BoolProperty(
	   name = "Create Collections",
	   description = "Create a collection for the mesh and for each LOD level. Note that collections are required for exporting LODs. Leaving this option enabled is recommended",
	   default = True)
	mergeArmature : StringProperty(
	   name = "",
	   description = "Merges the imported mesh's armature with the selected armature. Leave this blank if not merging with an armature",
	   default = "")
	importArmatureOnly : BoolProperty(
	   name = "Only Import Armature",
	   description = "Imports the armature of the mesh file, but not any of the meshes",
	   default = False)
	importAllLODs : BoolProperty(
	   name = "Import All LODs",
	   description = "Imports all LOD (level of detail) meshes. If unchecked, only the first LOD of each mesh will be imported",
	   default = False)
	rotate90 : BoolProperty(
	   name = "Y Up to Z Up",
	   description = "Rotate meshes and armatures by 90 degrees. Leaving this option enabled is recommended",
	   default = True)
	importBlendShapes : BoolProperty(
	   name = "Import Blend Shapes",
	   description = "Imports blend shapes as shape keys if present",
	   default = True)
	importShadowMeshes : BoolProperty(
	   name = "Import Shadow Cast Mesh",
	   description = "Imports shadow cast meshes if present",
	   default = True)
	mergeGroups : BoolProperty(
	   name = "Merge Mesh Groups",
	   description = "Merges all submeshes of a mesh group. IMPORTANT: MERGED MESHES CANNOT BE EXPORTED BACK TO MESH",
	   default = False)
	importOcclusionMeshes : BoolProperty(
	   name = "Import Occlusion Mesh",
	   description = "Imports occlusion meshes if present",
	   default = False)
	importBoundingBoxes : BoolProperty(
	   name = "Import Bounding Boxes",
	   description = "Import mesh and bone bounding boxes for debugging purposes",
	   default = False)
	
	

	def draw(self, context):
		layout = self.layout
		row = layout.row()
		row.prop(self, "clearScene")
		row.enabled = self.mergeArmature == ""
		layout.prop(self, "createCollections")
		layout.prop(self, "loadMaterials")
		layout.label(text = "Material Load Level")
		layout.prop(self, "materialLoadLevel")
		layout.prop(self, "reloadCachedTextures")
		layout.label(text = "MDF Manual Path")
		layout.prop(self, "mdfPath")
		layout.label(text = "Advanced Options")
		layout.prop(self, "importAllLODs")
		layout.label(text = "Merge With Armature")
		
		layout.prop_search(self, "mergeArmature",bpy.data,"armatures")
		layout.prop(self, "importArmatureOnly")
		layout.prop(self, "mergeGroups")
		#layout.prop(self, "importBlendShapes")
		layout.prop(self, "rotate90")
		#layout.prop(self, "importOcclusionMeshes")
		layout.prop(self, "importBoundingBoxes")
	def execute(self, context):
		try:
			os.makedirs(bpy.context.preferences.addons[__name__].preferences.textureCachePath,exist_ok = True)
		except:
			raiseWarning("Could not create texture cache directory at " + bpy.context.preferences.addons[__name__].preferences.textureCachePath)
		if self.mergeArmature:
			self.clearScene = False
		options = {"clearScene":self.clearScene,"createCollections":self.createCollections,"loadMaterials":self.loadMaterials,"materialLoadLevel":self.materialLoadLevel,"reloadCachedTextures":self.reloadCachedTextures,"mdfPath":self.mdfPath,"importAllLODs":self.importAllLODs,"importBlendShapes":self.importBlendShapes,"rotate90":self.rotate90,"mergeArmature":self.mergeArmature,"importArmatureOnly":self.importArmatureOnly,"mergeGroups":self.mergeGroups,"importShadowMeshes":self.importShadowMeshes,"importOcclusionMeshes":self.importOcclusionMeshes,"importBoundingBoxes":self.importBoundingBoxes}
		editorVersion = str(bl_info["version"][0])+"."+str(bl_info["version"][1])
		print(f"\n{textColors.BOLD}RE Mesh Editor V{editorVersion}{textColors.ENDC}")
		print(f"Blender Version {bpy.app.version[0]}.{bpy.app.version[1]}.{bpy.app.version[2]}")
		print("https://github.com/NSACloud/RE-Mesh-Editor")
		success = importREMeshFile(self.filepath,options)
		if success:
			return {"FINISHED"}
		else:
			self.report({"INFO"},"Failed to import RE Mesh. Make sure the mesh file is imported.")
			return {"CANCELLED"}
		
class ExportREMesh(Operator, ExportHelper):
	'''Export RE Mesh File'''
	bl_idname = "re_mesh.exportfile"
	bl_label = "Export RE Mesh"
	bl_options = {'PRESET'}
	
	filter_glob: StringProperty(default="*.mesh*", options={'HIDDEN'})
	
	filename_ext: EnumProperty(
		name="",
		description="Set which game to export the mesh for",
		items= [ 
				(".2109148288", "Monster Hunter Rise", "Monster Hunter Rise"),
				(".2101050001", "Resident Evil 8", "Resident Evil 8"),
				(".2109108288", "Resident Evil 2 / 3 Ray Tracing", "Resident Evil 2/3 Ray Tracing Version"),
			    (".221108797", "Resident Evil 4", "Resident Evil 4"),
				(".230110883", "Street Fighter 6", "Street Fighter 6"),
				(".231011879", "Dragon's Dogma 2", "Dragon's Dogma 2"),
			   ]
		)
	targetCollection: bpy.props.StringProperty(
		name="",
		description = "Set the collection containing the meshes to be exported",
		
		)
	selectedOnly : BoolProperty(
	   name = "Selected Objects Only",
	   description = "Limit export to selected objects",
	   default = False)

	
	exportAllLODs : BoolProperty(
	   name = "Export All LODs",
	   description = "Export all LODs. If disabled, only LOD0 will be exported. Note that LODs meshes must be grouped inside a collection for each level and that collection must be contained in another collection. See a mesh with LODs imported for reference on how it should look. A target collection must also be set",
	   default = True)
	exportBlendShapes : BoolProperty(
	   name = "Export Blend Shapes",
	   description = "Exports blend shapes from mesh if present",
	   default = True)
	rotate90 : BoolProperty(
	   name = "Convert Z Up To Y Up",
	   description = "Rotates objects 90 degrees for export. Leaving this option enabled is recommended",
	   default = True)
	autoSolveRepeatedUVs : BoolProperty(
	   name = "Auto Solve Repeated UVs",
	   description = "(RE Toolbox Required)\nSplits connected UV islands if present. The mesh format does not allow for multiple uvs assigned to a vertex.\nNOTE: This will modify the exported mesh. If auto smooth is disabled on the mesh, the normals may change",
	   default = True)
	preserveSharpEdges : BoolProperty(
	   name = "Split Sharp Edges",
	   description = "(RE Toolbox Required)\nEdge splits all edges marked as sharp to preserve them on the exported mesh.\nNOTE: This will modify the exported mesh",
	   default = False)
	useBlenderMaterialName : BoolProperty(
	   name = "Use Blender Material Names",
	   description = "If left unchecked, the exporter will get the material names to be used from the end of each object name. For example, if a mesh is named LOD_0_Group_0_Sub_0__Shirts_Mat, the material name is Shirts_Mat. If this option is enabled, the material name will instead be taken from the first material assigned to the object",
	   default = False)
	preserveBoneMatrices : BoolProperty(
	   name = "Preserve Bone Matrices",
	   description = "Export using the original matrices of the imported bones. Note that this option only applies armatures imported with this addon. Any newly added bones will have new matrices calculated",
	   default = False)
	exportBoundingBoxes : BoolProperty(
	   name = "Export Bounding Boxes",
	   description = "Exports the original bounding boxes from the \"Import Bounding Boxes\" import option. New bounding boxes will be generated for any bones that do not have them",
	   default = False)
	def invoke(self, context, event):
		if self.targetCollection == "":
			prevCollection = context.scene.get("REMeshLastImportedCollection","")
			if prevCollection in bpy.data.collections:
				self.targetCollection = prevCollection
			if ".mesh" in prevCollection:#Remove blender suffix after .mesh if it exists
				self.filepath = prevCollection.split(".mesh")[0]+".mesh" + self.filename_ext
		if context.scene.get("REMeshLastImportedMeshVersion",0) in meshFileVersionToGameNameDict:
			self.filename_ext = "."+str(context.scene["REMeshLastImportedMeshVersion"])
		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}
	def draw(self, context):
		layout = self.layout
		layout.label(text = "Mesh Version:")
		layout.prop(self, "filename_ext")
		layout.label(text = "Target Collection:")
		layout.prop_search(self, "targetCollection",bpy.data,"collections",icon = "COLLECTION_COLOR_01")
		layout.prop(self, "selectedOnly")
		layout.label(text = "Advanced Options")
		layout.prop(self, "exportAllLODs")
		#layout.prop(self, "exportBlendShapes")
		hasREToolbox = hasattr(bpy.types, "OBJECT_PT_re_tools_quick_export_panel")
		row = layout.row()
		row.enabled = hasREToolbox
		row.prop(self,"autoSolveRepeatedUVs")
		row2 = layout.row()
		row2.enabled = hasREToolbox
		row2.prop(self,"preserveSharpEdges")
		

		layout.prop(self, "rotate90")
		layout.prop(self, "useBlenderMaterialName")
		layout.prop(self, "preserveBoneMatrices")
		layout.prop(self, "exportBoundingBoxes")
	
	def execute(self, context):
		options = {"targetCollection":self.targetCollection,"selectedOnly":self.selectedOnly,"exportAllLODs":self.exportAllLODs,"exportBlendShapes":self.exportBlendShapes,"rotate90":self.rotate90,"useBlenderMaterialName":self.useBlenderMaterialName,"preserveBoneMatrices":self.preserveBoneMatrices,"exportBoundingBoxes":self.exportBoundingBoxes,"autoSolveRepeatedUVs":self.autoSolveRepeatedUVs,"preserveSharpEdges":self.preserveSharpEdges}
		try:
			meshVersion = int(os.path.splitext(self.filepath)[1].replace(".",""))
		except:
			self.report({"INFO"},"Mesh file path is missing number extension. Cannot export.")
			return{"CANCELLED"}
		editorVersion = str(bl_info["version"][0])+"."+str(bl_info["version"][1])
		print(f"\n{textColors.BOLD}RE Mesh Editor V{editorVersion}{textColors.ENDC}")
		print(f"Blender Version {bpy.app.version[0]}.{bpy.app.version[1]}.{bpy.app.version[2]}")
		print("https://github.com/NSACloud/RE-Mesh-Editor")
		
		
		success = exportREMeshFile(self.filepath,options)
		if success:
			self.report({"INFO"},"Exported RE Mesh successfully.")
			if hasattr(bpy.types, "OBJECT_PT_re_tools_quick_export_panel"):
				if not any(item.path == self.filepath for item in bpy.context.scene.re_toolbox_toolpanel.batchExportList_items):
					newExportItem = bpy.context.scene.re_toolbox_toolpanel.batchExportList_items.add()
					newExportItem.fileType = "MESH"
					newExportItem.path = self.filepath
					newExportItem.meshCollection = self.targetCollection
					newExportItem.exportAllLODs = self.exportAllLODs
					newExportItem.preserveSharpEdges = self.preserveSharpEdges
					newExportItem.rotate90 = self.rotate90
					newExportItem.exportBlendShapes = self.exportBlendShapes
					newExportItem.useBlenderMaterialName = self.useBlenderMaterialName
					newExportItem.preserveBoneMatrices = self.preserveBoneMatrices
					newExportItem.exportBoundingBoxes = self.exportBoundingBoxes
					print("Added path to RE Toolbox Batch Export list.")
		else:
			self.report({"INFO"},"RE Mesh export failed. See Window > Toggle System Console for info on how to fix it.")
		return {"FINISHED"}

class ImportREMDF(bpy.types.Operator, ImportHelper):
	'''Import RE Engine MDF File'''
	bl_idname = "re_mdf.importfile"
	bl_label = "Import RE MDF"
	bl_options = {'PRESET', "REGISTER", "UNDO"}
	files : CollectionProperty(
			name="File Path",
			type=OperatorFileListElement,
			)
	directory : StringProperty(
			subtype='DIR_PATH',
			)
	filename_ext = ".mdf.*"
	filter_glob: StringProperty(default="*.mdf2.*", options={'HIDDEN'})

	def execute(self, context):
		editorVersion = str(bl_info["version"][0])+"."+str(bl_info["version"][1])
		print(f"\n{textColors.BOLD}RE Mesh Editor V{editorVersion}{textColors.ENDC}")
		print(f"Blender Version {bpy.app.version[0]}.{bpy.app.version[1]}.{bpy.app.version[2]}")
		print("https://github.com/NSACloud/RE-Mesh-Editor")
		success = importMDFFile(self.filepath)
		if success:
			return {"FINISHED"}
		else:
			self.report({"INFO"},"Failed to import RE MDF.")
			return {"CANCELLED"}
supportedMDFVersions = set([23,19,21,32,31,40])		
class ExportREMDF(bpy.types.Operator, ExportHelper):
	'''Export RE Engine MDF File'''
	bl_idname = "re_mdf.exportfile"
	bl_label = "Export RE MDF"
	bl_options = {'PRESET'}
	filename_ext: EnumProperty(
		name="",
		description="Set which game to export the MDF for",
		items=[ 
				(".23", "Monster Hunter Rise", ""),
				(".19", "Resident Evil 8", ""),
				(".21", "Resident Evil 2 / 3 Ray Tracing", ""),
				(".32", "Resident Evil 4", ""),
				(".31", "Street Fighter 6", ""),
				(".40", "Dragon's Dogma 2", ""),
			  ]
		)
	targetCollection : StringProperty(
	   name = "",
	   description = "Set the MDF collection to be exported",
	   default = "")
	filter_glob: StringProperty(default="*.mdf2*", options={'HIDDEN'})
	def invoke(self, context, event):
		if bpy.data.collections.get(self.targetCollection,None) == None:
			if bpy.data.collections.get(bpy.context.scene.re_mdf_toolpanel.mdfCollection):
				self.targetCollection = bpy.context.scene.re_mdf_toolpanel.mdfCollection
				if self.targetCollection.endswith(".mdf2"):
					self.filepath = self.targetCollection + self.filename_ext
			self.filename_ext = bpy.context.scene.re_mdf_toolpanel.activeGame
		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}
	
	def draw(self, context):
		layout = self.layout
		layout.label(text = "MDF Version:")
		layout.prop(self,"filename_ext")
		layout.label(text = "MDF Collection:")
		layout.prop_search(self, "targetCollection",bpy.data,"collections",icon = "COLLECTION_COLOR_05")
	def execute(self, context):
		editorVersion = str(bl_info["version"][0])+"."+str(bl_info["version"][1])
		print(f"\n{textColors.BOLD}RE MDF Editor V{editorVersion}{textColors.ENDC}")
		print(f"Blender Version {bpy.app.version[0]}.{bpy.app.version[1]}.{bpy.app.version[2]}")
		print("https://github.com/NSACloud/RE-Mesh-Editor")
		success = exportMDFFile(self.filepath,self.targetCollection)
		if success:
			self.report({"INFO"},"Exported RE MDF successfully.")
			
			#Add batch export entry to RE Toolbox if it doesn't already have one
			if hasattr(bpy.types, "OBJECT_PT_re_tools_quick_export_panel"):
				if not any(item.path == self.filepath for item in bpy.context.scene.re_toolbox_toolpanel.batchExportList_items):
					newExportItem = bpy.context.scene.re_toolbox_toolpanel.batchExportList_items.add()
					newExportItem.fileType = "MDF"
					newExportItem.path = self.filepath
					newExportItem.mdfCollection = self.targetCollection
					print("Added path to RE Toolbox Batch Export list.")
			return {"FINISHED"}
		else:
			self.report({"INFO"},"Failed to export RE MDF. Check Window > Toggle System Console for details.")
			return {"CANCELLED"}

# Registration
classes = [
	#preferences
	ChunkPathPropertyGroup,
	AddItemOperator,
	RemoveItemOperator,
	ReorderItemOperator,
	MESH_UL_ChunkPathList,
	REMeshPreferences,
	#mesh
	
	ImportREMesh,
	ExportREMesh,
	WM_OT_OpenTextureCacheFolder,
	#mdf
	ImportREMDF,
	ExportREMDF,
	#property groups
	MDFMMTRSIndexPropertyGroup,
	MDFFlagsPropertyGroup,
	MDFToolPanelPropertyGroup,
	MDFPropPropertyGroup,
	MDFTextureBindingPropertyGroup,
	MDFMaterialPropertyGroup,
	
	MESH_UL_MDFPropertyList,
	MESH_UL_MDFTextureBindingList,
	MESH_UL_MDFMMTRSDataList,
	
	#ui panels
	OBJECT_PT_MDFObjectModePanel,
	OBJECT_PT_MDFMaterialPanel,
	OBJECT_PT_MDFFlagsPanel,
	OBJECT_PT_MDFMaterialTextureBindingListPanel,
	OBJECT_PT_MDFMaterialPropertyListPanel,
	OBJECT_PT_MDFMaterialMMTRSIndexListPanel,
	
	#operators
	WM_OT_NewMDFHeader,
	WM_OT_ReindexMaterials,
	WM_OT_AddPresetMaterial,
	WM_OT_SavePreset,
	WM_OT_OpenPresetFolder,
	WM_OT_ApplyMDFToMeshCollection,
	
	#tex
	#operators
	WM_OT_ConvertFolderToTex,
	WM_OT_CopyConvertedTextures,
	#ui panels
	OBJECT_PT_TexConversionPanel,
	
	
	]


class GU_PT_collection_custom_properties(bpy.types.Panel, PropertyPanel): #For adding custom properties to collections, fixed on 3.3 and up so not needed there
    _context_path = "collection"
    _property_type = bpy.types.Collection
    bl_label = "Custom Properties"
    bl_idname = "GU_PT_collection_custom_properties"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "collection"
	
def re_mesh_import(self, context):
	self.layout.operator(ImportREMesh.bl_idname, text="RE Mesh (.mesh.x)")
	
def re_mesh_export(self, context):
	self.layout.operator(ExportREMesh.bl_idname, text="RE Mesh (.mesh.x)")

def re_mdf_import(self, context):
	self.layout.operator(ImportREMDF.bl_idname, text="RE MDF (.mdf2.x)")
	
def re_mdf_export(self, context):
	self.layout.operator(ExportREMDF.bl_idname, text="RE MDF (.mdf2.x)")

def register():
	addon_updater_ops.register(bl_info)
	for classEntry in classes:
		bpy.utils.register_class(classEntry)
	if (3, 3, 0) > bpy.app.version:
		bpy.utils.register_class(GU_PT_collection_custom_properties)
	
	
	#REGISTER PROPERTY GROUP PROPERTIES
	bpy.types.Scene.re_mdf_toolpanel = PointerProperty(type=MDFToolPanelPropertyGroup)
	bpy.types.Object.re_mdf_material = PointerProperty(type=MDFMaterialPropertyGroup)
	
	bpy.types.TOPBAR_MT_file_import.append(re_mesh_import)
	bpy.types.TOPBAR_MT_file_export.append(re_mesh_export)
	bpy.types.TOPBAR_MT_file_import.append(re_mdf_import)
	bpy.types.TOPBAR_MT_file_export.append(re_mdf_export)
	
def unregister():
	addon_updater_ops.unregister()
	for classEntry in classes:
		bpy.utils.unregister_class(classEntry)
	
	if (3, 3, 0) > bpy.app.version:
		bpy.utils.unregister_class(GU_PT_collection_custom_properties)
	bpy.types.TOPBAR_MT_file_import.remove(re_mesh_import)
	bpy.types.TOPBAR_MT_file_export.remove(re_mesh_export)
	bpy.types.TOPBAR_MT_file_import.remove(re_mdf_import)
	bpy.types.TOPBAR_MT_file_export.remove(re_mdf_export)
if __name__ == '__main__':
	register()
	