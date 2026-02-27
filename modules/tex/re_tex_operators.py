#Author: NSA Cloud
import bpy
import os


from ..blender_utils import showErrorMessageBox,showMessageBox
from bpy.types import Operator,OperatorFileListElement
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty,CollectionProperty
from .file_re_tex import getTexVersionFromGameName
from .blender_re_tex import convertTexDDSList
from .re_tex_propertyGroups import PNGConversionEntryPropertyGroup
from ..mdf.file_re_mdf import getMDFVersionToGameName
from .re_tex_utils import DDSToTex,ImageListToDDS
from ..gen_functions import openFolder
import shutil
#from .re_tex_utils import



class WM_OT_ConvertDDSTexFile(Operator,ImportHelper):
	bl_label = "Convert Image/RE Tex Files"
	bl_idname = "re_tex.convert_tex_dds_files"
	bl_description = "Opens a window to select textures to convert. Selected image files will be converted to .tex and tex files will be converted to dds/png (configurable in preferences).\nIf you are using Blender 4.1 or higher, you can drag .tex or .dds files into the 3D view to convert them.\nSupported File Types:\n.dds, .png, .tga, .tiff"
	bl_options = {'REGISTER'}#Disable undo
	filter_glob: StringProperty(default="*.png;*.dds;*.tex.*", options={'HIDDEN'})
	files : CollectionProperty(
			name="File Path",
			type=OperatorFileListElement,
			)
	directory : StringProperty(
			subtype='DIR_PATH',
			options = {"SKIP_SAVE"}
			)
	skipPrompt : bpy.props.BoolProperty(
	   name = "Skip Conversion Prompt",
	   description = "Skip prompt to convert images to DDS.\nIf non DDS files are selected, the compression type will be set automatically",
	   default = False)
	def execute(self, context):
		
		fileList = []
		for file in self.files:
			fileEntry = dict()
			fileEntry["name"] = file.name
			fileList.append(fileEntry)
		result = bpy.ops.re_tex.dds_convert_window(
			"INVOKE_DEFAULT",
			files = fileList,
			directory = self.directory,
			outDir = self.directory,
			skipPrompt = self.skipPrompt,
			)
		return {"FINISHED"}
	def invoke(self, context, event):
		if self.directory:
			return self.execute(context)
		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

