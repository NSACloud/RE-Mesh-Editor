#Author: NSA Cloud
bl_info = {
	"name": "RE Mesh Editor",
	"author": "NSA Cloud",
	"version": (0, 59),
	"blender": (3, 3, 0),
	"location": "File > Import-Export",
	"description": "Import and export RE Engine Mesh files natively into Blender. No Noesis required.",
	"warning": "",
	"wiki_url": "https://github.com/NSACloud/RE-Mesh-Editor",
	"tracker_url": "https://github.com/NSACloud/RE-Mesh-Editor/issues",
	"category": "Import-Export"}

import bpy
from . import addon_updater_ops
from datetime import datetime
import os
from bpy_extras.io_utils import ExportHelper,ImportHelper
from bpy.props import StringProperty, BoolProperty,IntProperty, EnumProperty, CollectionProperty,PointerProperty
from bpy.types import Operator, OperatorFileListElement,AddonPreferences
from rna_prop_ui import PropertyPanel
from .modules.gen_functions import textColors,raiseWarning,getFolderSize,formatByteSize,splitNativesPath
from .modules.blender_utils import operator_exists
#mesh
from .modules.mesh.file_re_mesh import meshFileVersionToGameNameDict
from .modules.mesh.blender_re_mesh import importREMeshFile,exportREMeshFile
from .modules.mesh.re_mesh_propertyGroups import (
	ExporterNodePropertyGroup,
	MESH_UL_REExporterList
	)
from .modules.mesh.re_mesh_operators import (
	WM_OT_DeleteLoose,
	WM_OT_RenameMeshToREFormat,
	WM_OT_RemoveZeroWeightVertexGroups,
	WM_OT_LimitTotalNormalizeAll,
	WM_OT_CreateMeshCollection,
	WM_OT_REBatchExporter,

)
from .modules.mesh.ui_re_mesh_panels import (
	OBJECT_PT_MeshObjectModePanel,
	OBJECT_PT_MeshArmatureToolsPanel,
	OBJECT_PT_REAssetExtensionPanel,
	)


#mdf
from.modules.mdf.file_re_mdf import gameNameMDFVersionDict
from .modules.mdf.blender_re_mdf import importMDFFile,exportMDFFile
from .modules.mdf.ui_re_mdf_panels import (
	OBJECT_PT_MDFObjectModePanel,
	OBJECT_PT_MDFMaterialPresetPanel,
	OBJECT_PT_MDFMaterialPreviewPanel,
	OBJECT_PT_MDFMaterialPanel,
	OBJECT_PT_MDFFlagsPanel,
	OBJECT_PT_MDFMaterialPropertyListPanel,
	OBJECT_PT_MDFMaterialTextureBindingListPanel,
	OBJECT_PT_MDFMaterialMMTRSIndexListPanel,
	OBJECT_PT_MDFMaterialGPBFDataListPanel,
	OBJECT_PT_MDFMaterialLoadSettingsPanel,
	)
