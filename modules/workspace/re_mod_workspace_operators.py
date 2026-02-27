#Author: NSA Cloud
import bpy
import os
import shutil
from datetime import datetime
import json
import platform
from bpy.types import Operator
from zlib import crc32
from ..gen_functions import slugify,openFolder,raiseWarning
popup_regions = set()

from ..mesh.blender_re_mesh import joinObjects,getCollection
from ..mdf.blender_re_mdf import reindexMaterials
from ..mdf.re_mdf_presets import readPresetJSON
from .re_mod_workspace_propertyGroups import ConvertedMaterialEntryPropertyGroup
from .texturepacker.texture_bake import bakeMaterialMaps
from .texturepacker.texture_pack import packTextures
from .texturepacker.re_texture_analysis import analyzeMaterial,analyzePreset
from .texturepacker.image_utils import generatePlaceholderMaps
from ..blender_utils import showMessageBox

FILE_FORMAT = "TARGA"#Only viable option for all softwares, png is annoying to open in photoshop, tiff conversion doesn't work on linux, only problem is tga files are big
FILE_EXT = ".tga"

STANDARD_SAMPLES = 1
AO_SAMPLES = 1024




def does_region_exist(region):
	""" hack: https://github.com/blender/blender/blob/83dcaf0501390bef1c6073f9e3103923c405050a/scripts/addons_core/bl_pkg/bl_extension_notify.py#L544 """
	try:
		with bpy.context.temp_override(region=region):
			return True
	except TypeError:
		return False

def update_popups():
	#print('update popups')
	for region in list(popup_regions):
		if does_region_exist(region):
			region.tag_redraw()
			try:
				region.tag_refresh_ui()
			except:
				pass 
		else:
			popup_regions.discard(region)

	return 1

def createModInfo(filePath,modName):
	with open(filePath,"w") as file:
		file.write(

f"""name = {modName}
version = 1.0
screenshot = showcase.jpg
description = Your mod description here
author = Your name here

;Delete the semicolon before these options to use them.

;NameAsBundle = bundleNameHere
;This option will group any mods with the same bundle name.

;AddonFor = modNameHere
;This option will group this mod inside a menu of another mod.
"""
		)


def getAssetLibDir(gameName):
	targetLibName = f"RE Assets - {gameName}"
	for lib in bpy.context.preferences.filepaths.asset_libraries:
		if lib.name == targetLibName:
			libDir = bpy.path.abspath(lib.path)
			if os.path.isfile(os.path.join(libDir,f"GameInfo_{gameName}.json")):
				return libDir
			else:
				print(os.path.join(libDir,f"GameInfo_{gameName}.json") + " is missing.")
	return None

def verifyAssetLib(gameName):
	libDir = getAssetLibDir(gameName)
	if libDir != None:
		extractInfoPath = os.path.join(libDir,f"ExtractInfo_{gameName}.json")
		if os.path.isfile(extractInfoPath):
			return True
	return False

def getAssetLibEXEPath(gameName):
	libDir = getAssetLibDir(gameName)
	exePath = None
	if libDir != None:
		extractInfoPath = os.path.join(libDir,f"ExtractInfo_{gameName}.json")
		if os.path.isfile(extractInfoPath):
			extractInfo = None
			try:
				with open(extractInfoPath,"r", encoding ="utf-8") as file:
					#extractInfoDict["exePath"] = exePath
					#extractInfoDict["exeDate"] = os.path.getmtime(exePath)
					#extractInfoDict["exeCRC"] = getFileCRC(exePath)
					#extractInfoDict["extractPath"] = newDirPath
					extractInfo = json.load(file)
					
			except:
				print(f"Failed to load {extractInfoPath}")
			if extractInfo != None:
				exePath = extractInfo["exePath"]
	return exePath

def getMDFGameNames(self,context):
	return [(item.identifier, item.name, item.description) for item in context.scene.re_mdf_toolpanel.bl_rna.properties['activeGame'].enum_items]

def update_modName(self, context):#Force mod name to alphanumeric with underscores and hyphens
	self.internalName = slugify(self.modName,allow_unicode = False)

def update_internalName(self, context):
	self.invalidInternalName = self.internalName != slugify(self.internalName,allow_unicode = False)
		
def update_workDirectory(self, context):
	update_popups()

def update_gameName(self, context):
	legacyGameNames = {"DMC5","RE2","RE3"}
	if self.gameName in legacyGameNames:
		self.platform = "x64"
	else:
		self.platform = "STM"

def getSceneEXEPath():
	exePath = None
	if bpy.context.scene.get("modWorkspace_exePath",None) == None:
		exePath = getAssetLibEXEPath(bpy.context.scene["modWorkspace_gameName"])
		
		if exePath != None:
			bpy.context.scene["modWorkspace_exePath"] = exePath
			#Check to see if game uses direct storage or not to determine whether tex can be copied to the game dir without issue.
			allowTexCopy = True
			for entry in os.scandir(os.path.dirname(exePath)):
				if entry.name.endswith(".pak") and "sub_000" in entry.name:
					allowTexCopy = False
					break
			bpy.context.scene["modWorkspace_allowTexCopy"] = allowTexCopy
			print(f"Set EXE path for workspace: {exePath}")
			print(f"DirectStorage Used: {not allowTexCopy}")
	else:
		exePath = bpy.context.scene["modWorkspace_exePath"]
	return exePath

