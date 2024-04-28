import bpy
import os
def newALBDNode (nodeTree,textureType,texturePath,currentPos,nodeBSDF):
	imageNode = nodeTree.nodes.new('ShaderNodeTexImage')
	imageNode.label = textureType
	texture = bpy.data.images.get(os.path.split(texturePath)[1],None)
	if texture == None:
		imageNode.image = bpy.data.images.load(texturePath)
		
	else:
		imageNode.image = texture
	imageNode.image.colorspace_settings.name = "sRGB"
	imageNode.image.alpha_mode = "CHANNEL_PACKED"
	imageNode.location = currentPos
	
	nodeTree.links.new(imageNode.outputs["Color"],nodeBSDF.inputs["Base Color"])#Color > Color
	
	if nodeBSDF.name == "Principled BSDF":
		invertNode = nodeTree.nodes.new('ShaderNodeInvert')
		invertNode.location = (0,currentPos[1])		
		nodeTree.links.new(imageNode.outputs["Alpha"],invertNode.inputs["Color"])#Dielectric > Invert
		nodeTree.links.new(invertNode.outputs["Color"],nodeBSDF.inputs["Metallic"])#Inverted Dielectric > Metallic
def newALBMNode (nodeTree,textureType,texturePath,currentPos,nodeBSDF):
	imageNode = nodeTree.nodes.new('ShaderNodeTexImage')
	imageNode.label = textureType
	texture = bpy.data.images.get(os.path.split(texturePath)[1],None)
	if texture == None:
		imageNode.image = bpy.data.images.load(texturePath)
		
	else:
		imageNode.image = texture
	imageNode.image.colorspace_settings.name = "sRGB"
	imageNode.image.alpha_mode = "CHANNEL_PACKED"
	imageNode.location = currentPos
	
	nodeTree.links.new(imageNode.outputs["Color"],nodeBSDF.inputs["Base Color"])#Color > Color
	
	if nodeBSDF.name == "Principled BSDF":
		nodeTree.links.new(imageNode.outputs["Alpha"],nodeBSDF.inputs["Metallic"])
def newALBANode (nodeTree,textureType,texturePath,currentPos,nodeBSDF):
	imageNode = nodeTree.nodes.new('ShaderNodeTexImage')
	imageNode.label = textureType
	texture = bpy.data.images.get(os.path.split(texturePath)[1],None)
	if texture == None:
		imageNode.image = bpy.data.images.load(texturePath)
	else:
		imageNode.image = texture
	imageNode.image.colorspace_settings.name = "sRGB"
	imageNode.location = currentPos
	nodeTree.links.new(imageNode.outputs["Color"],nodeBSDF.inputs["Base Color"])#Color > Color
	if nodeBSDF.name == "Principled BSDF":
		nodeTree.links.new(imageNode.outputs["Alpha"],nodeBSDF.inputs["Alpha"])#Alpha > Alpha

def newALBNode (nodeTree,textureType,texturePath,currentPos,nodeBSDF):
	imageNode = nodeTree.nodes.new('ShaderNodeTexImage')
	imageNode.label = textureType
	texture = bpy.data.images.get(os.path.split(texturePath)[1],None)
	if texture == None:
		imageNode.image = bpy.data.images.load(texturePath)
	else:
		imageNode.image = texture
	imageNode.image.colorspace_settings.name = "sRGB"
	imageNode.image.alpha_mode = "CHANNEL_PACKED"
	imageNode.location = currentPos
	nodeTree.links.new(imageNode.outputs["Color"],nodeBSDF.inputs["Base Color"])

def newNRMRNode (nodeTree,textureType,texturePath,currentPos,nodeBSDF):
	imageNode = nodeTree.nodes.new('ShaderNodeTexImage')
	imageNode.label = textureType
	texture = bpy.data.images.get(os.path.split(texturePath)[1],None)
	if texture == None:
		imageNode.image = bpy.data.images.load(texturePath)
	else:
		imageNode.image = texture
	imageNode.image.colorspace_settings.name = "Non-Color"
	imageNode.image.alpha_mode = "CHANNEL_PACKED"
	imageNode.location = currentPos
	
	normalMapNode = nodeTree.nodes.new('ShaderNodeNormalMap')
	normalMapNode.location = (0,currentPos[1])
	
	nodeTree.links.new(imageNode.outputs["Color"],normalMapNode.inputs["Color"])#Normal Color > Normal Map Node
	nodeTree.links.new(normalMapNode.outputs["Normal"],nodeBSDF.inputs["Normal"])#Normal Map Node > Normal Map
	nodeTree.links.new(imageNode.outputs["Alpha"],nodeBSDF.inputs["Roughness"])#Roughness > Roughness

def newNAMNode (nodeTree,textureType,texturePath,currentPos,nodeBSDF):
	imageNode = nodeTree.nodes.new('ShaderNodeTexImage')
	imageNode.label = textureType
	texture = bpy.data.images.get(os.path.split(texturePath)[1],None)
	if texture == None:
		imageNode.image = bpy.data.images.load(texturePath)
	else:
		imageNode.image = texture
	imageNode.image.colorspace_settings.name = "Non-Color"
	imageNode.image.alpha_mode = "CHANNEL_PACKED"
	imageNode.location = currentPos
	
	normalMapNode = nodeTree.nodes.new('ShaderNodeNormalMap')
	normalMapNode.location = (0,currentPos[1])
	
	nodeTree.links.new(imageNode.outputs["Color"],normalMapNode.inputs["Color"])#Normal Color > Normal Map Node
	nodeTree.links.new(normalMapNode.outputs["Normal"],nodeBSDF.inputs["Normal"])#Normal Map Node > Normal Map
	nodeTree.links.new(imageNode.outputs["Alpha"],nodeBSDF.inputs["Alpha"])#Alpha > Alpha
