#Author: NSA Cloud
#TODO
#Add Blendshapes

#Import
#-Add armature only import x
#-Add armature merging x
#-Reload cached textures doesn't reload x
#-Add merge mesh groups import option x
#-Redo vertex color based material importing

#Export
#-Add common error checking x 
#-Add doubled uv checking x
#-Exporting imported mesh bounding sphere doesn't work properly
#-Submeshes aren't sorted
#-Add selected object only export
#-Fix scene collection mesh detection


import bpy
import bmesh
import os
from math import radians
from mathutils import Vector,Matrix
from itertools import chain, repeat, islice
from .file_re_mesh import readREMesh,writeREMesh,ParsedREMeshToREMesh,Sphere,AABB,Matrix4x4,meshFileVersionToGameNameDict
from .re_mesh_parse import ParsedREMesh,VisconGroup,LODLevel,SubMesh,ParsedBone,Skeleton
from ..mdf.file_re_mdf import readMDF
from ..mdf.blender_re_mesh_mdf import findMDFPathFromMeshPath,importMDF
from .re_mesh_export_errors import addErrorToDict,printErrorDict
from ..gen_functions import splitNativesPath,raiseWarning
from ..blender_utils import showErrorMessageBox
import time
import numpy as np																																																																												
timeFormat = "%d"
rotateNeg90Matrix = Matrix.Rotation(radians(-90.0), 4, 'X')
rotate90Matrix = Matrix.Rotation(radians(90.0), 4, 'X')
def pad_infinite(iterable, padding=None):
	return chain(iterable, repeat(padding))

def pad(iterable, size, padding=None):
	return islice(pad_infinite(iterable, padding), size)
def normalize(lst):
	s = sum(lst)
	return map(lambda x: float(x)/s, lst)
def normalizeVec(vec):
    return Vector(vec).normalized()
def dist(a, b) -> float:
    return  ((a[0] - b[0])**2 + (a[1] - b[1])**2 + (a[2] - b[2])**2)**0.5
def bounding_sphere_ritter(points):
    # Initial guess, same as before
    x = points[0]    #any arbitrary point in the point cloud works
    y = max(points,key= lambda p: dist(p,x) )    #choose point y furthest away from x
    z = max(points,key= lambda p: dist(p,y) )    #choose point z furthest away from y
    center, radius = (((y[0]+z[0])/2,(y[1]+z[1])/2,(y[2]+z[2])/2), dist(y,z)/2)    #initial bounding sphere
    
    # Note this doesn't use the radius^2 optimization that Ritter uses
    for p in points:
        d = dist(p, center)
        if d < radius:
            continue
        radius = .5 * (radius + d)
        old_to_new = d - radius
        new_center_x = (center[0] * radius + old_to_new * p[0]) / d
        new_center_y = (center[1] * radius + old_to_new * p[1]) / d
        new_center_z = (center[2] * radius + old_to_new * p[2]) / d
        center = (new_center_x, new_center_y, new_center_z)
    return center, radius
    
def vertexPosToGlobal(local_coords, world_matrix):

    # Reshape coords to Nx3 matrix
    local_coords.shape = (-1, 3)

    # Add an extra 1.0s column (for matrix dot product)
    local_coords = np.c_[local_coords, np.ones(local_coords.shape[0])]

    # Then:
    # Dot product matrix with the coords transpose
    # Keep the first 3 rows (x,y,z)
    # Transpose result to Nx3
    # Flatten
    global_coords = np.dot(world_matrix, local_coords.T)[0:3].T.reshape((-1))
    return np.reshape(global_coords,(-1,3))

def joinObjects(objList):
	ctx = bpy.context.copy()

	# one of the objects to join
	ctx['active_object'] = objList[0]
	ctx['selected_editable_objects'] = objList
	bpy.ops.object.join(ctx)
	
def createMaterialDict(materialNameList):
	materialDict = {}
	for materialName in materialNameList:
		material = bpy.data.materials.new(materialName)
		material.use_nodes = True;
		materialDict[materialName] = material
	return materialDict

def getCollection(collectionName,parentCollection = None,makeNew = False):
	if makeNew or not bpy.data.collections.get(collectionName):
		collection = bpy.data.collections.new(collectionName)
		collectionName = collection.name
		if parentCollection != None:
			parentCollection.children.link(collection)
		else:
			bpy.context.scene.collection.children.link(collection)
	return bpy.data.collections[collectionName]

def findArmatureObjFromData(armatureData):
	armatureObj = None
	for obj in bpy.context.scene.objects:
		if obj.type == "ARMATURE" and obj.data == armatureData:
			armatureObj = obj
			break
	return armatureObj
def importSkeleton(parsedSkeleton,armatureName,collection,rotate90,targetArmatureName = None):
	mergedArmature = False
	#Merging with existing armature if specified in import menu
	
	if targetArmatureName != "" and targetArmatureName in bpy.data.armatures:
		armatureObj = findArmatureObjFromData(bpy.data.armatures[targetArmatureName])
		if armatureObj != None:
			armatureData = armatureObj.data
			mergedArmature = True
		else:
			armatureData = bpy.data.armatures.new(armatureName)	
			armatureObj = bpy.data.objects.new(armatureName, armatureData)
			collection.objects.link(armatureObj)
		
	else:
		armatureData = bpy.data.armatures.new(armatureName)	
		armatureObj = bpy.data.objects.new(armatureName, armatureData)
		collection.objects.link(armatureObj)

	bpy.context.view_layer.objects.active = armatureObj
	bpy.ops.object.mode_set(mode='EDIT')
	
	boneNameIndexDict = {index: bone.boneName for index, bone in enumerate(parsedSkeleton.boneList)}
	
	if mergedArmature:
		print(f"Merging imported armature with {armatureObj.name}")
	elif targetArmatureName != "":
		print(f"The specified armature to merge with could not be found. Importing the armature as a new object.")
	
	for bone in parsedSkeleton.boneList:
		if bone.boneName not in armatureData.bones:
			editBone = armatureData.edit_bones.new(bone.boneName)
			editBone.tail = editBone.head + Vector((.0, .0, .1))
			if bone.parentIndex != -1:
				editBone.parent = armatureData.edit_bones[boneNameIndexDict[bone.parentIndex]]
			else:
				bone.head = Vector([.0, .0, .01])
			editBone.length = 0.1
			editBone.matrix = bone.worldMatrix.matrix
			editBone["reMeshWorldMatrix"] = bone.worldMatrix.matrix
			editBone["reMeshLocalMatrix"] = bone.localMatrix.matrix
			editBone["reMeshInverseMatrix"] = bone.inverseMatrix.matrix
			if mergedArmature:
				print(f"[MERGE] Added {bone.boneName} to {armatureObj.name}")
	bpy.ops.object.mode_set(mode='OBJECT')
	
	if rotate90 and targetArmatureName not in bpy.data.objects:
		prevSelection = bpy.context.selected_objects
		for obj in prevSelection:
			obj.select_set(False)
		
		armatureObj.matrix_world = armatureObj.matrix_world @ rotate90Matrix
		armatureObj.select_set(True)
		#I would prefer not to use bpy.ops but the data.transform on armatures does not function correctly.
		bpy.ops.object.transform_apply(location = False,rotation = True,scale = False)
		armatureObj.select_set(False)
		
		for obj in prevSelection:
			obj.select_set(True)
	return armatureObj

