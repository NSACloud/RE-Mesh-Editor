import os
import bpy
import glob
from mathutils import Vector,Quaternion,Matrix
from math import radians
from ..blender_utils import showMessageBox
from ..gen_functions import textColors,raiseWarning,splitNativesPath
from .file_re_sfur import readSFur,writeSFur,SFurFile,SFurEntry

def checkNameUsage(baseName,checkSubString = True, objList = None):
	if objList == None:
		objList = bpy.data.objects
	if checkSubString:
		return any(baseName in name for name in [obj.name for obj in objList])
	else:
		return baseName in [obj.name for obj in objList]

def createSFurCollection(collectionName,parentCollection = None):
	collection = bpy.data.collections.new(collectionName)
	collection.color_tag = "COLOR_08"
	collection["~TYPE"] = "RE_SFUR_COLLECTION"
	if parentCollection != None:
		parentCollection.children.link(collection)
	else:
		bpy.context.scene.collection.children.link(collection)
	bpy.context.scene.re_mdf_toolpanel.sFurCollection = collection
	return collection

def createCurveEmpty(name,propertyList,parent = None,collection = None):
	CURVE_DATA_NAME = "emptyCurve"#Share the data for all empty curves since it's not needed and it prevents unnecessary duplicates
	if CURVE_DATA_NAME in bpy.data.curves:
		curveData = bpy.data.curves[CURVE_DATA_NAME]
	else:	
		curveData = bpy.data.curves.new(CURVE_DATA_NAME, 'CURVE')
		curveData.use_path = False
		
	
	obj = bpy.data.objects.new(name, curveData)
	obj.parent = parent
	for property in propertyList:
 
		obj[property[0]] = property[1]
	if collection == None:
		collection = bpy.context.scene.collection
		
	collection.objects.link(obj)
		
		
	return obj

def reindexEntries(sFurCollection):
	
	if sFurCollection != None:
		
		currentIndex = 0
		for obj in sorted(sFurCollection.all_objects,key = lambda item: item.name):
			
			if obj.get("~TYPE",None) == "RE_SFUR_ENTRY":
				#Change the material name in the mdf material settings to the one in the object name
				#This allows for the user to set the material name by either method of renaming the object or setting it in the mdf material settings
				if "Shell Fur" in obj.name and "(" in obj.name:
					objMaterialName = obj.name.rsplit("(",1)[1].split(")")[0]
					if objMaterialName != obj.re_sfur_data.materialName:
						obj.re_sfur_data.materialName = objMaterialName
				obj.name = "Shell Fur "+str(currentIndex).zfill(2)+ " ("+obj.re_sfur_data.materialName+")"
				currentIndex += 1

def findSFurPathFromMeshPath(meshPath,gameName = None):
	split = meshPath.split(".mesh")
	fileRoot = glob.escape(split[0])
	meshVersion = split[1]
	sFurVersionDict = {
		".221108797":".4",#RE4
		".240423143":".5",#DD2NEW
		".241111606":".5",#MHWILDS
		".250925211":".5",#RE9
		}
	sFurVersion = sFurVersionDict.get(meshVersion,None)
	sFurPath = None
	if meshVersion in sFurVersionDict:
		sFurPath = f"{fileRoot}.sfur{sFurVersion}"
	if sFurPath != None and not os.path.isfile(sFurPath):
		#RE4, check directory above current one
		parentDir = os.path.dirname(os.path.split(meshPath)[0])
		try:
			sFurPath = f"{os.path.join(parentDir,os.path.split(fileRoot)[1])}.sfur{sFurVersion}"
		except:
			pass
		if not os.path.isfile(sFurPath):#Check another directory level above if not the first one
			try:
				sFurPath = f"{os.path.join(os.path.dirname(parentDir),os.path.split(fileRoot)[1])}.sfur{sFurVersion}"
				
			except:
				pass
			
	if sFurPath == None or not os.path.isfile(sFurPath):
		#print("No sfur file found.")
		sFurPath = None
	#print(sFurPath)
	return sFurPath

#SFUR IMPORT