def newNRRTNode (nodeTree,textureType,texturePath,currentPos,nodeBSDF):
	imageNode = nodeTree.nodes.new('ShaderNodeTexImage')
	imageNode.label = textureType
	texture = bpy.data.images.get(os.path.split(texturePath)[1],None)
	if texture == None:
		imageNode.image = bpy.data.images.load(texturePath)
	else:
		imageNode.image = texture
	imageNode.image.colorspace_settings.name = "Non-Color"
	imageNode.image.alpha_mode = "CHANNEL_PACKED"
	imageNode.location = currentPos
	
	
	separateNode = nodeTree.nodes.new('ShaderNodeSeparateRGB')
	separateNode.location = (-100,currentPos[1])
	
	nodeTree.links.new(imageNode.outputs["Color"],separateNode.inputs["Image"])# NRRT Color > Separate RGB
	
	
	combineNode = nodeTree.nodes.new('ShaderNodeCombineRGB')
	combineNode.location = (100,currentPos[1])
	combineNode.inputs["B"].default_value = 1.0#Set blue channel
	
	nodeTree.links.new(separateNode.outputs["R"],nodeBSDF.inputs["Roughness"])# Roughness > Roughness
	nodeTree.links.new(imageNode.outputs["Alpha"],combineNode.inputs["R"])# Normal X > Color Normal X
	nodeTree.links.new(separateNode.outputs["G"],combineNode.inputs["G"])# Normal Y > Color Normal Y
	#nodeTree.links.new(separateNode.outputs[2],nodeBSDF.inputs[1])# Translucency > Subsurface

	normalMapNode = nodeTree.nodes.new('ShaderNodeNormalMap')
	normalMapNode.location = (100,currentPos[1]-200)
	normalMapNode.inputs["Strength"].default_value = 0.4
	
	nodeTree.links.new(combineNode.outputs["Image"],normalMapNode.inputs["Color"])#Normal Color > Normal Map Node
	nodeTree.links.new(normalMapNode.outputs["Normal"],nodeBSDF.inputs["Normal"])#Normal Map Node > Normal Map
	
def newALPNode (nodeTree,textureType,texturePath,currentPos,nodeBSDF):
	imageNode = nodeTree.nodes.new('ShaderNodeTexImage')
	imageNode.label = textureType
	texture = bpy.data.images.get(os.path.split(texturePath)[1],None)
	if texture == None:
		imageNode.image = bpy.data.images.load(texturePath)
	else:
		imageNode.image = texture
	imageNode.image.colorspace_settings.name = "Non-Color"
	imageNode.location = currentPos
	
	bwNode = nodeTree.nodes.new('ShaderNodeRGBToBW')
	bwNode.location = (0,currentPos[1])
	nodeTree.links.new(imageNode.outputs["Color"],bwNode.inputs["Color"])
	nodeTree.links.new(bwNode.outputs["Val"],nodeBSDF.inputs["Alpha"])#Alpha > Alpha
def newEMINode (nodeTree,textureType,texturePath,currentPos,nodeBSDF):
	imageNode = nodeTree.nodes.new('ShaderNodeTexImage')
	imageNode.label = textureType
	texture = bpy.data.images.get(os.path.split(texturePath)[1],None)
	if texture == None:
		imageNode.image = bpy.data.images.load(texturePath)
	else:
		imageNode.image = texture
	imageNode.location = currentPos

def newATOSNode (nodeTree,textureType,texturePath,currentPos,nodeBSDF):
	imageNode = nodeTree.nodes.new('ShaderNodeTexImage')
	imageNode.label = textureType
	texture = bpy.data.images.get(os.path.split(texturePath)[1],None)
	if texture == None:
		imageNode.image = bpy.data.images.load(texturePath)
	else:
		imageNode.image = texture
	imageNode.image.colorspace_settings.name = "Non-Color"
	imageNode.image.alpha_mode = "CHANNEL_PACKED"
	imageNode.location = currentPos
	
	
	separateNode = nodeTree.nodes.new('ShaderNodeSeparateRGB')
	separateNode.location = (-100,currentPos[1])
	
	nodeTree.links.new(imageNode.outputs["Color"],separateNode.inputs["Image"])# ATOS Color > Separate RGB
	nodeTree.links.new(separateNode.outputs["R"],nodeBSDF.inputs["Alpha"])# Red > Alpha

def newUNKNNode (nodeTree,textureType,texturePath,currentPos,nodeBSDF):
	imageNode = nodeTree.nodes.new('ShaderNodeTexImage')
	imageNode.label = textureType
	texture = bpy.data.images.get(os.path.split(texturePath)[1],None)
	if texture == None:
		imageNode.image = bpy.data.images.load(texturePath)
	else:
		imageNode.image = texture
	imageNode.image.colorspace_settings.name = "Non-Color"
	imageNode.image.alpha_mode = "CHANNEL_PACKED"
	imageNode.location = currentPos

nodeDict = {
	"ALBD":newALBDNode,
	"ALBM":newALBMNode,
	"ALBA":newALBANode,
	"ALB":newALBNode,
	"NRMR":newNRMRNode,
	"NRRT":newNRRTNode,
	"ALP":newALPNode,
	"EMI":newEMINode,
	"ATOS":newATOSNode,
	"NAM":newNAMNode,
	"UNKN":newUNKNNode,
	
	}
def createTextureNode(nodeTree,nodeType,textureType,texturePath,currentPos,nodeBSDF):
	#print(nodeType)
	#print(textureType)
	#print(texturePath)
	nodeDict[nodeType](nodeTree,textureType,texturePath,currentPos,nodeBSDF)
	