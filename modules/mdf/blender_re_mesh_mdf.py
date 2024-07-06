#Author: NSA Cloud
#TODO Redo material importing
import os
import bpy

from ..gen_functions import raiseWarning,getBit,wildCardFileSearch
from .file_re_mdf import readMDF,getMDFVersionToGameName
from ..tex.blender_re_tex import loadTex
from .blender_nodes_re_mdf import createTextureNode
from ..ddsconv.directx.texconv import Texconv, unload_texconv
DEBUG_MODE = True
def debugprint(string):
	if DEBUG_MODE:
		print(string)

ADDON_NAME = __package__.split(".")[0]
def getChunkPathList(gameName):
	
	ADDON_PREFERENCES = bpy.context.preferences.addons[ADDON_NAME].preferences
	#print(gameName)
	chunkPathList = [item.path for item in ADDON_PREFERENCES.chunkPathList_items if item.gameName == gameName ]
	#print(chunkPathList)
	return chunkPathList

def findMDFPathFromMeshPath(meshPath):
	split = meshPath.split(".mesh")
	fileRoot = split[0]
	meshVersion = split[1]
	mdfVersionDict = {
		".1808312334":".10",#RE2
		".1902042334":".13",#RE3
		".32":".6",#RE7
		".2101050001":".19",#RE8
		".1808282334":".10",#DMC5
		".2008058288":".19",#MHRise
		".2109148288":".23",#MHRiseSunbreak
		".2010231143":".19",#REVerse
		".2109108288":".21",#RERT
		".220128762":".21",#RE7RT
		".221108797":".32",#RE4
		".230110883":".31",#SF6
		".231011879":".40",#DD2
		
		}
	mdfVersion = mdfVersionDict.get(meshVersion,None)
	if mdfVersion == None:#Allow for importing of mdfs that haven't had support added for them yet
		raiseWarning("Attempting to import unknown mdf version")	
		mdfPath = wildCardFileSearch(f"{fileRoot}.mdf2.*")
		if mdfPath == None:
			mdfPath = wildCardFileSearch(f"{fileRoot}_Mat.mdf2.*")
		if mdfPath == None:
			mdfPath = wildCardFileSearch(f"{fileRoot}_v00.mdf2.*")
		if not os.path.isfile(mdfPath) and fileRoot.endswith("_f"):
			
			mdfPath = wildCardFileSearch(f"{fileRoot[:-1] + 'm'}.mdf2.*")#DD2 female armor uses male mdf, so replace _f with _m
	else:	
		mdfPath = f"{fileRoot}.mdf2{mdfVersion}"
		if not os.path.isfile(mdfPath):
			print(f"Could not find {mdfPath}.\n Trying alternate mdf names...")
			mdfPath = f"{fileRoot}_Mat.mdf2{mdfVersion}"
		if not os.path.isfile(mdfPath):
			print(f"Could not find {mdfPath}.\n Trying alternate mdf names...")
			mdfPath = f"{fileRoot}_v00.mdf2{mdfVersion}"
			
		if not os.path.isfile(mdfPath) and fileRoot.endswith("_f"):
			
			mdfPath = f"{fileRoot[:-1] + 'm'}.mdf2{mdfVersion}"#DD2 female armor uses male mdf, so replace _f with _m
			
		if not os.path.isfile(mdfPath):
			print(f"Could not find {mdfPath}.")
			mdfPath = None
			
	return mdfPath
texVersionDict = {
	".6":".8",
	".10":".10",
	".13":".190820018",
	".19":".30",
	".21":".34",
	".23":".28",
	".32":".143221013",
	".40":".760230703",
  }	