def importMesh(meshName = "newMesh",vertexList = [],faceList = [],vertexNormalList = [],vertexColor0List = [],vertexColor1List = [],UV0List = [],UV1List = [],UV2List = [],boneNameList = [],vertexGroupWeightList = [],vertexGroupBoneIndicesList = [],boneNameRemapList = [],material="Material",armature = None,collection = None,rotate90 = True):
	meshData = bpy.data.meshes.new(meshName)
	#Import vertices and faces
	meshData.from_pydata(vertexList, [], faceList)
	
	#Import vertex normals
	if vertexNormalList != []:
		
		
		meshData.update(calc_edges=True)
		meshData.polygons.foreach_set("use_smooth", [True] * len(meshData.polygons))
		meshData.normals_split_custom_set_from_vertices([normalizeVec(v) for v in vertexNormalList])
		if bpy.app.version < (4,0,0):
			meshData.use_auto_smooth = True
			meshData.calc_normals_split()
		"""
		meshData.use_auto_smooth = True
		meshData.polygons.foreach_set("use_smooth", [True] * len(meshData.polygons))
		meshData.normals_split_custom_set_from_vertices(vertexNormalList)
		"""
	#Import UV Layers
	UVLayerList = (UV0List,UV1List,UV2List)
	for layerIndex,layer in enumerate(UVLayerList):
		if layer != []:
			newUVLayer = meshData.uv_layers.new(name = "UVMap"+str(layerIndex))
			for face in meshData.polygons:
				for vertexIndex, loopIndex in zip(face.vertices, face.loop_indices):
					newUVLayer.data[loopIndex].uv = layer[vertexIndex]
	
	
	#Import vertex color layer 0
	if vertexColor0List != []:
		vcol_layer = meshData.vertex_colors.new()
		for l,color in zip(meshData.loops, vcol_layer.data):
			color.color = vertexColor0List[l.vertex_index]
	
	meshObj = bpy.data.objects.new(meshName, meshData)
	
	#Import Weights
	if vertexGroupWeightList != [] and boneNameList != []:
		#Only create vertex groups for bones that get used
		
		
		#print(boneNameList)
		usedBoneIndices = sorted(list({x for vertex in vertexGroupBoneIndicesList for x in vertex}))#Get all used bone indices in hierarchy order
		for boneIndex in usedBoneIndices:
			meshObj.vertex_groups.new(name = boneNameList[boneIndex])
			
		for vertexIndex, boneIndexList in enumerate(vertexGroupBoneIndicesList):
			#print(vertexIndex)
			#print(boneIndexList)
			for weightIndex, boneIndex in enumerate(boneIndexList):
				if vertexGroupWeightList[vertexIndex][weightIndex] > 0:
					boneName = boneNameList[boneIndex]
					meshObj.vertex_groups[boneName].add([vertexIndex],vertexGroupWeightList[vertexIndex][weightIndex],'ADD')
	
	
	
	if armature != None:
		meshObj.parent = armature
		mod = meshObj.modifiers.new(name = 'Armature', type = 'ARMATURE')
		mod.object = armature
		#meshObj.matrix_parent_inverse = armature.matrix_world.inverted()
	if rotate90:
		meshObj.data.transform(rotate90Matrix)
			
		
		#meshObj.matrix_world = meshObj.matrix_world @ rotate90Matrix
	if material != None:
		meshObj.data.materials.append(material)
	if collection != None:
		collection.objects.link(meshObj)
	else:
		bpy.context.scene.collection.objects.link(meshObj)
	return meshObj

def importLODGroup(parsedMesh,meshType,meshCollection,materialDict,armatureObj,hiddenCollectionSet,meshOffsetDict,importAllLODs = False,createCollections = True,importShadowMeshes = False,rotate90 = True,mergeGroups = False):
	
	if meshType == "Main Mesh":
		shortName = "Main"
		targetLODList = parsedMesh.mainMeshLODList
	elif meshType == "Shadow Mesh":
		shortName = "Shadow"
		targetLODList = parsedMesh.shadowMeshLODList
	elif meshType == "Occlusion Mesh":
		shortName = "Occlusion"
	firstLOD = True
	
	if parsedMesh.skeleton != None and parsedMesh.skeleton.weightedBones != []:
		boneNameList = parsedMesh.skeleton.weightedBones
	else:
		boneNameList = []
	
	if not importAllLODs and targetLODList != []:
		targetLODList = [targetLODList[0]]
	
	
	for lodIndex,lod in enumerate(targetLODList):
		shadowLODString = ""
		if importShadowMeshes:
			if lod in parsedMesh.shadowMeshLinkedLODList:
				shadowLODString = f" + Shadow LOD{parsedMesh.shadowMeshLinkedLODList.index(lod)}"
		if createCollections:
			lodCollection = getCollection(f"{meshType} LOD{str(lodIndex)}{shadowLODString} - {meshCollection.name}",meshCollection,makeNew = True)
			lodCollection["LOD Distance"] = lod.lodDistance
		else:
			lodCollection = meshCollection
		if not firstLOD and createCollections:
			#lodCollection.hide_viewport = True
			hiddenCollectionSet.add(lodCollection.name)
		for visconGroup in lod.visconGroupList:
			objMergeList = []
			for subMesh in visconGroup.subMeshList:
				if subMesh.isReusedMesh:	
					lodCollection.objects.link(meshOffsetDict[subMesh.meshVertexOffset])
				else:
					materialName = parsedMesh.materialNameList[subMesh.materialIndex]
					#print(subMesh.vertexPosList)
					
					if importAllLODs:
						LODNum = f"LOD_{str(lodIndex)}_"
					else:
						LODNum = ""
					meshObj = importMesh(
						#meshName=f"LOD_{str(lodIndex)}_{shortName}_Group_{str(visconGroup.visconGroupNum)}_Sub_{str(subMesh.subMeshIndex)}__{materialName}",
						
						
						
						meshName=f"{LODNum}Group_{str(visconGroup.visconGroupNum)}_Sub_{str(subMesh.subMeshIndex)}__{materialName}",
						vertexList=subMesh.vertexPosList,
						faceList=subMesh.faceList,
						vertexNormalList=subMesh.normalList,
						
						vertexColor0List=subMesh.colorList,
						UV0List=subMesh.uvList,
						UV1List=subMesh.uv2List,
						boneNameList=boneNameList,
						vertexGroupWeightList=subMesh.weightList,
						vertexGroupBoneIndicesList=subMesh.weightIndicesList,
						material = materialDict[materialName],
						armature=armatureObj,
						collection=lodCollection,
						rotate90 = rotate90
						)
					if mergeGroups:
						objMergeList.append(meshObj)
					meshOffsetDict[subMesh.meshVertexOffset] = meshObj
			if mergeGroups and len(objMergeList) > 1:
				joinObjects(objMergeList)
		firstLOD = False