from .modules.mdf.re_mdf_propertyGroups import (
	MDFToolPanelPropertyGroup,
	MDFFlagsPropertyGroup,
	MDFPropPropertyGroup,
	MDFTextureBindingPropertyGroup,
	MDFMaterialPropertyGroup,
	MDFMMTRSIndexPropertyGroup,
	MDFGPBFDataPropertyGroup,
	
	MESH_UL_MDFPropertyList,
	MESH_UL_MDFTextureBindingList,
	MESH_UL_MDFMMTRSDataList,
	MESH_UL_MDFGPBFDataList,
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
from .modules.tex.file_re_tex import gameNameToTexVersionDict

from .modules.tex.ui_re_tex_panels import (
	OBJECT_PT_TexConversionPanel,
	)

from .modules.tex.re_tex_operators import (
	WM_OT_ConvertFolderToTex,
	WM_OT_CopyConvertedTextures,
	WM_OT_ConvertDDSTexFile,

)

from .modules.mesh.re_mesh_export_errors import  (
	REMeshErrorEntry,
	MESH_UL_REMeshErrorList,
	WM_OT_ShowREMeshErrorWindow,
	)
#fbxskel
from .modules.fbxskel.blender_re_fbxskel import importFBXSkelFile,exportFBXSkelFile
from .modules.fbxskel.re_fbxskel_operators import (
	WM_OT_LinkArmatureBones,
	WM_OT_ClearBoneLinkages
	)
from .modules.fbxskel.re_fbxskel_propertyGroups import (
	ToggleStringPropertyGroup,
	FBXSKEL_UL_ObjectCheckList
	)
os.system("color")#Enable console colors


#Used to circumvent the issue of properties not being able to used as defaults for other properties at startup
def setMeshImportDefaults(self):
	self.clearScene = bpy.context.preferences.addons[__name__].preferences.default_clearScene
	self.loadMaterials = bpy.context.preferences.addons[__name__].preferences.default_loadMaterials
	self.loadMDFData = bpy.context.preferences.addons[__name__].preferences.default_loadMDFData
	self.loadUnusedTextures = bpy.context.preferences.addons[__name__].preferences.default_loadUnusedTextures
	self.loadUnusedProps = bpy.context.preferences.addons[__name__].preferences.default_loadUnusedProps
	self.useBackfaceCulling = bpy.context.preferences.addons[__name__].preferences.default_useBackfaceCulling
	self.reloadCachedTextures = bpy.context.preferences.addons[__name__].preferences.default_reloadCachedTextures
	self.createCollections = bpy.context.preferences.addons[__name__].preferences.default_createCollections
	self.importArmatureOnly = bpy.context.preferences.addons[__name__].preferences.default_importArmatureOnly
	self.importAllLODs = bpy.context.preferences.addons[__name__].preferences.default_importAllLODs
	self.rotate90 = bpy.context.preferences.addons[__name__].preferences.default_rotate90
	self.importBlendShapes = bpy.context.preferences.addons[__name__].preferences.default_importBlendShapes
	self.importShadowMeshes = bpy.context.preferences.addons[__name__].preferences.default_importShadowMeshes
	self.mergeGroups = bpy.context.preferences.addons[__name__].preferences.default_mergeGroups
	self.importOcclusionMeshes = bpy.context.preferences.addons[__name__].preferences.default_importOcclusionMeshes
	self.importBoundingBoxes = bpy.context.preferences.addons[__name__].preferences.default_importBoundingBoxes
	#print("RE Mesh Editor: Loaded Default Import Settings")
	
def setMeshExportDefaults(self):
	self.selectedOnly = bpy.context.preferences.addons[__name__].preferences.default_selectedOnly
	self.exportAllLODs = bpy.context.preferences.addons[__name__].preferences.default_exportAllLODs
	self.exportBlendShapes = bpy.context.preferences.addons[__name__].preferences.default_exportBlendShapes
	self.rotate90 = bpy.context.preferences.addons[__name__].preferences.default_rotate90export
	self.autoSolveRepeatedUVs = bpy.context.preferences.addons[__name__].preferences.default_autoSolveRepeatedUVs
	self.preserveSharpEdges = bpy.context.preferences.addons[__name__].preferences.default_preserveSharpEdges
	self.useBlenderMaterialName = bpy.context.preferences.addons[__name__].preferences.default_useBlenderMaterialName
	self.preserveBoneMatrices = bpy.context.preferences.addons[__name__].preferences.default_preserveBoneMatrices
	self.exportBoundingBoxes = bpy.context.preferences.addons[__name__].preferences.default_exportBoundingBoxes
	#print("RE Mesh Editor: Loaded Default Export Settings")
	

def showMessageBox(message = "", title = "Message Box", icon = 'INFO'):

	def draw(self, context):
		self.layout.label(text = message)

	bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

def setModDirectoryFromFilePath(filePath):
	if "re_chunk_000" not in filePath and "re_dlc_stm" not in filePath and "natives" in filePath:
		try:
			bpy.context.scene.re_mdf_toolpanel.modDirectory = splitNativesPath(filePath)[0]
			print(f"Set mod directory to {bpy.context.scene.re_mdf_toolpanel.modDirectory}")
		except:
			print("ERROR: Failed to set mod directory, exported file path probably does not follow the chunk naming scheme.")
class WM_OT_OpenTextureCacheFolder(Operator):
	bl_label = "Open Texture Cache Folder"
	bl_description = "Opens the texture cache folder in File Explorer"
	bl_idname = "re_mesh.open_texture_cache_folder"

	def execute(self, context):
		try:
			os.startfile(bpy.path.abspath(bpy.context.preferences.addons[__name__].preferences.textureCachePath))
		except:
			pass
		checkTextureCacheSize()
		return {'FINISHED'}

class WM_OT_CheckTextureCacheSize(Operator):
	bl_label = "Check Cache Size"
	bl_description = "Shows the current size of the texture cache folder."
	bl_idname = "re_mesh.check_texture_cache_size"

	def execute(self, context):
		checkTextureCacheSize()
		return {'FINISHED'} 

class WM_OT_ClearTextureCacheFolder(Operator):
	bl_label = "Clear Texture Cache Folder"
	bl_description = "Deletes all cached converted textures. Note that any saved blend files will lose their textures if the cache is cleared."
	bl_idname = "re_mesh.clear_texture_cache_folder"
	def draw(self,context):
		layout = self.layout
		layout.label(text="Are you sure you want to delete all cached textures?")
		layout.label(text=f"Directory:")
		layout.label(text=f"{bpy.path.abspath(bpy.context.preferences.addons[__name__].preferences.textureCachePath)}")
	def invoke(self,context,event):
		checkTextureCacheSize()
		return context.window_manager.invoke_props_dialog(self,width = 400)
	def execute(self, context):
		imageExtensions = (".dds",".png",".tga",".tif",".tiff") 
		deletionList = []
		#I could do shutil.rmtree but deleting everything from a directory could be potentially dangerous if the path is somehow wrong.
		#So in order to minimize potential damage, it loops through and only deletes image files in the directory.
		for root, dirs, files in os.walk(bpy.path.abspath(bpy.context.preferences.addons[__name__].preferences.textureCachePath)):
			for file in files:
				if file.lower().endswith(imageExtensions):
					deletionList.append(os.path.join(root,file))
		
		print(f"Deleting {len(deletionList)} image files...")
		for path in deletionList:
			try:
				os.remove(path)
			except Exception as err:
				print(f"Failed to delete {path} - {str(err)}")
		self.report({"INFO"},"Cleared texture cache.")
		checkTextureCacheSize()
		return {'FINISHED'}

class ChunkPathPropertyGroup(bpy.types.PropertyGroup):
    gameName: EnumProperty(
		name="",
		description="Set the game",
		items= [ 
		("DMC5", "Devil May Cry 5", ""),
		("RE2", "Resident Evil 2", ""),
		("RE3", "Resident Evil 3", ""),
		("RE8", "Resident Evil 8", ""),	
		("RE2RT", "Resident Evil 2 Ray Tracing", ""),
		("RE3RT", "Resident Evil 3 Ray Tracing", ""),
		("RE7RT", "Resident Evil 7 Ray Tracing", ""),
		("MHRSB", "Monster Hunter Rise", ""),
		("SF6", "Street Fighter 6", ""),
		("RE4", "Resident Evil 4", ""),
		("DD2", "Dragon's Dogma 2", ""),
		("KG", "Kunitsu-Gami", ""),
		("DR", "Dead Rising", ""),
		("ONI2", "Onimusha 2", ""),
		("MHWILDS", "Monster Hunter Wilds", ""),
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

	def execute(self, context):
		
		chunkList = bpy.context.preferences.addons[__name__].preferences.chunkPathList_items
		index = bpy.context.preferences.addons[__name__].preferences.chunkPathList_index
		chunkList.remove(index)
		bpy.context.preferences.addons[__name__].preferences.chunkPathList_index = min(max(0, index - 1), len(chunkList) - 1)
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

	def move_index(self):
		index = bpy.context.preferences.addons[__name__].preferences.chunkPathList_index
		list_length = len(bpy.context.preferences.addons[__name__].preferences.chunkPathList_items)
		new_index = index + (-1 if self.direction == 'UP' else 1)
		bpy.context.preferences.addons[__name__].preferences.chunkPathList_index = max(0,min(new_index,list_length))
		
	def execute(self, context):
		chunkList = bpy.context.preferences.addons[__name__].preferences.chunkPathList_items
		index = bpy.context.preferences.addons[__name__].preferences.chunkPathList_index
		
		neighbor = index + (-1 if self.direction == 'UP' else 1)
		chunkList.move(neighbor, index)
		self.move_index()
		return {'FINISHED'}

class MESH_UL_ChunkPathList(bpy.types.UIList):
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
		layout.prop(item,"gameName")
		layout.prop(item,"path")

def checkTextureCacheSize():
	try:
		bpy.context.preferences.addons[__name__].preferences.textureCacheSizeString = formatByteSize(getFolderSize(bpy.path.abspath(bpy.context.preferences.addons[__name__].preferences.textureCachePath)))
		timestamp = str(datetime.now()).split(".")[0]
		bpy.context.preferences.addons[__name__].preferences.textureCacheCheckDate = timestamp
	except:
		pass
	
class REMeshPreferences(AddonPreferences):
	bl_idname = __name__
	
	dragDropImportOptions: BoolProperty(
		name="Show Drag and Drop Import Options (Blender 4.1 or higher)",
		description = "Show import options when dragging a mesh or mdf file into the 3D View.\nIf this is disabled, the default import options will be used.\nDrag and drop importing is only supported on Blender 4.1 or higher",
		default = False if bpy.app.version < (4,1,0) else True
	)
	showConsole: BoolProperty(
		name="Show Console During Import/Export",
		description = "When importing or exporting a file, the console will be opened so that progress can be viewed.\nNote that if the console is already opened before import or export, it will be closed instead.\n This is a limitation of Blender, there's no way to get the active state of the console window.",
		default = True
	)
	textureCachePath: StringProperty(
		name="Texture Cache Path",
		subtype='DIR_PATH',
		description = "Location to save converted textures",
		default = os.path.join(os.path.dirname(os.path.realpath(__file__)),"TextureCache")
	)
	useDDS: BoolProperty(
		name="Use DDS Textures (Blender 4.2 or higher)",
		description = "Use DDS textures instead of converting to TIF.\nThis greatly improves mesh import speed but is only usable on Blender 4.2 or higher.\nIf the Blender version is less than 4.2, this option will do nothing",
		default = False if bpy.app.version < (4,2,0) else True
	)
	
	saveChunkPaths: BoolProperty(
		name="Save Chunk Paths Automatically",
		description = "If a chunk path is detected when a mesh is imported, add it to the chunk path list automatically",
		default = True
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
	#Internal properties for grouping import/export settings
	showImportOptions : BoolProperty(
	   name = "Show Default Import Settings",
	   default = False)
	showExportOptions : BoolProperty(
	   name = "Show Default Export Settings",
	   default = False)
	
	textureCacheSizeString: bpy.props.StringProperty(
	    default="",
	)
	textureCacheCheckDate: bpy.props.StringProperty(
	    default="",
	)
	
	#Default import settings
	
	default_clearScene : BoolProperty(
	   name = "Clear Scene",
	   description = "Clears all objects before importing the mesh file",
	   default = False)
	default_loadMaterials : BoolProperty(
	   name = "Load Materials",
	   description = "Load materials from the MDF2 file. This may increase the time the mesh takes to import",
	   default = True)
	
	default_loadMDFData : BoolProperty(
	   name = "Load MDF Material Data",
	   description = "Imports the MDF materials as objects inside a collection in the outliner.\nYou can make changes to MDF materials by selecting the Material objects in the outliner.\nUnder the Object Properties tab (orange square), there's a panel called \"RE MDF Material Settings\".\nMake any changes to MDF materials there.\nIf you're not modding an RE Engine game, you can uncheck this option since it won't be needed",
	   default = True)
	
	default_loadUnusedTextures : BoolProperty(
	   name = "Load Unused Textures",
	   description = "Loads textures that have no function assigned to them in the material shader graph.\nLeaving this disabled will make materials load faster.\nOnly enable this if you plan on editing the material shader graph",
	   default = False)
	default_loadUnusedProps : BoolProperty(
	   name = "Load Unused Material Properties",
	   description = "Loads material properties that have no function assigned to them in the material shader graph.\nLeaving this disabled will make materials load faster.\nOnly enable this if you plan on editing the material shader graph",
	   default = False)
	default_useBackfaceCulling : BoolProperty(
	   name = "Use Backface Culling",
	   description = "Enables backface culling on materials. May improve Blender's performance on high poly meshes.\nBackface culling will only be enabled on materials without the two sided flag",
	   default = False)

	default_reloadCachedTextures : BoolProperty(
	   name = "Reload Cached Textures",
	   description = "Convert all textures again instead of reading from already converted textures. Use this if you make changes to textures and need to reload them",
	   default = False)
	
	default_createCollections : BoolProperty(
	   name = "Create Collections",
	   description = "Create a collection for the mesh and for each LOD level. Note that collections are required for exporting LODs and applying MDF changes. Leaving this option enabled is recommended",
	   default = True)
	
	default_importArmatureOnly : BoolProperty(
	   name = "Only Import Armature",
	   description = "Imports the armature of the mesh file, but not any of the meshes",
	   default = False)
	default_importAllLODs : BoolProperty(
	   name = "Import All LODs",
	   description = "Imports all LOD (level of detail) meshes. If unchecked, only the first LOD of each mesh will be imported",
	   default = False)
	default_rotate90 : BoolProperty(
	   name = "Y Up to Z Up",
	   description = "Rotate meshes and armatures by 90 degrees. Leaving this option enabled is recommended",
	   default = True)
	default_importBlendShapes : BoolProperty(
	   name = "Import Blend Shapes",
	   description = "Imports blend shapes as shape keys if present",
	   default = True)
	default_importShadowMeshes : BoolProperty(
	   name = "Import Shadow Cast Mesh",
	   description = "Imports shadow cast meshes if present",
	   default = True)
	default_mergeGroups : BoolProperty(
	   name = "Merge Mesh Groups",
	   description = "Merges all submeshes of a mesh group. IMPORTANT: MERGED MESHES CANNOT BE EXPORTED BACK TO MESH",
	   default = False)
	default_importOcclusionMeshes : BoolProperty(
	   name = "Import Occlusion Mesh",
	   description = "Imports occlusion meshes if present",
	   default = False)
	default_importBoundingBoxes : BoolProperty(
	   name = "Import Bounding Boxes",
	   description = "Import mesh and bone bounding boxes for debugging purposes",
	   default = False)
	
	#Default export options
	default_selectedOnly : BoolProperty(
	   name = "Selected Objects Only",
	   description = "Limit export to selected objects",
	   default = False)

	default_exportAllLODs : BoolProperty(
	   name = "Export All LODs",
	   description = "Export all LODs. If disabled, only LOD0 will be exported. Note that LODs meshes must be grouped inside a collection for each level and that collection must be contained in another collection. See a mesh with LODs imported for reference on how it should look. A target collection must also be set",
	   default = True)
	default_exportBlendShapes : BoolProperty(
	   name = "Export Blend Shapes",
	   description = "Exports blend shapes from mesh if present",
	   default = True)
	default_rotate90export : BoolProperty(
	   name = "Convert Z Up To Y Up",
	   description = "Rotates objects 90 degrees for export. Leaving this option enabled is recommended",
	   default = True)
	default_autoSolveRepeatedUVs : BoolProperty(
	   name = "Auto Solve Repeated UVs",
	   description = "Splits connected UV islands if present. The mesh format does not allow for multiple uvs assigned to a vertex.\nNOTE: This will modify the exported mesh. If auto smooth is disabled on the mesh, the normals may change",
	   default = True)
	default_preserveSharpEdges : BoolProperty(
	   name = "Split Sharp Edges",
	   description = "Edge splits all edges marked as sharp to preserve them on the exported mesh.\nNOTE: This will modify the exported mesh",
	   default = False)
	default_useBlenderMaterialName : BoolProperty(
	   name = "Use Blender Material Names",
	   description = "If left unchecked, the exporter will get the material names to be used from the end of each object name. For example, if a mesh is named LOD_0_Group_0_Sub_0__Shirts_Mat, the material name is Shirts_Mat. If this option is enabled, the material name will instead be taken from the first material assigned to the object",
	   default = False)
	default_preserveBoneMatrices : BoolProperty(
	   name = "Preserve Bone Matrices",
	   description = "Export using the original matrices of the imported bones. Note that this option only applies armatures imported with this addon. Any newly added bones will have new matrices calculated",
	   default = False)
	default_exportBoundingBoxes : BoolProperty(
	   name = "Export Bounding Boxes",
	   description = "Exports the original bounding boxes from the \"Import Bounding Boxes\" import option. New bounding boxes will be generated for any bones that do not have them",
	   default = False)
	
	
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
		layout.prop(self, "dragDropImportOptions")
		layout.prop(self, "showConsole")
		layout.prop(self, "useDDS")
		box = layout.box()
		row = box.row()
		
		if len(self.textureCachePath) > 110:
			row.alert = True
			row.prop(self,"textureCachePath")
			box.label(text="Texture cache path is very long.",icon = "ERROR")
			box.label(text="File paths may exceed the max length of 255 characters and fail to convert.")
			box.label(text="Consider changing this to a shorter path such as C:\REMeshTextureCache.")
		else:
			row.prop(self,"textureCachePath")
		row = box.row()
		if self.textureCacheCheckDate == "":
			checkTextureCacheSize()
		row.label(text=f"Cache Size: {self.textureCacheSizeString}")
		row.operator("re_mesh.check_texture_cache_size",icon = "FILE_REFRESH",text = "")
		box.label(text=f"Last Checked: {self.textureCacheCheckDate}")
		
		
		
		box.operator("re_mesh.open_texture_cache_folder")
		box.operator("re_mesh.clear_texture_cache_folder")
		
		op.url = 'https://ko-fi.com/nsacloud'
		
		#Import defaults
		row = layout.row()
		icon = 'DOWNARROW_HLT' if self.showImportOptions else 'RIGHTARROW'
		row.prop(self, 'showImportOptions', icon=icon, icon_only=True)
		row.label(text='Default Mesh Import Settings')
		split = layout.split(factor = 0.01)
		column = split.column()
		column2 = split.column()
		if self.showImportOptions:
			column2.prop(self, "default_clearScene")
			column2.prop(self, "default_loadMaterials")
			column2.prop(self, "default_loadMDFData")
			column2.prop(self, "default_reloadCachedTextures")
			column2.prop(self, "default_loadUnusedTextures")
			column2.prop(self, "default_loadUnusedProps")
			column2.prop(self, "default_useBackfaceCulling")
			column2.prop(self, "default_importAllLODs")
			column2.prop(self, "default_createCollections")
			column2.prop(self, "default_mergeGroups")
			column2.prop(self, "default_importArmatureOnly")
			column2.prop(self, "default_rotate90")
			column2.prop(self, "default_importBoundingBoxes")
		#Export defaults
		row = layout.row()
		icon = 'DOWNARROW_HLT' if self.showExportOptions else 'RIGHTARROW'
		row.prop(self, 'showExportOptions', icon=icon, icon_only=True)
		row.label(text='Default Mesh Export Options')
		split = layout.split(factor = 0.01)
		column = split.column()
		column2 = split.column()
		if self.showExportOptions:
			column2.prop(self, "default_selectedOnly")
			column2.prop(self, "default_exportAllLODs")
			column2.prop(self,"default_autoSolveRepeatedUVs")
			column2.prop(self,"default_preserveSharpEdges")
			column2.prop(self, "default_rotate90export")
			column2.prop(self, "default_useBlenderMaterialName")
			column2.prop(self, "default_preserveBoneMatrices")
			column2.prop(self, "default_exportBoundingBoxes")
		
		layout.label(text = "Chunk Path List")
		layout.prop(self, "saveChunkPaths")
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
	'''Import RE Engine Mesh File'''
	bl_idname = "re_mesh.importfile"
	bl_label = "Import RE Mesh"
	bl_options = {'PRESET', "REGISTER", "UNDO"}
	files : CollectionProperty(
			name="File Path",
			type=OperatorFileListElement,
			)
	directory : StringProperty(
			subtype='DIR_PATH',
			options={'SKIP_SAVE'}
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
	
	loadMDFData : BoolProperty(
	   name = "Load MDF Material Data",
	   description = "Imports the MDF materials as objects inside a collection in the outliner.\nYou can make changes to MDF materials by selecting the Material objects in the outliner.\nUnder the Object Properties tab (orange square), there's a panel called \"RE MDF Material Settings\".\nMake any changes to MDF materials there.\nIf you're not modding an RE Engine game, you can uncheck this option since it won't be needed",
	   default = True)
	
	loadUnusedTextures : BoolProperty(
	   name = "Load Unused Textures",
	   description = "Loads textures that have no function assigned to them in the material shader graph.\nLeaving this disabled will make materials load faster.\nOnly enable this if you plan on editing the material shader graph",
	   default = False)
	loadUnusedProps : BoolProperty(
	   name = "Load Unused Material Properties",
	   description = "Loads material properties that have no function assigned to them in the material shader graph.\nLeaving this disabled will make materials load faster.\nOnly enable this if you plan on editing the material shader graph",
	   default = False)
	useBackfaceCulling : BoolProperty(
	   name = "Use Backface Culling",
	   description = "Enables backface culling on materials. May improve Blender's performance on high poly meshes.\nBackface culling will only be enabled on materials without the two sided flag",
	   default = False)

	reloadCachedTextures : BoolProperty(
	   name = "Reload Cached Textures",
	   description = "Convert all textures again instead of reading from already converted textures. Use this if you make changes to textures and need to reload them",
	   default = False)
	mdfPath : StringProperty(
		name = "",
		description = "Manually set the path of the mdf2 file. The MDF is found automatically if this is left blank.\nTip:Hold shift and right click the mdf2 file and click \"Copy as path\", then paste into this field",
		default = "",
		)
	createCollections : BoolProperty(
	   name = "Create Collections",
	   description = "Create a collection for the mesh and for each LOD level. Note that collections are required for exporting LODs and applying MDF changes. Leaving this option enabled is recommended",
	   default = True)
	mergeArmature : StringProperty(
	   name = "",
	   description = "Merges the imported mesh's armature with the selected armature. Leave this blank if not merging with an armature",
	   default = "")
	mergeImportedArmatures : BoolProperty(
	   name = "Merge All New Armatures",
	   description = "If multiple mesh files are selected, merge the armatures of all newly imported mesh files into one",
	   default = False)
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
	
	#Internal properties for grouping material settings
	showAdvancedOptions : BoolProperty(
	   name = "Show Advanced Options",
	   default = False)
	showMaterialOptions : BoolProperty(
	   name = "Show Material Options",
	   default = True)
	
	def draw(self, context):
		layout = self.layout
		row = layout.row()
		row.prop(self, "clearScene")
		
		
		row.enabled = self.mergeArmature == ""
		
		#layout.prop(self, "importBlendShapes")
		
		layout.label(text = "Merge With Armature")
		
		
		layout.prop_search(self, "mergeArmature",bpy.data,"armatures")
		
		row = layout.row()
		row.prop(self, "mergeImportedArmatures")
		row.enabled = len(self.files) > 1
		
		row = layout.row()
		icon = 'DOWNARROW_HLT' if self.showMaterialOptions else 'RIGHTARROW'
		row.prop(self, 'showMaterialOptions', icon=icon, icon_only=True)
		row.label(text='Material Settings')
		split = layout.split(factor = 0.01)
		column = split.column()
		column2 = split.column()
		if self.showMaterialOptions:
			column2.prop(self, "loadMaterials")
			column2.prop(self, "loadMDFData")
			column2.prop(self, "reloadCachedTextures")
			column2.prop(self, "loadUnusedTextures")
			column2.prop(self, "loadUnusedProps")
			column2.prop(self, "useBackfaceCulling")
			column2.label(text = "Manual MDF Path")
			column2.prop(self, "mdfPath")	
		
		row = layout.row()
		icon = 'DOWNARROW_HLT' if self.showAdvancedOptions else 'RIGHTARROW'
		row.prop(self, 'showAdvancedOptions', icon=icon, icon_only=True)
		row.label(text='Advanced Options')
		split = layout.split(factor = 0.01)
		column = split.column()
		column2 = split.column()
		if self.showAdvancedOptions:
			column2.prop(self, "importAllLODs")
			column2.prop(self, "createCollections")
			column2.prop(self, "mergeGroups")
			column2.prop(self, "importArmatureOnly")
		
			column2.prop(self, "rotate90")
			column2.prop(self, "importBoundingBoxes")
			#column2.prop(self, "importOcclusionMeshes")  
		
	def execute(self, context):
		try:
			os.makedirs(bpy.path.abspath(bpy.context.preferences.addons[__name__].preferences.textureCachePath),exist_ok = True)
		except:
			raiseWarning("Could not create texture cache directory at " + bpy.context.preferences.addons[__name__].preferences.textureCachePath)
		if self.mergeArmature:
			self.clearScene = False
		options = {"clearScene":self.clearScene,"createCollections":self.createCollections,"loadMaterials":self.loadMaterials,"loadMDFData":self.loadMDFData,"loadUnusedTextures":self.loadUnusedTextures,"loadUnusedProps":self.loadUnusedProps,"useBackfaceCulling":self.useBackfaceCulling,"reloadCachedTextures":self.reloadCachedTextures,"mdfPath":self.mdfPath.replace("\"",""),"importAllLODs":self.importAllLODs,"importBlendShapes":self.importBlendShapes,"rotate90":self.rotate90,"mergeArmature":self.mergeArmature,"importArmatureOnly":self.importArmatureOnly,"mergeGroups":self.mergeGroups,"importShadowMeshes":self.importShadowMeshes,"importOcclusionMeshes":self.importOcclusionMeshes,"importBoundingBoxes":self.importBoundingBoxes}
		editorVersion = str(bl_info["version"][0])+"."+str(bl_info["version"][1])
		print(f"\n{textColors.BOLD}RE Mesh Editor V{editorVersion}{textColors.ENDC}")
		print(f"Blender Version {bpy.app.version[0]}.{bpy.app.version[1]}.{bpy.app.version[2]}")
		print("https://github.com/NSACloud/RE-Mesh-Editor")
		
		bpy.context.scene["REMeshDefaultImportSettingsLoaded"] = 1
		
		if bpy.context.preferences.addons[__name__].preferences.showConsole:
			 try: 
				 bpy.ops.wm.console_toggle()
			 except:
				 pass
		
		multiFileImport = len(self.files) > 1
		hasImportErrors = False
		mergeArmatureName = ""
		mergeArmatureNameIndex = 1
		if multiFileImport and self.mergeImportedArmatures:
			mergeArmatureName = self.files[0].name.split(".mesh")[0] + " Armature"
			baseMergeArmatureName = mergeArmatureName
			while mergeArmatureName in bpy.data.armatures:#Get the name of armature that will be imported, this accounts for if there's already an armature with that name imported
				mergeArmatureName = baseMergeArmatureName + "." + str(mergeArmatureNameIndex).zfill(3)
				mergeArmatureNameIndex += 1
			
		for index, file in enumerate(self.files):
			filepath = os.path.join(self.directory,file.name)
			if multiFileImport:
				print(f"Multi Mesh Import ({index+1}/{len(self.files)})")
				if index != 0:
					options["mergeArmature"] = mergeArmatureName
			if os.path.isfile(filepath):
				success = importREMeshFile(filepath,options)
				options["clearScene"] = False#Disable clear scene after first mesh is imported
				if not success: hasImportErrors = True
			else:
				hasImportErrors = True
				raiseWarning(f"Path does not exist, cannot import file. If you are importing multiple files at once, they must all be in the same directory.\nInvalid Path:{filepath}")
			
			
			
		if not hasImportErrors:
			if bpy.context.preferences.addons[__name__].preferences.showConsole:
				try: 
					bpy.ops.wm.console_toggle()
				except:
					 pass
				
				
			if not multiFileImport:
				self.report({"INFO"},"Imported RE Mesh file.")
			else:
				self.report({"INFO"},f"Imported {str(len(self.files))} RE Mesh files.")
			
			return {"FINISHED"}
		else:
			self.report({"INFO"},"Failed to import RE Mesh. Check the console for errors.")
			return {"CANCELLED"}
	
	def invoke(self, context, event):
		if not bpy.context.scene.get("REMeshDefaultImportSettingsLoaded"):
			setMeshImportDefaults(self)
			
		if self.directory:
			if bpy.context.preferences.addons[__name__].preferences.dragDropImportOptions:
				return context.window_manager.invoke_props_dialog(self)
			else:
				return self.execute(context)
		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}
def update_targetMeshCollection(self,context):
	temp = bpy.data.screens.get("temp")
	browserSpace = None
	if temp != None:
		for area in temp.areas:
			for space in area.spaces:
				try:
					if type(space.params).__name__ == "FileSelectParams":
						browserSpace = space
						break
						break
				except:
					pass
	if browserSpace != None:
		#print(browserSpace.params.filename)
		if ".mesh" in self.targetCollection:
			browserSpace.params.filename = self.targetCollection.split(".mesh")[0]+".mesh" + self.filename_ext
class ExportREMesh(Operator, ExportHelper):
	'''Export RE Engine Mesh File'''
	bl_idname = "re_mesh.exportfile"
	bl_label = "Export RE Mesh"
	bl_options = {'PRESET'}
	
	filter_glob: StringProperty(default="*.mesh*", options={'HIDDEN'})
	
	filename_ext: EnumProperty(
		name="",
		description="Set which game to export the mesh for",
		items= [
				(".1808282334", "Devil May Cry 5", "Devil May Cry 5"), 
				(".1808312334", "Resident Evil 2", "Resident Evil 2"),
				(".1902042334", "Resident Evil 3", "Resident Evil 3"),
				(".2101050001", "Resident Evil 8", "Resident Evil 8"),
				(".2109108288", "Resident Evil 2 / 3 Ray Tracing", "Resident Evil 2/3 Ray Tracing Version"),
				(".220128762", "Resident Evil 7 Ray Tracing", "Resident Evil 7 Ray Tracing Version"),
			    (".2109148288", "Monster Hunter Rise", "Monster Hunter Rise"),
				(".221108797", "Resident Evil 4", "Resident Evil 4"),
				(".230110883", "Street Fighter 6", "Street Fighter 6"),
				(".240423143", "Dragon's Dogma 2", "Dragon's Dogma 2"),
				(".240306278", "Kunitsu-Gami", "Kunitsu-Gami"),
				(".240424828", "Dead Rising", "Dead Rising"),
				(".240827123", "Onimusha 2", "Onimusha 2"),
				(".241111606", "Monster Hunter Wilds", "Monster Hunter Wilds"),
			   ]
		)
	targetCollection: bpy.props.StringProperty(
		name="",
		description = "Set the collection containing the meshes to be exported.\nNote: Mesh collections are red and end with .mesh",
		update = update_targetMeshCollection
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
	   description = "Splits connected UV islands if present. The mesh format does not allow for multiple uvs assigned to a vertex.\nNOTE: This will modify the exported mesh. If auto smooth is disabled on the mesh, the normals may change",
	   default = True)
	preserveSharpEdges : BoolProperty(
	   name = "Split Sharp Edges",
	   description = "Edge splits all edges marked as sharp to preserve them on the exported mesh.\nNOTE: This will modify the exported mesh",
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
		if not bpy.context.scene.get("REMeshDefaultExportSettingsLoaded"):
			setMeshExportDefaults(self)
			
		if context.scene.get("REMeshLastImportedMeshVersion",0) in meshFileVersionToGameNameDict:
			if context.scene["REMeshLastImportedMeshVersion"] == 231011879:
				#DD2 version update fix
				context.scene["REMeshLastImportedMeshVersion"] = 240423143
			elif context.scene["REMeshLastImportedMeshVersion"] == 2102020001:
				#Remap RE Verse to RE8
				context.scene["REMeshLastImportedMeshVersion"] = 2101050001
			elif context.scene["REMeshLastImportedMeshVersion"] == 240820143:
				#Remap MH Wilds beta to full release
				context.scene["REMeshLastImportedMeshVersion"] = 241111606
		
		if context.scene.get("REMeshLastExportedMeshVersion",0) in meshFileVersionToGameNameDict:
			if context.scene["REMeshLastExportedMeshVersion"] == 231011879:
				#DD2 version update fix
				context.scene["REMeshLastExportedMeshVersion"] = 240423143
			elif context.scene["REMeshLastExportedMeshVersion"] == 2102020001:
				#Remap RE Verse to RE8
				context.scene["REMeshLastExportedMeshVersion"] = 2101050001
			elif context.scene["REMeshLastExportedMeshVersion"] == 240820143:
				#Remap MH Wilds beta to full release
				context.scene["REMeshLastExportedMeshVersion"] = 241111606
		
		if self.targetCollection == "":
			
			
			#Get last exported collection, if there isn't one, get last imported
			exportCollection = context.scene.get("REMeshLastExportedCollection","")
			if exportCollection in bpy.data.collections:
				self.targetCollection = exportCollection
				if ".mesh" in exportCollection:#Remove blender suffix after .mesh if it exists
					if context.scene.get("REMeshLastExportedMeshVersion") in meshFileVersionToGameNameDict:
						self.filename_ext = "."+str(context.scene.get("REMeshLastExportedMeshVersion",1808282334))
					self.filepath = exportCollection.split(".mesh")[0]+".mesh" + self.filename_ext
			else:
				prevCollection = context.scene.get("REMeshLastImportedCollection","")
				if prevCollection in bpy.data.collections:
					self.targetCollection = prevCollection
				if ".mesh" in prevCollection:#Remove blender suffix after .mesh if it exists
					if context.scene.get("REMeshLastImportedMeshVersion") in meshFileVersionToGameNameDict:
						self.filename_ext = "."+str(context.scene.get("REMeshLastImportedMeshVersion",1808282334))
					self.filepath = prevCollection.split(".mesh")[0]+".mesh" + self.filename_ext

			
		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}
	def draw(self, context):
		layout = self.layout
		layout.label(text = "Mesh Version:")
		layout.prop(self, "filename_ext")
		layout.label(text = "Mesh Collection:")
		layout.prop_search(self, "targetCollection",bpy.data,"collections",icon = "COLLECTION_COLOR_01")
		
		if self.targetCollection in bpy.data.collections:
			collection = bpy.data.collections[self.targetCollection]
			if not collection.get("~TYPE") == "RE_MESH_COLLECTION" and not collection.name.endswith(".mesh"):
				row = layout.row()
				row.alert=True
				row.label(icon = "ERROR",text="Collection is not a mesh collection.")
		elif self.targetCollection == "":
			row = layout.row()
			row.alert=True
			row.label(icon = "ERROR",text="Collection is not a mesh collection.")
			
		else:
			row = layout.row()
			row.label(icon="ERROR",text="Chosen collection doesn't exist.")
			row.alert=True
		layout.prop(self, "selectedOnly")
		layout.label(text = "Advanced Options")
		layout.prop(self, "exportAllLODs")
		#layout.prop(self, "exportBlendShapes")
		#hasREToolbox = hasattr(bpy.types, "OBJECT_PT_re_tools_quick_export_panel")
		row = layout.row()
		#row.enabled = hasREToolbox
		row.prop(self,"autoSolveRepeatedUVs")
		row2 = layout.row()
		#row2.enabled = hasREToolbox
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
		
		bpy.context.scene["REMeshDefaultExportSettingsLoaded"] = 1
		
		if bpy.context.preferences.addons[__name__].preferences.showConsole:
			try: 
				bpy.ops.wm.console_toggle()
			except:
				pass
		success = exportREMeshFile(self.filepath,options)
		if success:
			self.report({"INFO"},"Exported RE Mesh successfully.")
			bpy.data.collections[self.targetCollection]["BatchExport_path"] = self.filepath
			bpy.data.collections[self.targetCollection]["BatchExport_exportAllLODs"] = self.exportAllLODs
			bpy.data.collections[self.targetCollection]["BatchExport_preserveSharpEdges"] = self.preserveSharpEdges
			bpy.data.collections[self.targetCollection]["BatchExport_rotate90"] = self.rotate90
			bpy.data.collections[self.targetCollection]["BatchExport_exportBlendShapes"] = self.exportBlendShapes
			bpy.data.collections[self.targetCollection]["BatchExport_useBlenderMaterialName"] = self.useBlenderMaterialName
			bpy.data.collections[self.targetCollection]["BatchExport_preserveBoneMatrices"] = self.preserveBoneMatrices
			bpy.data.collections[self.targetCollection]["BatchExport_exportBoundingBoxes"] = self.exportBoundingBoxes
		else:
			self.report({"INFO"},"RE Mesh export failed. See Window > Toggle System Console for info on how to fix it.")
		
		if bpy.context.scene.re_mdf_toolpanel.modDirectory == "":
			setModDirectoryFromFilePath(self.filepath)
		
		if bpy.context.preferences.addons[__name__].preferences.showConsole:
			try:
				bpy.ops.wm.console_toggle()
			except:
				 pass
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
			options={'SKIP_SAVE'}
			)
	filename_ext = ".mdf.*"
	filter_glob: StringProperty(default="*.mdf2.*", options={'HIDDEN'})

	def execute(self, context):
		editorVersion = str(bl_info["version"][0])+"."+str(bl_info["version"][1])
		print(f"\n{textColors.BOLD}RE Mesh Editor V{editorVersion}{textColors.ENDC}")
		print(f"Blender Version {bpy.app.version[0]}.{bpy.app.version[1]}.{bpy.app.version[2]}")
		print("https://github.com/NSACloud/RE-Mesh-Editor")
		multiFileImport = len(self.files) > 1
		hasImportErrors = False
		
		for index, file in enumerate(self.files):
			filepath = os.path.join(self.directory,file.name)
			if multiFileImport:
				print(f"Multi MDF Import ({index+1}/{len(self.files)})")
			if os.path.isfile(filepath):
				success = importMDFFile(filepath)
				if not success: hasImportErrors = True
			else:
				hasImportErrors = True
				raiseWarning(f"Path does not exist, cannot import file. If you are importing multiple files at once, they must all be in the same directory.\nInvalid Path:{filepath}")
			
			
		if not hasImportErrors:
			if not multiFileImport:
				self.report({"INFO"},"Imported RE MDF file.")
			else:
				self.report({"INFO"},f"Imported {str(len(self.files))} RE MDF files.")
			return {"FINISHED"}
		else:
			self.report({"INFO"},"Failed to import RE MDF. Check the console for errors.")
			return {"CANCELLED"}
	def invoke(self, context, event):
		if self.directory:
			return self.execute(context)
		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}
supportedMDFVersions = set([23,19,21,32,31,40,45])	

def update_targetMDFCollection(self,context):
	temp = bpy.data.screens.get("temp")
	browserSpace = None
	if temp != None:
	    for area in temp.areas:
	        for space in area.spaces:
	            if type(space.params).__name__ == "FileSelectParams":
	                browserSpace = space
	                break
	                break
	if browserSpace != None:
		#print(browserSpace.params.filename)
		if ".mdf2" in self.targetCollection:
			browserSpace.params.filename = self.targetCollection.split(".mdf2")[0]+".mdf2" + self.filename_ext	
class ExportREMDF(bpy.types.Operator, ExportHelper):
	'''Export RE Engine MDF File'''
	bl_idname = "re_mdf.exportfile"
	bl_label = "Export RE MDF"
	bl_options = {'PRESET'}
	filename_ext: EnumProperty(
		name="",
		description="Set which game to export the MDF for",
		items=[ 
				(".10", "Devil May Cry 5 / Resident Evil 2", ""),
				(".13", "Resident Evil 3", ""),
				(".19", "Resident Evil 8", ""),
				(".21", "Resident Evil 2 / 3 / 7 Ray Tracing", ""),
				(".23", "Monster Hunter Rise", ""),
				(".32", "Resident Evil 4", ""),
				(".31", "Street Fighter 6", ""),
				(".40", "Dragon's Dogma 2 / Kunitsu-Gami / Dead Rising", "Dragon's Dogma 2, Kunitsu-Gami, Dead Rising"),
				(".46", "Onimusha 2", "Onimusha 2"),
				(".45", "Monster Hunter Wilds", "Monster Hunter Wilds"),
			  ]
		)
	targetCollection : StringProperty(
	   name = "",
	   description = "Set the MDF collection to be exported\nNote: MDF collections are blue and end with .mdf2",
	   default = "",
	   update = update_targetMDFCollection)
	filter_glob: StringProperty(default="*.mdf2*", options={'HIDDEN'})
	def invoke(self, context, event):
		if bpy.data.collections.get(self.targetCollection,None) == None:
			if bpy.context.scene.re_mdf_toolpanel.mdfCollection:
				self.targetCollection = bpy.context.scene.re_mdf_toolpanel.mdfCollection.name
				if self.targetCollection.endswith(".mdf2"):
					self.filepath = self.targetCollection + self.filename_ext
			self.filename_ext = "."+str(gameNameMDFVersionDict[bpy.context.scene.re_mdf_toolpanel.activeGame])
		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}
	
	def draw(self, context):
		layout = self.layout
		layout.label(text = "MDF Version:")
		layout.prop(self,"filename_ext")
		layout.label(text = "MDF Collection:")
		layout.prop_search(self, "targetCollection",bpy.data,"collections",icon = "COLLECTION_COLOR_05")
		if self.targetCollection in bpy.data.collections:
			collection = bpy.data.collections[self.targetCollection]
			if not collection.get("~TYPE") == "RE_MDF_COLLECTION" and not collection.name.endswith(".mdf2"):
				row = layout.row()
				row.alert=True
				row.label(icon = "ERROR",text="Collection is not a MDF collection.")
		elif self.targetCollection == "":
			row = layout.row()
			row.alert=True
			row.label(icon = "ERROR",text="Collection is not a MDF collection.")
			
		else:
			row = layout.row()
			row.label(icon="ERROR",text="Chosen collection doesn't exist.")
			row.alert=True
	def execute(self, context):
		editorVersion = str(bl_info["version"][0])+"."+str(bl_info["version"][1])
		print(f"\n{textColors.BOLD}RE MDF Editor V{editorVersion}{textColors.ENDC}")
		print(f"Blender Version {bpy.app.version[0]}.{bpy.app.version[1]}.{bpy.app.version[2]}")
		print("https://github.com/NSACloud/RE-Mesh-Editor")
		success = exportMDFFile(self.filepath,self.targetCollection)
		if success:
			self.report({"INFO"},"Exported RE MDF successfully.")
			
			if bpy.context.scene.re_mdf_toolpanel.modDirectory == "":
				setModDirectoryFromFilePath(self.filepath)
			
			bpy.data.collections[self.targetCollection]["BatchExport_path"] = self.filepath
			return {"FINISHED"}
		else:
			self.report({"INFO"},"Failed to export RE MDF. Check Window > Toggle System Console for details.")
			return {"CANCELLED"}

class ImportREFBXSkel(bpy.types.Operator, ImportHelper):
	'''Import RE Engine FBXSkel File'''
	bl_idname = "re_fbxskel.importfile"
	bl_label = "Import RE FBXSkel"
	bl_options = {'PRESET', "REGISTER", "UNDO"}
	files : CollectionProperty(
			name="File Path",
			type=OperatorFileListElement,
			)
	directory : StringProperty(
			subtype='DIR_PATH',
			options={'SKIP_SAVE'}
			)
	filename_ext = ".fbxskel.*"
	filter_glob: StringProperty(default="*.fbxskel.*", options={'HIDDEN'})
	
	def invoke(self, context, event):
		if self.directory:
			return self.execute(context)
		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}
	def execute(self, context):
		success = importFBXSkelFile(self.filepath)
		if success:
			return {"FINISHED"}
		else:
			self.report({"INFO"},"Failed to import RE FBXSkel.")
			return {"CANCELLED"}