class WM_OT_PNGToTexConversionWindow(Operator):
	bl_label = "Image To Tex Conversion"
	bl_idname = "re_tex.dds_convert_window"
	bl_description = "Set compression format to be used by converted PNG files."
	bl_options = {'INTERNAL'}
	
	directory : bpy.props.StringProperty(
	   name = "fileDir",
	   description = "",
	   default = "",
	   options = {"HIDDEN"})
	outDir : bpy.props.StringProperty(
	   name = "outDir",
	   description = "",
	   default = "",
	   options = {"HIDDEN"})
	files : CollectionProperty(
			name="File Path",
			type=OperatorFileListElement,
			)
	fileList_items: bpy.props.CollectionProperty(type = PNGConversionEntryPropertyGroup)
	fileList_index: bpy.props.IntProperty(name="")
	
	gameName : bpy.props.StringProperty(
	   name = "gameName",
	   description = "",
	   default = "",
	   options = {"HIDDEN"})
	
	texVersion : bpy.props.StringProperty(
	   name = "texVersion",
	   description = "",
	   default = "",
	   options = {"HIDDEN"})
	
	generateMipmaps : bpy.props.BoolProperty(
	   name = "Generate Mipmaps",
	   description = "Generates lower quality texture levels for lower texture settings. Leave this on unless these are UI textures",
	   default = True)
	skipPrompt : bpy.props.BoolProperty(
	   name = "Skip Prompt",
	   description = "Internal, used to determine if called by a script or by user",
	   options = {"HIDDEN"},
	   default = False)
	
	def execute(self, context):
		convertedDDSList = []
		ddsTexList = []
		for file in self.files:
			if file.name.endswith(".dds") or ".tex." in file.name:
				ddsTexList.append(file.name)
				
		if len(self.fileList_items) != 0:
			print(f"Converting {len(self.fileList_items)} Images to DDS")
		imageConvertList = []
		for item in self.fileList_items:
			imagePath = os.path.join(self.directory,item.fileName)
			ddsOutPath = os.path.splitext(imagePath)[0]+".dds"
			imageConvertList.append((imagePath,item.ddsCompressionType))
			convertedDDSList.append(ddsOutPath)
		if len(imageConvertList) != 0:
			ImageListToDDS(imageConvertList,outDir = self.directory, generateMipMaps = self.generateMipmaps)
		#Check if pngs converted to dds and add it to the dds list if it did.
		for ddsPath in convertedDDSList:
			if os.path.isfile(ddsPath):
				#print(f"Added {ddsPath} to list")
				ddsTexList.append(os.path.split(ddsPath)[1])
		
		#Find preferences to check tex conversion filetype setting
		texToPNG = False
		for addon in bpy.context.preferences.addons:
               #print(addon)
			   if "RE-Mesh-Editor" in addon.module:
				   preferencesName = addon.module
				   texToPNG = bpy.context.preferences.addons[addon.module].preferences.convertTexToPNG
				   break
		successCount,failCount = convertTexDDSList(fileNameList = ddsTexList,inDir = self.directory, outDir = self.outDir, gameName = bpy.context.scene.re_mdf_toolpanel.activeGame,createStreamingTex=False,texToPNG = texToPNG)
		
		#Delete converted dds files after converting to tex
		for ddsPath in convertedDDSList:
			try:
				os.remove(ddsPath)
			except:
				pass
		if not self.skipPrompt:
			showMessageBox(f"Converted {str(successCount)} textures.",title = "Texture Conversion")
		self.report({"INFO"},f"Converted {str(successCount)} textures.")
		
			
		return {'FINISHED'}
	@classmethod
	def poll(self,context):
		return bpy.context.scene is not None
	
	def invoke(self, context, event):
		self.fileList_items.clear()
		
		#For displaying version in UI
		gameName = bpy.context.scene.re_mdf_toolpanel.activeGame
		self.gameName = str(gameName)
		if gameName != -1 and getTexVersionFromGameName(gameName) != -1:
			self.texVersion = str(getTexVersionFromGameName(gameName))
		supportedImageExtensions = set([".png",".tga",".tif",".tiff"])
		if self.directory != "":
			pngList = []
			for file in self.files:
				if os.path.splitext(file.name)[1] in supportedImageExtensions:
					item = self.fileList_items.add()
					item.fileName = file.name
					lowerFileName = item.fileName.lower()
					if "_alb" in lowerFileName or "_emi." in lowerFileName:
						item.ddsCompressionType = "BC7_UNORM_SRGB"
					else:
						item.ddsCompressionType = "BC7_UNORM"
		
		if len(self.fileList_items) == 0:
			self.skipPrompt = True
			
		if self.skipPrompt:
			return self.execute(context)
		else:
			return context.window_manager.invoke_props_dialog(self,width = 700,confirm_text = "Convert to RE Tex")


	def draw(self,context):
		layout = self.layout
		layout.label(text = f"Active Game: {self.gameName} - Tex Version: {self.texVersion}")
		layout.label(text = f"File Count: {str(len(self.fileList_items))}")
		layout.template_list(
			listtype_name = "TEX_UL_PNGConversionList", 
			list_id = "fileList",
			dataptr = self,
			propname = "fileList_items",
			active_dataptr = self,
			active_propname = "fileList_index",
			rows = 8,
			type='DEFAULT'
			)
		layout.prop(self,"generateMipmaps")
	