def importBoundingBox(bbox,bboxName,meshCollection,armatureObj = None,boneParent = None,rotate90 = True):
	bboxVertList = [
	(bbox.min.x,bbox.min.y,bbox.min.z),
	(bbox.max.x,bbox.max.y,bbox.max.z),
	
	]
	bboxData = bpy.data.meshes.new(bboxName)
	bboxData.from_pydata(bboxVertList, [], [])
	bboxData.update()
	
	bboxObj = bpy.data.objects.new(bboxName, bboxData)
	meshCollection.objects.link(bboxObj)
	
	if armatureObj != None and boneParent != None:
		constraint = bboxObj.constraints.new(type = "CHILD_OF")
		constraint.target = armatureObj
		constraint.subtarget = boneParent
		constraint.name = "BoneName"
		constraint.inverse_matrix =  Matrix()
		bboxObj["~TYPE"] = "RE_MESH_BONE_BOUNDING_BOX"
	else:
		bboxObj["~TYPE"] = "RE_MESH_BOUNDING_BOX"
		if rotate90:
			bboxObj.matrix_world = bboxObj.matrix_world @ rotate90Matrix
	
	
	bboxObj["MeshExportExclude"] = 1
	
	bboxObj.show_bounds = True
	return bboxObj
def importBoundingSphere(sphere,sphereName,meshCollection,rotate90 = True):
	# Create an empty mesh and the object.
	sphereData = bpy.data.meshes.new(sphereName)
	sphereObj = bpy.data.objects.new(sphereName, sphereData)
	sphereObj.location = (sphere.x,sphere.y,sphere.z)
	sphereObj.display_type = "BOUNDS"
	sphereObj.display_bounds_type ="SPHERE"
	sphereObj["~TYPE"] = "RE_MESH_BOUNDING_SPHERE"
	sphereObj["MeshExportExclude"] = 1
	#sphereData.update()
	
	# Add the object into the scene.
	meshCollection.objects.link(sphereObj)
	

	
	
	# Construct the bmesh sphere and assign it to the blender mesh.
	bm = bmesh.new()
	bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=8, radius=sphere.r)
	bm.to_mesh(sphereData)
	bm.free()
	bpy.context.view_layer.update()
	if rotate90:
		sphereObj.matrix_world = rotate90Matrix @ sphereObj.matrix_world
	return sphereObj
def importBoundingBoxes(meshBoundingBox,meshBoundingSphere,meshCollection,armatureObj,parsedSkeleton = None,rotate90 = True):
		meshBBox = importBoundingBox(meshBoundingBox,"Mesh Bounding Box",meshCollection,rotate90 = rotate90)
		meshSphere = importBoundingSphere(meshBoundingSphere,"Mesh Bounding Sphere",meshCollection,rotate90 = rotate90)
		if parsedSkeleton != None:
			for bone in parsedSkeleton.boneList:
				if bone.boundingBox != None:
					importBoundingBox(bone.boundingBox,f"Bone Bounding Box ({bone.boneName})",meshCollection,armatureObj,bone.boneName,rotate90)


#---RE MESH IO FUNCTIONS---#

def importREMeshFile(filePath,options):
	meshImportStartTime = time.time()
	fileName = os.path.split(filePath)[1].split(".mesh")[0]
	try:
		meshVersion = int(os.path.splitext(filePath)[1].replace(".",""))
	except:
		print("Unable to parse mesh version number in file path.")
		meshVersion = None
	if meshVersion in meshFileVersionToGameNameDict:
		gameName = meshFileVersionToGameNameDict[meshVersion]
	else:
		gameName = None
		
	warningList = []
	errorList = []
	
	if options["clearScene"]:
		for collection in bpy.data.collections:
			for obj in collection.objects:
				collection.objects.unlink(obj)
			bpy.data.collections.remove(collection)
		for bpy_data_iter in (bpy.data.objects,bpy.data.meshes,bpy.data.lights,bpy.data.cameras):
			for id_data in bpy_data_iter:
				bpy_data_iter.remove(id_data)
		for material in bpy.data.materials:
			bpy.data.materials.remove(material)
		for amt in bpy.data.armatures:
			bpy.data.armatures.remove(amt)
		for obj in bpy.data.objects:
			bpy.data.objects.remove(obj)
			obj.user_clear()

	print("\033[96m__________________________________\nRE Mesh import started.\033[0m")
		
	reMesh = readREMesh(filePath)
	meshFileName = os.path.splitext(os.path.split(filePath)[1])[0]
	meshParseStartTime = time.time()
	parsedMesh = ParsedREMesh()
	parsedMesh.ParseREMesh(reMesh)
	print("Parsed mesh.")
	meshParseEndTime = time.time()
	meshParseTime =  meshParseEndTime - meshParseStartTime
	print(f"Mesh parsing took {timeFormat%(meshParseTime * 1000)} ms.")
	armatureObj = None
	if options["createCollections"]:
		meshCollection = getCollection(meshFileName,makeNew = True)
		meshCollection.color_tag = "COLOR_01"
		bpy.context.scene.re_mdf_toolpanel.meshCollection = meshCollection.name
	else:
		meshCollection = bpy.context.scene.collection
	hiddenCollectionSet = set()
	if parsedMesh.skeleton != None:
		armatureObj = importSkeleton(parsedMesh.skeleton,meshFileName.split(".mesh")[0]+" Armature",meshCollection,options["rotate90"],options["mergeArmature"])
	#Create dictionary of material names mapping to material data to avoid assigning the wrong material in case of name duplication
	materialDict = createMaterialDict(parsedMesh.materialNameList)
	meshOffsetDict = dict()
	
	if not options["importArmatureOnly"]:
		importLODGroup(parsedMesh,"Main Mesh",meshCollection,materialDict,armatureObj,hiddenCollectionSet,meshOffsetDict,options["importAllLODs"],options["createCollections"],options["importShadowMeshes"],options["rotate90"],options["mergeGroups"])
	"""
	if options["importShadowMeshes"] and parsedMesh.shadowMeshLODList != []:
		importLODGroup(parsedMesh,"Shadow Mesh",meshCollection,materialDict,armatureObj,hiddenCollectionSet,meshOffsetDict)
	"""
	#Hide other lods in viewport
	#print(hiddenCollectionSet)
	collections = bpy.context.view_layer.layer_collection.children
	for collection in collections:
		if collection.name == meshCollection.name:	
			for childCollection in collection.children:
				if childCollection.name in hiddenCollectionSet:
					childCollection.hide_viewport = True
			break
	
	
	
	meshOffsetDict.clear()
	if options["loadMaterials"] and not options["importArmatureOnly"]:
		#print(filePath.split(".mesh")[1])
		if options["mdfPath"] != "":
			mdfPath = options["mdfPath"]
		else:
			mdfPath = findMDFPathFromMeshPath(filePath)
			#print(mdfPath)
		try:
			if mdfPath != None:
				split = splitNativesPath(mdfPath)
				if split != None:
					chunkPath = split[0]
				else:
					chunkPath = ""
				mdfImportStartTime = time.time()
				mdfFile = readMDF(mdfPath)
				importMDF(mdfFile,materialDict,options["materialLoadLevel"],options["reloadCachedTextures"],chunkPath = chunkPath)
				
				mdfImportEndTime = time.time()
				mdfImportTime =  mdfImportEndTime - mdfImportStartTime
				print(f"Material importing took {timeFormat%(mdfImportTime * 1000)} ms.")
			else:
				warningList.append("MDF file not found.")
		except Exception as err:
			print(str(err))
			warningList.append("Could not import " + mdfPath +":" + str(err))
	if options["createCollections"]:
		bpy.context.scene["REMeshLastImportedCollection"] = meshCollection.name
	bpy.context.scene["REMeshLastImportedMeshVersion"] = meshVersion	
	if options["importBoundingBoxes"]:
		if options["createCollections"]:
			boundingBoxCollection = getCollection(f"{meshFileName} Bounding Boxes",meshCollection,makeNew = True)
			boundingBoxCollection["~TYPE"] = "RE_MESH_BOUNDING_BOX_COLLECTION"
		else:
			boundingBoxCollection = meshCollection
		importBoundingBoxes(parsedMesh.boundingBox,parsedMesh.boundingSphere,boundingBoxCollection,armatureObj,parsedMesh.skeleton,options["rotate90"])
	meshImportEndTime = time.time()
	meshImportTime =  meshImportEndTime - meshImportStartTime
	print(f"Mesh imported in {timeFormat%(meshImportTime * 1000)} ms.")
	print("\033[92m__________________________________\nRE Mesh import finished.\033[0m")
	return (warningList,errorList)

