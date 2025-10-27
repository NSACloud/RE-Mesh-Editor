import os
import bpy

from ..blender_utils import showMessageBox,showErrorMessageBox
from ..gen_functions import textColors,raiseWarning,splitNativesPath,getAdjacentFileVersion
from .file_re_mdf import readMDF,writeMDF,MDFFile,Material,TextureBinding,Property,gameNameMDFVersionDict,getMDFVersionToGameName,MMTRSData,GPBFEntry
from .ui_re_mdf_panels import tag_redraw

MDFGameNameConflictDict = set(["RE2","RE2RT","DD2"])


def resolveMDFGameNameConflict(gameName,mdfFile,filePath):
	rootPath = os.path.split(filePath)[0].lower()
	realGameName = None
	if gameName == "RE2":
		if "re2" in rootPath:
			realGameName = "RE2"
		elif "dmc5" in rootPath or "dmcv" in rootPath:
			realGameName = "DMC5"
		if realGameName == None:
			meshVersion = getAdjacentFileVersion(rootPath,".mesh")
			if meshVersion == 1808312334: #RE2:
				realGameName = "RE2"
			elif meshVersion == 1808282334:
				realGameName = "DMC5"
		if realGameName == None:
			texVersion = getAdjacentFileVersion(rootPath,".tex")
			if texVersion == 10:
				realGameName = "RE2"
			elif texVersion == 11:
				realGameName = "DMC5"
		if realGameName == None and len(mdfFile.materialList) > 0:
			for texture in mdfFile.materialList[0].textureList:
				if "objectroot" in texture.texturePath.lower():
					realGameName = "RE2"
					break 
		if realGameName == None:
			realGameName = "DMC5"
	elif gameName == "RE2RT":
		if "re3" in rootPath:
			realGameName = "RE3RT"
		elif "re2" in rootPath:
			realGameName = "RE2RT"
		elif "re7" in rootPath:
			realGameName = "RE7RT"
		if realGameName == None and len(mdfFile.materialList) > 0:
			texVersion = getAdjacentFileVersion(rootPath,".tex")
			if texVersion == 35:
				realGameName = "RE7RT"
			else:
				for texture in mdfFile.materialList[0].textureList:
					if "escape" in texture.texturePath.lower():
						realGameName = "RE3RT"
						break
	elif gameName == "DD2":
		if "dd2" in rootPath:
			realGameName = "DD2"
			
		if realGameName == None:
			meshVersion = getAdjacentFileVersion(rootPath,".mesh")
			if meshVersion != -1:
				if meshVersion == 240306278:
					realGameName = "KG"
				elif meshVersion == 231011879:
					realGameName = "DD2"
				elif meshVersion == 240424828:
					realGameName = "DR"
		if realGameName == None:
			texVersion = getAdjacentFileVersion(rootPath,".tex")
			if texVersion != -1:
				if texVersion == 231106777:
					realGameName = "KG"
				elif texVersion == 760230703:
					realGameName = "DD2"
				elif texVersion == 240606151:
					realGameName = "DR"
	if realGameName == None:
		realGameName = gameName
	return realGameName
	