class WM_OT_ConvertFolderToTex(Operator):
	bl_label = "Convert Directory to Tex"
	bl_idname = "re_tex.convert_tex_directory"
	bl_description = "Converts all image files in the chosen directory to .tex\nConverted files will be saved inside a folder called \"converted\"\nSupported File Types:\n.dds, .png, .tga, .tiff"
	bl_options = {'REGISTER'}#Disable undo
	skipPrompt : bpy.props.BoolProperty(
	   name = "Skip Conversion Prompt",
	   description = "Skip prompt to convert images to DDS.\nIf non DDS files are selected, the compression type will be set automatically",
	   default = False,
	   options = {"HIDDEN"})
	def execute(self, context):
		texVersion = 28
		gameName = bpy.context.scene.re_mdf_toolpanel.activeGame
		if gameName != -1 and getTexVersionFromGameName(gameName) != -1:
			texVersion = getTexVersionFromGameName(gameName)
		
		supportedImageExtensions = set([".png",".tga",".tif",".tiff",".dds"])
		#TODO Add streaming texture generation, should also be doable with texconv's resize option
		texDir = os.path.realpath(bpy.context.scene.re_mdf_toolpanel.textureDirectory)
		convertedDir = os.path.join(texDir,"converted")
		
		
			
		if os.path.isdir(texDir):
			fileList = []
			for entry in os.scandir(texDir):
				if entry.is_file() and os.path.splitext(entry.name)[1] in supportedImageExtensions:
					fileEntry = dict()
					fileEntry["name"] = entry.name
					fileList.append(fileEntry)
			
			if fileList != []:
				result = bpy.ops.re_tex.dds_convert_window(
					"INVOKE_DEFAULT",
					files = fileList,
					directory = texDir,
					outDir = convertedDir,
					skipPrompt = self.skipPrompt,
					)
				return {"FINISHED"}
				if bpy.context.scene.re_mdf_toolpanel.openConvertedFolder:
					openFolder(convertedDir)
			else:
				showErrorMessageBox("No image files in provided directory")
		else:
			showErrorMessageBox("Provided Image Directory is not a directory or does not exist")
		return {"FINISHED"}

class WM_OT_CopyConvertedTextures(Operator):
	bl_label = "Copy Converted Tex Files"
	bl_idname = "re_tex.copy_converted_tex"
	bl_options = {'REGISTER'}#Disable undo
	bl_description = "Copies the textures in the converted tex folder into the specified Mod Natives Directory.\nThe textures are placed at the paths set in the active MDF collection"
	
	def execute(self, context):
		texDir = os.path.realpath(bpy.context.scene.re_mdf_toolpanel.textureDirectory)
		modDir = os.path.realpath(bpy.context.scene.re_mdf_toolpanel.modDirectory)
		convertedDir = os.path.join(texDir,"converted")
		mdfCollection = bpy.context.scene.re_mdf_toolpanel.mdfCollection
		pathDict = {}
		copyCount = 0
		totalTextureCount = 0
		if mdfCollection != None and os.path.exists(modDir):
		   for obj in mdfCollection.all_objects:
			   if obj.get("~TYPE") == "RE_MDF_MATERIAL":
				   for textureBinding in obj.re_mdf_material.textureBindingList_items:
					   pathDict[os.path.split(textureBinding.path)[1]] = textureBinding.path
		if os.path.isdir(convertedDir):
			for entry in os.scandir(convertedDir):
				if entry.is_file() and os.path.splitext(entry.name)[0] in pathDict:
					path = os.path.join(convertedDir,entry.name)
					outPath = os.path.realpath(os.path.join(modDir,pathDict[os.path.splitext(entry.name)[0]]+os.path.splitext(entry.name)[1]))
					os.makedirs(os.path.split(outPath)[0],exist_ok = True)
					shutil.copyfile(path, outPath)
					print(f"Copied {os.path.split(path)[1]} to {outPath}")
					copyCount += 1
					totalTextureCount += 1
				elif entry.is_file() and ".tex." in entry.name:
					totalTextureCount += 1
			self.report({"INFO"},f"Copied {copyCount}/{totalTextureCount} textures to mod directory")
		else:
			self.report({"ERROR"},f"Texture directory does not exist")
		
		return {"FINISHED"}

