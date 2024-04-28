import os
import bpy

from ..blender_utils import showMessageBox,showErrorMessageBox
from ..gen_functions import textColors,raiseWarning,splitNativesPath
from .file_re_mdf import readMDF,writeMDF,MDFFile,Material,TextureBinding,Property,gameNameMDFVersionDict,getMDFVersionToGameName
from .ui_re_mdf_panels import tag_redraw

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
	collection["~TYPE"] = "RE_CHAIN_COLLECTION"
	if parentCollection != None:
		parentCollection.children.link(collection)
	else:
		bpy.context.scene.collection.children.link(collection)
	bpy.context.scene.re_mdf_toolpanel.mdfCollection = collection.name
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


def getMDFFlags(obj,flags):
	obj.re_mdf_material.flags.flagIntValue = flags.asInt32
	
#MDF IMPORT


def importMDFFile(filePath):
	mdfFile = readMDF(filePath)
	mdfFileName = os.path.splitext(os.path.split(filePath)[1])[0]
	try:
		mdfVersion = int(os.path.splitext(filePath)[1].replace(".",""))
		if mdfVersion in gameNameMDFVersionDict:
			bpy.context.scene.re_mdf_toolpanel.activeGame = "."+str(mdfVersion)
	except:
		print("Unable to parse mdf version number in file path.")
		meshVersion = None
	#headerObj = createEmpty("MDF_HEADER ("+os.path.split(filePath)[1]+")",[("~TYPE","RE_MDF_HEADER"),("unknHeaderValue",mdfFile.Header.version),("MDFVersion",os.path.splitext(filePath)[1].split(".")[1])],None,"MDFData")
	mdfCollection = createMDFCollection(mdfFileName)
	#MATERIALS IMPORT
	for index, material in enumerate(mdfFile.materialList):
		name = "Material "+str(index).zfill(2)+ " ("+material.materialName+")"
		materialObj = createEmpty(name,[("~TYPE","RE_MDF_MATERIAL")],None,mdfCollection)
		gameName = getMDFVersionToGameName(mdfVersion)
		if gameName != -1:
			materialObj.re_mdf_material.gameName = gameName
		materialObj.re_mdf_material.materialName = material.materialName
		materialObj.re_mdf_material.shaderType = str(material.shaderType)
		materialObj.re_mdf_material.mmtrPath = material.mmtrPath
		materialObj.re_mdf_material.flags.ver32Unknown = material.ver32Unkn0
		
		getMDFFlags(materialObj,material.flags)
		addPropsToPropList(materialObj,material.propertyList)
		addTextureBindingsToBindingList(materialObj, material.textureList)
		#flagsObj = createEmpty("Material "+str(index).zfill(2)+" Flags", getMaterialFlags(material.flags.flags),None,mdfCollection)
		#textureBindingsObj = createEmpty("Material "+str(index).zfill(2)+" Texture Bindings", getTextureBindings(material.textureList),None,mdfCollection)
		#propertyListObj = createEmpty("Material "+str(index).zfill(2)+" Property List", getPropertyList(material.propertyList),None,mdfCollection)
	tag_redraw(bpy.context)
	return True


#MDF EXPORT

def reindexMaterials(collectionName = None):
	
	noesisMeshMaterialSet = set()
	if collectionName != None:
		mdfCollection = bpy.data.collections.get(collectionName,None)
	else:
		mdfCollection = bpy.data.collections.get(bpy.context.scene.re_mdf_toolpanel.mdfCollection,None)
	if mdfCollection != None:
		currentIndex = 0
		for obj in sorted(mdfCollection.all_objects,key = lambda item: item.name):
			if obj.get("~TYPE",None) == "RE_MDF_MATERIAL":
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
	
	meshCollection = bpy.data.collections.get(bpy.context.scene.re_mdf_toolpanel.meshCollection,None)
	if meshCollection != None:
		for obj in meshCollection.all_objects:
			if obj.type == "MESH" and not "MeshExportExclude" in obj and "__" in obj.name:
				matName = obj.name.split("__",1)[1].split(".")[0]
				meshMaterialSet.add(matName)
				if matName not in materialNameSet:
					warningList.append("The material ("+matName+") on mesh " + obj.name + " does not exist in the MDF. If this mesh is supposed to be used with this MDF, the number of materials and name of materials in the MDF must match the mesh.\nThe material will appear as a checkerboard texture in game." )
	if len(meshMaterialSet) != 0 and len(materialNameSet.difference(meshMaterialSet)) != 0:
		materialString = ""
		for materialName in materialNameSet.difference(meshMaterialSet):
			materialString += materialName+"\n"
		warningList.append("The following materials exist in the MDF but do not exist on the meshes in the scene:\n"+materialString+"\n If these meshes are supposed to be used with this MDF, the number of materials and name of materials in the MDF must match the mesh.\nThe material will appear as a checkerboard texture in game.")
		
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
	path = path.replace(os.sep,"/").split(".tex")[0]+".tex"#Fix incorrect directory separators and including version numbers on the tex path
	if "natives" in path:
		splitPath = splitNativesPath(path)
		if splitPath != None:
			path = splitPath[1]#Fix including the chunk root path in the tex path
	return path
def buildMDF(mdfCollectionName,mdfVersion = None):
	mdfCollection = bpy.data.collections.get(mdfCollectionName)
	if mdfVersion == None:
		mdfVersion = int(bpy.context.scene.re_mdf_toolpanel.activeGame[1::])
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
				materialEntry.propertyList.append(propertyEntry)
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