class WM_OT_CreateModWorkspace(Operator):
	bl_label = "Create Mod Workspace"
	bl_idname = "re_mod_workspace.create_mod_workspace"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Set up a mod workspace directory for RE Engine games.\nThe purpose of this is to streamline mod development by reducing redundant tasks where possible.\n"
	modName : bpy.props.StringProperty(
		name="Mod Name",
		description="Enter the name of your new mod",
		update = update_modName,
		options={'TEXTEDIT_UPDATE'},
		default = "New Mod"
		)
	internalName : bpy.props.StringProperty(
		name="Internal Mod Name",
		description="This is the mod name used in file paths.\nHyphens, underscores and alphanumeric characters only",
		update = update_internalName,
		default = "New_Mod"
		)
	invalidInternalName : bpy.props.BoolProperty(default = False)
	workDirectory : bpy.props.StringProperty(
		name="Work Directory",
		description="Location to place the newly created mod workspace folder",
		subtype='DIR_PATH',
		update = update_workDirectory
		)
	
	gameName: bpy.props.EnumProperty(
		name="Game",
		description="Choose which game you're creating the mod for. This is used to determine which asset library to extract files from",
		items=getMDFGameNames,
		update = update_gameName
		)
	platform: bpy.props.EnumProperty(
		name="Platform",
		description="Set where you downloaded the game from. This is used to determine the path needed to place files",
		items=[("x64", "Steam (Older Titles)", "(x64) Choose this option for DMC5 and the non ray tracing versions of RE2 and RE3. (Before 2021)"),
			   ("STM", "Steam", "(STM) Choose this option for all newer titles. (2021 or newer)"),
			   ("MSG", "Game Pass", "(MSG) Choose this option if you own the Microsoft Game Pass version of the game."),
			   ]
		,default = "STM"
		)
	saveBlendFile : bpy.props.BoolProperty(name = "Save .blend file to the mod workspace",description = "Save the current blend file to the newly created mod workspace directory",default = True)
	openWorkspace : bpy.props.BoolProperty(name = "Open mod workspace after creation",description = "After the mod workspace is created, open it in File Explorer",default = True)
	editMode : bpy.props.BoolProperty(name = "",default = False)
	
	def draw(self,context):
		region_popup = context.region_popup
		if region_popup:
			popup_regions.add(region_popup)
		layout = self.layout
		layout.prop(self,"modName")
		layout.prop(self,"internalName")
		if self.invalidInternalName:
			layout.label(icon = "ERROR",text = "Invalid internal name, only alphanumeric characters, hyphens and underscores can be used")
		layout.prop(self,"workDirectory")
		if os.path.isdir(self.workDirectory) and self.internalName != "":
			if self.editMode:
				layout.label(text="Mod files will be copied to:")
			else:
				layout.label(text="Mod files will be saved to:")
			layout.label(text =f"{os.path.join(bpy.path.abspath(self.workDirectory),self.internalName)}")
		else:
			layout.label(icon = "ERROR",text=f"Set the work directory and mod name to determine where to create the new mod directory.")
		layout.prop(self,"gameName")
		layout.prop(self,"platform")
		layout.prop(self,"saveBlendFile")
		layout.prop(self,"openWorkspace")
			
	def execute(self, context):
		
		
		
		workDir =  bpy.path.abspath(self.workDirectory)
		if not os.path.isdir(workDir):
			self.report({"ERROR"},"Invalid work directory.")
			return {'CANCELLED'}
		
		if self.internalName != slugify(self.internalName):
			self.report({"ERROR"},"Invalid internal mod name.")
			return {'CANCELLED'}
		
		if self.editMode:
			originalModDir = bpy.path.abspath(bpy.context.scene["modWorkspace_directory"])
		
		modDir = os.path.join(workDir,self.internalName)
		
		os.makedirs(modDir,exist_ok = True)
		os.makedirs(os.path.join(modDir,"textures_original"),exist_ok = True)
		#os.makedirs(os.path.join(modDir,"textures_bake"),exist_ok = True)
		os.makedirs(os.path.join(modDir,"textures_final"),exist_ok = True)
		os.makedirs(os.path.join(modDir,"modOutput",self.internalName,"natives",self.platform),exist_ok = True)
		
		if not self.editMode:
			createModInfo(os.path.join(modDir,"modOutput",self.internalName,"modinfo.ini"),self.modName)
		else:
			if originalModDir != modDir:
				print(f"Copying {originalModDir} to {modDir}")
				try:
					shutil.copytree(originalModDir, modDir, dirs_exist_ok=True)
				except Exception as e:
					print(f"Failed to copy {originalModDir} to {modDir} - {e}")
		bpy.context.scene["modWorkspace_setup"] = True
		bpy.context.scene["modWorkspace_directory"] = modDir
		bpy.context.scene["modWorkspace_modName"] = self.modName
		bpy.context.scene["modWorkspace_internalName"] = self.internalName
		bpy.context.scene["modWorkspace_gameName"] = self.gameName
		bpy.context.scene.re_mdf_toolpanel.activeGame = self.gameName
		bpy.context.scene.re_mdf_toolpanel.modDirectory = os.path.join(modDir,"modOutput",self.internalName,"natives",self.platform+os.sep)
		bpy.context.scene.re_mdf_toolpanel.textureDirectory = os.path.join(modDir,"textures_final")
		bpy.context.scene["modWorkspace_platform"] = self.platform
		try:
			shutil.copyfile(os.path.join(os.path.dirname(__file__),"mod_showcase_template.jpg"),os.path.join(modDir,"modOutput",self.internalName,"showcase.jpg"))
		except Exception as err:
			print("Failed to copy " + os.path.join(os.path.dirname(__file__),"mod_showcase_template.jpg")+" to "+os.path.join(modDir,"modOutput",self.internalName,"showcase.jpg") + " - " + str(err))
		bpy.context.scene["lastExportedPatchPak"] = os.path.join(modDir,"modOutput",self.internalName+".pak")
		if self.saveBlendFile:
			bpy.ops.wm.save_as_mainfile(filepath=os.path.join(modDir,self.internalName+".blend"))
		if self.openWorkspace:
			openFolder(modDir)
		
		#Get exe path from asset library if present
		exePath = getSceneEXEPath()
		
		self.report({"INFO"},"Created mod workspace.")
		
		return {'FINISHED'}
	
	def invoke(self,context,event):
		if bpy.context.scene.get("modWorkspace_setup") == True:
			self.editMode = True
			self.workDirectory = os.path.dirname(bpy.context.scene["modWorkspace_directory"])
			self.modName = bpy.context.scene["modWorkspace_modName"]
			self.internalName = bpy.context.scene["modWorkspace_internalName"]
			self.gameName = bpy.context.scene["modWorkspace_gameName"]
			self.platform = bpy.context.scene["modWorkspace_platform"]
			
		else:
			self.editMode = False
		self.gameName = bpy.context.scene.re_mdf_toolpanel.activeGame
		return context.window_manager.invoke_props_dialog(self,width = 500)
	
class WM_OT_EditModInfo(Operator):
	bl_label = "Edit modinfo.ini"
	bl_idname = "re_mod_workspace.edit_modinfo"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Open modinfo.ini in the text editor.\nThis sets the name of the mod and description shown in Fluffy Manager.\nBe sure to also replace showcase.jpg in the modOutput folder with an image for your mod"
	@classmethod
	def poll(self,context):
		return "modWorkspace_setup" in context.scene
	
	def execute(self, context):
		
		if bpy.context.scene.get("modWorkspace_setup"):
			filepath = os.path.join(bpy.context.scene["modWorkspace_directory"],"modOutput",bpy.context.scene["modWorkspace_internalName"],"modinfo.ini")
			
			bpy.ops.wm.window_new()
			new_window = bpy.context.window_manager.windows[-1]
			screen = new_window.screen
			
			text_area = screen.areas[0]
			text_area.type = 'TEXT_EDITOR'
			
			filename = os.path.basename(filepath)
			
			if filename in bpy.data.texts:
				text_block = bpy.data.texts[filename]
			else:
				text_block = bpy.data.texts.load(filepath)
			
			for area in screen.areas:
				if area.type == 'TEXT_EDITOR':
					area.spaces.active.text = text_block
					break
		return {'FINISHED'}