def update_targetFBXSkelArmature(self,context):
	temp = bpy.data.screens.get("temp")
	browserSpace = None
	if temp != None:
	    for area in temp.areas:
	        for space in area.spaces:
	            if type(space.params).__name__ == "FileSelectParams":
	                browserSpace = space
	                break
	                break
	if browserSpace != None:
		#print(browserSpace.params.filename)
		if ".fbxskel" in self.targetArmature:
			browserSpace.params.filename = self.targetArmature.split(".fbxskel")[0]+".fbxskel" + self.filename_ext	
		
class ExportREFBXSkel(bpy.types.Operator, ExportHelper):
	'''Export RE Engine FBXSkel File'''
	bl_idname = "re_fbxskel.exportfile"
	bl_label = "Export RE FBXSkel"
	bl_options = {'PRESET'}
	filename_ext: EnumProperty(
		name="",
		description="Set which game to export the FBXSkel for",
		items=[ (".3", "DMC5 (.3)", ""),
				(".4", "RERT (.4)", ""),
				(".5", "RE4R (.5)", ""),
				(".6", "DD2 (.6)", ""),
				(".7", "MHWILDS (.7)", ""),

			   ],
		default = ".7"
		)
	
	filter_glob: StringProperty(default="*.fbxskel*", options={'HIDDEN'})
	targetArmature : StringProperty(
	   name = "",
	   description = "Set the armature to be exported",
	   default = "",
	   update = update_targetFBXSkelArmature)
	
	def invoke(self, context, event):
		if self.targetArmature == "":
			if context.active_object != None:
				if context.active_object.type == "ARMATURE":
					self.targetArmature = context.active_object.name
					self.filepath = self.targetArmature.split(".fbxskel")[0]+".fbxskel" + self.filename_ext
			else:
				for obj in bpy.context.scene.objects:
					if obj.type == "ARMATURE" and ".fbxskel" in obj.name:
						self.targetArmature = obj.name
						self.filepath = self.targetArmature.split(".fbxskel")[0]+".fbxskel" + self.filename_ext
						break
		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}
	
	def draw(self, context):
		layout = self.layout
		layout.label(text = "FBXSkel Version:")
		layout.prop(self,"filename_ext")
		layout.label(text = "FBXSkel Armature:")
		layout.prop_search(self, "targetArmature",bpy.data,"objects",icon = "ARMATURE_DATA")
		if self.targetArmature in bpy.data.objects:
			obj = bpy.data.objects[self.targetArmature]
			if not obj.type == "ARMATURE":
				row = layout.row()
				row.alert=True
				row.label(icon = "ERROR",text="Object is not an armature.")
		elif self.targetArmature == "":
			row = layout.row()
			row.alert=True
			row.label(icon = "ERROR",text="No armature is selected.")
			
		else:
			row = layout.row()
			row.label(icon="ERROR",text="Armature doesn't exist.")
			row.alert=True
	
	def execute(self, context):
		success = exportFBXSkelFile(self.filepath,self.targetArmature)
		if success:
			self.report({"INFO"},"Exported RE FBXSkel successfully.")
			bpy.data.objects[self.targetArmature]["BatchExport_path"] = self.filepath
			return {"FINISHED"}
		else:
			self.report({"INFO"},"Failed to export RE FBXSkel. Check Window > Toggle System Console for details.")
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
	WM_OT_DeleteLoose,
	WM_OT_RenameMeshToREFormat,
	WM_OT_RemoveZeroWeightVertexGroups,
	WM_OT_LimitTotalNormalizeAll,
	WM_OT_CreateMeshCollection,
	WM_OT_OpenTextureCacheFolder,
	WM_OT_ClearTextureCacheFolder,
	WM_OT_CheckTextureCacheSize,
	ExporterNodePropertyGroup,
	MESH_UL_REExporterList,
	WM_OT_REBatchExporter,
	
	
	#mdf
	ImportREMDF,
	ExportREMDF,
	#property groups
	MDFMMTRSIndexPropertyGroup,
	MDFGPBFDataPropertyGroup,
	MDFFlagsPropertyGroup,
	MDFToolPanelPropertyGroup,
	MDFPropPropertyGroup,
	MDFTextureBindingPropertyGroup,
	MDFMaterialPropertyGroup,
	REMeshErrorEntry,
	MESH_UL_REMeshErrorList,
	
	MESH_UL_MDFPropertyList,
	MESH_UL_MDFTextureBindingList,
	MESH_UL_MDFMMTRSDataList,
	MESH_UL_MDFGPBFDataList,
	
	#ui panels
	OBJECT_PT_MDFObjectModePanel,
	OBJECT_PT_MDFMaterialPresetPanel,
	OBJECT_PT_MDFMaterialPreviewPanel,
	OBJECT_PT_MDFMaterialLoadSettingsPanel,
	OBJECT_PT_MeshObjectModePanel,
	OBJECT_PT_MeshArmatureToolsPanel,
	OBJECT_PT_MDFMaterialPanel,
	OBJECT_PT_MDFFlagsPanel,
	OBJECT_PT_MDFMaterialTextureBindingListPanel,
	OBJECT_PT_MDFMaterialPropertyListPanel,
	OBJECT_PT_MDFMaterialMMTRSIndexListPanel,
	OBJECT_PT_MDFMaterialGPBFDataListPanel,
	
	
	
	#operators
	WM_OT_NewMDFHeader,
	WM_OT_ReindexMaterials,
	WM_OT_AddPresetMaterial,
	WM_OT_SavePreset,
	WM_OT_OpenPresetFolder,
	WM_OT_ApplyMDFToMeshCollection,
	WM_OT_ShowREMeshErrorWindow,
	#tex
	#operators
	WM_OT_ConvertFolderToTex,
	WM_OT_CopyConvertedTextures,
	WM_OT_ConvertDDSTexFile,
	#ui panels
	OBJECT_PT_TexConversionPanel,
	
	#fbxskel
	ImportREFBXSkel,
	ExportREFBXSkel,
	#property groups
	ToggleStringPropertyGroup,
	FBXSKEL_UL_ObjectCheckList,
	#operators
	WM_OT_LinkArmatureBones,
	WM_OT_ClearBoneLinkages,
	
	
	#RE asset extra tools
	OBJECT_PT_REAssetExtensionPanel,
	
	]