def checkObjForUVDoubling(obj):
	hasUVDoubling = False
	UVPoints = dict()
	if len(obj.data.uv_layers) > 0:
		for loop in obj.data.loops:
			currentVertIndex = loop.vertex_index
			#Vertex UV
			uv = obj.data.uv_layers[0].data[loop.index].uv
			
			if currentVertIndex in UVPoints and UVPoints[currentVertIndex] != uv:
				hasUVDoubling = True
				break
				#raise Exception
			else:
				UVPoints[currentVertIndex] = uv
	return hasUVDoubling

def splitSharpEdges(obj):
	oldActiveObj = bpy.context.view_layer.objects.active
	bpy.context.view_layer.objects.active = obj
	bpy.ops.object.mode_set(mode='EDIT')
	obj = bpy.context.edit_object
	me = obj.data
	bm = bmesh.from_edit_mesh(me)
	# old seams
	sharp = [e for e in bm.edges if not e.smooth]
	bmesh.ops.split_edges(bm, edges=sharp)
	bmesh.update_edit_mesh(me)
	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.context.view_layer.objects.active = oldActiveObj

def exportREMeshFile(filePath,options):
	#TODO Warning Conditions
	#Invalid mesh naming scheme - notify when using blender material name and setting viscon id to 0
	#Vertex groups weighted to bones that aren't on the armature
	#If an mdf for the mesh imported, check if the mesh materials are mismatched with mdf
	
	#Error Conditions
	#No meshes in collection or selection x
	#More than one armature in collection x
	#No material on submesh x
	#Loose vertices on submesh x
	#No uv on submesh x
	#Max weighted bones exceeded x
	#Max weights per vertex exceeded x
	#Multiple uvs assigned to single vertex x
	#No vertices on submesh x
	#No faces on submesh x
	#Non triangulated face x
	#Max vertices exceeded x
	#Max faces exceeded x
	#No bones on armature x
	
	#TODO Error Conditions
	#More than one material on submesh
	
	
	
	
	

	
	errorDict = dict()
	#TODO Fix having all bones as weighted bones breaks export
	meshExportStartTime = time.time()
	vertexCount = 0
	faceCount = 0
	fileName = os.path.split(filePath)[1].split(".mesh")[0]
	try:
		meshVersion = int(os.path.splitext(filePath)[1].replace(".",""))
	except:
		print("Unable to parse mesh version number in file path.")
		meshVersion = 0
	if meshVersion in meshFileVersionToGameNameDict:
		gameName = meshFileVersionToGameNameDict[meshVersion]
	else:
		gameName = None
	
	print("\033[96m__________________________________\nRE Mesh export started.\033[0m")
	
	
	#Basic Error Checking
	#if errorList == []:

	
	maxWeightsPerVertex = 8
	maxWeightedBones = 256
	if gameName == "SF6":
		maxWeightsPerVertex = 6
		maxWeightedBones = 1024
	MAX_VERTICES = 65535
	MAX_FACES = 4294967295
	normalizeWeights = True
	rotate90 = False
	
	targetCollection = bpy.data.collections.get(options["targetCollection"])
	
	if targetCollection == None:
		print("No target collection set. Using scene collection.")
		targetCollection = bpy.context.scene.collection
	else:
		print(f"Target collection: {targetCollection.name}")
	#print(targetCollection)
	
	meshLODCollectionList = []
	addedMaterialsSet = set()
	dg = bpy.context.evaluated_depsgraph_get()
	parsedMesh = ParsedREMesh()
	parsedMesh.boundingBox = None
	parsedMesh.boundingSphere = None
	newMeshDataList = []
	vertexGroupsSet = set()
	weightedBonesSet = set()
	deleteCopiedMeshList = []
	boundingBoxCollection = None
	importedBoneBoundingBoxes = {}
	for childCollection in targetCollection.children:
		if "Main Mesh LOD" in childCollection.name:
			meshLODCollectionList.append(childCollection)
		elif childCollection.get("~TYPE") == "RE_MESH_BOUNDING_BOX_COLLECTION":
			boundingBoxCollection = childCollection
	
	#Find armature and parse it
	armatureObj = None
	for obj in targetCollection.objects:
		if obj.type == "ARMATURE":
			if armatureObj == None:
				armatureObj = obj
			else:
				addErrorToDict(errorDict, "MoreThanOneArmature", None)
	
	exportArmatureData = None
	if armatureObj != None:
		
		parsedMesh.skeleton = Skeleton()
		exportArmatureData = armatureObj.data.copy()
		if options["rotate90"]:
			transform = rotateNeg90Matrix @ armatureObj.matrix_world
		else:
			transform = armatureObj.matrix_world
		exportArmatureData.transform(transform)
		boneIndexDict = {bone.name: index for index, bone in enumerate(armatureObj.data.bones)}
		#print(boneIndexDict)
		for bone in exportArmatureData.bones:
			parsedBone = ParsedBone()
			#Get hierarchy
			parsedBone.boneName = bone.name
			parsedBone.boneIndex = boneIndexDict[bone.name]
			parsedBone.nextSiblingIndex = -1
			parsedBone.nextChildIndex = -1
			parsedBone.symmetryIndex = -1
			if bone.name[0:2] == "L_" and "R_"+bone.name[2::] in armatureObj.data.bones:
				parsedBone.symmetryIndex = boneIndexDict["R_"+bone.name[2::]]	
			elif bone.name[0:2] == "R_" and "L_"+bone.name[2::] in armatureObj.data.bones:
				parsedBone.symmetryIndex = boneIndexDict["L_"+bone.name[2::]]
				
			if bone.parent != None:
				parsedBone.parentIndex = boneIndexDict[bone.parent.name]
				for childBone in bone.parent.children:
					if childBone.name != bone.name and boneIndexDict[bone.name] < boneIndexDict[childBone.name]:
						parsedBone.nextSiblingIndex = boneIndexDict[childBone.name]
						break
			else:
				parsedBone.parentIndex = -1
			
			if len(bone.children) != 0:
				nextChildIndex = boneIndexDict[bone.children[0].name]
			#Get matrices
			if options["preserveBoneMatrices"]:
				if bone.get("reMeshWorldMatrix"):
					parsedBone.worldMatrix.matrix = bone["reMeshWorldMatrix"]
				if bone.get("reMeshLocalMatrix"):
					parsedBone.localMatrix.matrix = bone["reMeshLocalMatrix"]
				if bone.get("reMeshInverseMatrix"):
					parsedBone.inverseMatrix.matrix = bone["reMeshInverseMatrix"]
			else:
				
				worldMatrix = bone.matrix_local.to_4x4().transposed()
				#print(worldMatrix)
				
				if bone.parent != None:
				    localMatrix = (bone.parent.matrix_local.to_4x4().inverted() @ bone.matrix_local.to_4x4()).transposed()
				else:

					localMatrix = (bone.matrix_local).inverted().transposed()
				inverseMatrix = worldMatrix.inverted()
				
				parsedBone.worldMatrix.matrix = [list(row) for row in worldMatrix]
				parsedBone.localMatrix.matrix = [list(row) for row in localMatrix]
				parsedBone.inverseMatrix.matrix = [list(row) for row in inverseMatrix]
				
				"""
				#Get world matrix
				if bone.parent != None:
					if rotate90:
						parsedBone.worldMatrix.matrix = [list(row) for row in (rotate90Matrix @ (bone.parent.matrix_local.inverted() @ (bone.matrix_local)))]
					else:
						parsedBone.worldMatrix.matrix = [list(row) for row in (bone.parent.matrix_local.inverted() @ (bone.matrix_local))]
				else:
					
				#Get local matrix
				if bone.parent != None:
					parsedBone.localMatrix.matrix = [list(row) for row in armatureScaleMatrix @ (bone.parent.matrix_local.inverted() @ bone.matrix_local)]
				else:
					if rotate90:
						parsedBone.localMatrix.matrix = [list(row) for row in rotate90Matrix @ (armatureWorldMatrix @ bone.matrix_local)]
					else:
						parsedBone.localMatrix.matrix = [list(row) for row in (armatureWorldMatrix @ bone.matrix_local)]
				
				#Get inverse matrix
				if rotate90:
					parsedBone.inverseMatrix.matrix = [list(row) for row in (rotate90Matrix @ (armatureWorldMatrix @ (bone.matrix_local)))]
				else:
					parsedBone.inverseMatrix.matrix = [list(row) for row in (armatureWorldMatrix @ (bone.matrix_local))]
				"""
			parsedMesh.skeleton.boneList.append(parsedBone)
			
			#print(bone.name)
	#Get previously imported bounding boxes if option enabled
	if boundingBoxCollection != None and options["exportBoundingBoxes"]:
		for obj in boundingBoxCollection.objects:
			objType = obj.get("~TYPE")
			if objType == "RE_MESH_BONE_BOUNDING_BOX":
				if obj.constraints.get("BoneName") != None:
					if obj.data.vertices[0].co[0] < obj.data.vertices[1].co[0] \
					or obj.data.vertices[0].co[1] < obj.data.vertices[1].co[1] \
					or obj.data.vertices[0].co[2] < obj.data.vertices[1].co[2]: 
						minVert = obj.data.vertices[0].co
						maxVert = obj.data.vertices[1].co
					else:
						minVert = obj.data.vertices[1].co
						maxVert = obj.data.vertices[0].co
					
					if armatureObj != None:
						minVert = minVert @ armatureObj.matrix_world.inverted()#Cancel out the armature rotation
						maxVert = maxVert @ armatureObj.matrix_world.inverted()
					boneBBox = AABB()
					boneBBox.min.x = minVert[0]
					boneBBox.min.y = minVert[1]
					boneBBox.min.z = minVert[2]
					boneBBox.max.x = maxVert[0]
					boneBBox.max.y = maxVert[1]
					boneBBox.max.z = maxVert[2]
					importedBoneBoundingBoxes[obj.constraints["BoneName"].subtarget] = boneBBox
			elif objType == "RE_MESH_BOUNDING_BOX":
				importedMeshBoundingBox = AABB()
				if obj.data.vertices[0].co[0] < obj.data.vertices[1].co[0] \
				or obj.data.vertices[0].co[1] < obj.data.vertices[1].co[1] \
				or obj.data.vertices[0].co[2] < obj.data.vertices[1].co[2]: 
					minVert = obj.data.vertices[0]
					maxVert = obj.data.vertices[1]
				else:
					minVert = obj.data.vertices[1]
					maxVert = obj.data.vertices[0]
				parsedMesh.boundingBox.min.x = minVert.co[0]
				parsedMesh.boundingBox.min.y = minVert.co[1]
				parsedMesh.boundingBox.min.z = minVert.co[2]
				parsedMesh.boundingBox.max.x = maxVert.co[0]
				parsedMesh.boundingBox.max.y = maxVert.co[1]
				parsedMesh.boundingBox.max.z = maxVert.co[2]
			elif objType == "RE_MESH_BOUNDING_SPHERE":
				importedMeshBoundingSphere = Sphere()
				
				parsedMesh.boundingSphere.x = obj.location[0]
				parsedMesh.boundingSphere.y = obj.location[1]
				parsedMesh.boundingSphere.z = obj.location[2]
				parsedMesh.boundingSphere.r = obj.dimensions.x/2
	if meshLODCollectionList == []:
		meshLODCollectionList = [targetCollection]
	meshLODCollectionList.sort(key=lambda col: col.name)
	#Loop through all lod collections, or the scene collection if there is no collections
	meshDataStartTime = time.time()
	isFirstLOD = True
	remapDict = dict()
	boneVertDict = dict()
	for lodIndex, lod in enumerate(meshLODCollectionList):
		print(f"LOD {lodIndex} collection:{lod.name}")
		parsedLODLevel = LODLevel()
		if lod.get("LOD Distance") == None:
			lod["LOD Distance"] = 0.167932*(lodIndex+1)#Player model LOD distance, maybe calculate from a bounding box instead
		parsedLODLevel.lodDistance = lod["LOD Distance"]
		
		#Store all groups as a key in dictionary with submesh list as value
		visconDict = dict()
		boneRemapStartTime = time.time()
		#Get all meshes inside the collection
		doubledUVList = []
		for obj in lod.objects:
			if options["selectedOnly"]:
				selected = obj in bpy.context.selected_objects
			else:
				selected = True
			
				
			if obj.type == "MESH" and not obj.get("MeshExportExclude") and selected:
				
				if options["autoSolveRepeatedUVs"]:
					hasUVDoubling = checkObjForUVDoubling(obj)
					if hasUVDoubling:
						#print(f"Found doubled uvs on {obj.name}")
						doubledUVList.append(obj)
				
					
				if options["preserveSharpEdges"]:
					splitSharpEdges(obj)
					
				if "Group_" in obj.name:
					try:
						groupID = int(obj.name.split("Group_")[1].split("_")[0])
					except:
						pass
				else:
					print("Could not parse group ID in {obj.name}, setting to 0")
					groupID = 0
				
				#Build bone remap table from first LOD by first finding all bones that have vertex groups weighted to them
				if isFirstLOD and armatureObj != None:
					hasWeights = False
					for vg in obj.vertex_groups:#If weight is applied to any vertex groups, add them to weighted bone set
						
						if any(vg.index in [g.group for g in v.groups] for v in obj.data.vertices) and vg.name in armatureObj.data.bones:
							weightedBonesSet.add(vg.name)
							hasWeights = True
						else:
							remapDict[vg.name] = 0
					if armatureObj != None and not hasWeights:
						addErrorToDict(errorDict, "NoWeightsOnMesh", obj.name)  
						
				if not visconDict.get(groupID):
					visconDict[groupID] = [obj]
				else:
					visconDict[groupID].append(obj)
		
		
		if doubledUVList != []:
			previousSelection = bpy.context.selected_objects
			bpy.ops.object.select_all(action='DESELECT')
			for obj in doubledUVList:
				obj.select_set(True)
			if hasattr(bpy.types, "OBJECT_PT_re_tools_quick_export_panel"):#RE Toolbox installed
				bpy.ops.re_toolbox.solve_repeated_uvs()
			else:
				raiseWarning("RE Toolbox is not installed. Cannot solve repeated UVs automatically.")
			bpy.ops.object.select_all(action='DESELECT')
			for obj in previousSelection:
				obj.select_set(True)
		
		
		#Build remap dict once all objects of the first lod are looped through
		
		if isFirstLOD and armatureObj != None:
			remapIndex = 0
			for bone in armatureObj.data.bones:
				if bone.name in weightedBonesSet:
					parsedMesh.skeleton.weightedBones.append(bone.name)
					remapDict[bone.name] = remapIndex
					remapIndex += 1
			boneRemapEndTime = time.time()
			boneRemapTime =  boneRemapEndTime - boneRemapStartTime
			boneVertDict = {boneName: [] for boneName in parsedMesh.skeleton.weightedBones}
			#print(boneVertDict)
			#print(remapDict)
		#Once all viscons have been added, sort them, then parse the submeshes
		for visconGroupID in sorted(visconDict.keys()):
			print(f"  Group:{visconGroupID}")
			visconGroup = VisconGroup()
			visconGroup.visconGroupNum = visconGroupID
			#Sort by submesh number
			for submeshIndex,rawsubmesh in enumerate(sorted(visconDict[visconGroupID],key=lambda obj: obj.name)):
				rawsubmesh.data.update()
				#Get copy of sub mesh with modifiers applied
				evaluatedSubMeshData = bpy.data.meshes.new_from_object(rawsubmesh.evaluated_get(dg))
				deleteCopiedMeshList.append(evaluatedSubMeshData)
				
				if len((evaluatedSubMeshData.vertices)) == 0:
					addErrorToDict(errorDict, "NoVerticesOnSubMesh", rawsubmesh.name)
					
				if len((evaluatedSubMeshData.polygons)) == 0:
					addErrorToDict(errorDict, "NoFacesOnSubMesh", rawsubmesh.name)
				print(f"    Sub Mesh {str(submeshIndex)}:{rawsubmesh.name}")
				parsedSubMesh = SubMesh()
				parsedSubMesh.subMeshIndex = submeshIndex
				materialName = "NO_ASSIGNED_MATERIAL"
				if options["useBlenderMaterialName"]:#Material name from object material
					if len(evaluatedSubMeshData.materials) > 0:
						materialName = evaluatedSubMeshData.materials[0].name.split(".")[0]
					else:
						try:#Get material from mesh name if it isn't found
							materialName = rawsubmesh.name.split("__",1)[1].split(".")[0]
						except:
								addErrorToDict(errorDict, "NoMaterialOnSubMesh", rawsubmesh.name)
				
				else:#Material name from object name
					try:#Get material from mesh name if it isn't found
						materialName = rawsubmesh.name.split("__",1)[1].split(".")[0]
					except:#Fall back to blender material name if object material name is missing
						print(f"Couldn't split material name on {rawsubmesh.name}, using blender material name instead")
						if len(evaluatedSubMeshData.materials) > 0:
							materialName = evaluatedSubMeshData.materials[0].name.split(".")[0]
						else:
							addErrorToDict(errorDict, "NoMaterialOnSubMesh", rawsubmesh.name)
				if materialName not in addedMaterialsSet:
					addedMaterialsSet.add(materialName)
					parsedMesh.materialNameList.append(materialName)
					parsedMesh.nameList.append(materialName)
					parsedSubMesh.materialIndex = len(parsedMesh.materialNameList)-1
				else:
					parsedSubMesh.materialIndex = parsedMesh.materialNameList.index(materialName)
				# Convert to global
				if options["rotate90"]:
					subMeshWorldMatrix = rotateNeg90Matrix @ rawsubmesh.matrix_world
				else:
					subMeshWorldMatrix = rawsubmesh.matrix_world	
					
				evaluatedSubMeshData.transform(subMeshWorldMatrix)
				#evaluatedSubMeshData.normals_split_custom_set_from_vertices([vert.normal for vert in evaluatedSubMeshData.vertices])
				if bpy.app.version < (4,0,0):
					evaluatedSubMeshData.use_auto_smooth = True
					evaluatedSubMeshData.calc_normals_split()
				try:
					evaluatedSubMeshData.calc_tangents()
				except:
					pass
				vertexCount += len(evaluatedSubMeshData.vertices)
				faceCount += len(evaluatedSubMeshData.polygons)
				
				vertexGroupIndexToRemapDict = {vgroup.index: remapDict[vgroup.name] for vgroup in rawsubmesh.vertex_groups}
				
				#print(vertexGroupIndexToRemapDict)
				parsedMesh.bufferHasPosition = True
				parsedSubMesh.vertexPosList = np.zeros((len(evaluatedSubMeshData.vertices),3))
				parsedMesh.bufferHasNorTan = True
				parsedSubMesh.normalList = np.zeros((len(evaluatedSubMeshData.vertices),3))
				parsedSubMesh.tangentList = np.zeros((len(evaluatedSubMeshData.vertices),4),dtype="<B")
				if armatureObj != None:
					parsedMesh.bufferHasWeight = True
					parsedSubMesh.weightList = np.zeros((len(evaluatedSubMeshData.vertices),8))
					parsedSubMesh.weightIndicesList = np.zeros((len(evaluatedSubMeshData.vertices),8),dtype="<H")#ushort because of SF6
				#Get Faces
				parsedSubMesh.faceList = [tuple(f.vertices) for f in evaluatedSubMeshData.polygons]
				if any([len(face) != 3 for face in parsedSubMesh.faceList]):
					addErrorToDict(errorDict, "NonTriangulatedFace", rawsubmesh.name)
				if len(evaluatedSubMeshData.uv_layers) > 0:
					parsedSubMesh.uvList = np.zeros((len(evaluatedSubMeshData.vertices),2))
					meshHasUV = True
					parsedMesh.bufferHasUV = True
				else:
					meshHasUV = False
					addErrorToDict(errorDict, "NoUVMapOnSubMesh", rawsubmesh.name)
				if len(evaluatedSubMeshData.uv_layers) > 1:
					meshHasUV2 = True
					parsedSubMesh.uv2List = np.zeros((len(evaluatedSubMeshData.vertices),2))
					parsedMesh.bufferHasUV2 = True
				else:	
					parsedSubMesh.uv2List = None
					meshHasUV2 = False
				if len(evaluatedSubMeshData.vertex_colors) > 0:
					parsedSubMesh.colorList = np.zeros((len(evaluatedSubMeshData.vertices),4))
					meshHasColor = True
					parsedMesh.bufferHasColor = True
				else:
					meshHasColor = False
					parsedSubMesh.colorList = None
				
				#Credit to RaiderB and WoefulWolf for this, I thought this way of getting vertex data was pretty efficient
				#Get Vertex Data
				sortedLoops = sorted(evaluatedSubMeshData.loops, key=lambda loop: loop.vertex_index)
				previousIndex = -1
				
				#These are used to check if there's multiple uvs per vertex
				#If the current vert is already in the set, throw an error
				
				UVPoints = dict()
				UV2Points = dict()
				for loop in sortedLoops:
					currentVertIndex = loop.vertex_index
					#Vertex UV
					if meshHasUV:
						uv = evaluatedSubMeshData.uv_layers[0].data[loop.index].uv
						parsedSubMesh.uvList[currentVertIndex] = uv
						
						if currentVertIndex in UVPoints and UVPoints[currentVertIndex] != uv:
							addErrorToDict(errorDict, "MultipleUVsAssignedToVertex", rawsubmesh.name)
							#print(f"ERROR: Multiple UVs per vertex on UV1 of {rawsubmesh.name}")
							#raise Exception
						else:
							UVPoints[currentVertIndex] = uv
						#else:
							#print(f"ERROR: Multiple UVs per vertex on UV1 of {evaluatedSubMeshData.name}")
							#raise Exception
						if meshHasUV2:
							uv2 = evaluatedSubMeshData.uv_layers[1].data[loop.index].uv
							parsedSubMesh.uv2List[currentVertIndex] = uv2
							
							if currentVertIndex in UV2Points and UV2Points[currentVertIndex] != uv2:
								addErrorToDict(errorDict, "MultipleUVsAssignedToVertex", rawsubmesh.name)
								#print(f"ERROR: Multiple UVs per vertex on UV2 of {rawsubmesh.name}")
								#raise Exception
							else:
								UV2Points[currentVertIndex] = uv2
					
					if currentVertIndex == previousIndex:#Skip looping over vertices that have already been read
						continue

					previousIndex = currentVertIndex
					#Vertex Pos
					vertex = evaluatedSubMeshData.vertices[currentVertIndex]
					parsedSubMesh.vertexPosList[currentVertIndex] = vertex.co
					
					#Vertex Normal
					
					parsedSubMesh.normalList[currentVertIndex] = loop.normal
					
					#Vertex Tangent
					
					loopTangent = loop.tangent * 127
					tx = int(loopTangent[0] + 127.0)
					ty = int(loopTangent[1] + 127.0)
					tz = int(loopTangent[2] + 127.0)
					sign = int(-loop.bitangent_sign*127.0+128.0)

					parsedSubMesh.tangentList[currentVertIndex] = (tx, ty, tz, sign)
					
					
					#Vertex Color	
					if meshHasColor:
						parsedSubMesh.colorList[currentVertIndex] = evaluatedSubMeshData.vertex_colors[0].data[loop.index].color
						
				
					#Bone Weights
					if parsedMesh.bufferHasWeight:
						weightList = [g.weight for g in vertex.groups]
						weightIndicesList = [vertexGroupIndexToRemapDict[g.group] for g in vertex.groups]
						
						#print(weightIndicesList)
						if len(weightList) > maxWeightsPerVertex:
							addErrorToDict(errorDict, "MaxWeightsPerVertexExceeded", rawsubmesh.name)
						
						#Gather vertex positions of bone weights to generate bone bounding box
						if isFirstLOD:
							for weightIndex,weight in enumerate(weightList):
								if weight != 0.0:
									boneVertDict[parsedMesh.skeleton.weightedBones[weightIndicesList[weightIndex]]].append(vertex.co)
						parsedSubMesh.weightList[currentVertIndex] = list(pad(weightList,size=8,padding=0.0))
						parsedSubMesh.weightIndicesList[currentVertIndex] = list(pad(weightIndicesList,size=8,padding=0))
				
				visconGroup.subMeshList.append(parsedSubMesh)
				if any([vertIndex not in UVPoints for vertIndex in range(len(evaluatedSubMeshData.vertices))]):
					addErrorToDict(errorDict, "LooseVerticesOnSubMesh", rawsubmesh.name)  
				
				#End submesh
			parsedLODLevel.visconGroupList.append(visconGroup)
			#End viscon
		if "+ Shadow LOD" in lod.name:
			parsedMesh.shadowMeshLinkedLODList.append(parsedLODLevel)
			print(f"Shadow LOD {str(len(parsedMesh.shadowMeshLinkedLODList))} linked to Main Mesh LOD {str(lodIndex)}")
		parsedMesh.mainMeshLODList.append(parsedLODLevel)
		isFirstLOD = False
		#End LOD
		
	
	meshDataEndTime = time.time()
	meshDataExportTime =  meshDataEndTime - meshDataStartTime
	
	print(f"Gathering mesh data took {timeFormat%(meshDataExportTime * 1000)} ms.")
	
	#TODO Calculate bounding boxes
		
	#print(parsedMesh.materialNameList)
	#Get weights for meshes and calculate bone bounding boxes
	weightStartTime = time.time()
	if armatureObj != None:
		print(f"Generating bone remap dictionary took {timeFormat%(boneRemapTime * 1000)} ms.")
		boneBBoxDict = dict()
		for boneName in parsedMesh.skeleton.weightedBones:
			vecList = boneVertDict[boneName]
			#print(boneName)
			
			bonePos = exportArmatureData.bones[boneName].head_local
			#print(bonePos)
			
			#Get position relative to bone head
			if len(vecList) > 0:
				minVec = Vector((min([pos[0] for pos in vecList]),min([pos[1] for pos in vecList]),min([pos[2] for pos in vecList]))) - bonePos
				maxVec = Vector((max([pos[0] for pos in vecList]),max([pos[1] for pos in vecList]),max([pos[2] for pos in vecList]))) - bonePos
			else:
				raiseWarning(f"{boneName} has zero weight vertex groups assigned.")
				minVec = Vector((0.0,0.0,0.0))
				maxVec = Vector((0.01,0.01,0.01))
			#print(minVec)
			#print(maxVec)
			#boneVertDict[boneName] =
			boneBBoxDict[boneName] = {"min":minVec,"max":maxVec}
			
		
		#Assign bounding boxes to bones
		for bone in parsedMesh.skeleton.boneList:
			if bone.boneName in boneBBoxDict:
				if options["exportBoundingBoxes"] and bone.boneName in importedBoneBoundingBoxes:
					bone.boundingBox = importedBoneBoundingBoxes[bone.boneName]
				else:
					bone.boundingBox = AABB()
					bone.boundingBox.min.x =  boneBBoxDict[bone.boneName]["min"][0]
					bone.boundingBox.min.y =  boneBBoxDict[bone.boneName]["min"][1]
					bone.boundingBox.min.z =  boneBBoxDict[bone.boneName]["min"][2]
					bone.boundingBox.max.x =  boneBBoxDict[bone.boneName]["max"][0]
					bone.boundingBox.max.y =  boneBBoxDict[bone.boneName]["max"][1]
					bone.boundingBox.max.z =  boneBBoxDict[bone.boneName]["max"][2]
		weightEndTime = time.time()
		weightExportTime =  weightEndTime - weightStartTime
		print(f"Building bone bounding boxes took {timeFormat%(weightExportTime * 1000)} ms.")
		
	#Generate mesh bounding box and bounding sphere from lowest quality LOD level
	meshBBoxStartTime = time.time()
	vertArrayList = []
	for group in parsedMesh.mainMeshLODList[-1].visconGroupList:
		vertArrayList.extend([submesh.vertexPosList for submesh in group.subMeshList])
	#print(vertArrayList)
	fullVertArray = np.vstack(vertArrayList)
	if parsedMesh.boundingSphere == None:
		center,radius = bounding_sphere_ritter(fullVertArray)
		parsedMesh.boundingSphere = Sphere()
		parsedMesh.boundingSphere.x = center[0]
		parsedMesh.boundingSphere.y = center[1]
		parsedMesh.boundingSphere.z = center[2]
		parsedMesh.boundingSphere.r = radius
		#print(center)
		#print(radius)
	if parsedMesh.boundingBox == None:
		minVec = Vector((min([pos[0] for pos in fullVertArray]),min([pos[1] for pos in fullVertArray]),min([pos[2] for pos in fullVertArray])))
		maxVec = Vector((max([pos[0] for pos in fullVertArray]),max([pos[1] for pos in fullVertArray]),max([pos[2] for pos in fullVertArray])))
		parsedMesh.boundingBox = AABB()
		parsedMesh.boundingBox.min.x =  minVec[0]
		parsedMesh.boundingBox.min.y =  minVec[1]
		parsedMesh.boundingBox.min.z =  minVec[2]
		parsedMesh.boundingBox.max.x =  maxVec[0]
		parsedMesh.boundingBox.max.y =  maxVec[1]
		parsedMesh.boundingBox.max.z =  maxVec[2]
	meshBBoxEndTime = time.time()
	meshBBoxTime =  meshBBoxEndTime - meshBBoxStartTime
	print(f"Calculating mesh bounding sphere and bounding box took {timeFormat%(meshBBoxTime * 1000)} ms.")
	
	if parsedMesh.skeleton != None and parsedMesh.skeleton.weightedBones != None and len(parsedMesh.skeleton.weightedBones) > maxWeightedBones:
		print(f"Maximum Weighted Bones Exceeded! {str(len(parsedMesh.skeleton.weightedBones))} / {maxWeightedBones}")
		addErrorToDict(errorDict, "MaxWeightedBonesExceeded", None)
	"""
	if armatureObj != None and len(parsedMesh.skeleton.weightedBones) == 0 and len(parsedMesh.skeleton.boneList) > 0:
		raiseWarning(f"Mesh has armature, but the mesh is not weighted to the bones on the armature.\nWeighting meshes to {parsedMesh.skeleton.boneList[0].boneName} bone.")
		parsedMesh.skeleton.weightedBones.append(parsedMesh.skeleton.boneList[0].boneName)
		parsedMesh.skeleton.boneList[0].boundingBox = parsedMesh.boundingBox
	"""
	#Clear references
	newMeshDataList.clear()
	evaluatedSubMeshData = None
	if exportArmatureData != None:
		bpy.data.armatures.remove(exportArmatureData)
	for mesh in deleteCopiedMeshList:
		bpy.data.meshes.remove(mesh)
	deleteCopiedMeshList.clear()
	#print(remapDict)
	
	if errorDict != {}:
		showErrorMessageBox("Mesh contains errors and can not be exported. Check the console (Window > Toggle System Console) for info on how to fix it.")
		printErrorDict(errorDict)
		return False
	
	meshWriteStartTime = time.time()
	reMesh = ParsedREMeshToREMesh(parsedMesh, meshVersion)  
	writeREMesh(reMesh, filePath)
	meshWriteEndTime = time.time()
	meshWriteExportTime =  meshWriteEndTime - meshWriteStartTime
	print(f"Converting to RE Mesh took {timeFormat%(meshWriteExportTime * 1000)} ms.")
	vertexBufferString = ""
	if parsedMesh.bufferHasPosition:
		vertexBufferString += "[Position] "
	if parsedMesh.bufferHasNorTan:
		vertexBufferString += "[Normals] "
		
	if parsedMesh.bufferHasUV:
		vertexBufferString += "[UV1] "
		
	if parsedMesh.bufferHasUV2:
		vertexBufferString += "[UV2] "
		
	if parsedMesh.bufferHasWeight:
		vertexBufferString += "[Weight] "
	if parsedMesh.bufferHasColor:
		vertexBufferString += "[Color] " 
	
	meshExportEndTime = time.time()
	meshExportTime =  meshExportEndTime - meshExportStartTime
	print(f"Mesh export finished in {timeFormat%(meshExportTime * 1000)} ms.")
	
	print("\nMesh Info:")
	print(f"Vertex Count: {str(vertexCount)}")
	print(f"Face Count: {str(faceCount)}")
	print(f"Vertex Buffer Format: {vertexBufferString}")
	if parsedMesh.skeleton != None:
		print(f"Armature Bone Count: {str(len(parsedMesh.skeleton.boneList))}")
		print(f"Weighted Bone Count: {str(len(parsedMesh.skeleton.weightedBones))} / {maxWeightedBones}")
	print(f"Materials ({str(len(parsedMesh.materialNameList))}):")
	for materialName in parsedMesh.materialNameList:
		print(materialName)
	
	print("\033[92m__________________________________\nRE Mesh export finished.\033[0m")
	return True	
	