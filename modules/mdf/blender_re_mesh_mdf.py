#Author: NSA Cloud
#TODO Redo material importing
import os
import bpy
import re

from mathutils import Vector
from ..blender_utils import arrangeNodeTree
IMPORT_TRANSLUCENT = True#Disabled since it's not quite right yet


def getUsedTextureNodes(propFileList):
	propSet = set()
	path = os.path.split(__file__)[0]
	for file in propFileList:
		f = open(os.path.join(path,file),"r")
		for line in f.readlines():
			if "matInfo[\"textureNodeDict\"][\"" in line:
				propName = line.split("matInfo[\"textureNodeDict\"][\"")[1].split("\"]",1)[0]
				propSet.add(propName)
		f.close()
	return propSet
try:
	usedTextureSet = getUsedTextureNodes(
	propFileList = [
		"blender_re_mesh_mdf.py",
		"blender_nodes_re_mdf.py",])
except Exception as err:
	print(f"Unable to load usable properties - {str(err)}")
	usedTextureSet = set()

#Detail maps that use regular normal maps
legacyDetailMapGames = set(["RE2","RE2RT","RE3","RE3RT","RE7RT","DMC5"])

alphaBlendShaderTypes = set([1,2,3,4,5,8,10,12,13])#Decal,DecalWithMetallic,DecalNRMR,Transparent,Distortion,Water,GUI,GUIMeshTransparent,ExpensiveTransparent
	
#MMTRs that use the alpha channel of ATOS or ALBA as a mask and not alpha
#It might be able to be checked in the flags instead as AlphaMaskUsed, but flags are messed up in SF6 onwards and aren't reliable indicators
maskAlphaMMTRSet = set([
	"env_1layer_common_dirt.mmtr",#RE4
	"env_2layer_common_dirt.mmtr",#RE4
	"env_3layer_common_dirt.mmtr",#RE4
	#"env_default.mmtr",#RE4
	#"character_default.mmtr",#DMC5
	"record_fur.mmtr",#RE2
	
	])

props_MetallicOverrideSet = set([
	"Metallic_Param",
	"Metallic",
	])
props_RoughnessOverrideSet = set([
	"Roughness_Param",
	"Roughness",
	])