#Drag and drop importing, 4.1 or higher only
if bpy.app.version >= (4, 1, 0):
	meshExtensionsString = ""
	for meshVersion in meshFileVersionToGameNameDict.keys():
		meshExtensionsString += f".{str(meshVersion)};"
	class MESH_FH_drag_import(bpy.types.FileHandler):
		bl_idname = "MESH_FH_drag_import"
		bl_label = "File handler for RE Mesh importing"
		bl_import_operator = "re_mesh.importfile"
		bl_file_extensions = meshExtensionsString
	
		@classmethod
		def poll_drop(cls, context):
			return (context.area and context.area.type == 'VIEW_3D')
	mdfExtensionsString = ""
	for mdfVersion in gameNameMDFVersionDict.keys():
		if isinstance(mdfVersion,int):
			mdfExtensionsString += f".{str(mdfVersion)};"
	
	class MDF_FH_drag_import(bpy.types.FileHandler):
		bl_idname = "MDF_FH_drag_import"
		bl_label = "File handler for RE MDF importing"
		bl_import_operator = "re_mdf.importfile"
		bl_file_extensions = mdfExtensionsString
		
		@classmethod
		def poll_drop(cls, context):
			return (context.area and context.area.type == 'VIEW_3D')
	texExtensionsString = ".dds;"
	for texVersion in gameNameToTexVersionDict.values():
		texExtensionsString += f".{str(texVersion)};"
	texExtensionsString += ".31;"#RE Verse tex drag and drop support
	
	class TEX_FH_drag_import(bpy.types.FileHandler):
		bl_idname = "TEX_FH_drag_import"
		bl_label = "File handler for RE Tex Conversion"
		bl_import_operator = "re_tex.convert_tex_dds_files"
		bl_file_extensions = texExtensionsString
	
		@classmethod
		def poll_drop(cls, context):
			return (context.area and context.area.type == 'VIEW_3D')
		
	fbxSkelExtensionsString = ".4;.5;.6;.7;"#RE Verse tex drag and drop support
	
	class FBXSKEL_FH_drag_import(bpy.types.FileHandler):
		bl_idname = "FBXSKEL_FH_drag_import"
		bl_label = "File handler for RE FBXSkel importing"
		bl_import_operator = "re_fbxskel.importfile"
		bl_file_extensions = fbxSkelExtensionsString
	
		@classmethod
		def poll_drop(cls, context):
			return (context.area and context.area.type == 'VIEW_3D')