def RNAToDict(rna_obj):
    data = {}
    for prop in rna_obj.bl_rna.properties:
        if prop.is_readonly:
            continue

        identifier = prop.identifier

        try:
            value = getattr(rna_obj, identifier)

            # Only store simple serializable types
            if isinstance(value, (int, float, str, bool)):
                data[identifier] = value

        except Exception:
            pass

    return data


def saveRenderSettings(scene=None):
    if scene is None:
        scene = bpy.context.scene

    return {
        "engine": scene.render.engine,
        "render": RNAToDict(scene.render),
        "cycles": RNAToDict(scene.cycles) if hasattr(scene, "cycles") else {},
        "eevee": RNAToDict(scene.eevee) if hasattr(scene, "eevee") else {},
        "view_settings": RNAToDict(scene.view_settings),
        "display_settings": RNAToDict(scene.display_settings),
    }


def applyDictToRNA(rna_obj, data):
    for key, value in data.items():
        if not hasattr(rna_obj, key):
            continue

        try:
            setattr(rna_obj, key, value)
        except Exception:
            # Skip properties that fail (enum mismatch, engine mismatch, etc.)
            pass


def restoreRenderSettings(settingsDict, scene=None):
    if scene is None:
        scene = bpy.context.scene

    # Restore engine first (important!)
    if "engine" in settingsDict:
        scene.render.engine = settingsDict["engine"]

    # Apply main render settings
    applyDictToRNA(scene.render, settingsDict.get("render", {}))

    if scene.render.engine == 'CYCLES' and "cycles" in settingsDict:
        applyDictToRNA(scene.cycles, settingsDict["cycles"])

    if scene.render.engine == 'BLENDER_EEVEE' and "eevee" in settingsDict:
        applyDictToRNA(scene.eevee, settingsDict["eevee"])

    applyDictToRNA(scene.view_settings, settingsDict.get("view_settings", {}))
    applyDictToRNA(scene.display_settings, settingsDict.get("display_settings", {}))


def setCollectionVisibility(collectionName,hide):
    viewLayer = bpy.context.view_layer

    def findLayerCollection(layerCollection, name):
        if layerCollection.name == name:
            return layerCollection
        for child in layerCollection.children:
            result = findLayerCollection(child, name)
            if result:
                return result
        return None

    layerCollection = findLayerCollection(viewLayer.layer_collection, collectionName)

    if layerCollection:
        layerCollection.hide_viewport = hide

def getFileCRC(filePath):
	size = 1024*1024*10  # 10 MiB chunks
	with open(filePath, 'rb') as f:
	    crcval = 0
	    while chunk := f.read(size):
	        crcval = crc32(chunk, crcval)
	return crcval