def getTexPath(baseTexturePath,chunkPathList,mdfVersion):
	
	
	inputPath = None
	texVersion = texVersionDict.get(mdfVersion,"")
	for chunkPath in chunkPathList:
		inputPath = wildCardFileSearch(os.path.join(chunkPath,"streaming",baseTexturePath+f".tex{texVersion}*"))#Searches for texture even if the version is known because capcom can add platform or lang extensions
		
		if inputPath == None:
			inputPath = wildCardFileSearch(os.path.join(chunkPath,baseTexturePath+f".tex{texVersion}*"))
		if inputPath != None:
			break
	return inputPath	
	
	
#Material Load Levels
albedoTypeSet = set([
	"ALBDmap",
	"BackMap",
	"BaseMap",
	"BackMap_1",
	"BaseMetalMap",
	"BaseDielectricMapBase",
	#"BaseAlphaMap",
	"BaseDielectricMap",
	"""#Vertex Color
	"BaseDielectricMap_B",
	"BaseDielectricMap_G",
	"BaseDielectricMap_R",
	"""
	"BaseMap",
	"CloudMap",
	"CloudMap_1",
	"FaceBaseMap",
	"Face_BaseDielectricMap",
	"Moon_Tex",
	"Sky_Top_Tex",

	])
normalTypeSet = set([
	"Drop_NormalMap",
	"NRMR_NRRTMap",
	"NRMR_NRRTmap",
	"NRMmap",
	"NRRTMap",
	"NormalRoughnessOcclusionMap",
	"NormalRoughnessTranslucentMap",
	"NormalMap",
	"NormalRoughnessMap",
	"SnowNormalRoughnessMap",
	"snowNRMmap",
	"NormalReflactionMap",
	"NormalRoughnessMap",
	"NormalRoughnessMap_R",
	"NormalRoughnessCavityMap",
	"NormalRoughnessCavityMapBase",
	"NormalRoughnessOcclusionMap",
	"NormalRoughnessTranslucencyMap",
	"NRRTMap",
	])

alphaTypeSet = set([
	"AlphaMap"

	])
cmmTypeSet = set([
	"UserColorchangeMap",
	"ColormaskMap"

	])
emissionTypeSet = set([
	"EmissiveMap"
	])
albedoVertexColorTypeSet = set([
	"BaseDielectricMap_B",
	"BaseDielectricMap_G",
	"BaseDielectricMap_R",
	"MSK3",
	])
normalVertexColorTypeSet = set([
	"NormalRoughnessMap_B",
	"NormalRoughnessMap_G",
	"NormalRoughnessMap_R",
	])



NRMRTypes = set([
	"NormalReflactionMap",
	"NormalRoughnessMap",
	"NormalRoughnessMap_R",
	])
NRRTTypes = set([
	"NormalRoughnessCavityMap",
	"NormalRoughnessCavityMapBase",
	"NormalRoughnessOcclusionMap",
	"NormalRoughnessTranslucencyMap",
	"NormalRoughnessTranslucentMap",
	"NRRTMap",
	"NRMR_NRRTMap"
	])
ATOSTypes = set([
	"AlphaTranslucentOcclusionCavityMap",
	"AlphaTranslucentOcclusionSSSMap",
	])
NAMTypes = set([
	"Stitch_NAM",
	])	