class GU_PT_collection_custom_properties(bpy.types.Panel, PropertyPanel): #For adding custom properties to collections, fixed on 3.3 and up so not needed there
    _context_path = "collection"
    _property_type = bpy.types.Collection
    bl_label = "Custom Properties"
    bl_idname = "GU_PT_collection_custom_properties"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "collection"

"""	
def re_mesh_import(self, context):
	self.layout.operator(ImportREMesh.bl_idname, text="RE Mesh (.mesh.x)")
	
def re_mesh_export(self, context):
	self.layout.operator(ExportREMesh.bl_idname, text="RE Mesh (.mesh.x)")

def re_mdf_import(self, context):
	self.layout.operator(ImportREMDF.bl_idname, text="RE MDF (.mdf2.x)")
	
def re_mdf_export(self, context):
	self.layout.operator(ExportREMDF.bl_idname, text="RE MDF (.mdf2.x)")
"""

class IMPORT_MT_re_mesh_editor(bpy.types.Menu):
    bl_label = "RE Mesh Editor"
    bl_idname = "IMPORT_MT_re_mesh_editor"
    
    def draw(self, context):
        layout = self.layout
        
        layout.operator(ImportREMesh.bl_idname, text="RE Mesh (.mesh.x) (Model)",icon = "MESH_DATA")
        layout.operator(ImportREMDF.bl_idname, text="RE MDF (.mdf2.x) (Materials)",icon = "MATERIAL")
        layout.operator(ImportREFBXSkel.bl_idname, text="RE FBXSkel (.fbxskel.x) (Skeleton)",icon = "ARMATURE_DATA")

