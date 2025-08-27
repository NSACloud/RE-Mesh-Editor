import os
import bpy
from mathutils import Vector,Quaternion,Matrix
from math import radians
from ..blender_utils import showMessageBox
from ..gen_functions import textColors,raiseWarning
from .file_re_fbxskel import readFBXSkel,writeFBXSkel,FBXSkelFile,BoneEntry

rotate90Matrix = Matrix.Rotation(radians(90.0), 4, 'X')
rotateNeg90Matrix = Matrix.Rotation(radians(-90.0), 4, 'X')
#FBXSKEL IMPORT

def importFBXSkelFile(filePath):
	
	fbxSkelFile = readFBXSkel(filePath)
	fileName = os.path.splitext(os.path.split(filePath)[1])[0]
	armatureData = bpy.data.armatures.new(fileName)	
	armatureObj = bpy.data.objects.new(fileName, armatureData)
	armatureObj.show_in_front = True
	#armatureObj.display_type = "WIRE"#Change display type to make it visually different from a mesh armature
	armatureData.display_type = "STICK"#Change display type to make it visually different from a mesh armature
	bpy.context.scene.collection.objects.link(armatureObj)
	bpy.context.view_layer.objects.active = armatureObj
	bpy.ops.object.mode_set(mode='EDIT')
	boneIndexDict = {}
	boneNameIndexDict = {index: bone.boneName for index, bone in enumerate(fbxSkelFile.boneEntryList)}
	boneParentList = []
	
	for bone in fbxSkelFile.boneEntryList:
		boneName = bone.boneName
		editBone = armatureData.edit_bones.new(boneName)
		editBone.head = (0.0, 0.0, 0.0)
		editBone.tail = (0.0, 0.1, 0.0)
		editBone.length = .03
		
		pos = Vector(bone.translation)
		rot = Quaternion((bone.rotation[3],bone.rotation[0],bone.rotation[1],bone.rotation[2]))
		scale = Vector(bone.scale)
		
		editBone.matrix = editBone.matrix @ Matrix.LocRotScale(pos,rot,scale)
		
		if bone.parentIndex != -1:
			boneParentName = boneNameIndexDict[bone.parentIndex]
			boneParentList.append((editBone,boneParentName))#Set bone parents after all bones have been imported
		
	#Assign bone parents

	for editBone,parentBoneName in boneParentList:
		editBone.parent = armatureData.edit_bones[parentBoneName]
		editBone.matrix = editBone.parent.matrix @ editBone.matrix
	
	#armatureData.transform(armatureObj.matrix_world @ rotate90Matrix)
	bpy.ops.object.mode_set(mode='OBJECT')
	#Set color
	for bone in armatureData.bones:
		bone.color.palette = "THEME01"#Change bone color to make it visually different from a mesh armature
	prevSelection = bpy.context.selected_objects
	for obj in prevSelection:
		obj.select_set(False)
	
	armatureObj.matrix_world = armatureObj.matrix_world @ rotate90Matrix
	armatureObj.select_set(True)
	bpy.ops.object.transform_apply(location = False,rotation = True,scale = False)
	for bone in fbxSkelFile.boneEntryList:#Apply scale to pose bones since scale can't be applied to edit bones
		armaturePoseBone = armatureObj.pose.bones[bone.boneName]
		armaturePoseBone.scale = bone.scale
		armaturePoseBone["useSegmentScaling"] = bone.segmentScaling
	armatureObj.select_set(False)
	
	for obj in prevSelection:
		obj.select_set(True)
	
	bpy.context.view_layer.objects.active = armatureObj
	return armatureObj


#FBXSKEL EXPORT


def exportFBXSkelFile(filepath,targetArmature,usePose=True):
	fbxSkelFile = FBXSkelFile()
	armatureObj = bpy.data.objects.get(targetArmature,None)
	if armatureObj != None and armatureObj.type == "ARMATURE":
		print(f"Armature: {armatureObj.name}")
		exportArmatureData = armatureObj.data.copy()
		exportArmatureData.transform(rotateNeg90Matrix @ armatureObj.matrix_world)
		boneIndexDict = {bone.name: index for index, bone in enumerate(armatureObj.data.bones)}
		#print(boneIndexDict)
		for bone in exportArmatureData.bones:
			parsedBone = BoneEntry()
			#Get hierarchy
			parsedBone.boneName = bone.name
			parsedBone.boneIndex = boneIndexDict[bone.name]
			
			
			if bone.name.startswith("L_") :
				if "R"+bone.name[1::] in armatureObj.data.bones:
					parsedBone.boneIndex = boneIndexDict["R"+bone.name[1::]]
				
			elif bone.name.startswith("R_"):
				if "L"+bone.name[1::] in armatureObj.data.bones:
					parsedBone.boneIndex = boneIndexDict["L"+bone.name[1::]]
			
			elif bone.name.endswith("_L"):
				if bone.name[:-1]+"R" in armatureObj.data.bones:
					parsedBone.boneIndex = boneIndexDict[bone.name[:-1]+"R"]
			elif bone.name.endswith("_R"):
				if bone.name[:-1]+"L" in armatureObj.data.bones:
					parsedBone.boneIndex = boneIndexDict[bone.name[:-1]+"L"]
			
			
			
			if bone.parent != None:
				parsedBone.parentIndex = boneIndexDict[bone.parent.name]
				for childBone in bone.parent.children:
					if childBone.name != bone.name and boneIndexDict[bone.name] < boneIndexDict[childBone.name]:
						parsedBone.nextSiblingIndex = boneIndexDict[childBone.name]
						break
			else:
				parsedBone.parentIndex = -1
			
			if armatureObj.pose.bones[bone.name].get("useSegmentScaling",None):
				parsedBone.segmentScaling = armatureObj.pose.bones[bone.name].get("useSegmentScaling")
			#Get matrices
			
			if bone.parent != None:
				mat = exportArmatureData.bones[bone.parent.name].matrix_local.inverted() @ exportArmatureData.bones[bone.name].matrix_local
			else:
				mat = armatureObj.matrix_world @ exportArmatureData.bones[bone.name].matrix_local
			if usePose:
				mat = mat @ armatureObj.pose.bones[bone.name].matrix_basis
			transform,rotation,scale = mat.decompose()
			parsedBone.translation = transform
			parsedBone.rotation = (rotation[1],rotation[2],rotation[3],rotation[0])
			parsedBone.scale = scale
			
		if exportArmatureData != None:
			bpy.data.armatures.remove(exportArmatureData)
		writeFBXSkel(fbxSkelFile, filepath)
	return True