#Author: NSA Cloud
import bpy
import os
from bpy.types import Operator

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       )

from .re_mesh_propertyGroups import ExporterNodePropertyGroup,MESH_UL_REExporterList
from ..gen_functions import splitNativesPath
from ..blender_utils import showErrorMessageBox
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
	"""Limits the amount of bones influences per vertex and normalizes the weights of all vertex groups for all selected meshes"""
	bl_label = "Limit Total and Normalize All"
	bl_idname = "re_mesh.limit_total_normalize"
	maxWeights: EnumProperty(
		name="Weight Limit",
		description="Apply Data to attribute.",
		items=[ ("4", "4 Weights", "Safest option but potentially lower weight quality"),
				("6", "6 Weights (SF6)", "Maximum amount of weights for SF6"),
				("8", "8 Weights", "Note that certain materials may not support 8 weights"),
				("12", "12 Weights (MH Wilds Only)", "This is only supported in MH Wilds (and newer potentially)"),
			   ],
		default = "4"
		
		)
	def invoke(self,context,event):
		return context.window_manager.invoke_props_dialog(self)
	def execute(self, context):
		weightLimit = int(self.maxWeights)
		if context.selected_objects != []:
			selection = context.selected_objects	
		else:
			selection = bpy.context.scene.objects
		for selectedObj in selection:
			if selectedObj.type == "MESH":
				context.view_layer.objects.active  = selectedObj
				bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
				try:
					bpy.ops.object.vertex_group_limit_total(limit = weightLimit)
					bpy.ops.object.vertex_group_normalize_all(lock_active = False)
				except:
					pass
				print(f"Limited total weights to {weightLimit} and normalized {selectedObj.name}")
				bpy.ops.object.mode_set(mode='OBJECT')
		if context.selected_objects == []:
			self.report({"INFO"},f"Limited total weights to {weightLimit} and normalized on all objects")
		else:
			self.report({"INFO"},f"Limited total weights to {weightLimit} and normalized on selected objects")
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
			collection["~TYPE"] = "RE_MESH_COLLECTION"
			bpy.context.scene.re_mdf_toolpanel.meshCollection = collection
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

EXPORTER_WINDOW_SIZE = 800
SPLIT_FACTOR = .4

def update_checkAllItems(self, context):
	if self.checkAllItems == True:
		for item in self.itemList_items:
			item.enabled = True
		self.checkAllItems = False
def update_uncheckAllItems(self, context):
	if self.uncheckAllItems == True:
		for item in self.itemList_items:
			item.enabled = False
		self.uncheckAllItems = False

COLLECTION_TYPES = frozenset([
   "RE_MESH_COLLECTION",
   "RE_MDF_COLLECTION",
   "RE_CHAIN_COLLECTION",
   "RE_CLSP_COLLECTION",
   "RE_SFUR_COLLECTION"
])
def checkForChildRECollectionsRecursive(collection):#For checking if a collection should be included in the export list
	if collection.get("~TYPE") in COLLECTION_TYPES:
		return True
	else:
		for child in collection.children:
			if checkForChildRECollectionsRecursive(child):
				return True
	return False
def determineExportPath(modDirectory,exportType,assetPath,scene):
	filePath = ""
	fileVersion = ""
	if exportType == "MESH":
		if "REMeshLastExportedMeshVersion" in scene:
			fileVersion = "." + str(scene["REMeshLastExportedMeshVersion"])
		elif "REMeshLastImportedMeshVersion" in scene:
			fileVersion = "." + str(scene["REMeshLastImportedMeshVersion"])
	
	elif exportType == "MDF":
		if "REMeshLastExportedMDFVersion" in scene:
			fileVersion = "." + str(scene["REMeshLastExportedMDFVersion"])
		elif "REMeshLastImportedMDFVersion" in scene:
			fileVersion = "." + str(scene["REMeshLastImportedMDFVersion"])
	
	elif exportType == "FBXSKEL":
		if "REMeshLastExportedFBXSkelVersion" in scene:
			fileVersion = "." + str(scene["REMeshLastExportedFBXSkelVersion"])
		elif "REMeshLastImportedFBXSkelVersion" in scene:
			fileVersion = "." + str(scene["REMeshLastImportedFBXSkelVersion"])
	
	elif exportType == "SFUR":
		if "REMeshLastExportedSFURVersion" in scene:
			fileVersion = "." + str(scene["REMeshLastExportedSFURVersion"])
		elif "REMeshLastImportedSFURVersion" in scene:
			fileVersion = "." + str(scene["REMeshLastImportedSFURVersion"])
	
	elif exportType == "CHAIN":
		if "REChainLastExportedChainVersion" in scene:
			fileVersion = "." + str(scene["REChainLastExportedChainVersion"])
		elif "REChainLastImportedChainVersion" in scene:
			fileVersion = "." + str(scene["REChainLastImportedChainVersion"])
	
	elif exportType == "CHAIN2":
		if "REChainLastExportedChain2Version" in scene:
			fileVersion = "." + str(scene["REChainLastExportedChain2Version"])
		elif "REChainLastImportedChain2Version" in scene:
			fileVersion = "." + str(scene["REChainLastImportedChain2Version"])
			
	elif exportType == "CLSP":
		if "REChainLastExportedCLSPVersion" in scene:
			fileVersion = "." + str(scene["REChainLastExportedCLSPVersion"])
		elif "REChainLastImportedChain2Version" in scene:
			fileVersion = "." + str(scene["REChainLastImportedCLSPVersion"])
	filePath = os.path.join(modDirectory,assetPath+fileVersion)
	return filePath
	