def importMDF(mdfFile,meshMaterialDict,materialLoadLevel,reloadCachedTextures,chunkPath = ""):
	TEXTURE_CACHE_DIR = bpy.context.preferences.addons[ADDON_NAME].preferences.textureCachePath
	allowedTextureTypes = set()
	
	
	loadedImageDict = dict()
	errorFileSet = set()
	
	#MaterialLoadLevel
	"""
	1: Load Albedo only
	2: Load Albedo, Normal, Roughness, Metallic, Alpha
	3: Load all textures, including ones unusable by Blender
	"""
	mdfVersion = mdfFile.fileVersion
	gameName = getMDFVersionToGameName(mdfVersion)
	mdfMaterialDict = mdfFile.getMaterialDict()
	#if not os.path.isdir(chunkPath):
		#raiseWarning("Natives path not found, can't import textures")
		#raise Exception
	
	chunkPathList = [chunkPath]
	chunkPathList.extend(getChunkPathList(gameName))
	
	texConv = Texconv()
	if materialLoadLevel == "1":
		allowedTextureTypes.update(albedoTypeSet)
		allowedTextureTypes.update(albedoVertexColorTypeSet)
	
	elif materialLoadLevel == "2":
		allowedTextureTypes.update(albedoVertexColorTypeSet)
		allowedTextureTypes.update(normalVertexColorTypeSet)
		allowedTextureTypes.update(albedoTypeSet)
		allowedTextureTypes.update(normalTypeSet)
		allowedTextureTypes.update(alphaTypeSet)
		allowedTextureTypes.update(ATOSTypes)
		allowedTextureTypes.update(NAMTypes)

	for materialName in meshMaterialDict.keys():
		#print(materialName)
		blenderMaterial = meshMaterialDict[materialName]
		blenderMaterial.use_nodes = True
		blenderMaterial.node_tree.nodes.clear()
		mdfMaterial = mdfMaterialDict.get(materialName,None)
		textureNodeInfoList = []
		if mdfMaterial != None:
			hasAlpha = mdfMaterial.flags.flagValues.BaseAlphaTestEnable or mdfMaterial.flags.flagValues.AlphaTestEnable
			if mdfMaterial.ver32Unkn0 == 1:
				hasAlpha = True
			hasVertexColor = False
			vertexColorTextureDict = {}
			#Get paths/convert textures
			#Detect albedo texture if one isn't found by the type name
			detectedAlbedo = False
			for textureEntry in mdfMaterial.textureList:
				if textureEntry.textureType in albedoTypeSet:
					detectedAlbedo = True
					break
				
			for textureEntry in mdfMaterial.textureList:
				textureType = textureEntry.textureType
				texture = textureEntry.texturePath
				autoDetectedAlbedo = False
				if not detectedAlbedo:
					if "_ALB" in texture:
						autoDetectedAlbedo = True
						detectedAlbedo = True
				if allowedTextureTypes == set() or textureType in allowedTextureTypes or autoDetectedAlbedo:
					baseTexturePath = texture.replace("@","").replace(".tex","").replace('/',os.sep)
					outputPath = os.path.join(TEXTURE_CACHE_DIR,baseTexturePath+".tif")
					
					texPath = getTexPath(baseTexturePath,chunkPathList,mdfVersion)
					
					if texPath != None:
						if texPath in loadedImageDict:
							imageData = loadedImageDict[texPath]
						else:
							try:
								if texPath not in errorFileSet:
									imageData = loadTex(texPath,outputPath,texConv,reloadCachedTextures)
									loadedImageDict[texPath] = imageData
							except Exception as err:
								errorFileSet.add(texPath)
								
								raiseWarning(f"An error occured while attempting to convert {texPath} - {str(err)}")
					else:
						if texture not in errorFileSet:
							raiseWarning("Could not find texture: " + texture + ", skipping...")
							errorFileSet.add(texture)
					if os.path.exists(outputPath):
						#Determine what node to create for this texture
						
						if textureType in albedoVertexColorTypeSet or textureType in normalVertexColorTypeSet:
							hasVertexColor = True
							vertexColorTextureDict[textureType] = outputPath
						if textureType in albedoTypeSet:
							if textureType == "BaseDielectricMap" or textureType == "BaseDielectricMapBase":
								textureNodeInfoList.append(("ALBD",textureType,outputPath))
								vertexColorTextureDict[textureType] = outputPath
							elif textureType == "BaseMetalMap":
								textureNodeInfoList.append(("ALBM",textureType,outputPath))
							elif textureType == "BaseAlphaMap":
								textureNodeInfoList.append(("ALBA",textureType,outputPath))
								hasAlpha = True
							else:
								textureNodeInfoList.append(("ALB",textureType,outputPath))
							detectedAlbedo = True
						elif textureType in normalTypeSet:
							if textureType == "NormalRoughnessMap":
								textureNodeInfoList.append(("NRMR",textureType,outputPath))
								vertexColorTextureDict[textureType] = outputPath
							elif textureType in NRRTTypes:
								textureNodeInfoList.append(("NRRT",textureType,outputPath))
							elif textureType == "NRMR_NRRTMap":
								if "_NRRT" in baseTexturePath:
									textureNodeInfoList.append(("NRRT",textureType,outputPath))
								else:
									textureNodeInfoList.append(("NRMR",textureType,outputPath))
							else:
								textureNodeInfoList.append(("NRMR",textureType,outputPath))
							detectedNormal = True
						elif textureType in alphaTypeSet:
							textureNodeInfoList.append(("ALP",textureType,outputPath))
							hasAlpha = True
						#elif textureType in cmmTypeSet:
							#textureNodeInfoList.append(("CMM",textureType,outputPath))
						elif textureType in emissionTypeSet:
							textureNodeInfoList.append(("EMI",textureType,outputPath))
						elif textureType in ATOSTypes:
							textureNodeInfoList.append(("ATOS",textureType,outputPath))
						elif textureType in NAMTypes:
							textureNodeInfoList.append(("NAM",textureType,outputPath))
						elif autoDetectedAlbedo:
							textureNodeInfoList.append(("ALB","AutoDetected_ALB_"+textureType,outputPath))
						else:
							textureNodeInfoList.append(("UNKN",textureType,outputPath))
							#print(os.path.join(chunkPath,nativesRoot,baseTexturePath+".tex"+textureVersion))
			
			nodeMaterialOutput = blenderMaterial.node_tree.nodes.new('ShaderNodeOutputMaterial')
			nodeMaterialOutput.location = (800,0)
			#if materialLoadLevel == "1":
				#nodeBSDF = blenderMaterial.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
			#else:
			nodeBSDF = blenderMaterial.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
			
			nodeBSDF.location = (400,0)
			blenderMaterial.node_tree.links.new(nodeBSDF.outputs[0],nodeMaterialOutput.inputs[0])
			currentYPos = 500
			
			#Vertex color is reliant upon multiple textures so it's parsed differently
			#Vertex color materials don't have to have all of the color channels. In these cases, the material is imported without the vertex color blending because it's a pain to fix
			#if not hasVertexColor: #and vertexColorTextureDict.get("BaseDielectricMap",None) == None or vertexColorTextureDict.get("BaseDielectricMap_R",None) == None or vertexColorTextureDict.get("BaseDielectricMap_G",None) == None or vertexColorTextureDict.get("BaseDielectricMap_B",None) == None:
			for nodeInfo in textureNodeInfoList:
				try:
					newNode = createTextureNode(blenderMaterial.node_tree,nodeInfo[0],nodeInfo[1],nodeInfo[2],(-400,currentYPos),nodeBSDF)
				except Exception as err:
					raiseWarning(f"Failed to create {nodeInfo[0]} node on {materialName}: {str(err)}")
				currentYPos -= 500
			#else:
				#Removed vertex color material parsing to redo it later
				
				
			if hasAlpha:
				blenderMaterial.blend_method = "CLIP"
				blenderMaterial.shadow_method = "CLIP"

			if blenderMaterial.blend_method == "OPAQUE":#Remove alpha connection if the material doesn't have alpha enabled. ATOS causes black spots otherwise.
				if len(nodeBSDF.inputs['Alpha'].links) > 0:
					alphaLink = nodeBSDF.inputs['Alpha'].links[0]
					blenderMaterial.node_tree.links.remove(alphaLink)
		else:
			print("Material \"" + materialName + "\" is not in the MDF, cannot import")
	errorFileSet.clear()
	loadedImageDict.clear()
	unload_texconv()
	print("Finished loading materials.")