excludedPropertyNames = set(["~TYPE","_RNA_UI","_vs","s_curve"])
boolPropertySet = set(["BackFaceNormalFilp","uv1or2_AlphaMap"])#Manually define properties that are bools
colorPropertySet = set([])#Manually define properties that are colors
matShaderTypeEnum = {
	"Standard" : 0x0,
	"Decal" : 0x1,
	"DecalWithMetallic" : 0x2,
	"DecalNRMR" : 0x3,
	"Transparent" : 0x4,
	"Distortion" : 0x5,
	"PrimitiveMesh" : 0x6,
	"PrimitiveSolidMesh" : 0x7,
	"Water" : 0x8,
	"SpeedTree" : 0x9,
	"GUI" : 0xA,
	"GUIMesh" : 0xB,
	"GUIMeshTransparent" : 0xC,
	"ExpensiveTransparent" : 0xD,
	"Forward" : 0xE,
	"RenderTarget" : 0xF,
	"PostProcess" : 0x10,
	"PrimitiveMaterial" : 0x11,
	"PrimitiveSolidMaterial" : 0x12,
	"SpineMaterial" : 0x13,
	"Max" : 0x14,
	0x0 : "Standard",
	0x1 : "Decal",
	0x2 : "DecalWithMetallic",
	0x3 : "DecalNRMR",
	0x4 : "Transparent",
	0x5 : "Distortion",
	0x6 : "PrimitiveMesh",
	0x7 : "PrimitiveSolidMesh",
	0x8 : "Water",
	0x9 : "SpeedTree",
	0xA : "GUI",
	0xB : "GUIMesh",
	0xC : "GUIMeshTransparent",
	0xD : "ExpensiveTransparent",
	0xE : "Forward",
	0xF : "RenderTarget",
	0x10 : "PostProcess",
	0x11 : "PrimitiveMaterial",
	0x12 : "PrimitiveSolidMaterial",
	0x13 : "SpineMaterial",
	0x14 : "Max",
	}


def findHeaderObj():
	if bpy.data.collections.get("MDFData",None) != None:
		objList = bpy.data.collections["MDFData"].all_objects
		headerList = [obj for obj in objList if obj.get("~TYPE",None) == "RE_MDF_HEADER"]
		if len(headerList) >= 1:
			return headerList[0]
		else:
			return None
def createMDFCollection(collectionName,parentCollection = None):
	collection = bpy.data.collections.new(collectionName)
	collection.color_tag = "COLOR_05"
	collection["~TYPE"] = "RE_MDF_COLLECTION"
	if parentCollection != None:
		parentCollection.children.link(collection)
	else:
		bpy.context.scene.collection.children.link(collection)
	bpy.context.scene.re_mdf_toolpanel.mdfCollection = collection
	return collection

def checkNameUsage(baseName,checkSubString = True, objList = None):
	if objList == None:
		objList = bpy.data.objects
	if checkSubString:
		return any(baseName in name for name in [obj.name for obj in objList])
	else:
		return baseName in [obj.name for obj in objList]


def createEmpty(name,propertyList,parent = None,collection = None):
	obj = bpy.data.objects.new( name, None )
	obj.empty_display_size = .10
	obj.empty_display_type = 'PLAIN_AXES'
	obj.parent = parent
	for property in propertyList:#Reverse list so items get added in correct order
 
		obj[property[0]] = property[1]
	if collection == None:
		collection = bpy.context.scene.collection
		
	collection.objects.link(obj)
		
		
	return obj



def addPropsToPropList(obj,matPropertyList):
	obj.re_mdf_material.propertyList_items.clear()
	for prop in matPropertyList:
		newListItem = obj.re_mdf_material.propertyList_items.add()
		newListItem.prop_name = prop.propName
		newListItem.padding = prop.padding
		lowerPropName = prop.propName.lower()
		if prop.propName in colorPropertySet or (prop.paramCount == 4 and ("color" in lowerPropName or "_col_" in lowerPropName) and "rate" not in lowerPropName):
			newListItem.data_type = "COLOR"
			newListItem.color_value = prop.propValue
		elif prop.paramCount == 1 and ("Use" in prop.propName or "_or_" in prop.propName or prop.propName.startswith("is")) or prop.propName in boolPropertySet:
			newListItem.data_type = "BOOL"
			newListItem.bool_value = bool(prop.propValue[0])
		elif prop.paramCount > 1:
			newListItem.data_type = "VEC4"
			newListItem.float_vector_value = tuple(prop.propValue)
		else:
			newListItem.data_type = "FLOAT"
			newListItem.float_value = float(prop.propValue[0])