class WM_OT_ConvertToREEngine(Operator):
	bl_label = "Convert Model to RE Engine"
	bl_idname = "re_mod_workspace.convert_to_re_engine"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Convert a model into RE Engine format. Bakes textures, renames meshes and assigns materials.\nNOTE: This does not handle rigging the model to the RE Engine skeleton.\nYou have to rig the model to the skeleton yourself.\nThis feature works best on materials set up using a Principled BSDF shader."
	mode: bpy.props.EnumProperty(
		name="Mode",
		description="Set the way in which you want materials to be converted to RE Engine",
		items=[("BAKE", "Bake Materials","Bake all materials into standard PBR format and convert them into RE Engine texture formats.\nThis can take a long time depending on texture resolution and PC specs"),
			   ("PLACEHOLDER", "Generate Placeholder Textures", "Generate blank placeholder textures for the converted materials in the textures_final directory.\nUse this option if you don't have materials set up in Blender for your model or if you don't want to wait for baking.\nTip: You can apply changes to textures you made using the Apply Active MDF button in the RE MDF tools tab"),
			   ]
		,default = "BAKE"
		)
	meshCollectionName: bpy.props.StringProperty(
		name="Mesh File Name",
		description = "Set the collection to place converted meshes. If an existing collection is chosen, all existing meshes in it will be moved into a collection called Removed Meshes",
		default = "newModel.mesh"
		)
	mdfCollectionName: bpy.props.StringProperty(
		name="Material File Name",
		description = "Set the collection to place converted materials. If an existing collection is chosen, all existing materials in it will be moved into a collection called Removed Materials",
		default = "newModel.mdf2"
		)
	
	texturePath: bpy.props.StringProperty(
		name="Texture Path",
		description = "Set the path to place custom textures at",
		default = "custom_textures/"
		)
	materialList_items: bpy.props.CollectionProperty(type = ConvertedMaterialEntryPropertyGroup)
	materialList_index: bpy.props.IntProperty(name="")
	objectCount: bpy.props.IntProperty(#For display
		name="",
		default = 0
		)
	skipAOBake : bpy.props.BoolProperty(name = "Skip Ambient Occlusion Baking",description = "Skip baking ambient occlusion. This will decrease baking times significantly.\nThis option is the same as unchecking Bake Ambient Occlusion, this option is intended for saving time by not having to uncheck it on all materials",default = True)
	saveBakedTextures : bpy.props.BoolProperty(name = "Save Texture Bakes",description = "Save intermediary baked textures to the textures_bake directory.",default = True)
	useExistingBakes : bpy.props.BoolProperty(name = "Use Existing Bakes",description = "If textures already exist in the textures_bake directory, use them instead of rebaking",default = True)
	moveCollectionObjects : bpy.props.BoolProperty(name = "Move Existing Collection Objects",description = "Move all existing meshes and materials out of the specified mesh and MDF collection once the model is converted.\nMoved objects are placed into the Removed Meshes and Removed MDF Materials collections respectively.\nLeaving this enabled is recommended",default = True)
	debugBakeOnly : bpy.props.BoolProperty(name = "DEBUG - Bake Only",description = "Only bake the textures, do not pack or change objects",default = False)
	@classmethod
	def poll(self,context):
		return "modWorkspace_setup" in context.scene and len(bpy.context.selected_objects) != 0
	def invoke(self, context, event):
		region = bpy.context.region
		centerX = region.width // 2
		centerY = region.height
		objList = [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]
		if len(objList) == 0:
			self.report({"ERROR"},"No meshes are selected.")
			return {'CANCELLED'}
		self.objectCount = len(objList)
		#currentX = event.mouse_region_X
		#currentY = event.mouse_region_Y
		if "modWorkspace_gameName" not in bpy.context.scene:
			self.report({"ERROR"},"Mod workspace is not set up.")
			return {'CANCELLED'}
		
		gameName = bpy.context.scene["modWorkspace_gameName"]
		presetList = []
		presetDir = os.path.join(os.path.dirname(os.path.dirname(os.path.split(os.path.abspath(__file__))[0])),"Presets")
		gamePresetDir = os.path.join(presetDir,gameName)
		print(f"Preset Directory:{gamePresetDir}")
		
		if os.path.isdir(gamePresetDir):
			for entry in os.scandir(gamePresetDir):
				if entry.is_file() and entry.name.endswith(".json"):
					presetList.append(os.path.join(gameName,entry.name))
		
		if len(presetList) == 0:
			self.report({"ERROR"},f"There are no material presets saved for {gameName}. This feature cannot be used without presets.")
			return {'CANCELLED'} 
		
		#Get last imported mesh and mdf collection
		if "REMeshLastImportedCollection" in bpy.context.scene:
			if bpy.context.scene["REMeshLastImportedCollection"] in bpy.data.collections:
				meshCollection = bpy.data.collections[bpy.context.scene["REMeshLastImportedCollection"]]
				self.meshCollectionName = meshCollection.name
				#Find mdf collection by finding parent collection of mesh and then searching the child collection for the mdf
				parentCollection = None
				if meshCollection.users > 1:
					for collection in bpy.data.collections:
						if meshCollection.name in collection.children:
							parentCollection = collection
							break
				if parentCollection != None:
					for collection in parentCollection.children:
						if collection.get("~TYPE") == "RE_MDF_COLLECTION":
							mdfCollection = collection
							self.mdfCollectionName = mdfCollection.name
							break
				else:
					mdfCollection = None
					
		
		materialNameSet = set()
		for obj in objList:
			if obj.type == "MESH":
				for material in obj.data.materials:
					if material != None:
						materialNameSet.add(material.name)
		
		if len(materialNameSet) == 0:
			self.report({"ERROR"},f"The selected objects have no materials.")
			return {'CANCELLED'} 			
		
		for materialName in sorted(list(materialNameSet)):
			material = bpy.data.materials[materialName]
			matInfoDict = analyzeMaterial(material,presetList, gameName,self.meshCollectionName)
			item = self.materialList_items.add()
			item.oldMaterialName = materialName
			item.materialPreset = matInfoDict["materialPreset"]
			item.imageXRes = matInfoDict["imageXRes"]
			item.imageYRes = matInfoDict["imageYRes"]
			item.newMaterialName = slugify(materialName,allow_unicode = False)
			item.textureSetName = item.newMaterialName
			item.uv2AOBake = matInfoDict["uv2AOBake"]
			
		self.texturePath = os.path.join("custom_tex",bpy.context.scene["modWorkspace_internalName"]).replace(os.sep,"/")
		
		context.window.cursor_warp(centerX,centerY)
	
		return context.window_manager.invoke_props_dialog(self,width = 750,confirm_text = "Convert to RE Engine")
	def draw(self,context):
		layout = self.layout
		layout.label(text="This feature is experimental and may not work with all material setups.",icon = "ERROR")
		split = layout.split(factor=0.6)
		col = split.column()
		col.prop(self, "mode")
		col.separator()
		
		#layout.label(text=f"{self.objectCount} objects selected.")
		col.prop(self, "meshCollectionName",icon = "COLLECTION_COLOR_01")
		col.prop(self, "mdfCollectionName",icon = "COLLECTION_COLOR_05")
		col.prop(self, "texturePath")
		col = split.column()
		
		row = layout.row().separator()
		split = layout.split(factor = .55)
		col1 = split.column()
		split2 = col1.split()
		col1sub1 = split2.column()
		col1sub1.alignment = "LEFT"
		col1sub1.label(text="Material List")
		col1sub2 = col1.column()
		row = split2.row()
		row.alignment = "RIGHT"
		col1.template_list(
			listtype_name = "REMOD_UL_MaterialConversionList", 
			list_id = "materialList",
			dataptr = self,
			propname = "materialList_items",
			active_dataptr = self, 
			active_propname = "materialList_index",
			rows = 10,
			type='DEFAULT'
			)
		col2 = split.column()
		col2.label(text="Material Settings")
		if self.materialList_index != -1:
			item = self.materialList_items[self.materialList_index]
			#col2.label(text="")
			
			col2.prop(item, "newMaterialName",text="Name")
			col2.prop(item,"textureSetName",text="Texture Set")
			col2.label(text="Resolution")
			row = col2.row()
			row.prop(item,"imageXRes",text = "X")
			row.prop(item,"imageYRes",text = "Y")
			if not (((item.imageXRes & (item.imageXRes-1) == 0) and item.imageXRes != 0) and ((item.imageYRes & (item.imageYRes-1) == 0) and item.imageYRes != 0)):
				col2.label(text = "Invalid texture resolution.",icon="ERROR")
				col2.label(text = "Must be a power of two. (256,512,1024,2048,etc.)")
			col2.separator()
			col2.prop(item,"bakeAO")
			#col2.prop(item, "uv2AOBake")#Not implemented yet
		layout.separator(type = "LINE")
		layout.label(text = "Extra Options:")
		
		row = layout.row()
		col = row.column()
		col.enabled = self.mode != "PLACEHOLDER"
		col.prop(self,"skipAOBake")
		col.prop(self,"saveBakedTextures")
		col = row.column()
		col.prop(self,"moveCollectionObjects")
		col.prop(self,"useExistingBakes")
		
		#Debug
		
		#col.prop(self,"debugBakeOnly")
			
	def execute(self, context):
		if bpy.context.scene.get("modWorkspace_setup"):
			materialInfoDict = dict()
			for item in self.materialList_items:
				materialInfoDict[item.oldMaterialName] = {
					"materialName":slugify(item.newMaterialName),
					"textureSetName":slugify(item.textureSetName),
					"materialPreset":item.materialPreset,
					"imageXRes":item.imageXRes,
					"imageYRes":item.imageYRes,
					"bakeAO":item.bakeAO,
					"uv2AOBake":item.uv2AOBake,
					
					
					}
				if self.skipAOBake:
					materialInfoDict[item.oldMaterialName]["bakeAO"] = False
			gameName = bpy.context.scene["modWorkspace_gameName"]
			bpy.context.scene.re_mdf_toolpanel.activeGame = gameName
			presetDir = os.path.join(os.path.dirname(os.path.dirname(os.path.split(os.path.abspath(__file__))[0])),"Presets")
			
			
			bakeTextureDir = os.path.join(bpy.context.scene["modWorkspace_directory"],"textures_bake")
			if self.saveBakedTextures or self.debugBakeOnly:
				os.makedirs(bakeTextureDir,exist_ok = True)
			finalTextureDir = os.path.join(bpy.context.scene["modWorkspace_directory"],"textures_final")
			objNameList = [obj.name for obj in bpy.context.selected_objects if obj.type == "MESH"]
			try: 
				bpy.ops.wm.console_toggle()
			except:
				 pass
			
			if self.meshCollectionName in bpy.data.collections:
				meshCollection = getCollection(self.meshCollectionName)
			else:
				parentCollection = getCollection(self.meshCollectionName.split(".mesh")[0])
				meshCollection = getCollection(self.meshCollectionName,parentCollection)
				print("Created new mesh collection.")
			
			if self.meshCollectionName in bpy.data.collections:
				mdfCollection = getCollection(self.mdfCollectionName)
			else:
				parentCollection = getCollection(self.mdfCollectionName.split(".mdf2")[0])
				mdfCollection = getCollection(self.mdfCollectionName,parentCollection)
				bpy.context.scene.re_mdf_toolpanel.mdfCollection = mdfCollection
				print("Created new mdf collection.")
			
			if self.moveCollectionObjects:
				#Remove objects from existing collections
				removedMeshesCollection = getCollection("Removed Meshes")
				collectionObjNameList = []
				for obj in meshCollection.all_objects:
					if obj.type == "MESH":
						collectionObjNameList.append(obj.name)
				
				for objName in collectionObjNameList:
					obj = bpy.data.objects[objName]
					for collection in obj.users_collection:
						   collection.objects.unlink(obj)
					removedMeshesCollection.objects.link(obj)
				#Remove existing materials from collection
				removedMaterialsCollection = getCollection("Removed MDF Materials")
				collectionObjNameList = []
				for obj in mdfCollection.all_objects:
					collectionObjNameList.append(obj.name)
				
				for objName in collectionObjNameList:
					obj = bpy.data.objects[objName]
					for collection in obj.users_collection:
						   collection.objects.unlink(obj)
					removedMaterialsCollection.objects.link(obj)
			
			#Save current scene render/cycles settings to restore when finished
			savedRenderSettingsDict = saveRenderSettings()

			setCollectionVisibility(meshCollection.name,hide = False)
			setCollectionVisibility(meshCollection.name.split(".mesh")[0],hide = False)#Unhide parent collection if hidden

			print(f"Mesh Collection: {meshCollection.name}")
			print(f"MDF Collection: {mdfCollection.name}")
			
			print("Starting REE Bake Process")
			cloneObjList = []
			dg = bpy.context.evaluated_depsgraph_get()
			bakeObjCollection = getCollection("REE Bake Objects")
			for objName in objNameList:
				obj = bpy.data.objects[objName]
				cloneObj = bpy.data.objects.new(f"CLN_{obj.name}",bpy.data.meshes.new_from_object(obj.evaluated_get(dg)))
				bakeObjCollection.objects.link(cloneObj)
				print(f"Created temporary clone of {obj.name}")
				cloneObjList.append(cloneObj)

			bpy.ops.object.select_all(action='DESELECT')


			#Join all objects, then separate them by materials
			#Having each material as a separate mesh reduces the bake time by a lot
			bpy.context.view_layer.objects.active = cloneObjList[0]
			joinedObj = joinObjects(cloneObjList)
			joinedObj.name = "REE_BAKE_OBJECT"
			for collection in joinedObj.users_collection:
				   collection.objects.unlink(joinedObj)
			
			bakeObjCollection.objects.link(joinedObj)
			bpy.context.view_layer.objects.active = joinedObj
			oldObjNameSet = set([obj.name for obj in bpy.data.objects])
			bpy.ops.object.mode_set(mode='EDIT')
			bpy.ops.mesh.separate(type='MATERIAL')
			bpy.ops.object.mode_set(mode='OBJECT')
			newObjNameSet = set([obj.name for obj in bpy.data.objects])

			newObjNameList = list({joinedObj.name}.union(newObjNameSet.difference(oldObjNameSet)))

			#Create a flat plane for baking normal maps, this is so that the normal map can be transferred even if it uses a non standard format
			#Also avoids the issue of the object's low poly vertex normals affecting the bake
			normalBakeData = bpy.data.meshes.new("REE_NORMAL_BAKE_OBJECT")
			normalBakeData.from_pydata(
				[(-1.0, -1.0, 0.0), (1.0, -1.0, 0.0), (1.0, 1.0, 0.0), (-1.0, 1.0, 0.0)],
				[],
				[(0, 1, 2, 3)],	
				)
			
				
			normalBakeObj = bpy.data.objects.new("REE_NORMAL_BAKE_OBJECT",normalBakeData)
			bakeObjCollection.objects.link(normalBakeObj)
			#
			
			print("Switching to Cycles.")
			bpy.context.scene.render.engine = "CYCLES"
			newMatNameList = []
			uvList = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]#normal bake uvs
			
			oldImageNameSet = set([image.name for image in bpy.data.images])#Save names of images to determine what new images were baked
			
			print("Created bake objects.")
			savedRenderHideSettingsDict = {obj.name:obj.hide_render for obj in bpy.context.scene.objects if obj.type == "MESH"}
			for obj in bpy.context.scene.objects:
				if obj.type == "MESH":
					obj.hide_render = True
			for index, bakeObjName in enumerate(newObjNameList):
				bakeObj = bpy.data.objects[bakeObjName]
				bakeObj.hide_render = False
				bpy.ops.object.select_all(action='DESELECT')
				bakeObj.select_set(True)
				
				bpy.context.view_layer.objects.active = bakeObj
				
				#Clear existing uvs from normal bake
				uvIndex = len(normalBakeObj.data.uv_layers) - 1
				for uv in reversed(normalBakeObj.data.uv_layers):
					obj.data.uv_layers.remove(normalBakeObj.data.uv_layers[uvIndex])
					uvIndex -= 1
				
				#Copy uv map names from bake object to normal bake obj
				for i in range(0,len(bakeObj.data.uv_layers)):
					
					layer = normalBakeObj.data.uv_layers.new(name=bakeObj.data.uv_layers[i].name)
					for loop in normalBakeObj.data.loops:
						   layer.data[loop.index].uv = uvList[loop.vertex_index]
				
				
				if len(normalBakeObj.data.uv_layers) != 0:
					normalBakeObj.data.uv_layers.active = normalBakeObj.data.uv_layers[0]
				
				for slot in bakeObj.material_slots:
					if slot is not None:
						
						newMat = slot.material.copy()
						matInfo = materialInfoDict[slot.material.name]
						newMat.name = "REE_BAKE_" + matInfo["materialName"]
						newMatNameList.append(newMat.name)
						materialName = matInfo["materialName"]
						textureSetName = matInfo["textureSetName"]
						slot.material = newMat
						#Clear existing materials on normal bake
						normalBakeObj.data.materials.clear()
						normalBakeObj.data.materials.append(newMat)
						normalBakeObj.data.update()
						print(f"Baking material - {materialName} ({index+1} / {len(newObjNameList)})")
						print("Preset: "+matInfo["materialPreset"])
						presetPath = os.path.join(presetDir,matInfo["materialPreset"])
						textureMapDict = analyzePreset(presetPath)
						if self.mode != "PLACEHOLDER":
							bakeMaterialMaps(bakeObj,normalBakeObj,newMat,matInfo["textureSetName"],matInfo["imageXRes"],matInfo["imageYRes"],self.saveBakedTextures,bakeTextureDir,FILE_FORMAT,FILE_EXT,matInfo["bakeAO"],self.useExistingBakes)
						else:
							generatePlaceholderMaps(matInfo["textureSetName"],matInfo["imageXRes"],matInfo["imageYRes"],self.useExistingBakes,bakeTextureDir,FILE_EXT)
						if not self.debugBakeOnly:
							packTextures(textureSetName,list(textureMapDict.values()),matInfo["imageXRes"],matInfo["imageYRes"],finalTextureDir,FILE_FORMAT,FILE_EXT)
						
							materialObj = readPresetJSON(presetPath,mdfCollection)
							if materialObj:
								materialObj.re_mdf_material.materialName = matInfo["materialName"]
								textureSetName = matInfo["textureSetName"]
								for entry in materialObj.re_mdf_material.textureBindingList_items:
									if entry.textureType in textureMapDict:
										entry.path = os.path.join(self.texturePath,f"{textureSetName}_{textureMapDict[entry.textureType]}.tex").replace(os.sep,"/")
							else:
								raiseWarning(f"Failed to create MDF material from {presetPath}")
				bakeObj.hide_render = True
						
			#Unhide all
			for objName in savedRenderHideSettingsDict:
				if objName in bpy.context.scene.objects:
					bpy.context.scene.objects[objName].hide_render = savedRenderHideSettingsDict[objName]
			if self.debugBakeOnly:
				return {'FINISHED'}
			#Clean up render objects and materials
			for bakeObjName in newObjNameList:
				bpy.data.objects.remove(bpy.data.objects[bakeObjName],do_unlink = True)
			bpy.data.objects.remove(normalBakeObj,do_unlink = True)
			bpy.data.collections.remove(bakeObjCollection)
			
			for matName in newMatNameList:
				bpy.data.materials.remove(bpy.data.materials[matName])

			newImageNameSet = set([image.name for image in bpy.data.images])#Save names of images to determine what new images were baked
			
			for imageName in newImageNameSet.difference(oldImageNameSet):
				#print("Removing Image: " + imageName)
				bpy.data.images.remove(bpy.data.images[imageName])

			restoreRenderSettings(savedRenderSettingsDict)
			
			oldObjNameSet = set([obj.name for obj in bpy.data.objects])
			newObjNameList = []
			
			for objName in objNameList:#Move all meshes into the mesh collection
				obj = bpy.data.objects[objName]
				
				newObjNameList.append(objName)
				for collection in obj.users_collection:
					   collection.objects.unlink(obj)
				meshCollection.objects.link(obj)
				bpy.context.view_layer.objects.active = obj
				#Split each object by material
				bpy.ops.object.mode_set(mode='EDIT')
				bpy.ops.mesh.separate(type='MATERIAL')
				bpy.ops.object.mode_set(mode='OBJECT')
			newObjNameSet = set([obj.name for obj in bpy.data.objects])
			#print("new objects: " + str(newObjNameSet.difference(oldObjNameSet)))
			newObjNameList.extend(list(newObjNameSet.difference(oldObjNameSet)))#Get names of new objects created by material splitting if there are any
			newObjNameList.sort()
			materialSubMeshIndexDict = dict()
			#Rename objects to RE format
			for objName in newObjNameList:
				obj = bpy.data.objects[objName]
				if obj.data.materials[0].name not in materialSubMeshIndexDict:
					materialSubMeshIndexDict[obj.data.materials[0].name] = 0
				obj.name = f"Group_0_Sub_{materialSubMeshIndexDict[obj.data.materials[0].name]}__"+materialInfoDict[obj.data.materials[0].name]["materialName"]
				materialSubMeshIndexDict[obj.data.materials[0].name] += 1
			reindexMaterials(mdfCollection)
			
			bpy.ops.re_tex.convert_tex_directory(skipPrompt = True)
			bpy.ops.re_tex.copy_converted_tex()
			bpy.ops.re_mdf.apply_mdf()
			showMessageBox("Model converted to RE Engine format." + "\nExisting objects in collection were moved into the \"Removed Meshes\" collection." if self.moveCollectionObjects else "",title = "RE Model Conversion")
			self.report({"INFO"},"Converted selected models to RE Engine format.")
			try: 
				bpy.ops.wm.console_toggle()
			except:
				 pass
		return {'FINISHED'}

