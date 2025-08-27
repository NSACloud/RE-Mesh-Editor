#Author: NSA Cloud
import bpy

from bpy.types import Operator

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       )

class WM_OT_DeleteLoose(Operator):
	bl_label = "Delete Loose Geometry"
	bl_idname = "re_mesh.delete_loose"
	bl_description = "Deletes loose vertices and edges with no faces on selected meshes"
	def execute(self, context):
		if context.selected_objects != []:
			selection = context.selected_objects	
		else:
			selection = bpy.context.scene.objects
		for selectedObj in selection:
			if selectedObj.type == "MESH":
				context.view_layer.objects.active  = selectedObj
				bpy.ops.object.mode_set(mode='EDIT')
				bpy.ops.mesh.select_all(action='SELECT')
				print(f"Deleted loose geometry on {selectedObj.name}")
				bpy.ops.mesh.delete_loose()
				bpy.ops.object.mode_set(mode='OBJECT')
		if context.selected_objects == []: 
			self.report({"INFO"},"Deleted loose geometry on all objects")
		else:
			self.report({"INFO"},"Deleted loose geometry on selected objects")
		return {'FINISHED'}
class WM_OT_RenameMeshToREFormat(Operator):
	bl_label = "Rename Meshes"
	bl_idname = "re_mesh.rename_meshes"
	bl_description = "Renames selected meshes to RE mesh naming scheme (Example: Group_0_Sub_0__Shirts_Mat)"
	def execute(self, context):
		groupIndexDict = dict()
		if context.selected_objects != []:
			selection = context.selected_objects	
		else:
			selection = bpy.context.scene.objects
		for selectedObj in selection:
			if selectedObj.type == "MESH":
				if "Group_" in selectedObj.name:
					try:
						groupID = int(selectedObj.name.split("Group_")[1].split("_")[0])
					except:
						pass
				else:
					print("Could not parse group ID in {selectedObj.name}, setting to 0")
					groupID = 0
				if groupID not in groupIndexDict:
					groupIndexDict[groupID] = 0
				if len(selectedObj.data.materials) > 0:
					materialName = selectedObj.data.materials[0].name.split(".",1)[0].strip()
				else:
					materialName = "NO_MATERIAL"
				selectedObj.name = f"Group_{str(groupID)}_Sub_{str(groupIndexDict[groupID])}__{materialName}"
				groupIndexDict[groupID] += 1
				
		if context.selected_objects == []: 
			self.report({"INFO"},"Renamed all objects to RE Mesh format")
		else:
			self.report({"INFO"},"Renamed selected objects to RE Mesh format")
		return {'FINISHED'}


#Weights

class WM_OT_RemoveZeroWeightVertexGroups(Operator):
	"""Remove all vertex groups that have no weight assigned to them"""
	bl_label = "Remove Empty Vertex Groups"
	bl_idname = "re_mesh.remove_zero_weight_vertex_groups"

	def execute(self, context):
		if context.selected_objects != []:
			selection = context.selected_objects	
		else:
			selection = bpy.context.scene.objects
		for obj in selection:
			emptyGroupList = []
			for vertexGroup in obj.vertex_groups:
				if not any(vertexGroup.index in [g.group for g in v.groups] for v in obj.data.vertices):
					emptyGroupList.append(vertexGroup)
			for group in emptyGroupList:
				obj.vertex_groups.remove(group)
		if context.selected_objects == []: 
			self.report({"INFO"},"Removed empty vertex groups on all objects.")
		else:
			self.report({"INFO"},"Removed empty vertex groups on selected objects.")		
		return {'FINISHED'}
	
class WM_OT_LimitTotalNormalizeAll(Operator):
	"""Limits the amount of bones influences per vertex to 6 and normalizes the weights of all vertex groups for all selected meshes"""
	bl_label = "Limit Total and Normalize All"
	bl_idname = "re_mesh.limit_total_normalize"

	def execute(self, context):
		if context.selected_objects != []:
			selection = context.selected_objects	
		else:
			selection = bpy.context.scene.objects
		for selectedObj in selection:
			if selectedObj.type == "MESH":
				context.view_layer.objects.active  = selectedObj
				bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
				try:
					bpy.ops.object.vertex_group_limit_total(limit = 6)
					bpy.ops.object.vertex_group_normalize_all(lock_active = False)
				except:
					pass
				print(f"Limited total weights to 6 and normalized {selectedObj.name}")
				bpy.ops.object.mode_set(mode='OBJECT')
		if context.selected_objects == []:
			self.report({"INFO"},"Limited total weights to 6 and normalized on all objects")
		else:
			self.report({"INFO"},"Limited total weights to 6 normalized on selected objects")
		return {'FINISHED'}
class WM_OT_CreateMeshCollection(Operator):
	bl_label = "Create Mesh Collection"
	bl_idname = "re_mesh.create_mesh_collection"
	bl_description = "Creates a collection for RE Engine meshes"
	bl_options = {'UNDO'}
	collectionName : bpy.props.StringProperty(name = "Mesh Name",
										 description = "The name of the newly created mesh collection",
										 default = "newMesh"
										)
	lodCount : bpy.props.IntProperty(name = "LOD Amount",
									  description = "The amount of lower quality model levels to switch between.\nLeave this at 1 unless you have a set of lower quality models",
									  default = 1,
									  min = 1,
									  max = 8)
	def execute(self, context):
		if self.collectionName.strip() != "":
			collection = bpy.data.collections.new(self.collectionName+".mesh")
			bpy.context.scene["REMeshLastImportedCollection"] = collection.name
			bpy.context.scene.collection.children.link(collection)
			collection.color_tag = "COLOR_01"
			bpy.context.scene.re_mdf_toolpanel.meshCollection = collection.name
			if self.lodCount > 1:
				for i in range(self.lodCount):
					lodCollection = bpy.data.collections.new(f"Main Mesh LOD{str(i)} - {collection.name}")
					lodCollection["LOD Distance"] = 0.167932*(i+1)
					collection.children.link(lodCollection)
			self.report({"INFO"},"Created new RE mesh collection.")
			return {'FINISHED'}
		else:
			self.report({"ERROR"},"Invalid mesh collection name.")
			return {'CANCELLED'}
	
	def invoke(self,context,event):
		return context.window_manager.invoke_props_dialog(self)

