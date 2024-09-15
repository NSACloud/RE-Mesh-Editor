#Author: NSA Cloud
import bpy
import os


from ..blender_utils import showErrorMessageBox,showMessageBox
from bpy.types import Operator,OperatorFileListElement
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty,CollectionProperty
from .file_re_tex import getTexVersionFromGameName
from .blender_re_tex import convertTexDDSList
from ..mdf.file_re_mdf import getMDFVersionToGameName
from .re_tex_utils import DDSToTex
import shutil
#from .re_tex_utils import



class WM_OT_ConvertDDSTexFile(Operator,ImportHelper):
	bl_label = "Convert DDS/Tex Files"
	bl_idname = "re_tex.convert_tex_dds_files"
	bl_description = "Opens a window to select textures to convert. Selected .dds files will be converted to .tex and tex files will be converted to dds.\nIf you are using Blender 4.1 or higher, you can drag .tex or .dds files into the 3D view to convert them"
	filter_glob: StringProperty(default="*.dds;*.tex.*", options={'HIDDEN'})
	files : CollectionProperty(
			name="File Path",
			type=OperatorFileListElement,
			)
	directory : StringProperty(
			subtype='DIR_PATH',
			options = {"SKIP_SAVE"}
			)
	def execute(self, context):
		fileList = [file.name for file in self.files]
		successCount,failCount = convertTexDDSList(fileNameList = fileList,inDir = self.directory, outDir = self.directory, gameName = bpy.context.scene.re_mdf_toolpanel.activeGame,createStreamingTex=False)
		showMessageBox(f"Converted {str(successCount)} textures.",title = "Texture Conversion")
		self.report({"INFO"},f"Converted {str(successCount)} textures.")
		
		return {"FINISHED"}
	def invoke(self, context, event):
		if self.directory:
			return self.execute(context)
		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

class WM_OT_ConvertFolderToTex(Operator):
	bl_label = "Convert Directory to Tex"
	bl_idname = "re_tex.convert_tex_directory"
	bl_description = "Converts all .dds files in the chosen directory to .tex\nConverted files will be saved inside a folder called \"converted\"\nSave DDS files with compression settings set to BC7 sRGB for albedo/color textures and BC7 Linear for anything else"
	def execute(self, context):
		texVersion = 28
		gameName = bpy.context.scene.re_mdf_toolpanel.activeGame
		if gameName != -1 and getTexVersionFromGameName(gameName) != -1:
			texVersion = getTexVersionFromGameName(gameName)
		#TODO Add support for other image formats, should be doable with texconv
		#Also add streaming texture generation, should also be doable with texconv's resize option
		texDir = os.path.realpath(bpy.context.scene.re_mdf_toolpanel.textureDirectory)
		convertedDir = os.path.join(texDir,"converted")
		if os.path.isdir(texDir):
			otherImageConversionList = []
			ddsConversionList = []
			
			for entry in os.scandir(texDir):
				if entry.is_file() and entry.name.lower().endswith(".dds"):
					ddsConversionList.append(entry.name)
			
			if ddsConversionList != []:
				successCount,failCount = convertTexDDSList(fileNameList = ddsConversionList,inDir = texDir, outDir = convertedDir, gameName = bpy.context.scene.re_mdf_toolpanel.activeGame,createStreamingTex=False)
				self.report({"INFO"},f"Converted {str(successCount)} textures")
				if bpy.context.scene.re_mdf_toolpanel.openConvertedFolder:
					os.startfile(convertedDir)
			else:
				showErrorMessageBox("No .dds files in provided directory")
		else:
			showErrorMessageBox("Provided Image Directory is not a directory or does not exist")
		return {"FINISHED"}

class WM_OT_CopyConvertedTextures(Operator):
	bl_label = "Copy Converted Tex Files"
	bl_idname = "re_tex.copy_converted_tex"
	bl_options = {'UNDO'}
	bl_description = "Copies the textures in the converted tex folder into the specified Mod Natives Directory.\nThe textures are placed at the paths set in the active MDF collection"
	def execute(self, context):
		texDir = os.path.realpath(bpy.context.scene.re_mdf_toolpanel.textureDirectory)
		modDir = os.path.realpath(bpy.context.scene.re_mdf_toolpanel.modDirectory)
		convertedDir = os.path.join(texDir,"converted")
		mdfCollection = bpy.data.collections.get(bpy.context.scene.re_mdf_toolpanel.mdfCollection,None)
		pathDict = {}
		copyCount = 0
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
			self.report({"INFO"},f"Copied {str(copyCount)} textures to mod directory")
		else:
			self.report({"ERROR"},f"Texture directory does not exist")
		
		return {"FINISHED"}