def populateCollectionList(itemList,collection,recursionLevel,parentName):
	
	item = itemList.add()
	item.name = collection.name
	if collection.color_tag == "NONE":
		item.icon = "OUTLINER_COLLECTION"
	else:
		item.icon = f"COLLECTION_{collection.color_tag}"
	item.hierarchyLevel = recursionLevel
	item.parentName = parentName
	
	recursionLevel += 1
	if collection.get("~TYPE") not in COLLECTION_TYPES:
		for child in collection.children:
			if checkForChildRECollectionsRecursive(child):
				item.hasChild = True
				populateCollectionList(itemList,child,recursionLevel,parentName = collection.name)
	else:
		item.invalid = True#Will be set to valid once a usable path is entered
		if "BatchExport_enabled" in collection:
			item.enabled = bool(collection["BatchExport_enabled"])
		if "BatchExport_path" in collection:
			item.path = collection["BatchExport_path"]
			#print(f"Batch Export: Loaded previous values for {item.name}")
			
		
		if collection["~TYPE"] == "RE_MESH_COLLECTION":
			item.exportType = "MESH"
			
			if "BatchExport_exportAllLODs" in collection:
				try:
					item.exportAllLODs = collection["BatchExport_exportAllLODs"]
					item.preserveSharpEdges = collection["BatchExport_preserveSharpEdges"]
					item.rotate90 = collection["BatchExport_rotate90"]
					#item.exportBlendShapes = collection["BatchExport_exportBlendShapes"]
					item.useBlenderMaterialName = collection["BatchExport_useBlenderMaterialName"]
					item.preserveBoneMatrices = collection["BatchExport_preserveBoneMatrices"]
					item.exportBoundingBoxes = collection["BatchExport_exportBoundingBoxes"]
				except Exception as err:
					print(f"Failed to load default values for {item.name} - {str(err)}")
					
		elif collection["~TYPE"] == "RE_MDF_COLLECTION":
			item.exportType = "MDF"
		elif collection["~TYPE"] == "RE_CHAIN_COLLECTION":
			if ".chain2" in item.name:
				item.exportType = "CHAIN2"
			else:
				item.exportType = "CHAIN"
		elif collection["~TYPE"] == "RE_CLSP_COLLECTION":
			item.exportType = "CLSP"
		elif collection["~TYPE"] == "RE_SFUR_COLLECTION":
			item.exportType = "SFUR"
		
		if item.path == "":
			if bpy.context.scene.re_mdf_toolpanel.modDirectory != "":
				try:
					split = splitNativesPath(bpy.context.scene.re_mdf_toolpanel.modDirectory)
					if split != None:
						assetPath = collection.get("~ASSETPATH",None)
						if assetPath != None:
							item.path = determineExportPath(split[0],item.exportType,assetPath.replace("/",os.sep),bpy.context.scene)
				except Exception as err:
					print(f"Batch Export: Cannot auto determine path for {item.name}: {str(err)}")
