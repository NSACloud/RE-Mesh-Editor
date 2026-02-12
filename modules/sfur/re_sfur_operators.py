#Author: NSA Cloud
import bpy
import os

from bpy.types import Operator
from ..gen_functions import raiseWarning

from .blender_re_sfur import createCurveEmpty,reindexEntries,createSFurCollection,checkNameUsage
from .ui_re_sfur_panels import tag_redraw

PRESET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.split(os.path.abspath(__file__))[0])),"Presets")
class WM_OT_NewSFurHeader(Operator):
	bl_label = "Create SFur Collection"
	bl_idname = "re_sfur.create_sfur_collection"
	bl_options = {'UNDO'}
	bl_description = "Create an SFur collection for putting shell fur data into.\nNOTE: The name of the collection is not important, you can rename it if you want to"
	collectionName : bpy.props.StringProperty(name = "SFur Name",
										 description = "The name of the newly created sfur collection.\nUse the same name as the mesh file",
										 default = "newSFur"
										)
	def execute(self, context):
		if self.collectionName.strip() != "":
			createSFurCollection(self.collectionName.strip()+".sfur")
			self.report({"INFO"},"Created new RE SFur collection.")
			return {'FINISHED'}
		else:
			self.report({"ERROR"},"Invalid SFur collection name.")
			return {'CANCELLED'}
	
	def invoke(self,context,event):
		return context.window_manager.invoke_props_dialog(self)
class WM_OT_ReindexEntries(Operator):
	bl_label = "Reindex Fur Entries"
	bl_description = "Reorders the shell fur entries and sets their names to the name set in the custom properties. This is done automatically upon exporting"
	bl_idname = "re_sfur.reindex_entries"

	@classmethod
	def poll(self,context):
		return context.scene.re_mdf_toolpanel.sFurCollection is not None

	def execute(self, context):
		reindexEntries(bpy.context.scene.re_mdf_toolpanel.sFurCollection)
		self.report({"INFO"},"Reindexed fur entries.")
		return {'FINISHED'}

class WM_OT_AddFurEntry(Operator):
	bl_label = "Add Shell Fur"
	bl_description = "Add a new shell fur entry.\nTip: Selecting an MDF material beforehand will automatically set the name for the new shell fur entry."
	bl_idname = "re_sfur.add_sfur_entry"
	bl_options = {'UNDO'}
	
	@classmethod
	def poll(self,context):
		return context.scene.re_mdf_toolpanel.sFurCollection is not None
	
	def execute(self, context):
		sFurCollection = bpy.context.scene.re_mdf_toolpanel.sFurCollection
		
		tag_redraw(bpy.context)
		if sFurCollection != None:
			materialName = None
			if bpy.context.active_object != None and bpy.context.active_object.get("~TYPE") == "RE_MDF_MATERIAL":
				materialName = bpy.context.active_object.re_mdf_material.materialName
			
			currentIndex = 0
			subName = "Shell Fur " + str(currentIndex).zfill(2)
			while(checkNameUsage(subName,checkSubString=True,objList = sFurCollection.all_objects)):
				currentIndex +=1
				subName = "Shell Fur " + str(currentIndex).zfill(2)
				
			if materialName == None:
				materialName = "ShellFurMat"+str(currentIndex).zfill(2)
			name = subName + " ("+materialName+")"
			furObj = createCurveEmpty(name,[("~TYPE","RE_SFUR_ENTRY")],None,sFurCollection)
			furObj.re_sfur_data.materialName = materialName
			self.report({"INFO"},"Added shell fur entry.")
			return {'FINISHED'}
		else:
			return {'CANCELLED'}
		
class WM_OT_ApplySFurToMeshCollection(Operator):
	bl_label = "Apply Shell Fur Preview"
	bl_description = "Applies the Active SFur Collection to the specified Mesh Collection.\nThis is for previewing in Blender only and has no effect on the exported file."
	bl_idname = "re_sfur.apply_sfur"

	@classmethod
	def poll(self,context):
		return context.scene.re_mdf_toolpanel.sFurCollection is not None
	
	def execute(self, context):
		#reindexMaterials()
		sFurCollection = bpy.context.scene.re_mdf_toolpanel.sFurCollection
		meshCollection = bpy.context.scene.re_mdf_toolpanel.meshCollection
		
		#TODO
		
		if sFurCollection != None and meshCollection != None:
			
			self.report({"INFO"},"Applied SFur to mesh collection.")
		else:
			self.report({"ERROR"},"Invalid mesh or SFur collection.")
		return {'FINISHED'}