def re_mesh_editor_import(self, context):
	self.layout.menu("IMPORT_MT_re_mesh_editor",icon = "MOD_LINEART")
	
class EXPORT_MT_re_mesh_editor(bpy.types.Menu):
    bl_label = "RE Mesh Editor"
    bl_idname = "EXPORT_MT_re_mesh_editor"
    
    def draw(self, context):
        layout = self.layout
        
        layout.operator(ExportREMesh.bl_idname, text="RE Mesh (.mesh.x) (Model)",icon = "MESH_DATA")
        layout.operator(ExportREMDF.bl_idname, text="RE MDF (.mdf2.x) (Materials)",icon = "MATERIAL")
        layout.operator(ExportREFBXSkel.bl_idname, text="RE FBXSkel (.fbxskel.x) (Skeleton)",icon = "ARMATURE_DATA")

def re_mesh_editor_export(self, context):
	self.layout.menu("EXPORT_MT_re_mesh_editor",icon = "MOD_LINEART")

def register():
	addon_updater_ops.register(bl_info)
	for classEntry in classes:
		bpy.utils.register_class(classEntry)
		
	bpy.utils.register_class(IMPORT_MT_re_mesh_editor)
	bpy.utils.register_class(EXPORT_MT_re_mesh_editor)
	
	if (3, 3, 0) > bpy.app.version:
		bpy.utils.register_class(GU_PT_collection_custom_properties)
	
	
	#REGISTER PROPERTY GROUP PROPERTIES
	bpy.types.Scene.re_mdf_toolpanel = PointerProperty(type=MDFToolPanelPropertyGroup)
	bpy.types.Object.re_mdf_material = PointerProperty(type=MDFMaterialPropertyGroup)
	
	
	
	#bpy.types.TOPBAR_MT_file_import.append(re_mesh_import)
	#bpy.types.TOPBAR_MT_file_export.append(re_mesh_export)
	#bpy.types.TOPBAR_MT_file_import.append(re_mdf_import)
	#bpy.types.TOPBAR_MT_file_export.append(re_mdf_export)
	
	bpy.types.TOPBAR_MT_file_import.append(re_mesh_editor_import)
	bpy.types.TOPBAR_MT_file_export.append(re_mesh_editor_export)

	#Blender 4.1 and higher drag and drop operators
	if bpy.app.version >= (4, 1, 0):
		bpy.utils.register_class(MESH_FH_drag_import)
		bpy.utils.register_class(MDF_FH_drag_import)
		bpy.utils.register_class(TEX_FH_drag_import)
		bpy.utils.register_class(FBXSKEL_FH_drag_import)
		
	