def getTextureBindings(matTextureList):
	RNADict = {"~TYPE":{"description":"For internal use. Do not change"},"~KEY_ORDER":{"description":"For internal use. Do not change"}}
	customPropList = [("~TYPE","RE_MDF_TEXTUREBINDINGS"),("_RNA_UI",RNADict)]
	keyOrderList = []
	for texture in matTextureList:
		keyOrderList.append(texture.textureType)
		customPropList.append((str(texture.textureType),str(texture.texturePath)))
	customPropList.append(("~KEY_ORDER",keyOrderList))
	return customPropList

def addTextureBindingsToBindingList(obj,matTextureList):
	for texture in matTextureList:
		newListItem = obj.re_mdf_material.textureBindingList_items.add()
		newListItem.textureType = texture.textureType
		newListItem.path = texture.texturePath

def addMMTRSDataToList(obj,mmtrsData):
	for indexList in mmtrsData.indexDataList:
		newListItem = obj.re_mdf_material.mmtrsData_items.add()
		newString = ""
		for i, index in enumerate(indexList):
			newString+=f"{str(index)}"
			if i != len(indexList)-1:
				newString+=","
		newListItem.indexString = newString

def addGPBFDataToList(obj,bufferNameList,bufferPathList):
	for i in range(0,len(bufferNameList)):
		newListItem = obj.re_mdf_material.gpbfData_items.add()
		newListItem.gpbfDataString = f"{bufferNameList[i].name},{bufferPathList[i].name},{str(bufferPathList[i].nameUTF16Hash)},{str(bufferPathList[i].nameUTF8Hash)}"

def getMDFFlags(obj,flags):
	obj.re_mdf_material.flags.flagIntValue = flags.asInt32
	
#MDF IMPORT


def importMDFFile(filePath,parentCollection = None):
	mdfFile = readMDF(filePath)
	mdfFileName = os.path.splitext(os.path.split(filePath)[1])[0]
	try:
		mdfVersion = int(os.path.splitext(filePath)[1].replace(".",""))
		if mdfVersion in gameNameMDFVersionDict:
			gameName = gameNameMDFVersionDict[mdfVersion]
			if gameName in MDFGameNameConflictDict:
				gameName = resolveMDFGameNameConflict(gameName, mdfFile, filePath)
				print(f"MDF version {str(mdfVersion)} is used by more than one game, detected {gameName}")
			bpy.context.scene.re_mdf_toolpanel.activeGame = gameName
		else:
			gameName = -1
			
	except:
		print("Unable to parse mdf version number in file path.")
		gameName = -1
		mdfVersion = 45
	#headerObj = createEmpty("MDF_HEADER ("+os.path.split(filePath)[1]+")",[("~TYPE","RE_MDF_HEADER"),("unknHeaderValue",mdfFile.Header.version),("MDFVersion",os.path.splitext(filePath)[1].split(".")[1])],None,"MDFData")
	mdfCollection = createMDFCollection(mdfFileName,parentCollection)
	bpy.context.scene["REMeshLastImportedMDFVersion"] = mdfVersion
	try:
			split = splitNativesPath(filePath)
			if split != None:
				assetPath = os.path.splitext(split[1])[0].replace(os.sep,"/")
				mdfCollection["~ASSETPATH"] = assetPath#Used to determine where to export automatically
	except:
		print("Failed to set asset path from file path, file is likely not in a natives folder.")
	#MATERIALS IMPORT
	for index, material in enumerate(mdfFile.materialList):
		name = "Material "+str(index).zfill(2)+ " ("+material.materialName+")"
		materialObj = createEmpty(name,[("~TYPE","RE_MDF_MATERIAL")],None,mdfCollection)
		#gameName = getMDFVersionToGameName(mdfVersion)
		if gameName != -1:
			materialObj.re_mdf_material.gameName = gameName
		materialObj.re_mdf_material.materialName = material.materialName
		materialObj.re_mdf_material.shaderType = str(material.shaderType)
		materialObj.re_mdf_material.mmtrPath = material.mmtrPath
		materialObj.re_mdf_material.flags.ver32Unknown = material.ver32Unkn0
		materialObj.re_mdf_material.flags.ver32Unknown1 = material.ver32Unkn1
		materialObj.re_mdf_material.flags.ver32Unknown2 = material.ver32Unkn2
		
		getMDFFlags(materialObj,material.flags)
		if gameName == "SF6":
			for prop in material.propertyList:
				if "CustomizeRoughness" in prop.propName or "CustomizeMetal" in prop.propName:#Fix for imported SF6 materials, this shouldn't matter in game since it gets overriden by the cmd files
					if prop.propValue[0] == 0.0:
						prop.propValue = [1.0]
				elif "CustomizeColor"  in prop.propName:
					if prop.propValue == [0.501960813999176, 0.501960813999176, 0.501960813999176, 1.0]:
						prop.propValue = [1.0,1.0,1.0,1.0]
		addPropsToPropList(materialObj,material.propertyList)
		addTextureBindingsToBindingList(materialObj, material.textureList)
		if material.mmtrsData != None:
			addMMTRSDataToList(materialObj,material.mmtrsData)
		if material.GPBFBufferNameCount > 0:
			addGPBFDataToList(materialObj,material.gpbfBufferNameList,material.gpbfBufferPathList)
		#flagsObj = createEmpty("Material "+str(index).zfill(2)+" Flags", getMaterialFlags(material.flags.flags),None,mdfCollection)
		#textureBindingsObj = createEmpty("Material "+str(index).zfill(2)+" Texture Bindings", getTextureBindings(material.textureList),None,mdfCollection)
		#propertyListObj = createEmpty("Material "+str(index).zfill(2)+" Property List", getPropertyList(material.propertyList),None,mdfCollection)
	tag_redraw(bpy.context)
	return True