class WM_OT_TexturePacker(Operator):
	bl_label = "Texture Packer"
	bl_idname = "re_mod_workspace.texture_packer"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = ""
	@classmethod
	def poll(self,context):
		return "modWorkspace_setup" in context.scene
	
	def execute(self, context):
		if bpy.context.scene.get("modWorkspace_setup"):
			pass#TODO
		return {'FINISHED'}

#Blacklist for when files are copied from the mod directory to the game directory
FILE_BLACKLIST_NO_TEX = (".tex.",".png",".jpg",".ini",".txt",".pak")
FILE_BLACKLIST = (".png",".jpg",".ini",".txt",".pak")

class WM_OT_ToggleModFileTracking(bpy.types.Operator):
	bl_idname = "re_mod_workspace.toggle_mod_file_tracking"
	bl_label = "Toggle Mod File Tracking"
	bl_description = "Tracks changes made to files inside the modOutput directory and copies them to the game directory automatically. This is useful for editing files while the game is running.\nRE Asset Library must be installed.\nThe asset libary for the game must be installed and have the game extract paths set.\nNOTE: In MH Wilds and newer, .tex files are not copied, this is because tex files cannot be loose loaded in RE Engine games from 2025 and newer.\nUse the Create Patch Pak button to create a pak mod"
	
	_timer = None
	@classmethod
	def poll(self,context):
		return "modWorkspace_setup" in context.scene
	

	def execute(self, context):
		wm = context.window_manager
		if wm.enableModFileTracking:
			wm.enableModFileTracking = False
			return {'CANCELLED'}
		else:
			exePath = getSceneEXEPath()
			if bpy.context.scene.get("modWorkspace_directory") and os.path.isfile(exePath):
				print("Mod File Tracker: Started.")
				self.filePathDict = dict()
				self.pakPathDict = dict()
				self.allowTexCopy = bpy.context.scene["modWorkspace_allowTexCopy"]
				self.extensionBlackList = FILE_BLACKLIST if self.allowTexCopy else FILE_BLACKLIST_NO_TEX
				self.watchDir = os.path.join(bpy.context.scene["modWorkspace_directory"],"modOutput",bpy.context.scene["modWorkspace_internalName"])
				self.watchDirPak = os.path.join(bpy.context.scene["modWorkspace_directory"],"modOutput")
				print(f"Watching: {self.watchDir}")
				self.outDir = os.path.split(exePath)[0]
				print(f"Copying Changes To: {self.outDir}")
				#Get polling rate from preferences
				pollingRate = 5#5 seconds
				for addon in bpy.context.preferences.addons:
				   #print(addon)
				   if "RE-Mesh-Editor" in addon.module:
					   preferencesName = addon.module
					   pollingRate = bpy.context.preferences.addons[addon.module].preferences.modFileTrackingPollingRate
					   break
				if os.path.isdir(self.watchDir) and os.path.isdir(self.outDir):
					self._timer = wm.event_timer_add(pollingRate, window=context.window)
					wm.modal_handler_add(self)
					wm.enableModFileTracking = True
				else:
					self.report({"ERROR"},"Invalid directory.")
					return {'CANCELLED'} 
			else:
				self.report({"ERROR"},"Mod workspace not set or asset library is not set up.")
				return {'CANCELLED'} 
			return {'RUNNING_MODAL'}
		
	def modal(self, context, event):
		wm = context.window_manager
		if not wm.enableModFileTracking:
			self.cancel(context)
			return {'CANCELLED'}

		if event.type == 'TIMER':
			now = datetime.now()
			#Format as HH:MM:SS
			currentTime = now.strftime("%H:%M:%S")
			trackedFileCount = 0
			for root, _, files in os.walk(self.watchDir):
				for file in files:
					if not any(ext in file.lower() for ext in self.extensionBlackList):
						filePath = os.path.join(root, file)
						trackedFileCount += 1
						if filePath not in self.filePathDict:
							relPath = os.path.relpath(filePath,start = self.watchDir)
							print(f"Mod File Tracker: [{currentTime}] New File - {relPath}")
							self.filePathDict[filePath] = os.stat(filePath).st_mtime
							try:
								outPath = os.path.join(self.outDir,relPath)
								os.makedirs(os.path.split(outPath)[0],exist_ok = True)
								shutil.copyfile(filePath,outPath)
							except PermissionError:
								pass#Sometimes it gives permission errors when placing new files in the directory, it'll be copied on the next tick
							except Exception as e:
									print(f"Failed to copy {filePath} - {e}")
						else:
							if os.stat(filePath).st_mtime != self.filePathDict[filePath]:
								relPath = os.path.relpath(filePath,start = self.watchDir)
								self.filePathDict[filePath] = os.stat(filePath).st_mtime
								print(f"Mod File Tracker: [{currentTime}] File Modified - {relPath}")
								try:
									outPath = os.path.join(self.outDir,relPath)
									os.makedirs(os.path.split(outPath)[0],exist_ok = True)
									shutil.copyfile(filePath,outPath)
								except PermissionError:
									pass#Sometimes it gives permission errors when placing new files in the directory, it'll be copied on the next tick
								except Exception as e:
									print(f"Failed to copy {filePath} - {e}")
									
			if trackedFileCount != len(self.filePathDict):
				#Find which files were deleted, remove them from the game directory and path dict
				for filePath in list(self.filePathDict.keys()):
					if not os.path.isfile(filePath):
						try:
							relPath = os.path.relpath(filePath,start = self.watchDir)
							outPath = os.path.join(self.outDir,relPath)
							os.remove(outPath)
							print(f"Mod File Tracker: [{currentTime}] File Deleted - {relPath}")
						except Exception as e:
							print(f"Failed to delete {outPath} - {e}")
							
						del self.filePathDict[filePath]
				#print("Mod File Tracker: File deletion detected.")
			if not self.allowTexCopy:
				#If it's a game that uses direct storage, paks have to be used
				#Check for paks in the mod output directory and copy them into the pak_mods directory in the game folder. This only works for direct storage games so paks won't be copied on older games
				for entry in os.scandir(self.watchDirPak):
					if entry.name.endswith(".pak"):
						filePath = os.path.join(self.watchDirPak, entry.name)
						if filePath not in self.pakPathDict:
							print(f"Mod File Tracker: [{currentTime}] New Pak File - {relPath}")
							self.pakPathDict[filePath] = os.stat(filePath).st_mtime
							try:
								outPath = os.path.join(self.outDir,"pak_mods",entry.name)
								os.makedirs(os.path.split(outPath)[0],exist_ok = True)
								shutil.copyfile(filePath,outPath)
							except PermissionError:
								pass#Sometimes it gives permission errors when placing new files in the directory, it'll be copied on the next tick
							except Exception as e:
									print(f"Failed to copy {filePath} - {e}")
						else:
							if os.stat(filePath).st_mtime != self.pakPathDict[filePath]:
								relPath = os.path.relpath(filePath,start = self.watchDir)
								self.pakPathDict[filePath] = os.stat(filePath).st_mtime
								print(f"Mod File Tracker: [{currentTime}] Pak File Modified - {relPath}")
								try:
									outPath = os.path.join(self.outDir,relPath)
									os.makedirs(os.path.split(outPath)[0],exist_ok = True)
									shutil.copyfile(filePath,outPath)
								except PermissionError:
									pass#Sometimes it gives permission errors when placing new files in the directory, it'll be copied on the next tick
								except Exception as e:
									print(f"Failed to copy {filePath} - {e}")
		return {'PASS_THROUGH'}

	def cancel(self, context):
		print("Mod File Tracker: Stopped.")
		wm = context.window_manager
		wm.event_timer_remove(self._timer)

