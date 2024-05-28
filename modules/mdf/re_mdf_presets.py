#Author: NSA Cloud
import json
import os
import re
import bpy

from ..gen_functions import textColors,raiseWarning
from ..blender_utils import showErrorMessageBox
from .file_re_mdf import getMDFVersionToGameName
from .blender_re_mdf import createEmpty, checkNameUsage

from .blender_re_mdf import boolPropertySet,colorPropertySet
def findHeaderObj():
	if bpy.data.collections.get("MDFData",None) != None:
		objList = bpy.data.collections["MDFData"].all_objects
		headerList = [obj for obj in objList if obj.get("~TYPE",None) == "RE_MDF_HEADER"]
		if len(headerList) >= 1:
			return headerList[0]
		else:
			return None

PRESET_VERSION = 3#To be changed when there are changes to material variables
PRESET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.split(os.path.abspath(__file__))[0])),"Presets")
def saveAsPreset(activeObj,presetName,gameName):
	folderPath = os.path.join(PRESET_DIR,gameName)
	if activeObj != None:
		MDFObjType = activeObj.get("~TYPE",None)

		if not re.search(r'^[\w,\s-]+\.[A-Za-z]{3}$',presetName) and not ".." in presetName:#Check that the preset name contains no invalid characters for a file name
			presetDict = {}
			materialJSONDict = {}
			if MDFObjType == "RE_MDF_MATERIAL":
				materialJSONDict["presetType"] = "RE_MDF_MATERIAL"
				materialJSONDict["MDFVersion"] = int(bpy.context.scene.re_mdf_toolpanel.activeGame[1::])
				materialJSONDict["presetVersion"] = PRESET_VERSION
				
				materialJSONDict["Material Header"] = {
					"Material Name":activeObj.re_mdf_material.materialName,
					"Master Material Path":activeObj.re_mdf_material.mmtrPath,
					"Material Shader Type":activeObj.re_mdf_material.shaderType,
					}
				
				materialJSONDict["Flags"] = {
					"Ver32Unknown":activeObj.re_mdf_material.flags.ver32Unknown,
					"Ver32Unknown1":activeObj.re_mdf_material.flags.ver32Unknown1,
					"Ver32Unknown2":activeObj.re_mdf_material.flags.ver32Unknown2,
					"FlagBitFlag":activeObj.re_mdf_material.flags.flagIntValue,
					}
				
				materialJSONDict["Property List"] = []
				for prop in activeObj.re_mdf_material.propertyList_items:
					
					if prop.data_type == "VEC4":
						value = list(prop.float_vector_value)
					elif prop.data_type == "COLOR":
						value = list(prop.color_value)
						
					elif prop.data_type == "BOOL":
						if prop.bool_value:
							value = 1.0
						else:
							value = 0.0
					else:#float
						value = prop.float_value
						
					if value.__class__.__name__ == "IDPropertyArray":
						value = value.to_list()
					#print(value)	
					propDict = {"Property Name":prop.prop_name,"Data Type":prop.data_type,"Value":value,"Padding":prop.padding}
					materialJSONDict["Property List"].append(propDict)
				
				materialJSONDict["Texture Bindings"] = []
				for binding in activeObj.re_mdf_material.textureBindingList_items:
					bindingDict = {"Texture Type":binding.textureType,"Texture Path":binding.path}
					materialJSONDict["Texture Bindings"].append(bindingDict)
				materialJSONDict["MMTRS Data"] = []
				for item in activeObj.re_mdf_material.mmtrsData_items:
					materialJSONDict["MMTRS Data"].append(str(item.indexString))
			else:
				showErrorMessageBox("Selected object can not be made into a preset.")
			
			if materialJSONDict != {}:
				
				
				jsonPath = os.path.join(PRESET_DIR,folderPath,presetName+".json")
				try:
					os.makedirs(os.path.split(jsonPath)[0])
				except:
					pass
				with open(jsonPath, 'w', encoding='utf-8') as f:
					json.dump(materialJSONDict, f, ensure_ascii=False, indent=4)
					print(textColors.OKGREEN+"Saved preset to " + str(jsonPath) + textColors.ENDC)
					return True
		else:
			showErrorMessageBox("Invalid preset file name. ")
	else:
		showErrorMessageBox("A material object must be selected when saving a preset.")
		

