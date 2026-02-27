#Uses Substance Painter's naming scheme
#In theory should be able to throw textures from substance in the textures_bake folder and they'll get used if baked using standard metallic roughness PBR settings and saved as tga.

#TODO Replace bakes into roughness into bakes into emission

import bpy
import os
import time
import sys
from contextlib import contextmanager
from ...gen_functions import raiseWarning

MARGIN = 512#Amount of pixels to stretch edges, prevents mipmapping issues

STANDARD_SAMPLES = 32
AO_SAMPLES = 1024

@contextmanager
def stdout_redirected(to=os.devnull):#For sending blender's console spam to the void
	fd = sys.stdout.fileno()
	def _redirect_stdout(to):
		sys.stdout.close() # + implicit flush()
		os.dup2(to.fileno(), fd) # fd writes to 'to' file
		sys.stdout = os.fdopen(fd, 'w') # Python writes to fd

	with os.fdopen(os.dup(fd), 'w') as old_stdout:
		with open(to, 'w') as file:
			_redirect_stdout(to=file)
		try:
			yield # allow code to be run with the redirected stdout
		finally:
			_redirect_stdout(to=old_stdout) # restore stdout.
											# buffering and flags such as
											# CLOEXEC may be different
def findNodeByTypeRecursive(node_tree,nodeType = "BSDF_PRINCIPLED"):
    for node in node_tree.nodes:
        if node.type == nodeType:
            yield (node,node_tree)
        if hasattr(node, "node_tree"):
            yield from findNodeByTypeRecursive(node.node_tree,nodeType)									
											