def unregister():
	addon_updater_ops.unregister()
	for classEntry in classes:
		bpy.utils.unregister_class(classEntry)
		
	bpy.utils.unregister_class(IMPORT_MT_re_mesh_editor)
	bpy.utils.unregister_class(EXPORT_MT_re_mesh_editor)
	
	if (3, 3, 0) > bpy.app.version:
		bpy.utils.unregister_class(GU_PT_collection_custom_properties)
		
	
	#bpy.types.TOPBAR_MT_file_import.remove(re_mesh_import)
	#bpy.types.TOPBAR_MT_file_export.remove(re_mesh_export)
	#bpy.types.TOPBAR_MT_file_import.remove(re_mdf_import)
	#bpy.types.TOPBAR_MT_file_export.remove(re_mdf_export)
	
	bpy.types.TOPBAR_MT_file_import.remove(re_mesh_editor_import)
	bpy.types.TOPBAR_MT_file_export.remove(re_mesh_editor_export)
	
	if bpy.app.version >= (4, 1, 0):
		bpy.utils.unregister_class(MESH_FH_drag_import)
		bpy.utils.unregister_class(MDF_FH_drag_import)
		bpy.utils.unregister_class(TEX_FH_drag_import)
		bpy.utils.unregister_class(FBXSKEL_FH_drag_import)
if __name__ == '__main__':
	register()
	