def readPresetJSON(filepath):
	mdfCollection = bpy.data.collections.get(bpy.context.scene.re_mdf_toolpanel.mdfCollection,None)
	if mdfCollection != None:	
		try:
			with open(filepath) as jsonFile:
				materialJSONDict = json.load(jsonFile)
				if materialJSONDict["presetVersion"] > PRESET_VERSION:
					showErrorMessageBox("Preset was created in a newer version and cannot be used. Update to the latest version of the MDF editor.")
					return False
				
		except Exception as err:
			showErrorMessageBox("Failed to read json file. \n" + str(err))
			return False
		
		if materialJSONDict["presetType"] != "RE_MDF_MATERIAL":
			showErrorMessageBox("Preset type is not supported")
			return False
		
		print("Adding preset material " + materialJSONDict["Material Header"]["Material Name"])
		MDFVersion = materialJSONDict.get("MDFVersion",None)
		
		currentIndex = 0
		subName = "Material " + str(currentIndex).zfill(2)
		while(checkNameUsage(subName,checkSubString=True,objList = mdfCollection.all_objects)):
			currentIndex +=1
			subName = "Material " + str(currentIndex).zfill(2)
		RNADict = {"~TYPE":{"description":"For internal use. Do not change"}}
		name = subName + " ("+materialJSONDict["Material Header"]["Material Name"]+")"
		materialObj = createEmpty(name,[("~TYPE","RE_MDF_MATERIAL")],None,mdfCollection)
		gameName = getMDFVersionToGameName(MDFVersion)
		if gameName != -1:
			materialObj.re_mdf_material.gameName = getMDFVersionToGameName(materialJSONDict["MDFVersion"])
		materialObj.re_mdf_material.materialName = materialJSONDict["Material Header"]["Material Name"]
		materialObj.re_mdf_material.shaderType = materialJSONDict["Material Header"]["Material Shader Type"]
		materialObj.re_mdf_material.mmtrPath = materialJSONDict["Material Header"]["Master Material Path"]
		materialObj.re_mdf_material.flags.ver32Unknown = materialJSONDict["Flags"]["Ver32Unknown"]
		try:
			materialObj.re_mdf_material.flags.ver32Unknown1 = materialJSONDict["Flags"]["Ver32Unknown1"]
			materialObj.re_mdf_material.flags.ver32Unknown2 = materialJSONDict["Flags"]["Ver32Unknown2"]
		except:
			pass
		materialObj.re_mdf_material.flags.flagIntValue = materialJSONDict["Flags"]["FlagBitFlag"]
		
		for propEntry in materialJSONDict["Property List"]:
			prop = materialObj.re_mdf_material.propertyList_items.add()
			prop.prop_name = propEntry["Property Name"]
			prop.data_type = propEntry["Data Type"]
			try:
				prop.padding = propEntry["Padding"]
			except:
				pass
			if prop.data_type == "VEC4":
				prop.float_vector_value = propEntry["Value"]
			elif prop.data_type == "COLOR":
				prop.color_value = propEntry["Value"]
				
			elif prop.data_type == "BOOL":
				prop.bool_value = propEntry["Value"] == 1.0
			else:#float
				prop.float_value = propEntry["Value"]
				
		for bindingEntry in materialJSONDict["Texture Bindings"]:
			binding = materialObj.re_mdf_material.textureBindingList_items.add()
			binding.textureType = bindingEntry["Texture Type"]
			binding.path = bindingEntry["Texture Path"]
		
		if "MMTRS Data" in materialJSONDict:
			for indexString in materialJSONDict["MMTRS Data"]:
				item = materialObj.re_mdf_material.mmtrsData_items.add()
				item.indexString = indexString
		bpy.context.view_layer.objects.active = materialObj
	else:
		showErrorMessageBox("The active MDF collection must be set.")
	return True
def reloadPresets(folderPath):
	presetList = []
	relPathStart = os.path.join(PRESET_DIR,folderPath)
	#print(relPathStart)
	if os.path.exists(relPathStart):
		for entry in os.scandir(relPathStart):
			if entry.name.endswith(".json") and entry.is_file():
				presetList.append((os.path.relpath(os.path.join(relPathStart,entry),start = PRESET_DIR),os.path.splitext(entry.name)[0],""))
	#print("Loading " + folderPath + " presets...")
	#print("DEBUG:" + str(presetList)+"\n")#debug
	return presetList