def bakeMaterialMaps(obj,normalBakeObj,material,textureSetName,imageXRes,imageYRes,SAVE_RAW_MAPS,BAKE_OUTPUT_DIR,FILE_FORMAT,FILE_EXT,bakeAO = False,useExistingBakes = True):
	obj.select_set(True)
	bpy.context.view_layer.objects.active = obj
	obj.active_material = material
	
	principledBSDFNode = None
	
	bsdfList = list(findNodeByTypeRecursive(material.node_tree,nodeType="BSDF_PRINCIPLED"))#Returns list of tuples containing bsdf node and the node tree that contains it
	if bsdfList:
		if len(bsdfList) > 1:
			raiseWarning(f"Multiple principled BSDF nodes found. Choosing {str(bsdfList[0])}")#I don't know why someone would do this but I'm sure there's some screwed up material like this somewhere
		principledBSDFNode = bsdfList[0][0]
		nodeTree = bsdfList[0][1]
		nodes = nodeTree.nodes
		links = nodeTree.links
	if principledBSDFNode == None:
		nodes = material.node_tree.nodes
		links = material.node_tree.links
		raiseWarning("No principled BSDF shader node found on material. Baked textures may not appear as intended.")
	
	#These are for adding image nodes to bake to
	#The root nodes value can be different from nodes since the bsdf could be nested in a node group
	rootNodes = material.node_tree.nodes
	rootLinks = material.node_tree.links
	print(f"Texture Set: {textureSetName}")
	print(f"Resolution: {imageXRes}x{imageYRes}")
	
	nodePos = [0,900]
	tileSize = max([imageXRes,imageYRes])
	if tileSize > 4096:#Cap tile size at 4096
		tileSize = 4096
	prefs = bpy.context.preferences
	cycles_prefs = prefs.addons['cycles'].preferences

	enabled_devices = []
	
		
	bpy.context.scene.cycles.tile_size = max([imageXRes,imageYRes]) 
	bpy.context.scene.cycles.use_denoising = True
	bpy.context.scene.render.bake.normal_g = "NEG_Y"#Bake directX normal map
	if cycles_prefs.compute_device_type == "OPTIX":
		bpy.context.scene.cycles.device = 'GPU'
		bpy.context.scene.cycles.denoiser = 'OPTIX'
	else:
		bpy.context.scene.cycles.denoiser = 'OPENIMAGEDENOISE'
	bpy.context.scene.cycles.adaptive_threshold = 0.01
	#Bake diffuse ----------------------------------------------
	
	#Temporarily reset metallic value to 0 because the diffuse won't bake properly with it enabled
	originalMetallicSocket = None
	tempMetallicValue = None
	alphaValue = None
	alphaLink = None
	if principledBSDFNode != None:
		
		#Unlink alpha from material until finished because it will cause artifacting issues when baking otherwise
		if principledBSDFNode.inputs["Alpha"].is_linked:
			#print("DEBUG Unlinked alpha")
			alphaLink = principledBSDFNode.inputs["Alpha"].links[0].from_socket
			links.remove(principledBSDFNode.inputs["Alpha"].links[0])
		
		else:
			#print("DEBUG Created new alpha value and linked to roughness")
			alphaValue = nodes.new("ShaderNodeValue")
			alphaValue.name = "Alpha Value"
			alphaValue.outputs["Value"].default_value = 1.0#principledBSDFNode.inputs["Alpha"].default_value
			alphaLink = alphaValue.outputs["Value"]
				
		if principledBSDFNode.inputs["Metallic"].is_linked:
			originalMetallicSocket = principledBSDFNode.inputs["Metallic"].links[0].from_socket
		tempMetallicValue = nodes.new("ShaderNodeValue")
		tempMetallicValue.outputs["Value"].default_value = 0.0
		links.new(tempMetallicValue.outputs["Value"],principledBSDFNode.inputs["Metallic"])
   
   
	
	imageName = f"{textureSetName}_BaseColor"
	
	skipBake = False
	bakePath = os.path.join(BAKE_OUTPUT_DIR,imageName+FILE_EXT)
	if useExistingBakes and os.path.isfile(bakePath):
		img = bpy.data.images.load(bakePath,check_existing = True)
		img.name = imageName
		print(f"\tLoaded existing bake for {imageName}")
		skipBake = True
	if imageName in bpy.data.images:
		img = bpy.data.images[imageName]
		img.scale(imageXRes,imageYRes)
	else:
		img = bpy.data.images.new(imageName,imageXRes,imageYRes)
		
	img.colorspace_settings.name = "sRGB"
	
	if not skipBake:
		print("\tBaking Base Color...")
		bakeStartTime = time.time()
		textureNode = rootNodes.new('ShaderNodeTexImage')
		textureNode.name = 'BaseColor_Bake'
		textureNode.location = nodePos
		textureNode.image = img #Assign the image to the node
		
		if principledBSDFNode.inputs["Base Color"].is_linked:
			obj.select_set(False)
			normalBakeObj.hide_render = False	
			bpy.context.view_layer.objects.active = normalBakeObj#Switch to baking from flat plane
			normalBakeObj.select_set(True)
		
		#Bake settings
		bpy.context.scene.cycles.samples = STANDARD_SAMPLES
		bpy.context.scene.cycles.adaptive_min_samples = 0
		bpy.context.scene.cycles.bake_type = "DIFFUSE"
		bpy.context.scene.render.bake.use_pass_direct = False
		bpy.context.scene.render.bake.use_pass_indirect = False
		bpy.context.scene.render.bake.use_pass_color = True
		bpy.context.scene.render.bake.margin = MARGIN
		rootNodes.active = textureNode
		textureNode.select = True
		with stdout_redirected():
			bpy.ops.object.bake(type = "DIFFUSE",save_mode = "INTERNAL")
		
		print(f"\tBase Color bake took {int((time.time() - bakeStartTime)*1000)} ms.")
		if originalMetallicSocket != None:
			links.new(originalMetallicSocket,principledBSDFNode.inputs["Metallic"])
		if tempMetallicValue != None:
			nodes.remove(tempMetallicValue)
		
		if SAVE_RAW_MAPS:
			img.file_format = FILE_FORMAT
			img.filepath_raw = os.path.join(BAKE_OUTPUT_DIR,imageName+FILE_EXT)
			img.save()
		normalBakeObj.hide_render = True
		normalBakeObj.select_set(False)
		bpy.context.view_layer.objects.active = obj
		obj.select_set(True)
		nodePos[0] += 300
	
	#Bake normal ----------------------------------------------
	imageName = f"{textureSetName}_Normal"
	
	skipBake = False
	bakePath = os.path.join(BAKE_OUTPUT_DIR,imageName+FILE_EXT)
	if useExistingBakes and os.path.isfile(bakePath):
		img = bpy.data.images.load(bakePath,check_existing = True)
		img.name = imageName
		print(f"\tLoaded existing bake for {imageName}")
		skipBake = True
	if imageName in bpy.data.images:
		img = bpy.data.images[imageName]
		img.scale(imageXRes,imageYRes)
	else:
		img = bpy.data.images.new(imageName,imageXRes,imageYRes)
		
	img.colorspace_settings.name = "Non-Color"
	
	if not skipBake:
		print("\tBaking Normal...")#There's a very slight difference in brightness between baked and original, not exactly sure if it's fixable but the difference isn't noticable in game.
		obj.select_set(False)
		normalBakeObj.hide_render = False	
		bpy.context.view_layer.objects.active = normalBakeObj#Switch to baking from flat plane
		normalBakeObj.select_set(True)
		
		bakeStartTime = time.time()
		textureNode = rootNodes.new('ShaderNodeTexImage')
		textureNode.name = 'Normal_Bake'
		textureNode.location = nodePos
		textureNode.image = img #Assign the image to the node
		#Bake settings
		bpy.context.scene.cycles.samples = STANDARD_SAMPLES
		bpy.context.scene.cycles.adaptive_min_samples = 0
		bpy.context.scene.cycles.bake_type = "NORMAL"
		bpy.context.scene.render.bake.margin = MARGIN
		rootNodes.active = textureNode
		textureNode.select = True
		with stdout_redirected():
			bpy.ops.object.bake(type = "NORMAL",save_mode = "INTERNAL")
		
		print(f"\tNormal bake took {int((time.time() - bakeStartTime)*1000)} ms.")
		if SAVE_RAW_MAPS:	 
			img.file_format = FILE_FORMAT
			img.filepath_raw = os.path.join(BAKE_OUTPUT_DIR,imageName+FILE_EXT)
			img.save()
		normalBakeObj.hide_render = True
		normalBakeObj.select_set(False)
		bpy.context.view_layer.objects.active = obj
		obj.select_set(True)
		nodePos[0] += 300
	#Bake roughness ----------------------------------------------
	imageName = f"{textureSetName}_Roughness"
	
	skipBake = False
	bakePath = os.path.join(BAKE_OUTPUT_DIR,imageName+FILE_EXT)
	if useExistingBakes and os.path.isfile(bakePath):
		img = bpy.data.images.load(bakePath,check_existing = True)
		img.name = imageName
		print(f"\tLoaded existing bake for {imageName}")
		skipBake = True
	if imageName in bpy.data.images:
		img = bpy.data.images[imageName]
		img.scale(imageXRes,imageYRes)
	else:
		img = bpy.data.images.new(imageName,imageXRes,imageYRes)
	
	img.colorspace_settings.name = "Non-Color"
	
	if not skipBake:
		print("\tBaking Roughness...")
		bakeStartTime = time.time()
		textureNode = rootNodes.new('ShaderNodeTexImage')
		textureNode.name = 'Roughness_Bake'
		textureNode.location = nodePos
		textureNode.image = img #Assign the image to the node
		
		#Bake settings
		bpy.context.scene.cycles.samples = STANDARD_SAMPLES
		bpy.context.scene.cycles.adaptive_min_samples = 0
		bpy.context.scene.cycles.bake_type = "ROUGHNESS"
		bpy.context.scene.render.bake.margin = MARGIN
		rootNodes.active = textureNode
		textureNode.select = True
		with stdout_redirected():
			bpy.ops.object.bake(type = "ROUGHNESS",save_mode = "INTERNAL")
		
		print(f"\tRoughness bake took {int((time.time() - bakeStartTime)*1000)} ms.")
		if SAVE_RAW_MAPS:	 
			img.file_format = FILE_FORMAT
			img.filepath_raw = os.path.join(BAKE_OUTPUT_DIR,imageName+FILE_EXT)
			img.save()
		
		nodePos[0] += 300
	#Bake emission ----------------------------------------------
	imageName = f"{textureSetName}_Emissive"
	skipBake = False
	
	bakePath = os.path.join(BAKE_OUTPUT_DIR,imageName+FILE_EXT)
	if useExistingBakes and os.path.isfile(bakePath):
		img = bpy.data.images.load(bakePath,check_existing = True)
		img.name = imageName
		print(f"\tLoaded existing bake for {imageName}")
		skipBake = True
	if imageName in bpy.data.images:
		img = bpy.data.images[imageName]
		img.scale(imageXRes,imageYRes)
	else:
		img = bpy.data.images.new(imageName,imageXRes,imageYRes)
		
	img.colorspace_settings.name = "sRGB"
	if not skipBake:
		print("\tBaking Emissive...")
		bakeStartTime = time.time()
		textureNode = rootNodes.new('ShaderNodeTexImage')
		textureNode.name = 'Emissive_Bake'
		textureNode.location = nodePos
		textureNode.image = img #Assign the image to the node
		
		#Bake settings
	
		bpy.context.scene.cycles.samples = STANDARD_SAMPLES
		bpy.context.scene.cycles.adaptive_min_samples = 0
		bpy.context.scene.cycles.bake_type = "EMIT"
		bpy.context.scene.render.bake.margin = MARGIN
		rootNodes.active = textureNode
		textureNode.select = True
		with stdout_redirected():
			bpy.ops.object.bake(type = "EMIT",save_mode = "INTERNAL")
		
		print(f"\tEmissive bake took {int((time.time() - bakeStartTime)*1000)} ms.")
		if SAVE_RAW_MAPS:	 
			img.file_format = FILE_FORMAT
			img.filepath_raw = os.path.join(BAKE_OUTPUT_DIR,imageName+FILE_EXT)
			img.save()
		
		nodePos[0] += 300
	#Bake AO ----------------------------------------------
	imageName = f"{textureSetName}_AO"
	
	skipBake = False
	bakePath = os.path.join(BAKE_OUTPUT_DIR,imageName+FILE_EXT)
	if useExistingBakes and os.path.isfile(bakePath):
		img = bpy.data.images.load(bakePath,check_existing = True)
		img.name = imageName
		print(f"\tLoaded existing bake for {imageName}")
		skipBake = True
	if imageName in bpy.data.images:
		img = bpy.data.images[imageName]
		img.scale(imageXRes,imageYRes)
	else:
		img = bpy.data.images.new(imageName,imageXRes,imageYRes)
		
	img.colorspace_settings.name = "Non-Color"
	if not skipBake:
		if bakeAO:
			print("\tBaking Ambient Occlusion...")
			bakeStartTime = time.time()
			textureNode = rootNodes.new('ShaderNodeTexImage')
			textureNode.name = 'AO_Bake'
			textureNode.location = nodePos
			textureNode.image = img #Assign the image to the node
			
			#Bake settings
			bpy.context.scene.cycles.samples = AO_SAMPLES
			if imageXRes >= 4096 or imageYRes >= 4096:
				bpy.context.scene.cycles.adaptive_min_samples = AO_SAMPLES//4
			else:
				bpy.context.scene.cycles.adaptive_min_samples = AO_SAMPLES//2
			bpy.context.scene.cycles.bake_type = "AO"
			bpy.context.scene.render.bake.margin = MARGIN
			rootNodes.active = textureNode
			textureNode.select = True
			with stdout_redirected():
				bpy.ops.object.bake(type = "AO",save_mode = "INTERNAL")
			
			print(f"\tAmbient Occlusion bake took {int((time.time() - bakeStartTime)*1000)} ms.")
			if SAVE_RAW_MAPS:
				img.file_format = FILE_FORMAT
				img.filepath_raw = os.path.join(BAKE_OUTPUT_DIR,imageName+FILE_EXT)
				img.save()
		else:
			print("\tSkipping Ambient Occlusion bake because it is disabled.")
			#Set image to fully white
			pixels = [1.0] * (imageXRes * imageYRes * 4)
			img.pixels.foreach_set(pixels)
	
	
		nodePos[0] += 300
	
	#Bake Metallic ----------------------------------------------
	imageName = f"{textureSetName}_Metallic"
	
	skipBake = False
	bakePath = os.path.join(BAKE_OUTPUT_DIR,imageName+FILE_EXT)
	if useExistingBakes and os.path.isfile(bakePath):
		img = bpy.data.images.load(bakePath,check_existing = True)
		img.name = imageName
		print(f"\tLoaded existing bake for {imageName}")
		skipBake = True
	if imageName in bpy.data.images:
		img = bpy.data.images[imageName]
		img.scale(imageXRes,imageYRes)
	else:
		img = bpy.data.images.new(imageName,imageXRes,imageYRes)
		
	img.colorspace_settings.name = "Non-Color"
	metallicValue = None
	
	if not skipBake:
		if principledBSDFNode != None:
			oldRoughnessLink = None if not principledBSDFNode.inputs["Roughness"].is_linked else principledBSDFNode.inputs["Roughness"].links[0].from_socket
			if originalMetallicSocket != None:
				links.new(originalMetallicSocket,principledBSDFNode.inputs["Metallic"])
			if principledBSDFNode.inputs["Metallic"].is_linked:
				#print("DEBUG Linked metallic node to roughness")
				links.new(principledBSDFNode.inputs["Metallic"].links[0].from_socket,principledBSDFNode.inputs["Roughness"])
			else:
					#print("DEBUG No metallic value connected, created new value node linked to roughness")
					metallicValue = nodes.new("ShaderNodeValue")
					metallicValue.name = "Metallic Value"
					metallicValue.outputs["Value"].default_value = principledBSDFNode.inputs["Metallic"].default_value
					links.new(metallicValue.outputs["Value"],principledBSDFNode.inputs["Roughness"])
	   
			print("\tBaking Metallic...")
			bakeStartTime = time.time()
			textureNode = rootNodes.new('ShaderNodeTexImage')
			textureNode.name = 'Metallic_Bake'
			textureNode.location = nodePos
			textureNode.image = img #Assign the image to the node
			
			
			#Bake settings
			bpy.context.scene.cycles.samples = STANDARD_SAMPLES
			bpy.context.scene.cycles.adaptive_min_samples = 0
			bpy.context.scene.cycles.bake_type = "ROUGHNESS"
			bpy.context.scene.render.bake.margin = MARGIN
			rootNodes.active = textureNode
			textureNode.select = True
			with stdout_redirected():
				bpy.ops.object.bake(type = "ROUGHNESS",save_mode = "INTERNAL")
			print(f"\tMetallic bake took {int((time.time() - bakeStartTime)*1000)} ms.")
			
			#Relink roughness node to whatever it was before changing it
			if oldRoughnessLink != None:
				#print("DEBUG Connected old roughness link back to roughness")
				links.new(oldRoughnessLink,principledBSDFNode.inputs["Roughness"])
			else:
				#print("DEBUG Unlinked roughness")
				links.remove(principledBSDFNode.inputs["Roughness"].links[0])
			if metallicValue != None:
				#print("DEBUG Removed metallic value node")
				nodes.remove(metallicValue)
		else:
			print("\tSkipping Metallic bake due to missing Principled BSDF Node.")
		
		if SAVE_RAW_MAPS:	 
			img.file_format = FILE_FORMAT
			img.filepath_raw = os.path.join(BAKE_OUTPUT_DIR,imageName+FILE_EXT)
			img.save()
		
		
		nodePos[0] += 300
	#Bake Alpha ----------------------------------------------
	imageName = f"{textureSetName}_Opacity"
	
	skipBake = False
	bakePath = os.path.join(BAKE_OUTPUT_DIR,imageName+FILE_EXT)
	if useExistingBakes and os.path.isfile(bakePath):
		img = bpy.data.images.load(bakePath,check_existing = True)
		img.name = imageName
		print(f"\tLoaded existing bake for {imageName}")
		skipBake = True
	if imageName in bpy.data.images:
		img = bpy.data.images[imageName]
		img.scale(imageXRes,imageYRes)
	else:
		img = bpy.data.images.new(imageName,imageXRes,imageYRes)
		
	img.colorspace_settings.name = "Non-Color"
	if not skipBake:
		if principledBSDFNode != None:
			
			obj.select_set(False)
			normalBakeObj.hide_render = False	
			bpy.context.view_layer.objects.active = normalBakeObj#Switch to baking from flat plane
			normalBakeObj.select_set(True)
			
			alphaValue = None
			emissionStrengthValue = None
			oldEmissionColorLink = None if not principledBSDFNode.inputs["Emission Color"].is_linked else principledBSDFNode.inputs["Emission Color"].links[0].from_socket
			oldEmissionStrengthLink = None if not principledBSDFNode.inputs["Emission Strength"].is_linked else principledBSDFNode.inputs["Emission Strength"].links[0].from_socket
			if alphaLink:
				#print("DEBUG Linked alpha input to roughness")
				links.new(alphaLink,principledBSDFNode.inputs["Emission Color"])
			else:
					#print("DEBUG Created new alpha value and linked to roughness")
					alphaValue = nodes.new("ShaderNodeValue")
					alphaValue.name = "Alpha Value"
					alphaValue.outputs["Value"].default_value = principledBSDFNode.inputs["Alpha"].default_value
					links.new(alphaValue.outputs["Value"],principledBSDFNode.inputs["Emission Color"])
			emissionStrengthValue = nodes.new("ShaderNodeValue")
			emissionStrengthValue.name = "Emission Strength Value"
			emissionStrengthValue.outputs["Value"].default_value = 1.0
			links.new(emissionStrengthValue.outputs["Value"],principledBSDFNode.inputs["Emission Strength"])
			print("\tBaking Opacity...")
			bakeStartTime = time.time()
			textureNode = rootNodes.new('ShaderNodeTexImage')
			textureNode.name = 'Opacity_Bake'
			textureNode.location = nodePos
			textureNode.image = img #Assign the image to the node
			
			#Bake settings
			bpy.context.scene.cycles.samples = STANDARD_SAMPLES
			bpy.context.scene.cycles.adaptive_min_samples = 0
			bpy.context.scene.cycles.bake_type = "EMIT"
			bpy.context.scene.render.bake.margin = MARGIN
			rootNodes.active = textureNode
			
			textureNode.select = True
			#print(f"Baking from {bpy.context.view_layer.objects.active.name}")
			with stdout_redirected():
				bpy.ops.object.bake(type = "EMIT",save_mode = "INTERNAL")
			print(f"\tOpacity bake took {int((time.time() - bakeStartTime)*1000)} ms.")
			
			#Relink roughness node to whatever it was before changing it
			if oldEmissionColorLink != None:
				#print("DEBUG Linked old emission color to emission color")
				links.new(oldEmissionColorLink,principledBSDFNode.inputs["Emission Color"])
			else:
				#print("DEBUG emission color")
				links.remove(principledBSDFNode.inputs["Emission Color"].links[0])
			
			if oldEmissionStrengthLink != None:
				#print("DEBUG Linked old emission strength socket to emission strength")
				links.new(oldEmissionStrengthLink,principledBSDFNode.inputs["Emission Strength"])
			else:
				#print("DEBUG Unlinked emission strength")
				links.remove(principledBSDFNode.inputs["Emission Strength"].links[0])
			
			if alphaLink != None:#Relink alpha values to material
				#print("DEBUG Relinked alpha socket")
				links.new(alphaLink,principledBSDFNode.inputs["Alpha"])
			
			if emissionStrengthValue != None:
				#print("DEBUG Removed alpha value node")
				nodes.remove(emissionStrengthValue)
			
			
			if alphaValue != None:
				#print("DEBUG Removed alpha value node")
				nodes.remove(alphaValue)
				
			normalBakeObj.hide_render = True
			normalBakeObj.select_set(False)
			bpy.context.view_layer.objects.active = obj
			obj.select_set(True)
		else:
			#Set image to fully white
			pixels = [1.0] * (imageXRes * imageYRes * 4)
			img.pixels.foreach_set(pixels)
			print("\tSkipping Opacity bake due to missing Principled BSDF Node.")
		
		if SAVE_RAW_MAPS:	 
			img.file_format = FILE_FORMAT
			img.filepath_raw = os.path.join(BAKE_OUTPUT_DIR,imageName+FILE_EXT)
			img.save()
		
		nodePos[0] += 300
	