class WM_OT_REBatchExporter(Operator):
	bl_label = "RE Batch Exporter"
	bl_idname = "re_mesh.batch_exporter"
	bl_description = "Export all selected RE Engine files quickly"
	bl_options = {'INTERNAL'}
	
	itemList_items: bpy.props.CollectionProperty(type = ExporterNodePropertyGroup)
	itemList_index: bpy.props.IntProperty(name="")
	
	checkAllItems : bpy.props.BoolProperty(
	   name = "Check All Items",
	   description = "Select all files to be exported",
	   default = False,
	   update = update_checkAllItems
	   )
	uncheckAllItems : bpy.props.BoolProperty(
	   name = "Uncheck All Items",
	   description = "Deselect all files to be exported",
	   default = False,
	   update = update_uncheckAllItems
	   )
	
	def execute(self, context):
		print("Batch export started.")
		
		#Save which files are enabled
		for item in self.itemList_items:
			if item.exportType != "":
				if item.exportType == "FBXSKEL":
					bpy.data.objects[item.name]["BatchExport_enabled"] = item.enabled
				else:
					bpy.data.collections[item.name]["BatchExport_enabled"] = item.enabled
		
		exportItemList = [item for item in self.itemList_items if not item.hasChild and item.enabled and item.exportType != ""]
		failCount = 0
		for index,exportItem in enumerate(exportItemList):
			if exportItem.invalid:
				print(f"Skipping {exportItem.name} ({index+1}/{len(exportItemList)}) due to an invalid export path: {exportItem.path}")
				failCount += 1
				continue
			
			
			
			print(f"Exporting File: {exportItem.name} ({index+1}/{len(exportItemList)})")
			os.makedirs(os.path.split(exportItem.path)[0],exist_ok = True)
			if exportItem.exportType == "MESH":
				try:
					bpy.ops.re_mesh.exportfile(
						filepath = exportItem.path,
						targetCollection = exportItem.name,
						exportAllLODs = exportItem.exportAllLODs,
						autoSolveRepeatedUVs = exportItem.autoSolveRepeatedUVs,
						preserveSharpEdges = exportItem.preserveSharpEdges,
						rotate90 = exportItem.rotate90,
						useBlenderMaterialName = exportItem.useBlenderMaterialName,
						preserveBoneMatrices = exportItem.preserveBoneMatrices,
						exportBoundingBoxes = exportItem.exportBoundingBoxes,
						)
				except Exception as err:
					print(f"Mesh Export Failed: {str(err)}")
					failCount += 1
			elif exportItem.exportType == "MDF":
				try:
					bpy.ops.re_mdf.exportfile(
						filepath = exportItem.path,
						targetCollection = exportItem.name,
						)
				except Exception as err:
					print(f"MDF Export Failed: {str(err)}")
					failCount += 1
			elif exportItem.exportType == "FBXSKEL":
				try:
					bpy.ops.re_fbxskel.exportfile(
						filepath = exportItem.path,
						targetArmature = exportItem.name,
						)
				except Exception as err:
					print(f"FBXSkel Export Failed: {str(err)}")
					failCount += 1
			elif exportItem.exportType == "CHAIN":
				if hasattr(bpy.types, "OBJECT_PT_chain_object_mode_panel"):
					try:
						bpy.ops.re_chain.exportfile(
							filepath = exportItem.path,
							targetCollection = exportItem.name,
							)
					except Exception as err:
						print(f"Chain Export Failed: {str(err)}")
						failCount += 1
				else:
					print("RE Chain Editor is not installed. Skipping batch export entry.")
					failCount += 1
			elif exportItem.exportType == "CHAIN2":
				if hasattr(bpy.types, "OBJECT_PT_chain_object_mode_panel"):
					try:
						bpy.ops.re_chain2.exportfile(
							filepath = exportItem.path,
							targetCollection = exportItem.name,
							)
					except Exception as err:
						print(f"Chain2 Export Failed: {str(err)}")
						failCount += 1
				else:
					print("RE Chain Editor is not installed. Skipping batch export entry.")
					failCount += 1
			elif exportItem.exportType == "CLSP":
				if hasattr(bpy.types, "OBJECT_PT_chain_object_mode_panel"):
					try:
						bpy.ops.re_clsp.exportfile(
							filepath = exportItem.path,
							targetCollection = exportItem.name,
							)
					except Exception as err:
						print(f"Chain Export Failed: {str(err)}")
						failCount += 1
				else:
					print("RE Chain Editor is not installed. Skipping batch export entry.")
					failCount += 1
			elif exportItem.exportType == "SFUR":
				try:
					bpy.ops.re_sfur.exportfile(
						filepath = exportItem.path,
						targetCollection = exportItem.name,
						)
				except Exception as err:
					print(f"SFUR Export Failed: {str(err)}")
					failCount += 1
			else:
				print(f"Unsupported File Type ({exportItem.exportType}), skipping")
				failCount += 1
		if failCount != 0:
			showErrorMessageBox(f"{failCount}/{len(exportItemList)} files failed to export.\nSee console for details. (Window > Toggle System Console)")
		else:
			self.report({"INFO"},"Batch export finished successfully.")
		return {'FINISHED'}
	
	def invoke(self, context, event):
		region = bpy.context.region
		centerX = region.width // 2
		centerY = region.height
		
		#currentX = event.mouse_region_X
		#currentY = event.mouse_region_Y
		
		parentDict = {None:None}
		for collection in bpy.data.collections:
			parentDict[collection] = None
			
		for collection in bpy.data.collections:
			for child in collection.children:
				parentDict[child] = collection
		collectionRoots = set()
		for collection in bpy.data.collections:
			if collection.get("~TYPE") in COLLECTION_TYPES:
				parentCol = parentDict[collection]
				#print(f"Found supported collection: {collection.name},Parent:{parentDict[collection]}")
				
				while parentDict[parentCol] != None:
					parentCol = parentDict[parentCol]
				else:
					#print(f"Root collection:{parentCol.name}")
					if parentCol == None:
						collectionRoots.add(collection)
					else:
						collectionRoots.add(parentCol)
		
		#Populate list
		self.itemList_items.clear()
		for collection in collectionRoots:
			populateCollectionList(self.itemList_items, collection, recursionLevel = 0,parentName = "")
		
		#Add fbxskel armatures for export
		for armatureObj in [obj for obj in bpy.data.objects if obj.type == "ARMATURE" and (".fbxskel" in obj.name.lower() or (".skeleton" in obj.name.lower()))]:
			item = self.itemList_items.add()
			item.name = armatureObj.name
			item.icon = "ARMATURE_DATA"
			item.exportType = "FBXSKEL"
			item.invalid = True
			if "BatchExport_enabled" in armatureObj:
				item.enabled = bool(armatureObj["BatchExport_enabled"])
			if "BatchExport_path" in armatureObj:
				item.path = armatureObj["BatchExport_path"]
			if item.path == "":
				if bpy.context.scene.re_mdf_toolpanel.modDirectory != "":
					try:
						split = splitNativesPath(bpy.context.scene.re_mdf_toolpanel.modDirectory)
						if split != None:
							assetPath = armatureObj.get("~ASSETPATH",None)
							if assetPath != None:
								item.path = determineExportPath(split[0],item.exportType,assetPath.replace("/",os.sep),bpy.context.scene)
					except Exception as err:
						print(f"Batch Export: Cannot auto determine path for {item.name}: {str(err)}")
		#Move cursor to center so extract window is at the center of the window
		context.window.cursor_warp(centerX,centerY)
	
		return context.window_manager.invoke_props_dialog(self,width = EXPORTER_WINDOW_SIZE,confirm_text = "Batch Export Files")

	
	def draw(self,context):
		layout = self.layout
		rowCount = 13
		uifontscale = 9 * context.preferences.view.ui_scale
		max_label_width = int((EXPORTER_WINDOW_SIZE*(1-SPLIT_FACTOR)*(2-SPLIT_FACTOR)) // uifontscale)
		row = layout.row().separator()
		split = layout.split(factor = SPLIT_FACTOR)#Indent list slightly to make it more clear it's a part of a sub panel
		col1 = split.column()
		split2 = col1.split()
		col1sub1 = split2.column()
		col1sub1.alignment = "LEFT"
		col1sub1.label(text=f"Files ({sum(1 for item in self.itemList_items if (not item.hasChild and item.enabled))} selected)")
		col1sub2 = col1.column()
		row = split2.row()
		row.alignment = "RIGHT"
		row.prop(self,"checkAllItems",icon="CHECKMARK", icon_only=True)
		row.prop(self,"uncheckAllItems",icon="X", icon_only=True)
		col1.template_list(
			listtype_name = "MESH_UL_REExporterList", 
			list_id = "itemList",
			dataptr = self,
			propname = "itemList_items",
			active_dataptr = self, 
			active_propname = "itemList_index",
			rows = rowCount,
			type='DEFAULT'
			)
		col2 = split.column()
		col2.label(text="Export Settings")
		box = col2.box()
		if self.itemList_index != -1:
			item = self.itemList_items[self.itemList_index]
			if not item.hasChild and item.exportType != "":
				box.label(text=f"Type: {item.exportType}")
				box.label(text="Export Path")
				
				box.prop(item,"path")
				if item.invalid:
					row = box.row()
					row.alert = True
					row.label(text="Path is empty or missing the file version number on the end. ",icon = "ERROR")
				if item.exportType == "MESH":
					box.prop(item, "exportAllLODs")
					#box.prop(self, "exportBlendShapes")
					box.prop(item,"autoSolveRepeatedUVs")
					box.prop(item,"preserveSharpEdges")
					box.prop(item, "rotate90")
					box.prop(item, "useBlenderMaterialName")
					box.prop(item, "preserveBoneMatrices")
					box.prop(item, "exportBoundingBoxes")
			else:
				box.label(text=f"Select a file from the list to configure export settings.")