#MDF EXPORT

def reindexMaterials(collectionName):
	
	if bpy.data.collections.get(collectionName,None) != None:
		mdfCollection = bpy.data.collections[collectionName]
	else:
		mdfCollection = bpy.context.scene.re_mdf_toolpanel.mdfCollection
	if mdfCollection != None:
		
		currentIndex = 0
		for obj in sorted(mdfCollection.all_objects,key = lambda item: item.name):
			
			if obj.get("~TYPE",None) == "RE_MDF_MATERIAL":
				#Change the material name in the mdf material settings to the one in the object name
				#This allows for the user to set the material name by either method of renaming the object or setting it in the mdf material settings
				if "Material" in obj.name and "(" in obj.name:
					objMaterialName = obj.name.rsplit("(",1)[1].split(")")[0]
					if objMaterialName != obj.re_mdf_material.materialName:
						obj.re_mdf_material.materialName = objMaterialName
				obj.name = "Material "+str(currentIndex).zfill(2)+ " ("+obj.re_mdf_material.materialName+")"
				currentIndex += 1
def MDFErrorCheck(collectionName):
	print("\nChecking for problems with MDF structure...")
	
	#Check that there is mdf data collection
	#Check that there is only one header
	#Check that all materials have only one flag, property list and texture binding objects
	#Check that all materials are parented to the header
	#Check that parenting structure is valid
	#Check for duplicate material names
	errorList = []
	warningList = []
	materialNameSet = set()
	meshMaterialSet = set()
	if bpy.data.collections.get(collectionName,None) != None:
		objList = bpy.data.collections[collectionName].all_objects
	else:
		errorList.append("MDF objects must be grouped in a collection.")
		objList = []
	headerCount = 0
	if bpy.context.active_object != None and bpy.context.active_object.get("~TYPE",None) == "RE_MDF_HEADER":
		findHeader = False
		headerCount = 1
	else:
		findHeader = True
	for obj in objList:
		
		if obj.get("~TYPE",None) == "RE_MDF_MATERIAL":
			if obj.re_mdf_material.materialName not in materialNameSet:
				materialNameSet.add(obj.re_mdf_material.materialName)
			else:
				errorList.append("Duplicate material name on " + obj.name+". Set the material name in the custom properties of the material object to a different name.")
	
	meshCollectionName = collectionName.replace(".mdf2",".mesh",1).replace("_v00","",1).replace("_Mat","",1)
	meshCollection = bpy.data.collections.get(meshCollectionName,None)
	if meshCollection != None:
		for obj in meshCollection.all_objects:
			if obj.type == "MESH" and not "MeshExportExclude" in obj and "__" in obj.name:
				matName = obj.name.split("__",1)[1].split(".")[0]
				meshMaterialSet.add(matName)
				if matName not in materialNameSet:
					warningList.append("The material ("+matName+") on mesh " + obj.name + " does not exist in the MDF.")
	else:
		raiseWarning(f"Could not find mesh collection ({meshCollectionName}) to check materials against.")
	if len(meshMaterialSet) != 0 and len(materialNameSet.difference(meshMaterialSet)) != 0:
		materialString = ""
		for materialName in materialNameSet.difference(meshMaterialSet):
			materialString += materialName+"\n"
		warningList.append(f"The following materials exist in the MDF ({collectionName}) but do not exist in the mesh ({meshCollectionName}):\n{materialString}")
	if warningList != []:
		warningList.append("If this mesh is supposed to be used with this MDF, the number of materials and name of materials in the MDF must match the mesh.\nThe material will appear as a checkerboard texture in game.")
		for warning in warningList:
			raiseWarning(warning)
				
	if errorList == []:
		print("No errors found.")
		#print(noesisMeshMaterialSet)
		if warningList != []:
			showMessageBox("Warnings occured during export. Check Window > Toggle System Console for details.",title = "Export Warning", icon = "ERROR")
		return True
	else:
		errorString = ""
		for error in errorList:
			errorString += textColors.FAIL +"ERROR: " + error + textColors.ENDC +"\n"
		showMessageBox("MDF structure contains errors and cannot export. Check Window > Toggle System Console for details.",title = "Export Error", icon = "ERROR")
		print(errorString)
		print(textColors.FAIL + "__________________________________\nMDF export failed."+textColors.ENDC)
		return False