#Material Load Levels
albedoTypeSet = set([
	"ALBD",
	"ALBDmap",
	"BackMap",
	"BaseMap",
	"BackMap_1",
	"BaseMetalMap",
	"BaseMetalMapArray",
	"BaseShiftMap",
	"BaseAnisoShiftMap",
	#"BaseDielectricMapBase",
	"BaseAlphaMap",
	"BaseDielectricMap",
	#Vertex Color
	#"BaseDielectricMap_B",
	#"BaseDielectricMap_G",
	#"BaseDielectricMap_R",
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
	"NormalRoughnessMapArray",
	"NormalRoughnessOcclusionMap",
	"NormalRoughnessTranslucentMap",
	"NormalMap",
	"NormalRoughnessMap",
	"SnowNormalRoughnessMap",
	"snowNRMmap",
	"NormalReflactionMap",
	"NormalRoughnessMap",
	#"NormalRoughnessMap_R",
	"NormalRoughnessCavityMap",
	#"NormalRoughnessCavityMapBase",
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
cmaskTypeSet = set([
	"CustomizeColor_Mask",
	"CustomizeColor_Mask2"

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
	#"NormalRoughnessMap_R",
	"NormalRoughnessMapArray",
	])
NRRTTypes = set([
	"NormalRoughnessCavityMap",
	#"NormalRoughnessCavityMapBase",
	"NormalRoughnessOcclusionMap",
	"NormalRoughnessTranslucencyMap",
	"NormalRoughnessTranslucentMap",
	"NRRTMap",
	])
ATOSTypes = set([
	"AlphaTranslucentOcclusionCavityMap",
	"AlphaTranslucentOcclusionSSSMap",
	])
NAMTypes = set([
	"Stitch_NAM",
	])	
usedTextureSet.update(albedoVertexColorTypeSet)
usedTextureSet.update(normalVertexColorTypeSet)
usedTextureSet.update(albedoTypeSet)
usedTextureSet.update(cmmTypeSet)
usedTextureSet.update(cmaskTypeSet)
usedTextureSet.update(emissionTypeSet)
usedTextureSet.update(normalTypeSet)
usedTextureSet.update(alphaTypeSet)
usedTextureSet.update(ATOSTypes)
usedTextureSet.update(NAMTypes)

#print(sorted(list(usedTextureSet)))
baseUVTilingList = set([#Node types that use UV_Tiling property
	"BaseDielectricMapBase",
	"NormalRoughnessCavityMapBase",
	])


from ..gen_functions import raiseWarning,getBit,wildCardFileSearch
from .file_re_mdf import readMDF,getMDFVersionToGameName
from ..tex.blender_re_tex import loadTex
from .blender_nodes_re_mdf import addImageNode,addTextureNode,addPropertyNode,dynamicColorMixLayerNodeGroup,getBentNormalNodeGroup,getDualUVMappingNodeGroup
from ..ddsconv.directx.texconv import Texconv, unload_texconv
DEBUG_MODE = False
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
	



def importMDF(mdfFile,meshMaterialDict,loadUnusedTextures,loadUnusedProps,useBackfaceCulling,reloadCachedTextures,chunkPath = "",gameName = None,arrangeNodes = False):
	TEXTURE_CACHE_DIR = bpy.context.preferences.addons[ADDON_NAME].preferences.textureCachePath
	USE_DDS = bpy.context.preferences.addons[ADDON_NAME].preferences.useDDS == True and bpy.app.version >= (4,2,0)
	allowedTextureTypes = set()
	
	
	loadedImageDict = dict()
	errorFileSet = set()
	mdfVersion = mdfFile.fileVersion
	if gameName == None:
		gameName = getMDFVersionToGameName(mdfVersion)
	mdfMaterialDict = mdfFile.getMaterialDict()
	#if not os.path.isdir(chunkPath):
		#raiseWarning("Natives path not found, can't import textures")
		#raise Exception
	
	chunkPathList = [chunkPath]
	chunkPathList.extend(getChunkPathList(gameName))
	
	texConv = Texconv()

	for materialName in meshMaterialDict.keys():
		#print(materialName)
		blenderMaterial = meshMaterialDict[materialName]
		blenderMaterial.use_nodes = True
		blenderMaterial.blend_method = "HASHED"#Blender 4.2 removed clip and opaque blend options, so everything has to be hash or blend
		blenderMaterial.shadow_method = "HASHED"
		blenderMaterial.node_tree.nodes.clear()
		mdfMaterial = mdfMaterialDict.get(materialName,None)
		textureNodeInfoList = []
		if mdfMaterial != None:
			hasAlpha = mdfMaterial.flags.flagValues.BaseAlphaTestEnable or mdfMaterial.flags.flagValues.AlphaTestEnable or mdfMaterial.flags.flagValues.AlphaMaskUsed
			if mdfMaterial.ver32Unkn0 == 1:
				hasAlpha = True
			hasVertexColor = False
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
				if loadUnusedTextures or textureType in usedTextureSet or autoDetectedAlbedo:
					baseTexturePath = texture.replace("@","").replace(".tex","").replace('/',os.sep)
					outputPath = os.path.join(TEXTURE_CACHE_DIR,baseTexturePath+".tif")
					
					texPath = getTexPath(baseTexturePath,chunkPathList,mdfVersion)
					
					if texPath != None:
						if texPath not in loadedImageDict:
							try:
								if texPath not in errorFileSet:
									imageList = loadTex(texPath,outputPath,texConv,reloadCachedTextures,USE_DDS)
									loadedImageDict[texPath] = imageList
									#print(imageList)
							except Exception as err:
								imageList = [None]
								loadedImageDict[texPath] = imageList
								errorFileSet.add(texPath)
								
								raiseWarning(f"An error occured while attempting to convert {texPath} - {str(err)}")
						else:
							imageList = loadedImageDict[texPath]
					else:
						if texture not in errorFileSet:
							raiseWarning("Could not find texture: " + texture + ", skipping...")
							errorFileSet.add(texture)
							imageList = [None]
					#if os.path.exists(outputPath):
						#Determine what node to create for this texture
					
					if textureType in albedoVertexColorTypeSet or textureType in normalVertexColorTypeSet:
						hasVertexColor = True
					if textureType in albedoTypeSet:
						if textureType == "BaseDielectricMap" or textureType == "BaseDielectricMapBase":
							textureNodeInfoList.append(("ALBD",textureType,imageList,outputPath))
						elif textureType == "BaseMetalMap" or textureType == "BaseMetalMapArray":
							textureNodeInfoList.append(("ALBM",textureType,imageList,outputPath))
						elif textureType == "BaseAlphaMap":
							textureNodeInfoList.append(("ALBA",textureType,imageList,outputPath))
							
							#hasAlpha = True
							#Capcom uses this type for things other than alpha :/
						else:
							textureNodeInfoList.append(("ALB",textureType,imageList,outputPath))
						detectedAlbedo = True
					elif textureType in normalTypeSet:
						if textureType == "NormalRoughnessMap":
							textureNodeInfoList.append(("NRMR",textureType,imageList,outputPath))
						elif textureType in NRRTTypes:
							textureNodeInfoList.append(("NRRT",textureType,imageList,outputPath))
						elif textureType == "NRMR_NRRTMap":
							
							if "_nrrt" in baseTexturePath.lower():
								textureNodeInfoList.append(("NRRT",textureType,imageList,outputPath))
							else:
								textureNodeInfoList.append(("NRMR",textureType,imageList,outputPath))
						else:
							textureNodeInfoList.append(("NRMR",textureType,imageList,outputPath))
						detectedNormal = True
					elif textureType in alphaTypeSet:
						textureNodeInfoList.append(("ALP",textureType,imageList,outputPath))
						hasAlpha = True
					elif textureType in cmmTypeSet:
						textureNodeInfoList.append(("CMM",textureType,imageList,outputPath))
					elif textureType in cmaskTypeSet:
						textureNodeInfoList.append(("CMASK",textureType,imageList,outputPath))
					elif textureType in emissionTypeSet:
						textureNodeInfoList.append(("EMI",textureType,imageList,outputPath))
					elif textureType in ATOSTypes:
						textureNodeInfoList.append(("ATOS",textureType,imageList,outputPath))
					elif textureType in NAMTypes:
						textureNodeInfoList.append(("NAM",textureType,imageList,outputPath))
					elif autoDetectedAlbedo:
						textureNodeInfoList.append(("ALB",textureType,imageList,outputPath))
					else:
						textureNodeInfoList.append(("UNKN",textureType,imageList,outputPath))
						#print(os.path.join(chunkPath,nativesRoot,baseTexturePath+".tex"+textureVersion))
		
			nodeMaterialOutput = blenderMaterial.node_tree.nodes.new('ShaderNodeOutputMaterial')
			nodeMaterialOutput.location = (800,0)
			#if materialLoadLevel == "1":
					#nodeBSDF = blenderMaterial.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
			#else:
			nodeBSDF = blenderMaterial.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
			
			nodeBSDF.location = (400,0)
			blenderMaterial.node_tree.links.new(nodeBSDF.outputs[0],nodeMaterialOutput.inputs[0])
			currentYPos = 800
			
			
			currentXPos = -1900
			currentPropPos = [-2200,2000]
			if arrangeNodes:
				currentPropPos = [-3000,2000]
				currentXPos = -2000
			matInfo = {
				"mmtrName":os.path.split(mdfMaterial.mmtrPath)[1],
				"flags":mdfMaterial.flags.flagValues,
				"textureNodeDict":{},
				"mPropDict":mdfMaterial.getPropertyDict(),
				"currentPropPos":currentPropPos,
				"blenderMaterial":blenderMaterial,
				"albedoNodeLayerGroup":dynamicColorMixLayerNodeGroup(blenderMaterial.node_tree),
				"normalNodeLayerGroup":dynamicColorMixLayerNodeGroup(blenderMaterial.node_tree),
				"roughnessNodeLayerGroup":dynamicColorMixLayerNodeGroup(blenderMaterial.node_tree),
				"metallicNodeLayerGroup":dynamicColorMixLayerNodeGroup(blenderMaterial.node_tree),
				"emissionColorNodeLayerGroup":dynamicColorMixLayerNodeGroup(blenderMaterial.node_tree),
				"emissionStrengthNodeLayerGroup":dynamicColorMixLayerNodeGroup(blenderMaterial.node_tree),
				"cavityNodeLayerGroup":dynamicColorMixLayerNodeGroup(blenderMaterial.node_tree),
				"aoNodeLayerGroup":dynamicColorMixLayerNodeGroup(blenderMaterial.node_tree),
				"alphaSocket":None,
				"translucentSocket":None,
				"subsurfaceSocket":None,
				"sheenSocket":None,
				"detailNormalSocket":None,
				"isDielectric":False,
				"isNRRT":False,
				"isMaskAlphaMMTR": os.path.split(mdfMaterial.mmtrPath)[1].lower() in maskAlphaMMTRSet,
				"isAlphaBlend":False,
				"shaderType":mdfMaterial.shaderType,
				"currentShaderOutput":nodeBSDF.outputs["BSDF"],
				"gameName":gameName,
				}
			#print(gameName)
			nodes = blenderMaterial.node_tree.nodes
			links = blenderMaterial.node_tree.links
			nodeTree = blenderMaterial.node_tree
			
			UVMap1Node = nodes.new("ShaderNodeUVMap")
			UVMap1Node.name = "UVMap1Node"
			UVMap1Node.location = (-800,900)
			UVMap1Node.uv_map = "UVMap0"
			
			UVMap2Node = nodes.new("ShaderNodeUVMap")
			UVMap2Node.name = "UVMap2Node"
			UVMap2Node.location = (-800,600)
			UVMap2Node.uv_map = "UVMap1"
			
			blenderMaterial.use_backface_culling = useBackfaceCulling and not (matInfo["flags"].BaseTwoSideEnable == 1 or matInfo["flags"].TwoSideEnable == 1)
			
			arrayImageNodeList = []
			
			if matInfo["shaderType"] in alphaBlendShaderTypes:
				matInfo["isAlphaBlend"] = True
				blenderMaterial.shadow_method = "NONE"
			
			for (_,textureType,imageList,texturePath) in textureNodeInfoList:
				try:
					newNode = addImageNode(blenderMaterial.node_tree,textureType,imageList,texturePath,(currentXPos,currentYPos))
					currentYPos += 350
					#print(newNode)
					matInfo["textureNodeDict"][textureType] = newNode
					
					if newNode.bl_idname == "ShaderNodeGroup":
						
						if newNode.node_tree.name == "ImagePassThroughNodeGroup":
							arrayImageNodeList.append(newNode.name)
					
				except Exception as err:
					raiseWarning(f"Failed to create {textureType} node on {materialName}: {str(err)}")
				
			
			
			for (nodeType,textureType,_,_) in textureNodeInfoList:
				#Loop through node list again once all image nodes are added
				if nodeType != "UNKN" and textureType in nodes:
					addTextureNode(blenderMaterial.node_tree, nodeType, textureType, matInfo)
			
			
			
			#Base layer overrides
			if "Roughness" in matInfo["mPropDict"]:
				roughnessNode = addPropertyNode(matInfo["mPropDict"]["Roughness"], matInfo["currentPropPos"], nodeTree)
				matInfo["roughnessNodeLayerGroup"].addMixLayer(roughnessNode.outputs["Value"],factorOutSocket = None,mixType = "MULTIPLY",mixFactor = 1.0)
			elif "Roughness_Param" in matInfo["mPropDict"]:
				roughnessNode = addPropertyNode(matInfo["mPropDict"]["Roughness_Param"], matInfo["currentPropPos"], nodeTree)
				matInfo["roughnessNodeLayerGroup"].addMixLayer(roughnessNode.outputs["Value"],factorOutSocket = None,mixType = "MULTIPLY",mixFactor = 1.0)
			
			
			
			
			
			#Tiling
			if "UV_Tiling" in matInfo["mPropDict"]:
				uvTilingNode = addPropertyNode(matInfo["mPropDict"]["UV_Tiling"], matInfo["currentPropPos"], nodeTree)
				
				uvMappingGroupNode = nodeTree.nodes.new("ShaderNodeGroup")
				uvMappingGroupNode.node_tree = getDualUVMappingNodeGroup()
				uvMappingGroupNode.location = uvTilingNode.location + Vector((300,0))
				nodeTree.links.new(UVMap1Node.outputs["UV"],uvMappingGroupNode.inputs["UV1"])
				nodeTree.links.new(UVMap2Node.outputs["UV"],uvMappingGroupNode.inputs["UV2"])
				nodeTree.links.new(uvTilingNode.outputs["Value"],uvMappingGroupNode.inputs["Tiling"])
				if "UV_Tiling_Offset" in matInfo["mPropDict"]:
					uvTilingLocationNode = addPropertyNode(matInfo["mPropDict"]["UV_Tiling_Offset"], matInfo["currentPropPos"], nodeTree)
					nodeTree.links.new(uvTilingLocationNode.outputs[0],uvMappingGroupNode.inputs["OffsetX"])
					nodeTree.links.new(uvTilingLocationNode.outputs[1],uvMappingGroupNode.inputs["OffsetY"])
				
				
				
				for textureType in baseUVTilingList:
					if textureType in nodeTree.nodes:
						links.new(uvMappingGroupNode.outputs["Vector"],nodeTree.nodes[textureType].inputs["Vector"])
			
			#Vertex Color Processing
			if hasVertexColor:
				vertexColorNode = nodes.new("ShaderNodeVertexColor")
				vertexColorNode.layer_name = "Col"
				vertexColorNode.location=(-400,0)
				vertexColorChannelSepNode = nodes.new("ShaderNodeSeparateRGB")
				vertexColorNode.location=(-150,0)
				
				links.new(vertexColorNode.outputs["Color"],vertexColorChannelSepNode.inputs["Image"])
				if matInfo["albedoNodeLayerGroup"] != None:
					if "BaseDielectricMap_R" in matInfo["textureNodeDict"]:
						node = matInfo["textureNodeDict"]["BaseDielectricMap_R"]
						matInfo["albedoNodeLayerGroup"].addMixLayer(node.outputs["Color"],vertexColorChannelSepNode.outputs["R"],mixType = "MIX")
						matInfo["metallicNodeLayerGroup"].addMixLayer(node.outputs["Alpha"],vertexColorChannelSepNode.outputs["R"],mixType = "MIX")
					if "BaseDielectricMap_G" in matInfo["textureNodeDict"]:
						node = matInfo["textureNodeDict"]["BaseDielectricMap_G"]
						matInfo["albedoNodeLayerGroup"].addMixLayer(node.outputs["Color"],vertexColorChannelSepNode.outputs["G"],mixType = "MIX")
						matInfo["metallicNodeLayerGroup"].addMixLayer(node.outputs["Alpha"],vertexColorChannelSepNode.outputs["G"],mixType = "MIX")
					if "BaseDielectricMap_B" in matInfo["textureNodeDict"]:
						node = matInfo["textureNodeDict"]["BaseDielectricMap_B"]
						matInfo["albedoNodeLayerGroup"].addMixLayer(node.outputs["Color"],vertexColorChannelSepNode.outputs["B"],mixType = "MIX")
						matInfo["metallicNodeLayerGroup"].addMixLayer(node.outputs["Alpha"],vertexColorChannelSepNode.outputs["B"],mixType = "MIX")
				if matInfo["normalNodeLayerGroup"] != None:
					if "NormalRoughnessMap_R" in matInfo["textureNodeDict"]:
						node = matInfo["textureNodeDict"]["NormalRoughnessMap_R"]
						matInfo["normalNodeLayerGroup"].addMixLayer(node.outputs["Color"],vertexColorChannelSepNode.outputs["R"],mixType = "MIX")
						matInfo["roughnessNodeLayerGroup"].addMixLayer(node.outputs["Alpha"],vertexColorChannelSepNode.outputs["R"],mixType = "MIX")
					if "NormalRoughnessMap_G" in matInfo["textureNodeDict"]:
						node = matInfo["textureNodeDict"]["NormalRoughnessMap_G"]
						matInfo["normalNodeLayerGroup"].addMixLayer(node.outputs["Color"],vertexColorChannelSepNode.outputs["G"],mixType = "MIX")
						matInfo["roughnessNodeLayerGroup"].addMixLayer(node.outputs["Alpha"],vertexColorChannelSepNode.outputs["G"],mixType = "MIX")
					
					if "NormalRoughnessMap_B" in matInfo["textureNodeDict"]:
						node = matInfo["textureNodeDict"]["NormalRoughnessMap_B"]
						matInfo["normalNodeLayerGroup"].addMixLayer(node.outputs["Color"],vertexColorChannelSepNode.outputs["B"],mixType = "MIX")
						matInfo["roughnessNodeLayerGroup"].addMixLayer(node.outputs["Alpha"],vertexColorChannelSepNode.outputs["B"],mixType = "MIX")
			
			if "LayerMaskOcclusionMap" in matInfo["textureNodeDict"]:
				LYMONode = matInfo["textureNodeDict"]["LayerMaskOcclusionMap"]
				LYMOSepNode = nodes.new("ShaderNodeSeparateRGB")
				LYMOSepNode.location = LYMONode.location + Vector((300,0))
				links.new(LYMONode.outputs["Color"],LYMOSepNode.inputs["Image"])
				matInfo["aoNodeLayerGroup"].addMixLayer(LYMONode.outputs["Alpha"],mixType = "MULTIPLY",mixFactor = 1.0)
				
				
				layerMaskUVMappingGroupNode = nodeTree.nodes.new("ShaderNodeGroup")
				layerMaskUVMappingGroupNode.node_tree = getDualUVMappingNodeGroup()
				layerMaskUVMappingGroupNode.location = LYMONode.location + Vector((-300,0))
				layerMaskUVMappingGroupNode.inputs["Tiling"].default_value = 1.0
				nodeTree.links.new(UVMap1Node.outputs["UV"],layerMaskUVMappingGroupNode.inputs["UV1"])
				nodeTree.links.new(UVMap2Node.outputs["UV"],layerMaskUVMappingGroupNode.inputs["UV2"])
				if "LayerMask_Use_SecondaryUV" in matInfo["mPropDict"]:
					layerMaskUV2Node = addPropertyNode(matInfo["mPropDict"]["LayerMask_Use_SecondaryUV"], matInfo["currentPropPos"], nodeTree)
					links.new(layerMaskUV2Node.outputs["Value"],layerMaskUVMappingGroupNode.inputs["UseSecondaryUV"])
				#
				links.new(layerMaskUVMappingGroupNode.outputs["Vector"],LYMONode.inputs["Vector"])
				if "BaseAlphaMap" in nodeTree.nodes:
					#Use secondary uv on base alpha texture if it's enabled on the layer mask
					#TODO Check this in game, there's a mesh that uses secondary uv but doesn't have base secondary uv flag enabled: "RE4_EXTRACT\re_chunk_000\natives\STM\_Chainsaw\Environment\sm\sm2X\sm21\sm21_515\sm21_515_00.mesh.221108797"
					links.new(layerMaskUVMappingGroupNode.outputs["Vector"],nodeTree.nodes["BaseAlphaMap"].inputs["Vector"])
				layer1UVMappingGroupNode = None
				layer2UVMappingGroupNode = None
				if "UV_Tiling1" in matInfo["mPropDict"]:
					uvTiling1Node = addPropertyNode(matInfo["mPropDict"]["UV_Tiling1"], matInfo["currentPropPos"], nodeTree)
					layer1UVMappingGroupNode = nodeTree.nodes.new("ShaderNodeGroup")
					layer1UVMappingGroupNode.node_tree = getDualUVMappingNodeGroup()
					layer1UVMappingGroupNode.location = uvTiling1Node.location + Vector((-300,0))
					nodeTree.links.new(UVMap1Node.outputs["UV"],layer1UVMappingGroupNode.inputs["UV1"])
					nodeTree.links.new(UVMap2Node.outputs["UV"],layer1UVMappingGroupNode.inputs["UV2"])
					nodeTree.links.new(uvTiling1Node.outputs["Value"],layer1UVMappingGroupNode.inputs["Tiling"])
					if "UV_Tiling_Offset1" in matInfo["mPropDict"]:
						uvTiling1LocationNode = addPropertyNode(matInfo["mPropDict"]["UV_Tiling_Offset1"], matInfo["currentPropPos"], nodeTree)
						nodeTree.links.new(uvTiling1LocationNode.outputs[0],layer1UVMappingGroupNode.inputs["OffsetX"])
						nodeTree.links.new(uvTiling1LocationNode.outputs[1],layer1UVMappingGroupNode.inputs["OffsetY"])
						
				
				if "UV_Tiling2" in matInfo["mPropDict"]:
					uvTiling2Node = addPropertyNode(matInfo["mPropDict"]["UV_Tiling2"], matInfo["currentPropPos"], nodeTree)
					layer2UVMappingGroupNode = nodeTree.nodes.new("ShaderNodeGroup")
					layer2UVMappingGroupNode.node_tree = getDualUVMappingNodeGroup()
					layer2UVMappingGroupNode.location = uvTiling2Node.location + Vector((-300,0))
					nodeTree.links.new(UVMap1Node.outputs["UV"],layer2UVMappingGroupNode.inputs["UV1"])
					nodeTree.links.new(UVMap2Node.outputs["UV"],layer2UVMappingGroupNode.inputs["UV2"])
					nodeTree.links.new(uvTiling2Node.outputs["Value"],layer2UVMappingGroupNode.inputs["Tiling"])
					if "UV_Tiling_Offset2" in matInfo["mPropDict"]:
						uvTiling2LocationNode = addPropertyNode(matInfo["mPropDict"]["UV_Tiling_Offset2"], matInfo["currentPropPos"], nodeTree)
						nodeTree.links.new(uvTiling2LocationNode.outputs[0],layer2UVMappingGroupNode.inputs["OffsetX"])
						nodeTree.links.new(uvTiling2LocationNode.outputs[1],layer2UVMappingGroupNode.inputs["OffsetY"])
					
				
				if "BaseDielectricMapBase" in matInfo["textureNodeDict"]:
					matInfo["isDielectric"] = True
					
					node = matInfo["textureNodeDict"]["BaseDielectricMapBase"]
					matInfo["albedoNodeLayerGroup"].addMixLayer(node.outputs["Color"],LYMOSepNode.outputs["B"],mixType = "MIX")
					matInfo["metallicNodeLayerGroup"].addMixLayer(node.outputs["Alpha"],LYMOSepNode.outputs["B"],mixType = "MIX")
				
				if "BaseDielectricMap1" in matInfo["textureNodeDict"]:
					node = matInfo["textureNodeDict"]["BaseDielectricMap1"]
					matInfo["albedoNodeLayerGroup"].addMixLayer(node.outputs["Color"],LYMOSepNode.outputs["R"],mixType = "MIX")
					matInfo["metallicNodeLayerGroup"].addMixLayer(node.outputs["Alpha"],LYMOSepNode.outputs["R"],mixType = "MIX")
					if layer1UVMappingGroupNode != None:
						links.new(layer1UVMappingGroupNode.outputs["Vector"],node.inputs["Vector"])
					
				if "BaseDielectricMap2" in matInfo["textureNodeDict"]:
					node = matInfo["textureNodeDict"]["BaseDielectricMap2"]
					matInfo["albedoNodeLayerGroup"].addMixLayer(node.outputs["Color"],LYMOSepNode.outputs["G"],mixType = "MIX")
					matInfo["metallicNodeLayerGroup"].addMixLayer(node.outputs["Alpha"],LYMOSepNode.outputs["G"],mixType = "MIX")
					if layer1UVMappingGroupNode != None:
						links.new(layer1UVMappingGroupNode.outputs["Vector"],node.inputs["Vector"])
				
				
				if "NormalRoughnessCavityMapBase" in matInfo["textureNodeDict"]:
					node = matInfo["textureNodeDict"]["NormalRoughnessCavityMapBase"]
					nodeGroupNode = nodeTree.nodes.new("ShaderNodeGroup")
					nodeGroupNode.node_tree = getBentNormalNodeGroup()
					nodeGroupNode.location = node.location + Vector((300,0))
					nodeTree.links.new(node.outputs["Color"],nodeGroupNode.inputs["Color"])
					nodeTree.links.new(node.outputs["Alpha"],nodeGroupNode.inputs["Alpha"])
					matInfo["normalNodeLayerGroup"].addMixLayer(nodeGroupNode.outputs["Color"],LYMOSepNode.outputs["B"],mixType = "MIX")
					matInfo["roughnessNodeLayerGroup"].addMixLayer(nodeGroupNode.outputs["Roughness"],LYMOSepNode.outputs["B"],mixType = "MIX")
					matInfo["cavityNodeLayerGroup"].addMixLayer(nodeGroupNode.outputs["BlueChannel"],LYMOSepNode.outputs["B"],mixType = "MIX")
					
				if "NormalRoughnessCavityMap1" in matInfo["textureNodeDict"]:
					node = matInfo["textureNodeDict"]["NormalRoughnessCavityMap1"]
					nodeGroupNode = nodeTree.nodes.new("ShaderNodeGroup")
					nodeGroupNode.node_tree = getBentNormalNodeGroup()
					nodeGroupNode.location = node.location + Vector((300,0))
					nodeTree.links.new(node.outputs["Color"],nodeGroupNode.inputs["Color"])
					nodeTree.links.new(node.outputs["Alpha"],nodeGroupNode.inputs["Alpha"])
					matInfo["normalNodeLayerGroup"].addMixLayer(nodeGroupNode.outputs["Color"],LYMOSepNode.outputs["R"],mixType = "MIX")
					matInfo["roughnessNodeLayerGroup"].addMixLayer(nodeGroupNode.outputs["Roughness"],LYMOSepNode.outputs["R"],mixType = "MIX")
					matInfo["cavityNodeLayerGroup"].addMixLayer(nodeGroupNode.outputs["BlueChannel"],LYMOSepNode.outputs["R"],mixType = "MIX")
					if layer1UVMappingGroupNode != None:
						links.new(layer1UVMappingGroupNode.outputs["Vector"],node.inputs["Vector"])
				if "NormalRoughnessCavityMap2" in matInfo["textureNodeDict"]:
					node = matInfo["textureNodeDict"]["NormalRoughnessCavityMap2"]
					nodeGroupNode = nodeTree.nodes.new("ShaderNodeGroup")
					nodeGroupNode.node_tree = getBentNormalNodeGroup()
					nodeGroupNode.location = node.location + Vector((300,0))
					nodeTree.links.new(node.outputs["Color"],nodeGroupNode.inputs["Color"])
					nodeTree.links.new(node.outputs["Alpha"],nodeGroupNode.inputs["Alpha"])
					matInfo["normalNodeLayerGroup"].addMixLayer(nodeGroupNode.outputs["Color"],LYMOSepNode.outputs["G"],mixType = "MIX")
					matInfo["roughnessNodeLayerGroup"].addMixLayer(nodeGroupNode.outputs["Roughness"],LYMOSepNode.outputs["G"],mixType = "MIX")
					matInfo["cavityNodeLayerGroup"].addMixLayer(nodeGroupNode.outputs["BlueChannel"],LYMOSepNode.outputs["G"],mixType = "MIX")
					if layer2UVMappingGroupNode != None:
						links.new(layer2UVMappingGroupNode.outputs["Vector"],node.inputs["Vector"])
			if "DirtWearMap" in matInfo["textureNodeDict"]:
				DirtWearNode = matInfo["textureNodeDict"]["DirtWearMap"]
				
				dirtMapUVMappingGroupNode = nodeTree.nodes.new("ShaderNodeGroup")
				dirtMapUVMappingGroupNode.node_tree = getDualUVMappingNodeGroup()
				dirtMapUVMappingGroupNode.location = DirtWearNode.location + Vector((-300,0))
				dirtMapUVMappingGroupNode.inputs["Tiling"].default_value = 1.0
				nodeTree.links.new(UVMap1Node.outputs["UV"],dirtMapUVMappingGroupNode.inputs["UV1"])
				nodeTree.links.new(UVMap2Node.outputs["UV"],dirtMapUVMappingGroupNode.inputs["UV2"])
				if "DirtMap_Use_SecondaryUV" in matInfo["mPropDict"]:
					dirtMapUV2Node = addPropertyNode(matInfo["mPropDict"]["DirtMap_Use_SecondaryUV"], matInfo["currentPropPos"], nodeTree)
					links.new(dirtMapUV2Node.outputs["Value"],dirtMapUVMappingGroupNode.inputs["UseSecondaryUV"])
				#
				if "DirtWearMap_Tiling" in matInfo["mPropDict"]:
					DirtWearTiling = addPropertyNode(matInfo["mPropDict"]["DirtWearMap_Tiling"], matInfo["currentPropPos"], nodeTree)
					links.new(DirtWearTiling.outputs["Value"],dirtMapUVMappingGroupNode.inputs["Tiling"])
				if "DirtWearMap_Tiling_Offset" in matInfo["mPropDict"]:
					DirtWearLocation = addPropertyNode(matInfo["mPropDict"]["DirtWearMap_Tiling_Offset"], matInfo["currentPropPos"], nodeTree)
					links.new(DirtWearLocation.outputs[0],dirtMapUVMappingGroupNode.inputs["OffsetX"])
					links.new(DirtWearLocation.outputs[1],dirtMapUVMappingGroupNode.inputs["OffsetY"])
					
				links.new(dirtMapUVMappingGroupNode.outputs["Vector"],DirtWearNode.inputs["Vector"])
				
				DirtWearBrightContrastNode = nodes.new("ShaderNodeBrightContrast")
				DirtWearBrightContrastNode.location = DirtWearNode.location + Vector((300,0))
				links.new(DirtWearNode.outputs["Color"],DirtWearBrightContrastNode.inputs["Color"])
				if "DirtMask_Brightness" in matInfo["mPropDict"]:
					dirtWearBrightnessNode = addPropertyNode(matInfo["mPropDict"]["DirtMask_Brightness"], matInfo["currentPropPos"], nodeTree)
					
					correctionNode = nodes.new("ShaderNodeMath")
					correctionNode.location =  DirtWearNode.location + Vector((600,0))
					correctionNode.operation = "ADD"
					correctionNode.inputs[0].default_value = -1
					
					links.new(dirtWearBrightnessNode.outputs["Value"],correctionNode.inputs[1])
					links.new(correctionNode.outputs["Value"],DirtWearBrightContrastNode.inputs["Bright"])
				if "DirtMask_Contrast" in matInfo["mPropDict"]:
					dirtWearContrastNode = addPropertyNode(matInfo["mPropDict"]["DirtMask_Contrast"], matInfo["currentPropPos"], nodeTree)
					correctionNode = nodes.new("ShaderNodeMath")
					correctionNode.location =  DirtWearNode.location + Vector((600,-300))
					correctionNode.operation = "ADD"
					correctionNode.inputs[0].default_value = 0#TODO Figure out how contrast in game differs from blender's
					
					links.new(dirtWearContrastNode.outputs["Value"],correctionNode.inputs[1])
					links.new(correctionNode.outputs["Value"],DirtWearBrightContrastNode.inputs["Contrast"])
				DirtWearHueNode = nodes.new("ShaderNodeHueSaturation")
				DirtWearHueNode.location = DirtWearNode.location + Vector((900,0))
				if "DirtColorControl" in matInfo["mPropDict"]:
					dirtWearColorControlNode = addPropertyNode(matInfo["mPropDict"]["DirtColorControl"], matInfo["currentPropPos"], nodeTree)
					links.new(dirtWearColorControlNode.outputs["Value"],DirtWearHueNode.inputs["Hue"])
				links.new(DirtWearBrightContrastNode.outputs["Color"],DirtWearHueNode.inputs["Color"])
				DirtWearSepNode = nodes.new("ShaderNodeSeparateRGB")
				DirtWearSepNode.location = DirtWearNode.location + Vector((1200,0))
				links.new(DirtWearHueNode.outputs["Color"],DirtWearSepNode.inputs["Image"])
				
				dirtRoughnessNode = None
				if "Dirt_Roughness" in matInfo["mPropDict"]:
					dirtRoughnessNode = addPropertyNode(matInfo["mPropDict"]["Dirt_Roughness"], matInfo["currentPropPos"], nodeTree)
				
				
				#The color channels are BGR for some reason
				if "DirtColor1" in matInfo["mPropDict"]:
					node = addPropertyNode(matInfo["mPropDict"]["DirtColor1"], matInfo["currentPropPos"], nodeTree)
					matInfo["albedoNodeLayerGroup"].addMixLayer(node.outputs["Color"],DirtWearSepNode.outputs["B"],mixType = "MULTIPLY")#TODO Mix probably isn't the right operation, but others didn't look quite right either, fix
					if dirtRoughnessNode != None:
						matInfo["roughnessNodeLayerGroup"].addMixLayer(dirtRoughnessNode.outputs["Value"],DirtWearSepNode.outputs["R"],mixType = "MULTIPLY")
				if "DirtColor2" in matInfo["mPropDict"]:
					node = addPropertyNode(matInfo["mPropDict"]["DirtColor2"], matInfo["currentPropPos"], nodeTree)
					matInfo["albedoNodeLayerGroup"].addMixLayer(node.outputs["Color"],DirtWearSepNode.outputs["G"],mixType = "MULTIPLY")
					if dirtRoughnessNode != None:
						matInfo["roughnessNodeLayerGroup"].addMixLayer(dirtRoughnessNode.outputs["Value"],DirtWearSepNode.outputs["G"],mixType = "MULTIPLY")
				if "DirtColor3" in matInfo["mPropDict"]:
					node = addPropertyNode(matInfo["mPropDict"]["DirtColor3"], matInfo["currentPropPos"], nodeTree)
					matInfo["albedoNodeLayerGroup"].addMixLayer(node.outputs["Color"],DirtWearSepNode.outputs["R"],mixType = "MULTIPLY")
					if dirtRoughnessNode != None:
						matInfo["roughnessNodeLayerGroup"].addMixLayer(dirtRoughnessNode.outputs["Value"],DirtWearSepNode.outputs["B"],mixType = "MULTIPLY")
				
			
			#RE4 detail map
			if "DetailMap" in matInfo["textureNodeDict"]:
				detailMapNode = matInfo["textureNodeDict"]["DetailMap"]
				currentPos = [detailMapNode.location[0]+300,detailMapNode.location[1]]
				#R Normal X
				#G Normal Y
				#B Cavity
				#A Roughness
				MaskMapSeparateNode = None
				if "MaskMap" in matInfo["textureNodeDict"]:
					MaskMapNode = matInfo["textureNodeDict"]["MaskMap"]
					MaskMapSeparateNode = nodes.new("ShaderNodeSeparateRGB")
					MaskMapSeparateNode.location = (MaskMapNode.location[0] + 300,MaskMapNode.location[1])
					links.new(MaskMapNode.outputs["Color"],MaskMapSeparateNode.inputs["Image"])
				elif "DetailMaskMap" in matInfo["textureNodeDict"]:
					MaskMapNode = matInfo["textureNodeDict"]["DetailMaskMap"]
					MaskMapSeparateNode = nodes.new("ShaderNodeSeparateRGB")
					MaskMapSeparateNode.location = (MaskMapNode.location[0] + 300,MaskMapNode.location[1])
					links.new(MaskMapNode.outputs["Color"],MaskMapSeparateNode.inputs["Image"])
				if "DetailMap_Level" in matInfo["mPropDict"] and "ARRAY_DetailMap_SELECTOR" in nodes:
					detailMapLevelNode = addPropertyNode(matInfo["mPropDict"]["DetailMap_Level"], matInfo["currentPropPos"], nodeTree)
					subtractNode = nodes.new("ShaderNodeMath")
					subtractNode.location = currentPos
					subtractNode.operation = "SUBTRACT"
					links.new(detailMapLevelNode.outputs["Value"],subtractNode.inputs[0])
					subtractNode.inputs[1].default_value = 1.0
					links.new(subtractNode.outputs["Value"],nodes["ARRAY_DetailMap_SELECTOR"].inputs["Value"])
				detailMappingNode = nodes.new("ShaderNodeMapping")
				detailMappingNode.location = currentPos
				links.new(UVMap1Node.outputs["UV"],detailMappingNode.inputs["Vector"])
				links.new(detailMappingNode.outputs["Vector"],detailMapNode.inputs["Vector"])
				if "DetailMap_Tiling_Offset" in matInfo["mPropDict"]:
					tilingScaleNode = addPropertyNode(matInfo["mPropDict"]["DetailMap_Tiling_Offset"], matInfo["currentPropPos"], nodeTree)
					tilingScaleXYZNode = nodes.new("ShaderNodeCombineXYZ")
					tilingScaleXYZNode.location = (tilingScaleNode.location[0] + 300,tilingScaleNode.location[1])
					links.new(tilingScaleNode.outputs[0],tilingScaleXYZNode.inputs["X"])
					links.new(tilingScaleNode.outputs[1],tilingScaleXYZNode.inputs["Y"])
					links.new(tilingScaleXYZNode.outputs["Vector"],detailMappingNode.inputs["Scale"])
				elif "Detail_UVScale" in matInfo["mPropDict"]:
					tilingScaleNode = addPropertyNode(matInfo["mPropDict"]["Detail_UVScale"], matInfo["currentPropPos"], nodeTree)
					tilingScaleMultNode = nodes.new("ShaderNodeMath")
					tilingScaleMultNode.location = (tilingScaleNode.location[0] + 300,tilingScaleNode.location[1])
					tilingScaleMultNode.operation = "MULTIPLY"
					links.new(tilingScaleNode.outputs["Value"],tilingScaleMultNode.inputs[0])
					tilingScaleMultNode.inputs[1].default_value = 100.0					
					links.new(tilingScaleMultNode.outputs["Value"],detailMappingNode.inputs["Scale"])
				currentPos[0] += 300
				
				separateRGBNode = nodes.new("ShaderNodeSeparateRGB")
				separateRGBNode.location = currentPos
				currentPos[0] += 300
				
				if matInfo["gameName"] not in legacyDetailMapGames:
				
					nodeGroupNode = nodeTree.nodes.new("ShaderNodeGroup")
					nodeGroupNode.node_tree = getBentNormalNodeGroup()
					nodeGroupNode.location = currentPos
					nodeTree.links.new(separateRGBNode.outputs["G"],nodeGroupNode.inputs["Color"])
					nodeTree.links.new(separateRGBNode.outputs["R"],nodeGroupNode.inputs["Alpha"])
					
				else:
					nodeGroupNode = detailMapNode
				
				links.new(detailMapNode.outputs["Color"],separateRGBNode.inputs["Image"])
				currentPos[0]+=300
				normalInfluenceNode = nodes.new("ShaderNodeMath")
				normalInfluenceNode.location = currentPos
				normalInfluenceNode.operation = "MULTIPLY"
				normalInfluenceNode.inputs[0].default_value = 1.0
				
				currentPos[0] += 300
				
				detailNormalNode = nodes.new("ShaderNodeNormalMap")
				detailNormalNode.location = currentPos
				
				if MaskMapSeparateNode != None:
					multiplyNormalBlendNode = nodes.new("ShaderNodeMath")
					multiplyNormalBlendNode.location = currentPos
					multiplyNormalBlendNode.operation = "MULTIPLY"
					links.new(MaskMapSeparateNode.outputs["R"],multiplyNormalBlendNode.inputs[0])
					links.new(multiplyNormalBlendNode.outputs["Value"],normalInfluenceNode.inputs[0])
					multiplyNormalBlendNode.inputs[1].default_value = 1.0
					normalInfluenceNode.inputs[1].default_value = 1.0
					if "Detail_NormalBlend" in matInfo["mPropDict"]:
						detailNormalBlendNode = addPropertyNode(matInfo["mPropDict"]["Detail_NormalBlend"], matInfo["currentPropPos"], nodeTree)
						links.new(detailNormalBlendNode.outputs["Value"],multiplyNormalBlendNode.inputs[1])
					elif "Detail_Normal_Intensity" in matInfo["mPropDict"]:
						detailNormalBlendNode = addPropertyNode(matInfo["mPropDict"]["Detail_Normal_Intensity"], matInfo["currentPropPos"], nodeTree)
						links.new(detailNormalBlendNode.outputs["Value"],multiplyNormalBlendNode.inputs[1])
					currentPos[0]+= 300
					
					if "Detail_RoughnessBlend" in matInfo["mPropDict"]:
						currentPos[1]-= 300
						detailRoughnessBlendNode = addPropertyNode(matInfo["mPropDict"]["Detail_RoughnessBlend"], matInfo["currentPropPos"], nodeTree)
						
						multiplyRoughnessBlendNode = nodes.new("ShaderNodeMath")
						multiplyRoughnessBlendNode.location = currentPos
						multiplyRoughnessBlendNode.operation = "MULTIPLY"
						links.new(detailRoughnessBlendNode.outputs["Value"],multiplyRoughnessBlendNode.inputs[0])
						links.new(MaskMapSeparateNode.outputs["R"],multiplyRoughnessBlendNode.inputs[1])
						currentPos[0]+= 300
						
						roughnessDistanceMulitplyNode = nodes.new("ShaderNodeMath")
						roughnessDistanceMulitplyNode.location = currentPos
						roughnessDistanceMulitplyNode.operation = "MULTIPLY"
						links.new(multiplyRoughnessBlendNode.outputs["Value"],roughnessDistanceMulitplyNode.inputs[0])
						roughnessDistanceMulitplyNode.inputs[1].default_value = 1.0
						currentPos[0]+= 300
						
						roughnessCorrectionNode = nodes.new("ShaderNodeMath")#Can't seem to get roughness values to match in game, so an approximation is used here
						roughnessCorrectionNode.location = currentPos
						roughnessCorrectionNode.operation = "ADD"
						roughnessCorrectionNode.use_clamp = True
						links.new(detailMapNode.outputs["Alpha"],roughnessCorrectionNode.inputs[0])
						roughnessCorrectionNode.inputs[1].default_value = 0.4
						currentPos[0]+= 300
						matInfo["roughnessNodeLayerGroup"].addMixLayer(roughnessCorrectionNode.outputs["Value"],factorOutSocket = roughnessDistanceMulitplyNode.outputs["Value"],mixType = "MULTIPLY",mixFactor = 1.0)
					if "Detail_Cavity" in matInfo["mPropDict"]:
						currentPos[1]-= 300
						detailCavityNode = addPropertyNode(matInfo["mPropDict"]["Detail_Cavity"], matInfo["currentPropPos"], nodeTree)
						
						multiplyCavityNode = nodes.new("ShaderNodeMath")
						multiplyCavityNode.location = currentPos
						multiplyCavityNode.operation = "MULTIPLY"
						links.new(detailCavityNode.outputs["Value"],multiplyCavityNode.inputs[0])
						links.new(MaskMapSeparateNode.outputs["R"],multiplyCavityNode.inputs[1])
						
						currentPos[0]+= 300
						
						cavityDistanceMulitplyNode = nodes.new("ShaderNodeMath")
						cavityDistanceMulitplyNode.location = currentPos
						cavityDistanceMulitplyNode.operation = "MULTIPLY"
						links.new(multiplyCavityNode.outputs["Value"],cavityDistanceMulitplyNode.inputs[0])
						cavityDistanceMulitplyNode.inputs[1].default_value = 1.0
						currentPos[0]+= 300
						
						matInfo["cavityNodeLayerGroup"].addMixLayer(MaskMapSeparateNode.outputs["B"],factorOutSocket = cavityDistanceMulitplyNode.outputs["Value"],mixType = "MULTIPLY",mixFactor = 1.0)
					
				links.new(normalInfluenceNode.outputs["Value"],detailNormalNode.inputs["Strength"])
				links.new(nodeGroupNode.outputs["Color"],detailNormalNode.inputs["Color"])
				matInfo["detailNormalSocket"] = detailNormalNode.outputs["Normal"]
			#Texture map overrides
			if "BaseColor" in matInfo["mPropDict"]:
				baseColorNode = addPropertyNode(matInfo["mPropDict"]["BaseColor"], matInfo["currentPropPos"], nodeTree)
				matInfo["albedoNodeLayerGroup"].addMixLayer(baseColorNode.outputs["Color"],factorOutSocket = None,mixType = "MULTIPLY",mixFactor = 1.0)
			
			if "Sheen" in matInfo["mPropDict"]:
				sheenNode = addPropertyNode(matInfo["mPropDict"]["Sheen"], matInfo["currentPropPos"], nodeTree)
				matInfo["sheenSocket"] = sheenNode.outputs["Value"]
			
			
			#mmtr specific nodes
			#if "eye" in matInfo["mmtrName"]:
			if "eye" in matInfo["blenderMaterial"].name or "eye" in matInfo["mmtrName"].lower() or matInfo["mmtrName"].lower().endswith("_ao.mmtr"):
				#Tearline mat setup
				if "ColorParam" in matInfo["mPropDict"]:  
					baseColorNode = addPropertyNode(matInfo["mPropDict"]["ColorParam"], matInfo["currentPropPos"], nodeTree)
					matInfo["albedoNodeLayerGroup"].addMixLayer(baseColorNode.outputs["Color"],factorOutSocket = None,mixType = "MULTIPLY",mixFactor = 1.0)
				elif "TearColor" in matInfo["mPropDict"]:  
					baseColorNode = addPropertyNode(matInfo["mPropDict"]["TearColor"], matInfo["currentPropPos"], nodeTree)
					matInfo["albedoNodeLayerGroup"].addMixLayer(baseColorNode.outputs["Color"],factorOutSocket = None,mixType = "MULTIPLY",mixFactor = 1.0)
					
				elif "Eyelash_Color" in matInfo["mPropDict"]:  
					baseColorNode = addPropertyNode(matInfo["mPropDict"]["Eyelash_Color"], matInfo["currentPropPos"], nodeTree)
					matInfo["albedoNodeLayerGroup"].addMixLayer(baseColorNode.outputs["Color"],factorOutSocket = None,mixType = "MULTIPLY",mixFactor = 1.0)
				
				if "TearRoughness" in matInfo["mPropDict"]:  
					roughnessNode = addPropertyNode(matInfo["mPropDict"]["TearRoughness"], matInfo["currentPropPos"], nodeTree)
					matInfo["roughnessNodeLayerGroup"].addMixLayer(roughnessNode.outputs["Value"],factorOutSocket = None,mixType = "MULTIPLY",mixFactor = 1.0)
				if "TearBlendRate" in matInfo["mPropDict"]:  
					alphaNode = addPropertyNode(matInfo["mPropDict"]["TearBlendRate"], matInfo["currentPropPos"], nodeTree)
					matInfo["alphaSocket"] = alphaNode.outputs["Value"]	
				if "DisappearanceRate" in matInfo["mPropDict"]:
					alphaNode = addPropertyNode(matInfo["mPropDict"]["DisappearanceRate"], matInfo["currentPropPos"], nodeTree)
					matInfo["alphaSocket"] = alphaNode.outputs["Value"]
				
				if "Alpha" in matInfo["mPropDict"] or "Transparent" in matInfo["mPropDict"] or "TearBlendRate" in matInfo["mPropDict"]:#Add property node for this later
					matInfo["isAlphaBlend"] = True
				
				if "BaseAlphaMap" in matInfo["textureNodeDict"]:
					node = nodes["BaseAlphaMap"]
					matInfo["alphaSocket"] = node.outputs["Alpha"]
			if "Alpha" in matInfo["mPropDict"]:  
				alphaNode = addPropertyNode(matInfo["mPropDict"]["Alpha"], matInfo["currentPropPos"], nodeTree)
				if matInfo["alphaSocket"] == None:
					matInfo["alphaSocket"] = alphaNode.outputs["Value"]
				else:
					alphaMultNode = nodes.new("ShaderNodeMath")
					alphaMultNode.location = matInfo["alphaSocket"].node.location + Vector((300,0))
					alphaMultNode.operation = "MULTIPLY"
					links.new(matInfo["alphaSocket"],alphaMultNode.inputs[0])
					links.new(alphaNode.outputs["Value"],alphaMultNode.inputs[1])
					matInfo["alphaSocket"] = alphaMultNode.outputs["Value"]
			elif "AlphaIntensity" in matInfo["mPropDict"]:  
				alphaNode = addPropertyNode(matInfo["mPropDict"]["AlphaIntensity"], matInfo["currentPropPos"], nodeTree)
				if matInfo["alphaSocket"] == None:
					matInfo["alphaSocket"] = alphaNode.outputs["Value"]
				else:
					alphaMultNode = nodes.new("ShaderNodeMath")
					alphaMultNode.location = matInfo["alphaSocket"].node.location + Vector((300,0))
					alphaMultNode.operation = "MULTIPLY"
					links.new(matInfo["alphaSocket"],alphaMultNode.inputs[0])
					links.new(alphaNode.outputs["Value"],alphaMultNode.inputs[1])
					matInfo["alphaSocket"] = alphaMultNode.outputs["Value"]
			elif "Transparent" in matInfo["mPropDict"]:  
				alphaNode = addPropertyNode(matInfo["mPropDict"]["Transparent"], matInfo["currentPropPos"], nodeTree)
				if matInfo["alphaSocket"] == None:
					matInfo["alphaSocket"] = alphaNode.outputs["Value"]
				else:
					alphaMultNode = nodes.new("ShaderNodeMath")
					alphaMultNode.location = matInfo["alphaSocket"].node.location + Vector((300,0))
					alphaMultNode.operation = "MULTIPLY"
					links.new(matInfo["alphaSocket"],alphaMultNode.inputs[0])
					links.new(alphaNode.outputs["Value"],alphaMultNode.inputs[1])
					matInfo["alphaSocket"] = alphaMultNode.outputs["Value"]
		
			
			#Finish process by linking to bsdf shader
			
			
			if matInfo["cavityNodeLayerGroup"].currentOutSocket != None:#Add cavity layers into AO
				matInfo["aoNodeLayerGroup"].addMixLayer(matInfo["cavityNodeLayerGroup"].currentOutSocket,factorOutSocket = None,mixType = "MULTIPLY",mixFactor = 0.6)
			
			normalNode = None
			normalVectorRotateNode = None
			if matInfo["normalNodeLayerGroup"].currentOutSocket != None:
				
				normalNode = nodes.new("ShaderNodeNormalMap")
				normalNode.location = (matInfo["normalNodeLayerGroup"].currentOutSocket.node.location[0] + 300,matInfo["normalNodeLayerGroup"].currentOutSocket.node.location[1])
				"""
				if matInfo["isNRRT"]:
					normalNode.inputs["Strength"].default_value = .4
				"""
				
				links.new(matInfo["normalNodeLayerGroup"].currentOutSocket,normalNode.inputs["Color"])
				if matInfo["detailNormalSocket"] == None:
					links.new(normalNode.outputs["Normal"],nodeBSDF.inputs["Normal"])
				else:
					detailNodeLoc = matInfo["detailNormalSocket"].node.location
					if "textureCoordinateNode" in nodeTree.nodes:
						textureCoordinateNode = nodeTree.nodes["textureCoordinateNode"]
					else:
						textureCoordinateNode = nodeTree.nodes.new("ShaderNodeTexCoord")
						textureCoordinateNode.name = "textureCoordinateNode"
						textureCoordinateNode.location = (-800,400)
					crossProductNode =  nodeTree.nodes.new("ShaderNodeVectorMath")
					crossProductNode.location = (detailNodeLoc[0] + 300,detailNodeLoc[1]+300)
					crossProductNode.operation = "CROSS_PRODUCT"
					links.new(matInfo["detailNormalSocket"],crossProductNode.inputs[0])
					links.new(textureCoordinateNode.outputs["Normal"],crossProductNode.inputs[1])
					
					dotProductNode = nodeTree.nodes.new("ShaderNodeVectorMath")
					dotProductNode.location = (detailNodeLoc[0] + 300,detailNodeLoc[1])
					dotProductNode.operation = "DOT_PRODUCT"
					links.new(matInfo["detailNormalSocket"],dotProductNode.inputs[0])
					links.new(textureCoordinateNode.outputs["Normal"],dotProductNode.inputs[1])
					
					arcCosineNode =  nodeTree.nodes.new("ShaderNodeMath")
					arcCosineNode.location = (detailNodeLoc[0] + 600,detailNodeLoc[1])
					arcCosineNode.operation = "ARCCOSINE"
					links.new(dotProductNode.outputs["Value"],arcCosineNode.inputs[0])
					
					normalVectorRotateNode = nodeTree.nodes.new("ShaderNodeVectorRotate")
					normalVectorRotateNode.location = (detailNodeLoc[0] + 900,detailNodeLoc[1])
					
					links.new(normalNode.outputs["Normal"],normalVectorRotateNode.inputs["Vector"])
					links.new(crossProductNode.outputs["Vector"],normalVectorRotateNode.inputs["Axis"])
					links.new(arcCosineNode.outputs["Value"],normalVectorRotateNode.inputs["Angle"])
					
					links.new(normalVectorRotateNode.outputs["Vector"],nodeBSDF.inputs["Normal"])
					
			if "BaseShiftMap" in matInfo["textureNodeDict"] or "BaseAnisoShiftMap" in matInfo["textureNodeDict"] :
				#TODO Add proper hair setup here, this is a hacky temporary setup
				shiftNodeName = "BaseShiftMap" if "BaseShiftMap" in matInfo["textureNodeDict"] else "BaseAnisoShiftMap"
				fresnelNode = nodes.new("ShaderNodeFresnel")
				fresnelNode.location = matInfo["textureNodeDict"][shiftNodeName].location + Vector((300,0))
				links.new(matInfo["textureNodeDict"][shiftNodeName].outputs["Alpha"],fresnelNode.inputs["IOR"])
				if normalNode != None:
					links.new(normalNode.outputs["Normal"],fresnelNode.inputs["Normal"])
				fresnelClampNode = nodes.new("ShaderNodeClamp")
				fresnelClampNode.location = fresnelNode.location + Vector((300,0))
				fresnelClampNode.inputs["Max"].default_value = 0.75
				links.new(fresnelNode.outputs["Fac"],fresnelClampNode.inputs["Value"])
				
				matInfo["metallicNodeLayerGroup"].addMixLayer(fresnelClampNode.outputs["Result"])
			if matInfo["aoNodeLayerGroup"].currentOutSocket != None:
				#This isn't the correct way to apply AO but EEVEE has no good ways of doing AO maps that doesn't have downsides (such as killing screenspace reflections and subsurface)
				
				aoNode = nodes.new("ShaderNodeAmbientOcclusion")
				
				links.new(matInfo["aoNodeLayerGroup"].currentOutSocket,aoNode.inputs["Color"])
				if normalVectorRotateNode != None:#Use combined detail normal
					links.new(normalVectorRotateNode.outputs["Vector"],aoNode.inputs["Normal"])
				elif normalNode != None:
					links.new(normalNode.outputs["Normal"],aoNode.inputs["Normal"])
				matInfo["albedoNodeLayerGroup"].addMixLayer(aoNode.outputs["Color"],aoNode.outputs["AO"],mixType = "MULTIPLY")
			
			
			if matInfo["albedoNodeLayerGroup"].currentOutSocket != None:
				links.new(matInfo["albedoNodeLayerGroup"].currentOutSocket,nodeBSDF.inputs["Base Color"])
			
			
			if matInfo["roughnessNodeLayerGroup"].currentOutSocket != None:
				clampNode = nodes.new("ShaderNodeClamp")
				clampNode.location = (matInfo["roughnessNodeLayerGroup"].currentOutSocket.node.location[0]+300,matInfo["roughnessNodeLayerGroup"].currentOutSocket.node.location[1])
				links.new(matInfo["roughnessNodeLayerGroup"].currentOutSocket,clampNode.inputs["Value"])
				links.new(clampNode.outputs["Result"],nodeBSDF.inputs["Roughness"])
			
			if matInfo["metallicNodeLayerGroup"].currentOutSocket != None:
				clampNode = nodes.new("ShaderNodeClamp")
				clampNode.location = (matInfo["metallicNodeLayerGroup"].currentOutSocket.node.location[0]+300,matInfo["metallicNodeLayerGroup"].currentOutSocket.node.location[1])
				
				links.new(clampNode.outputs["Result"],nodeBSDF.inputs["Metallic"])
				metallicNode = None
				if "Metallic" in matInfo["mPropDict"]:
					metallicNode = addPropertyNode(matInfo["mPropDict"]["Metallic"], matInfo["currentPropPos"], nodeTree)
					#matInfo["metallicNodeLayerGroup"].addMixLayer(metallicNode.outputs["Value"],factorOutSocket = None,mixType = "MULTIPLY",mixFactor = 1.0)
				elif "Metallic_Param" in matInfo["mPropDict"]:
					metallicNode = addPropertyNode(matInfo["mPropDict"]["Metallic_Param"], matInfo["currentPropPos"], nodeTree)
					#matInfo["metallicNodeLayerGroup"].addMixLayer(metallicNode.outputs["Value"],factorOutSocket = None,mixType = "MULTIPLY",mixFactor = 1.0)
				
				if matInfo["isDielectric"]:
					invertNode = nodes.new("ShaderNodeInvert")
					invertNode.location = (matInfo["metallicNodeLayerGroup"].currentOutSocket.node.location[0]+300,matInfo["metallicNodeLayerGroup"].currentOutSocket.node.location[1])
					links.new(matInfo["metallicNodeLayerGroup"].currentOutSocket,invertNode.inputs["Color"])
					
					if metallicNode != None:
					
						multNode = nodes.new("ShaderNodeMath")
						multNode.location = invertNode.location + Vector((300,0))
						multNode.operation = "MULTIPLY"
						
						links.new(invertNode.outputs["Color"],multNode.inputs[0])
						links.new(metallicNode.outputs["Value"],multNode.inputs[1])
						links.new(matInfo["metallicNodeLayerGroup"].currentOutSocket,clampNode.inputs["Value"])
						links.new(multNode.outputs["Value"],clampNode.inputs["Value"])
					else:
						links.new(invertNode.outputs["Color"],clampNode.inputs["Value"])
				else:
					if metallicNode != None:
					
						multNode = nodes.new("ShaderNodeMath")
						multNode.location = matInfo["metallicNodeLayerGroup"].nodeLoc + Vector((300,0))
						multNode.operation = "MULTIPLY"
						
						links.new(matInfo["metallicNodeLayerGroup"].currentOutSocket,multNode.inputs[0])
						links.new(metallicNode.outputs["Value"],multNode.inputs[1])
						links.new(multNode.outputs["Value"],clampNode.inputs["Value"])
					else:
						links.new(matInfo["metallicNodeLayerGroup"].currentOutSocket,clampNode.inputs["Value"])
			
			if matInfo["emissionColorNodeLayerGroup"].currentOutSocket != None:
				
				if bpy.app.version < (4,0,0):
					links.new(matInfo["emissionColorNodeLayerGroup"].currentOutSocket,nodeBSDF.inputs["Emission"])
			
				else:#I swear Blender changes things just to break addon compatibility
				#I had to dig through the source code just to find the actual name of this socket since it's not listed anywhere and Blender only gives you it's index :/
					links.new(matInfo["emissionColorNodeLayerGroup"].currentOutSocket,nodeBSDF.inputs["Emission Color"])
			
					
			if matInfo["emissionStrengthNodeLayerGroup"].currentOutSocket != None:
				emissionClampNode = nodes.new("ShaderNodeClamp")#Prevent negative emission values
				emissionClampNode.location = (matInfo["emissionStrengthNodeLayerGroup"].nodeLoc[0] + 300, matInfo["emissionStrengthNodeLayerGroup"].nodeLoc[1])
				emissionClampNode.inputs["Max"].default_value = 9999
				links.new(matInfo["emissionStrengthNodeLayerGroup"].currentOutSocket,emissionClampNode.inputs["Value"])
				links.new(emissionClampNode.outputs["Result"],nodeBSDF.inputs["Emission Strength"])
				
			
			alphaClippingNode = None
			disableShadowCast = False
			#if hasAlpha:
			if matInfo["alphaSocket"] != None:
				clippingThresholdOutSocket = None
				if "Nuki" in matInfo["mPropDict"]:#I wish capcom didn't use 1000 different names for the same thing
					#clippingThresholdNode = addPropertyNode(matInfo["mPropDict"]["Nuki"], matInfo["currentPropPos"], nodeTree)
					nukiNode = addPropertyNode(matInfo["mPropDict"]["Nuki"], matInfo["currentPropPos"], nodeTree)
					if "UseNuki_Dissolve" in matInfo["mPropDict"]:
						useNukiNode = addPropertyNode(matInfo["mPropDict"]["UseNuki_Dissolve"], matInfo["currentPropPos"], nodeTree)
						dissolveNode = addPropertyNode(matInfo["mPropDict"]["Nuki_Dissolve"], matInfo["currentPropPos"], nodeTree)
						
						mixNukiNode = nodes.new("ShaderNodeMixRGB")
						mixNukiNode.location = useNukiNode.location + Vector((300,0))
						links.new(nukiNode.outputs["Value"],mixNukiNode.inputs["Color1"])
						links.new(dissolveNode.outputs["Value"],mixNukiNode.inputs["Color2"])
						links.new(useNukiNode.outputs["Value"],mixNukiNode.inputs["Fac"])
						clippingThresholdOutSocket = mixNukiNode.outputs["Color"]
						
					else:
						clippingThresholdOutSocket = nukiNode.outputs["Value"]
				elif "Nuki_Dissolve" in matInfo["mPropDict"]:
					dissolveNode = addPropertyNode(matInfo["mPropDict"]["Nuki_Dissolve"], matInfo["currentPropPos"], nodeTree)
					clippingThresholdOutSocket = dissolveNode.outputs["Value"]
				
				#Using this as the clipping threshold might not be right but certain things don't work correctly if it's the default threshold instead
				elif "AlphaTestRef" in matInfo["mPropDict"]:
					dissolveNode = addPropertyNode(matInfo["mPropDict"]["AlphaTestRef"], matInfo["currentPropPos"], nodeTree)
					clippingThresholdOutSocket = dissolveNode.outputs["Value"]
				#	correctionNode = nodes.new("ShaderNodeMath")
				#	correctionNode.location =  (dissolveNode.location[0] + 300,dissolveNode.location[1])
				#	correctionNode.operation = "SUBTRACT"
				#	correctionNode.inputs[0].default_value = 1
				#	links.new(dissolveNode.outputs["Value"],correctionNode.inputs[1])
				#	clippingThresholdOutSocket = correctionNode.outputs["Value"]
				

				elif "DissolveThreshold" in matInfo["mPropDict"]:
					dissolveNode = addPropertyNode(matInfo["mPropDict"]["DissolveThreshold"], matInfo["currentPropPos"], nodeTree)
					clippingThresholdOutSocket = dissolveNode.outputs["Value"]
				

				if not matInfo["isAlphaBlend"] and "reflectivetransparent" not in matInfo["mmtrName"].lower() and "alphadissolve" not in matInfo["mmtrName"].lower():
					alphaClippingNode = nodes.new("ShaderNodeMath")
					alphaClippingNode.location = nodeBSDF.location + Vector((-300,-400))
					alphaClippingNode.operation = "GREATER_THAN"
					alphaClippingNode.outputs["Value"].default_value = 1.0
					
					links.new(alphaClippingNode.outputs["Value"],nodeBSDF.inputs["Alpha"])
					if clippingThresholdOutSocket != None:
						links.new(clippingThresholdOutSocket,alphaClippingNode.inputs[1])
					
					if matInfo["alphaSocket"] != None:
						
						links.new(matInfo["alphaSocket"],alphaClippingNode.inputs[0])
				else:
					if bpy.app.version < (4,2,0):
						matInfo["blenderMaterial"].blend_method = "BLEND"
						matInfo["blenderMaterial"].shadow_method = "NONE"
					else:
						matInfo["blenderMaterial"].surface_render_method = "BLENDED"
						matInfo["blenderMaterial"].use_transparent_shadow = True
						disableShadowCast = True
					if matInfo["alphaSocket"] != None: 
						links.new(matInfo["alphaSocket"],nodeBSDF.inputs["Alpha"])
				#Blender removed blend and shadow method in 4.2+ so everything will just be alpha hashed now
				#blenderMaterial.blend_method = "CLIP"
				#blenderMaterial.shadow_method = "CLIP"
			
			if matInfo["sheenSocket"] != None:
				if bpy.app.version < (4,0,0):
					links.new(matInfo["sheenSocket"],nodeBSDF.inputs["Sheen"])
				else:
					links.new(matInfo["sheenSocket"],nodeBSDF.inputs["Sheen Weight"])
			
			#Mix Shaders
			
			currentPos = [nodeBSDF.location[0]+300,nodeBSDF.location[1]]
			
			#Only enabled for hair and MHR wing materials atm since it doesn't look right on much else
			if IMPORT_TRANSLUCENT and matInfo["translucentSocket"] != None and ("Translucency" in matInfo["mPropDict"] or "Translucency_Param" in matInfo["mPropDict"]) and ("wing" in matInfo["mmtrName"].lower() or "hair" in matInfo["mmtrName"].lower()):
				
				gammaNode = nodes.new("ShaderNodeGamma")#Needs a gamma change for the mixed shader nodes to look right
				gammaNode.location = currentPos
				gammaNode.inputs["Gamma"].default_value = 0.65
				if matInfo["albedoNodeLayerGroup"].currentOutSocket != None:
					links.new(matInfo["albedoNodeLayerGroup"].currentOutSocket,gammaNode.inputs["Color"])
				 
				
				currentPos[0] += 300
				
				translucentNode = nodes.new("ShaderNodeBsdfTranslucent")
				translucentNode.location = currentPos
				links.new(gammaNode.outputs["Color"],translucentNode.inputs["Color"])
				if normalNode != None: 
					links.new(normalNode.outputs["Normal"],translucentNode.inputs["Normal"])
				currentPos[0] += 300
				
				translucentParam = None
				baseTranslucentParam = None
				if "Translucency" in matInfo["mPropDict"]:
					translucentParam = addPropertyNode(matInfo["mPropDict"]["Translucency"], matInfo["currentPropPos"], nodeTree)
					if "BaseTranslucency" in matInfo["mPropDict"]:
						baseTranslucentParam = addPropertyNode(matInfo["mPropDict"]["BaseTranslucency"], matInfo["currentPropPos"], nodeTree)
				elif "Translucency_Param" in matInfo["mPropDict"]:
					translucentParam = addPropertyNode(matInfo["mPropDict"]["Translucency_Param"], matInfo["currentPropPos"], nodeTree)
				
				
				if translucentParam != None:
					translucentMultNode = nodes.new("ShaderNodeMath")
					translucentMultNode.location = currentPos
					translucentMultNode.operation = "MULTIPLY"
					
					
					
					currentPos[0] += 300
					if baseTranslucentParam != None:
						baseTranslucentMultNode = nodes.new("ShaderNodeMath")
						baseTranslucentMultNode.location = currentPos
						baseTranslucentMultNode.operation = "MULTIPLY"
						currentPos[0] += 300
						
						links.new(baseTranslucentParam.outputs["Value"],baseTranslucentMultNode.inputs[0])
						links.new(translucentParam.outputs["Value"],baseTranslucentMultNode.inputs[1])
						links.new(matInfo["translucentSocket"],translucentMultNode.inputs[0])
						links.new(baseTranslucentMultNode.outputs["Value"],translucentMultNode.inputs[1])
					else:
						links.new(matInfo["translucentSocket"],translucentMultNode.inputs[0])
						links.new(translucentParam.outputs["Value"],translucentMultNode.inputs[1])
				multNode = nodes.new("ShaderNodeMath")#Apply alpha to translucent factor
				multNode.location = currentPos
				multNode.operation = "MULTIPLY"
				if translucentParam == None:
					links.new(matInfo["translucentSocket"],multNode.inputs[0])
				else:
					links.new(translucentMultNode.outputs["Value"],multNode.inputs[0])
				multNode.inputs[1].default_value = 1.0
				if alphaClippingNode != None:
					links.new(alphaClippingNode.outputs["Value"],multNode.inputs[1])
				currentPos[0] += 300
				mixShader = nodes.new("ShaderNodeMixShader")
				mixShader.location = currentPos
				links.new(matInfo["currentShaderOutput"],mixShader.inputs[1])
				links.new(translucentNode.outputs["BSDF"],mixShader.inputs[2])
				links.new(multNode.outputs["Value"],mixShader.inputs["Fac"])
				
				matInfo["currentShaderOutput"] = mixShader.outputs["Shader"]
				currentPos[0] += 300
				
			if disableShadowCast:
				#Blender 4.2 made it such a pain to disable shadow casting on a material
				#Used to be just a drop down menu :/
				transparentNode = nodes.new("ShaderNodeBsdfTransparent")
				transparentNode.location = currentPos
				currentPos[0] += 300
				
				lightPathNode = nodes.new("ShaderNodeLightPath")
				lightPathNode.location = currentPos
				currentPos[0] += 300
				
				mixShader = nodes.new("ShaderNodeMixShader")
				mixShader.location = currentPos
				links.new(matInfo["currentShaderOutput"],mixShader.inputs[1])
				links.new(transparentNode.outputs["BSDF"],mixShader.inputs[2])
				links.new(lightPathNode.outputs["Is Shadow Ray"],mixShader.inputs["Fac"])
				matInfo["currentShaderOutput"] = mixShader.outputs["Shader"]
			
			#if blenderMaterial.blend_method == "OPAQUE":#Remove alpha connection if the material doesn't have alpha enabled. ATOS causes black spots otherwise.
			#	if len(nodeBSDF.inputs['Alpha'].links) > 0:
			#		alphaLink = nodeBSDF.inputs['Alpha'].links[0]
			#		blenderMaterial.node_tree.links.remove(alphaLink)
			
			if loadUnusedProps:
				for prop in matInfo["mPropDict"].values():
					propNode = addPropertyNode(prop,currentPropPos,blenderMaterial.node_tree)
			
			
			#Fix array image dependency cycle
			for arrayImageNodeName in arrayImageNodeList:
				arrayImageNode = nodeTree.nodes[arrayImageNodeName]
				#Get the source of vector input if it's connected and connect it directly to the array images to fix the dependency loop
				if arrayImageNode.inputs["Vector"].links:	
					linkSource = arrayImageNode.inputs["Vector"].links[0].from_socket
					#print(arrayImageNode.inputs["Vector"].links[0].from_socket.node.name)
				else:
					linkSource = None
				for link in arrayImageNode.outputs["Vector"].links:
					if linkSource == None:
						nodeTree.links.remove(link)
					else:
						links.new(linkSource,link.to_socket)
			links.new(matInfo["currentShaderOutput"],nodes["Material Output"].inputs["Surface"])
			if arrangeNodes:
				#TODO Force blender to update node dimensions so that a large margin doesn't need to be used as a workaround
				arrangeNodeTree(blenderMaterial.node_tree,margin_x = 300,margin_y = 300,centerNodes = True)
		else:
			print("Material \"" + materialName + "\" is not in the MDF, cannot import")
	errorFileSet.clear()
	loadedImageDict.clear()
	unload_texconv()
	print("Finished loading materials.")