class WM_OT_CopyModFilesToGameDir(Operator):
	bl_label = "Copy Mod Files to Game"
	bl_idname = "re_mod_workspace.copy_mod_files_to_game_dir"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Copies files from the modOutput directory into the game directory.\nRE Asset Library must be installed.\nThe asset libary for the game must be installed and have the game extract paths set.\nNOTE: In MH Wilds and newer, .tex files are not copied, this is because tex files cannot be loose loaded in RE Engine games from 2025 and newer.\nUse the Create Patch Pak button to create a pak mod"
	@classmethod
	def poll(self,context):
		return "modWorkspace_setup" in context.scene
	
	def execute(self, context):
		copyCount = 0
		fileCount = 0
		pakCopyFailed = False
		if bpy.context.scene.get("modWorkspace_setup"):
			gameName = bpy.context.scene["modWorkspace_gameName"]
			exePath = getSceneEXEPath()
			if exePath == None:
				self.report({"ERROR"},f"Install the asset library for {gameName} and set the game extract paths first.")
				return {'CANCELLED'}
			else:
				exePath = bpy.context.scene["modWorkspace_exePath"]
				inDir = os.path.join(bpy.context.scene["modWorkspace_directory"],"modOutput",bpy.context.scene["modWorkspace_internalName"])
				print(f"Copying From: {inDir}")
				outDir = os.path.split(exePath)[0]
				print(f"Copying To: {outDir}")
				allowTexCopy = bpy.context.scene["modWorkspace_allowTexCopy"]
				extensionBlackList = FILE_BLACKLIST if allowTexCopy else FILE_BLACKLIST_NO_TEX
				for root, _, files in os.walk(inDir):
					for file in files:
						if not any(ext in file.lower() for ext in extensionBlackList):
							fileCount += 1
							filePath = os.path.join(root, file)
							relPath = os.path.relpath(filePath,start = inDir)
							print(f"Copying: {relPath}")
							try:
								outPath = os.path.join(outDir,relPath)
								os.makedirs(os.path.split(outPath)[0],exist_ok = True)
								shutil.copyfile(filePath,outPath)
								copyCount += 1
							except Exception as e:
									print(f"Failed to copy {filePath} - {e}")
									
				if not allowTexCopy:
					pakDir = os.path.join(bpy.context.scene["modWorkspace_directory"],"modOutput")
					pakOutDir = os.path.join(os.path.split(exePath)[0],"pak_mods")
					#If it's a game that uses direct storage, paks have to be used
					#Check for paks in the mod output directory and copy them into the pak_mods directory in the game folder. This only works for direct storage games so paks won't be copied on older games
					for entry in os.scandir(pakDir):
						if entry.name.endswith(".pak"):
							
							filePath = os.path.join(pakDir, entry.name)
							
							outPath = os.path.join(pakOutDir,entry.name)
							localPakCRC = getFileCRC(filePath)
							if os.path.isfile(outPath):
								remotePakCRC = getFileCRC(outPath)
							else:
								remotePakCRC = 0
							if localPakCRC != remotePakCRC:
								fileCount += 1
									
								try:
									print(f"Copying: {entry.name} to {pakOutDir}")
									os.makedirs(os.path.split(outPath)[0],exist_ok = True)
									shutil.copyfile(filePath,outPath)
									copyCount += 1
								except PermissionError as e:
									pakCopyFailed = True
									print(f"Permission Error - Failed to copy {filePath}\nMake sure the game isn't running when copying pak files.")
								except Exception as e:
									print(f"Failed to copy {filePath} - {e}")
							else:
								print(f"{entry.name} is unchanged, skipping copy.")
									
			self.report({"INFO"},f"Copied {copyCount} / {fileCount} files." + (" Pak file was not copied, make sure the game isn't running." if pakCopyFailed else ""))
		return {'FINISHED'}
	