def importSFurFile(filePath,parentCollection = None):
	
	sFurFile = readSFur(filePath)
	sFurVersion = sFurFile.header.version
	bpy.context.scene["REMeshLastImportedSFurVersion"] = sFurVersion
	fileName = os.path.splitext(os.path.split(filePath)[1])[0]
	sFurCollection = createSFurCollection(fileName,parentCollection)
	
	for index, entry in enumerate(sFurFile.furEntryList):
		name = "Shell Fur "+str(index).zfill(2)+ " ("+entry.materialName+")"
		furObj = createCurveEmpty(name,[("~TYPE","RE_SFUR_ENTRY")],None,sFurCollection)

		furObj.re_sfur_data.shellCount = entry.shellCount
		furObj.re_sfur_data.shellThinType = str(entry.shellThinType)
		furObj.re_sfur_data.groomingTexCoordType = str(entry.groomingTexCoordType)
		furObj.re_sfur_data.shellHeight = entry.shellHeight
		furObj.re_sfur_data.bendRate = entry.bendRate
		furObj.re_sfur_data.bendRootRate = entry.bendRootRate
		furObj.re_sfur_data.normalTransformRate = entry.normalTransformRate
		furObj.re_sfur_data.stiffness = entry.stiffness
		furObj.re_sfur_data.stiffnessDistribution = entry.stiffnessDistribution
		furObj.re_sfur_data.springCoefficient = entry.springCoefficient
		furObj.re_sfur_data.damping = entry.damping
		furObj.re_sfur_data.gravityForceScale = entry.gravityForceScale
		furObj.re_sfur_data.directWindForceScale = entry.directWindForceScale
		furObj.re_sfur_data.isForceTwoSide = entry.isForceTwoSide
		furObj.re_sfur_data.isForceAlphaTest = entry.isForceAlphaTest
		furObj.re_sfur_data.unknownFlag = entry.padding
		furObj.re_sfur_data.materialName = entry.materialName
		furObj.re_sfur_data.groomingTexturePath = entry.groomingTexturePath
	
		#TODO Find each submesh using material and add a shell fur geonode modifier to this object for it
	
	try:
		split = splitNativesPath(filePath)
		if split != None:
			assetPath = os.path.splitext(split[1])[0].replace(os.sep,"/")
			sFurCollection["~ASSETPATH"] = assetPath#Used to determine where to export automatically
	except:
		print("Failed to set asset path from file path, file is likely not in a natives folder.")
	
	
	
	return True


#SFUR EXPORT


def exportSFurFile(filepath,targetCollection):
	sFurFile = SFurFile()
	try:
		sfurVersion = int(os.path.splitext(filepath)[1].replace(".",""))
	except:
		print("Unable to parse sfur version number in file path, defaulting to 5.")
		sfurVersion = 5
	sFurFile.header.version = sfurVersion
	collection = bpy.data.collections.get(targetCollection,None)
	if collection != None:
		reindexEntries(collection)
		for furObj in collection.all_objects:
			if furObj.get("~TYPE") == "RE_SFUR_ENTRY":
				entry = SFurEntry()
				entry.shellCount = furObj.re_sfur_data.shellCount
				entry.shellThinType = int(furObj.re_sfur_data.shellThinType)
				entry.groomingTexCoordType = int(furObj.re_sfur_data.groomingTexCoordType)
				entry.shellHeight = furObj.re_sfur_data.shellHeight
				entry.bendRate = furObj.re_sfur_data.bendRate
				entry.bendRootRate = furObj.re_sfur_data.bendRootRate
				entry.normalTransformRate = furObj.re_sfur_data.normalTransformRate
				entry.stiffness = furObj.re_sfur_data.stiffness
				entry.stiffnessDistribution = furObj.re_sfur_data.stiffnessDistribution
				entry.springCoefficient = furObj.re_sfur_data.springCoefficient
				entry.damping = furObj.re_sfur_data.damping
				entry.gravityForceScale = furObj.re_sfur_data.gravityForceScale
				entry.directWindForceScale = furObj.re_sfur_data.directWindForceScale
				entry.isForceTwoSide = furObj.re_sfur_data.isForceTwoSide
				entry.isForceAlphaTest = furObj.re_sfur_data.isForceAlphaTest
				entry.padding = furObj.re_sfur_data.unknownFlag
				entry.materialName = furObj.re_sfur_data.materialName
				entry.groomingTexturePath = furObj.re_sfur_data.groomingTexturePath
				
				sFurFile.furEntryList.append(entry)
				
		writeSFur(sFurFile, filepath)
	return True