def getPropValue(propertyEntry):
	if propertyEntry.data_type == "VEC4":
		value = propertyEntry.float_vector_value 
	elif propertyEntry.data_type == "COLOR":
		value = propertyEntry.color_value
		
	elif propertyEntry.data_type == "BOOL":
		if propertyEntry.bool_value:
			value = [1.0]
		else:
			value = [0.0]
	else:#float
		value = [propertyEntry.float_value]
	
	return value

def fixTexPath(path):#Fix potential path problems
	if not path.endswith(".rtex"):
		path = path.replace(os.sep,"/").split(".tex")[0]+".tex"#Fix incorrect directory separators and including version numbers on the tex path
		if "natives" in path.lower():
			splitPath = splitNativesPath(path)
			if splitPath != None:
				path = splitPath[1]#Fix including the chunk root path in the tex path
	return path
def buildMDF(mdfCollectionName,mdfVersion = None):
	mdfCollection = bpy.data.collections.get(mdfCollectionName)
	if mdfVersion == None:
		
		mdfVersion = getMDFVersionToGameName(bpy.context.scene.re_mdf_toolpanel.activeGame)
	reindexMaterials(mdfCollectionName)
	if mdfCollection != None:
		valid = MDFErrorCheck(mdfCollectionName)
	else:
		showErrorMessageBox("MDF collection is not set, cannot export")
		valid = False
	if valid:
		materialObjList = sorted([child for child in mdfCollection.all_objects if child.get("~TYPE",None) == "RE_MDF_MATERIAL"],key = lambda item: item.name)
		newMDFFile = MDFFile()
		newMDFFile.fileVersion = mdfVersion
		newMDFFile.Header.version = 1
		for materialObj in materialObjList:
			materialEntry = Material()
			materialEntry.shaderType = int(materialObj.re_mdf_material.shaderType)
			materialEntry.materialName = materialObj.re_mdf_material.materialName
			materialEntry.mmtrPath = materialObj.re_mdf_material.mmtrPath
			materialEntry.ver32Unkn0 = materialObj.re_mdf_material.flags.ver32Unknown
			materialEntry.ver32Unkn1 = materialObj.re_mdf_material.flags.ver32Unknown1
			materialEntry.ver32Unkn2 = materialObj.re_mdf_material.flags.ver32Unknown2
			
			materialEntry.hideInGame = materialObj.re_mdf_material.flags.hideMaterialInGame
			
			materialEntry.flags.asInt32 = materialObj.re_mdf_material.flags.flagIntValue
			for textureBinding in materialObj.re_mdf_material.textureBindingList_items:
				textureEntry = TextureBinding()
				textureEntry.textureType = textureBinding.textureType
				textureEntry.texturePath = fixTexPath(textureBinding.path)
				materialEntry.textureList.append(textureEntry)
			
			for prop in materialObj.re_mdf_material.propertyList_items:
				propertyEntry = Property()
				propertyEntry.propName = prop.prop_name
				propertyEntry.propValue = getPropValue(prop)
				propertyEntry.padding = prop.padding
				propertyEntry.paramCount = len(propertyEntry.propValue)
				materialEntry.propertyList.append(propertyEntry)
				
			if len(materialObj.re_mdf_material.mmtrsData_items) != 0:
				materialEntry.mmtrsData = MMTRSData()
				for item in materialObj.re_mdf_material.mmtrsData_items:
					indexList = []
					rawIndicesList = item.indexString.split(",")
					for entry in rawIndicesList:
						if entry.isdigit():
							indexList.append(int(entry))
					materialEntry.mmtrsData.indexDataList.append(indexList)
					
			if len(materialObj.re_mdf_material.gpbfData_items) != 0:
				for item in materialObj.re_mdf_material.gpbfData_items:
					nameEntry = GPBFEntry()
					pathEntry = GPBFEntry()
					split = item.gpbfDataString.split(",")
					nameEntry.name = split[0]
					pathEntry.name = split[1]
					if split[2].isdigit():
						pathEntry.nameUTF16Hash = int(split[2])
					else:
						pathEntry.nameUTF16Hash = 0
					if split[3].isdigit():
						pathEntry.nameUTF8Hash = int(split[3])
					else:
						pathEntry.nameUTF8Hash = 1
					
					materialEntry.gpbfBufferNameList.append(nameEntry)
					materialEntry.gpbfBufferPathList.append(pathEntry)
			if mdfVersion == 31:#SF6
			#Set altered customize values back to original values since some files do use them
				for prop in materialEntry.propertyList:
					if "CustomizeRoughness" in prop.propName or "CustomizeMetal" in prop.propName:
						if prop.propValue[0] == 1.0:
							prop.propValue = [0.0]
					elif "CustomizeColor"  in prop.propName:
						if prop.propValue == [1.0,1.0,1.0,1.0]:
							prop.propValue = [0.501960813999176, 0.501960813999176, 0.501960813999176, 1.0]
			newMDFFile.materialList.append(materialEntry)
		return newMDFFile
	else:
		return None
def exportMDFFile(filepath,mdfCollectionName = ""):
	try:
		mdfVersion = int(os.path.splitext(filepath)[1].replace(".",""))
	except:
		mdfVersion = None
		print("Unable to parse MDF version number in file path.")
	mdfFile = buildMDF(mdfCollectionName,mdfVersion)
	if mdfFile != None:
		writeMDF(mdfFile,filepath)
		return True
	else:
		return False