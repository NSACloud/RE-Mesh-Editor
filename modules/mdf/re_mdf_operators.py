	#Author: NSA Cloud
import bpy
import os

from bpy.types import Operator
from ..gen_functions import raiseWarning

from .blender_re_mdf import createEmpty,reindexMaterials,createMDFCollection,checkNameUsage,buildMDF
from .blender_re_mesh_mdf import importMDF
from ..blender_utils import showErrorMessageBox
from .file_re_mdf import getMDFVersionToGameName
from .re_mdf_presets import saveAsPreset,readPresetJSON
from .ui_re_mdf_panels import tag_redraw

PRESET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.split(os.path.abspath(__file__))[0])),"Presets")
class WM_OT_NewMDFHeader(Operator):
	bl_label = "Create MDF Collection"
	bl_idname = "re_mdf.create_mdf_collection"
	bl_options = {'UNDO'}
	bl_description = "Create an MDF collection for putting materials into.\nNOTE: The name of the collection is not important, you can rename it if you want to"
	collectionName : bpy.props.StringProperty(name = "MDF Name",
										 description = "The name of the newly created mdf collection.\nUse the same name as the mesh file",
										 default = "newMDF"
										)
	def execute(self, context):
		if self.collectionName.strip() != "":
			createMDFCollection(self.collectionName.strip()+".mdf2")
			self.report({"INFO"},"Created new RE MDF collection.")
			return {'FINISHED'}
		else:
			self.report({"ERROR"},"Invalid MDF collection name.")
			return {'CANCELLED'}
	
	def invoke(self,context,event):
		return context.window_manager.invoke_props_dialog(self)
class WM_OT_ReindexMaterials(Operator):
	bl_label = "Reindex Materials"
	bl_description = "Reorders the materials and sets their names to the name set in the custom properties. This is done automatically upon exporting"
	bl_idname = "re_mdf.reindex_materials"

	def execute(self, context):
		reindexMaterials(bpy.context.scene.re_mdf_toolpanel.mdfCollection)
		self.report({"INFO"},"Reindexed materials.")
		return {'FINISHED'}

class WM_OT_AddPresetMaterial(Operator):
	bl_label = "Add Preset Material"
	bl_description = "Add a new material to the file and configure it to the selected preset"
	bl_idname = "re_mdf.add_preset_material"
	bl_options = {'UNDO'}
	def execute(self, context): 
		enumValue = bpy.context.scene.re_mdf_toolpanel.materialPresets

		if enumValue != "":
			finished = readPresetJSON(os.path.join(PRESET_DIR,enumValue))
		else:
			finished = False
		tag_redraw(bpy.context)
		if finished:
			self.report({"INFO"},"Added preset material.")
			return {'FINISHED'}
		else:
			return {'CANCELLED'}
class WM_OT_ApplyMDFToMeshCollection(Operator):
	bl_label = "Apply Active MDF"
	bl_description = "Applies the Active MDF Collection to the specified Mesh Collection.\nThis will remove all materials on the mesh and rebuild them using the active MDF.\nTextures will be fetched from the chunk path set in the addon preferences"
	bl_idname = "re_mdf.apply_mdf"

	def execute(self, context):
		#reindexMaterials()
		mdfCollection = bpy.data.collections.get(bpy.context.scene.re_mdf_toolpanel.mdfCollection,None)
		meshCollection = bpy.data.collections.get(bpy.context.scene.re_mdf_toolpanel.meshCollection,None)
		
		
		
		modDir = os.path.realpath(bpy.context.scene.re_mdf_toolpanel.modDirectory)
		#removedMaterialSet = set()
		if mdfCollection != None and meshCollection != None and os.path.isdir(modDir):
			mdfFile = buildMDF(mdfCollection.name)
			meshMaterialDict = dict()
			for obj in meshCollection.all_objects:
				if obj.type == "MESH" and not obj.get("MeshExportExclude"):
					materialName = None
					if "__" in obj.name:
						materialName = obj.name.split("__",1)[1].split(".")[0]
						for material in obj.data.materials:
							if material.name.split(".")[0] == materialName:
								meshMaterialDict[materialName] = material
							#removedMaterialSet.add(material)
					obj.data.materials.clear()
					if materialName not in meshMaterialDict:
						if materialName != None:
							newMat = bpy.data.materials.new(name=materialName)
							newMat.use_nodes = True
							obj.data.materials.append(newMat)
							meshMaterialDict[materialName] = newMat
						else:
							raiseWarning(f"No material in mesh name, cannot apply materials: {obj.name}")
					else:
						obj.data.materials.append(meshMaterialDict[materialName])
			"""						
			#If the removed materials have no more users, remove them
			for material in removedMaterialSet:
				if material.users == 0:
					print(f"Removed {material.name}")
					bpy.data.materials.remove(material)
			"""
			importMDF(mdfFile, meshMaterialDict,bpy.context.scene.re_mdf_toolpanel.loadUnusedTextures,bpy.context.scene.re_mdf_toolpanel.loadUnusedProps,bpy.context.scene.re_mdf_toolpanel.useBackfaceCulling,bpy.context.scene.re_mdf_toolpanel.reloadCachedTextures,chunkPath = modDir,gameName = bpy.context.scene.re_mdf_toolpanel.activeGame,arrangeNodes = True)
			self.report({"INFO"},"Applied MDF to mesh collection.")
		else:
			self.report({"ERROR"},"Invalid mesh or MDF collection.")
		return {'FINISHED'}
class WM_OT_OpenPresetFolder(Operator):
	bl_label = "Open Preset Folder"
	bl_description = "Opens the preset folder in File Explorer"
	bl_idname = "re_mdf.open_preset_folder"

	def execute(self, context):
		os.startfile(PRESET_DIR)
		return {'FINISHED'}

class WM_OT_SavePreset(Operator):
	bl_label = "Save Selected As Preset"
	bl_idname = "re_mdf.save_selected_as_preset"
	bl_context = "objectmode"
	bl_description = "Save the selected material object as a preset for easy reuse and sharing. Presets can be accessed using the Open Preset Folder button"
	presetName : bpy.props.StringProperty(name = "Enter Preset Name",default = "newPreset")
	
	@classmethod
	def poll(self,context):
		return context.active_object is not None
	
	def execute(self, context):
		gameName = bpy.context.scene.re_mdf_toolpanel.activeGame
		finished = saveAsPreset(context.active_object, self.presetName,gameName)
		if finished:
			self.report({"INFO"},"Saved preset.")
			return {'FINISHED'}
		else:
			return {'CANCELLED'}
	def invoke(self,context,event):
		return context.window_manager.invoke_props_dialog(self)

		return {'FINISHED'}	
