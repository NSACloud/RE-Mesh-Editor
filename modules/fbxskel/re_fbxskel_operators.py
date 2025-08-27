#Author: NSA Cloud
import bpy

from bpy.types import Operator

from ..blender_utils import showMessageBox
from .re_fbxskel_propertyGroups import ToggleStringPropertyGroup
EXTRACT_WINDOW_SIZE = 400
SPLIT_FACTOR = .45

def linkArmatures(mainArmatureObj,linkArmaturesList):
	armatureLinkCount = 0
	for armatureObj in linkArmaturesList:
		linkCount = 0
		for bone in armatureObj.pose.bones:
			if bone.name in mainArmatureObj.data.bones:
				if "BoneLinkage" in bone.constraints:
					constraint = bone.constraints["BoneLinkage"]
				else:
					constraint = bone.constraints.new("COPY_TRANSFORMS")
					constraint.name = "BoneLinkage"
				constraint.target = mainArmatureObj
				constraint.subtarget = bone.name
				linkCount += 1
		if linkCount != 0:
			armatureLinkCount += 1
	print(f"Linked {linkCount} bones on {armatureObj.name} to {mainArmatureObj.name}.")
	return armatureLinkCount
def update_checkAllArmatures(self, context):
	if self.checkAllArmatures == True:
		for item in self.armatureList_items:
			item.enabled = True
		self.checkAllArmatures = False
def update_uncheckAllArmatures(self, context):
	if self.uncheckAllArmatures == True:
		for item in self.armatureList_items:
			item.enabled = False
		self.uncheckAllArmatures = False

class WM_OT_LinkArmatureBones(Operator):
	bl_label = "Link Armature Bones"
	bl_idname = "re_fbxskel.link_armature_bones"
	bl_description = "Link bones from different armatures to a main armature. This copies all transforms on the main armature to all chosen armatures.\nThe intended use is for constraining bones to an FBXSkel armature with an animation applied.\nAn armature must be selected"
	bl_options = {'INTERNAL'}
	
	targetArmature : bpy.props.StringProperty(
	   name = "Main Armature",
	   description = "",
	   default = "",
	   options = {"HIDDEN"})
	
	armatureList_items: bpy.props.CollectionProperty(type = ToggleStringPropertyGroup)
	armatureList_index: bpy.props.IntProperty(name="")
	
	checkAllArmatures : bpy.props.BoolProperty(
	   name = "Check All Armatures",
	   description = "Select all armatures to be linked",
	   default = False,
	   update = update_checkAllArmatures
	   )
	uncheckAllArmatures : bpy.props.BoolProperty(
	   name = "Uncheck All Armatures",
	   description = "Deselect all armatures to be linked",
	   default = False,
	   update = update_uncheckAllArmatures
	   )
	
	def execute(self, context):
		mainArmature = context.active_object
		
		armatureLinkList = []
		for item in self.armatureList_items:
			if item.enabled:
				if item.name in bpy.data.objects:
					obj = bpy.data.objects[item.name]
					if obj.type == "ARMATURE" and mainArmature != obj:
						armatureLinkList.append(obj)
		
		armatureLinkCount = linkArmatures(mainArmature,armatureLinkList)
		self.report({"INFO"},f"Linked {armatureLinkCount} armatures to the selected armature.")
		return {'FINISHED'}
	@classmethod
	def poll(self,context):
		return bpy.context.active_object is not None and bpy.context.active_object.type == "ARMATURE"
	
	def invoke(self, context, event):
		region = bpy.context.region
		centerX = region.width // 2
		centerY = region.height
		
		#currentX = event.mouse_region_X
		#currentY = event.mouse_region_Y
		
		armatureObjList = sorted([obj for obj in bpy.data.objects if obj.type == "ARMATURE" and obj != context.active_object],key = lambda obj: obj.name)
		self.armatureList_items.clear()
		for entry in armatureObjList:
			item = self.armatureList_items.add()
			item.name = entry.name
		
		
		#Move cursor to center so extract window is at the center of the window
		context.window.cursor_warp(centerX,centerY)
	
		return context.window_manager.invoke_props_dialog(self,width = EXTRACT_WINDOW_SIZE,confirm_text = "Link Main Armature")

	
	def draw(self,context):
		layout = self.layout
		rowCount = 8
		uifontscale = 9 * context.preferences.view.ui_scale
		max_label_width = int((EXTRACT_WINDOW_SIZE*(1-SPLIT_FACTOR)*(2-SPLIT_FACTOR)) // uifontscale)
		layout.label(text=f"Main Armature: {context.active_object.name}")
		col = layout.column()
		
		
		col.label(text = f"Armature Count: {str(len(self.armatureList_items))}")
		row = col.row()
		row.alignment = "RIGHT"
		row.prop(self,"checkAllArmatures",icon="CHECKMARK", icon_only=True)
		row.prop(self,"uncheckAllArmatures",icon="X", icon_only=True)
		col.template_list(
			listtype_name = "FBXSKEL_UL_ObjectCheckList", 
			list_id = "armatureList",
			dataptr = self,
			propname = "armatureList_items",
			active_dataptr = self, 
			active_propname = "armatureList_index",
			rows = rowCount,
			type='DEFAULT'
			)
		layout.label(text=f"All checked armatures will be constrained to main armature.")
class WM_OT_ClearBoneLinkages(Operator):
	bl_label = "Clear Bone Linkages"
	bl_description = "Removes all bone linkages on the selected armatures.\n"
	bl_idname = "re_fbxskel.clear_bone_linkages"
	@classmethod
	def poll(self,context):
		return bpy.context.active_object is not None and bpy.context.active_object.type == "ARMATURE"
	def execute(self, context):
		for obj in context.selected_objects:
			if obj.type == "ARMATURE":
				for bone in obj.pose.bones:
					if "BoneLinkage" in bone.constraints:
						constraint = bone.constraints["BoneLinkage"]
						bone.constraints.remove(constraint)
		self.report({"INFO"},"Cleared bone linkages on selected armatures.")
		return {'FINISHED'}
	