class WM_OT_UninstallModFilesFromGameDir(Operator):
	bl_label = "Uninstall Mod Files From Game"
	bl_idname = "re_mod_workspace.uninstall_mod_files_from_game_dir"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Deletes installed mod files from the game directory.\nNOTE:Only files that are present in the modOutput folder will be deleted.\nMod File Tracking will be turned off if it's on"
	@classmethod
	def poll(self,context):
		return "modWorkspace_setup" in context.scene
	
	def execute(self, context):
		deleteCount = 0
		fileCount = 0
		pakDeleteFailed = False
		if bpy.context.scene.get("modWorkspace_setup"):
			gameName = bpy.context.scene["modWorkspace_gameName"]
			exePath = getSceneEXEPath()
			if exePath == None:
				self.report({"ERROR"},f"Install the asset library for {gameName} and set the game extract paths first.")
				return {'CANCELLED'}
			else:
				exePath = bpy.context.scene["modWorkspace_exePath"]
			inDir = os.path.join(bpy.context.scene["modWorkspace_directory"],"modOutput",bpy.context.scene["modWorkspace_internalName"])
			print(f"Checking: {inDir}")
			outDir = os.path.split(exePath)[0]
			bpy.context.window_manager.enableModFileTracking = False
			print(f"Removing From: {outDir}")
			allowTexCopy = bpy.context.scene["modWorkspace_allowTexCopy"]
			extensionBlackList = FILE_BLACKLIST if allowTexCopy else FILE_BLACKLIST_NO_TEX
			
			for root, _, files in os.walk(inDir):
				for file in files:
					if not any(ext in file.lower() for ext in extensionBlackList):
						filePath = os.path.join(root, file)
						relPath = os.path.relpath(filePath,start = inDir)
						
						try:
							outPath = os.path.join(outDir,relPath)
							#print(outPath)
							if os.path.isfile(outPath):
								fileCount += 1
								os.remove(outPath)
								print(f"Deleted: {relPath}")
								deleteCount += 1
						except Exception as e:
								print(f"Failed to delete {outPath} - {e}")
			if not allowTexCopy:
				pakDir = os.path.join(bpy.context.scene["modWorkspace_directory"],"modOutput")
				pakOutDir = os.path.join(os.path.split(exePath)[0],"pak_mods")
				#If it's a game that uses direct storage, paks have to be used
				#Check for paks in the mod output directory and copy them into the pak_mods directory in the game folder. This only works for direct storage games so paks won't be copied on older games
				for entry in os.scandir(pakDir):
					if entry.name.endswith(".pak"):
						filePath = os.path.join(pakDir, entry.name)
						outPath = os.path.join(pakOutDir,entry.name)
						try:
							outPath = os.path.join(pakOutDir,entry.name)
							if os.path.isfile(outPath):
								fileCount += 1
								os.remove(outPath)
								deleteCount += 1
						except PermissionError as e:
							pakDeleteFailed = True
							print(f"Permission Error - Failed to delete {outPath}\nMake sure the game isn't running when deleting pak files.")
						except Exception as e:
							pakDeleteFailed = True
							print(f"Failed to copy {outPath} - {e}")
			self.report({"INFO"},f"Deleted {deleteCount} / {fileCount} files."  + (" Pak file was not deleted, make sure the game isn't running." if pakDeleteFailed else ""))
		return {'FINISHED'}


