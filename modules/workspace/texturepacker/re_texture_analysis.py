import bpy
import os
import json
TEX_RES_X = 1024
TEX_RES_Y = 1024
OVERRIDE_RES = False

def analyzeMaterial(material,presetList,gameName,meshCollectionName = "newModel.mesh"):#Determine the best preset to use for material conversion,returns dict containing material settings to apply
	presetNameDict = {}
	presetNameList = []
	for entry in presetList:
		presetName = os.path.splitext(os.path.split(entry)[1])[0]
		presetNameDict[presetName] = {"path":entry,"score":0}
		presetNameList.append(presetName)
	
	matInfoDict = dict()
	imageXRes = 0
	imageYRes = 0
	maxTotalRes = 0
	
	lowPriorityKeywords = set()
	midPriorityKeywords = set()
	highPriorityKeywords = set()
	imageNameList = []
	
	
	for node in material.node_tree.nodes:
		#Get highest quality image res used in the material
		if node.type == "TEX_IMAGE":
		
			if node.image and not OVERRIDE_RES:
				imageNameList.append(node.image.name.lower())
				if (node.image.size[0] * node.image.size[1]) > maxTotalRes:
					imageXRes = node.image.size[0]
					imageYRes = node.image.size[1]
					maxTotalRes = node.image.size[0] * node.image.size[1]
					
	if imageXRes == 0:
		imageXRes = TEX_RES_X
		imageYRes = TEX_RES_Y
		
	#Check texture names for info that could determine preset type
	#Match presets based on keywords, the more keywords matched, the higher the score of the preset.
	#Highest score preset gets picked
	#TODO add more criteria
	
	lowerMeshCollectionName = meshCollectionName.lower()
	if lowerMeshCollectionName.startswith("wp"):
		lowPriorityKeywords.add("weapon")
	if lowerMeshCollectionName.startswith("it"):
		lowPriorityKeywords.add("weapon")
	elif lowerMeshCollectionName.startswith("ch"):
		lowPriorityKeywords.add("character")
	elif lowerMeshCollectionName.startswith("pl"):
		lowPriorityKeywords.add("character")
	elif lowerMeshCollectionName.startswith("em"):
		lowPriorityKeywords.add("character")
	elif lowerMeshCollectionName.startswith("sm"):
		lowPriorityKeywords.add("stage")
	elif lowerMeshCollectionName.startswith("st"):
		lowPriorityKeywords.add("stage")
	elif lowerMeshCollectionName.startswith("gm"):
		lowPriorityKeywords.add("stage")
	
	
	
	nameList = [material.name.lower()] + imageNameList
	
	eyeIgnoreKeywords = ("eyebrow","eyelash","eyeshadow","eyeblend","lens")
	for name in nameList:
		if "body" in name:
			highPriorityKeywords.add("skin")
		if "skin" in name:
			highPriorityKeywords.add("skin")
		if "eye" in name and not any(string in name for string in eyeIgnoreKeywords):
			highPriorityKeywords.add("eye")
		if "lens" in name:
			highPriorityKeywords.add("eye lens")
		if "eyebrow" in name:
			highPriorityKeywords.add("hair")
		if "eyelash" in name:
			highPriorityKeywords.add("hair")
		if "fur" in name:
			highPriorityKeywords.add("hair")
		if "hair" in name:
			highPriorityKeywords.add("hair")
		if "head" in name:
			highPriorityKeywords.add("face")
		if "face" in name:
			highPriorityKeywords.add("face")
		#if "fur" in name:
		#	highPriorityKeywords.add("fur")
		if "decal" in name:
			highPriorityKeywords.add("decal")
		if "blend" in name:
			highPriorityKeywords.add("decal")
		if "shadow" in name:
			highPriorityKeywords.add("decal")
		if "tearline" in name:
			highPriorityKeywords.add("decal")
		if name.endswith("dec"):
			highPriorityKeywords.add("decal")
		
		if "_emi" in name:
			midPriorityKeywords.add("emissive")
		if "emit" in name:
			midPriorityKeywords.add("emissive")
		#if "_emissive" in name:
		#	midPriorityKeywords.add("emissive")
		#if "_emission" in name:
		#	midPriorityKeywords.add("emissive")
	
	
			
	#Decide preset based on which keywords it matches
	for presetName in presetNameList:
		lowerPresetName = presetName.lower()
		for keyword in highPriorityKeywords:
			if keyword in lowerPresetName:
				presetNameDict[presetName]["score"] += 3
				
		for keyword in midPriorityKeywords:
			if keyword in lowerPresetName:
				presetNameDict[presetName]["score"] += 2
		
		for keyword in lowPriorityKeywords:
			if keyword in lowerPresetName:
				presetNameDict[presetName]["score"] += 1
	
	#Add tuple of score and preset to list to determine highest value
	priorityList = []
	for presetName in presetNameDict:
		priorityList.append((presetName,presetNameDict[presetName]["score"]))
	
	priorityList.sort(key = lambda i: i[1],reverse = True)
	highestScore = priorityList[0][1]
	#Sort the list by preset name length
	#This makes the entries with the same score get decided by the less specific preset (ex: Weapon instead of Weapon Emissive)
	priorityList.sort(key = lambda i: len(i[0]))
	for entry in priorityList:
		if entry[1] == highestScore:
			outputPreset = presetNameDict[entry[0]]["path"]
			break
	
	#Debug
	#print(material.name)
	#print(highPriorityKeywords | midPriorityKeywords | lowPriorityKeywords)
	#print(priorityList)
	#print()
	
	matInfoDict["imageXRes"] = imageXRes
	matInfoDict["imageYRes"] = imageYRes
	matInfoDict["materialPreset"] = outputPreset
	matInfoDict["uv2AOBake"] = False#TODO Enable for hair in games like dmc 5
	
	return matInfoDict

def analyzePreset(presetPath):#Determine the best preset to use for material conversion,returns dict containing material settings to apply
	texInfoDict = dict()
	whitelistPath = os.path.join(os.path.dirname(os.path.abspath(__file__)),"tex_bindings_whitelist.json")
	try:
		with open(whitelistPath,"r", encoding ="utf-8") as file:
			texTypeWhitelist = set(json.load(file))
			#print(f"Loaded {whitelistPath}")
	except Exception as err:
		print(f"Failed to load {whitelistPath} - {err}")
	texBindingTypePath = os.path.join(os.path.dirname(os.path.abspath(__file__)),"tex_binding_types.json")
	try:
		with open(texBindingTypePath,"r", encoding ="utf-8") as file:
			texBindingTypeDict = json.load(file)
			#print(f"Loaded {texBindingTypePath}")
	except Exception as err:
		print(f"Failed to load {texBindingTypePath} - {err}")

	try:
		with open(presetPath,"r", encoding ="utf-8") as file:
			presetDict = json.load(file)
			print(f"Loaded {presetPath}")
	except Exception as err:
		print(f"Failed to load {presetPath} - {err}")
		
	for entry in presetDict["Texture Bindings"]:
		if entry["Texture Type"] in texTypeWhitelist:
			if entry["Texture Type"] in texBindingTypeDict:
				texInfoDict[entry["Texture Type"]] = texBindingTypeDict[entry["Texture Type"]]
				print(f"Binding: " + entry["Texture Type"] +": "+texBindingTypeDict[entry["Texture Type"]])
	return texInfoDict