class WM_OT_LaunchGame(Operator):
	bl_label = "Launch Game"
	bl_idname = "re_mod_workspace.launch_game"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Launch the game.\nExtract paths must be set in the asset library.\nThis feature is only supported on Windows"
	@classmethod
	def poll(self,context):
		return "modWorkspace_setup" in context.scene
	
	def execute(self, context):
		if bpy.context.scene.get("modWorkspace_setup"):
			gameName = bpy.context.scene["modWorkspace_gameName"]
			exePath = getSceneEXEPath()
			if exePath == None:
				self.report({"ERROR"},f"Install the asset library for {gameName} and set the game extract paths first.")
				return {'CANCELLED'}
			
			if platform.system() == 'Windows' and os.path.isfile(exePath):
				os.startfile(exePath)
			else:
				self.report({"ERROR"},f"This feature is only supported on Windows.")
					
		return {'FINISHED'}
	
class WM_OT_OpenModWorkspace(Operator):
	bl_label = "Open Mod Workspace"
	bl_idname = "re_mod_workspace.open_mod_workspace"
	bl_options = {'REGISTER'}
	bl_description = "Open the folder set as the mod workspace"
	@classmethod
	def poll(self,context):
		return "modWorkspace_setup" in context.scene
	
	def execute(self, context):
		if os.path.isdir(bpy.context.scene["modWorkspace_directory"]):
			openFolder(bpy.context.scene["modWorkspace_directory"])
					
		return {'FINISHED'}