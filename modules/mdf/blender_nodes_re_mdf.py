import bpy
import os
from .blender_re_mdf import colorPropertySet
from .blender_re_mesh_mdf import albedoTypeSet

from mathutils import Vector
#Hair meshes use ambient occlusion with the second UV map
legacyUV2HairOcclusionList = set(["RE2","RE2RT","RE3","RE3RT","RE7RT","DMC5"])

def addLoc(node,delta):#Just to shorten what would otherwise be a long line
	return (node.location[0] + delta[0],node.location[1] + delta[0])

def getColorNodeGroup(nodeTree):#No RGBA node in shader editor so a custom group is needed
	if "ColorNodeGroup" in bpy.data.node_groups:
		nodeGroup = bpy.data.node_groups["ColorNodeGroup"]
	else:
		nodeGroup = bpy.data.node_groups.new(type="ShaderNodeTree", name="ColorNodeGroup")
	
		if bpy.app.version < (4,0,0):
			nodeGroup.inputs.new("NodeSocketColor","Color")
			nodeGroup.inputs.new("NodeSocketFloat","Alpha")
		else:
			nodeGroup.interface.new_socket(name="Color",description="",in_out ="INPUT", socket_type="NodeSocketColor")
			nodeGroup.interface.new_socket(name="Alpha",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
		
		inNode = nodeGroup.nodes.new('NodeGroupInput')
		
		outNode = nodeGroup.nodes.new('NodeGroupOutput')
		if bpy.app.version < (4,0,0):
			nodeGroup.outputs.new('NodeSocketColor', 'Color')
			nodeGroup.outputs.new('NodeSocketFloat', 'Alpha')
		else:
			nodeGroup.interface.new_socket(name="Color",description="",in_out ="OUTPUT", socket_type="NodeSocketColor")
			nodeGroup.interface.new_socket(name="Alpha",description="",in_out ="OUTPUT", socket_type="NodeSocketFloat")
		nodeGroup.links.new(inNode.outputs["Color"],outNode.inputs["Color"])
		nodeGroup.links.new(inNode.outputs["Alpha"],outNode.inputs["Alpha"])
	
	nodeGroupNode = nodeTree.nodes.new("ShaderNodeGroup")
	nodeGroupNode.node_tree = nodeGroup
	
	return nodeGroupNode

def getImagePassThroughNodeGroup(nodeTree):#Same as color node group but with vector input/output, used for texture array selection
	if "ImagePassThroughNodeGroup" in bpy.data.node_groups:
		nodeGroup = bpy.data.node_groups["ImagePassThroughNodeGroup"]
	else:
		nodeGroup = bpy.data.node_groups.new(type="ShaderNodeTree", name="ImagePassThroughNodeGroup")
	
		if bpy.app.version < (4,0,0):
			nodeGroup.inputs.new("NodeSocketColor","Color")
			nodeGroup.inputs.new("NodeSocketFloat","Alpha")
			nodeGroup.inputs.new("NodeSocketVector","Vector")
		else:
			nodeGroup.interface.new_socket(name="Color",description="",in_out ="INPUT", socket_type="NodeSocketColor")
			nodeGroup.interface.new_socket(name="Alpha",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="Vector",description="",in_out ="INPUT", socket_type="NodeSocketVector")
		
		inNode = nodeGroup.nodes.new('NodeGroupInput')
		
		outNode = nodeGroup.nodes.new('NodeGroupOutput')
		if bpy.app.version < (4,0,0):
			nodeGroup.outputs.new('NodeSocketColor', 'Color')
			nodeGroup.outputs.new('NodeSocketFloat', 'Alpha')
			nodeGroup.outputs.new('NodeSocketVector', 'Vector')
		else:
			nodeGroup.interface.new_socket(name="Color",description="",in_out ="OUTPUT", socket_type="NodeSocketColor")
			nodeGroup.interface.new_socket(name="Alpha",description="",in_out ="OUTPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="Vector",description="",in_out ="OUTPUT", socket_type="NodeSocketVector")
		nodeGroup.links.new(inNode.outputs["Color"],outNode.inputs["Color"])
		nodeGroup.links.new(inNode.outputs["Alpha"],outNode.inputs["Alpha"])
		nodeGroup.links.new(inNode.outputs["Vector"],outNode.inputs["Vector"])
	
	nodeGroupNode = nodeTree.nodes.new("ShaderNodeGroup")
	nodeGroupNode.node_tree = nodeGroup
	
	return nodeGroupNode

def getVec4NodeGroup(nodeTree):
	if "Vec4NodeGroup" in bpy.data.node_groups:
		nodeGroup = bpy.data.node_groups["Vec4NodeGroup"]
	else:
		nodeGroup = bpy.data.node_groups.new(type="ShaderNodeTree", name="Vec4NodeGroup")
	
		if bpy.app.version < (4,0,0):
			nodeGroup.inputs.new("NodeSocketFloat","X")
			nodeGroup.inputs.new("NodeSocketFloat","Y")
			nodeGroup.inputs.new("NodeSocketFloat","Z")
			nodeGroup.inputs.new("NodeSocketFloat","W")
		else:
			nodeGroup.interface.new_socket(name="X",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="Y",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="Z",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="W",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
		inNode = nodeGroup.nodes.new('NodeGroupInput')
		
		outNode = nodeGroup.nodes.new('NodeGroupOutput')
		if bpy.app.version < (4,0,0):
			nodeGroup.outputs.new('NodeSocketFloat', "X")
			nodeGroup.outputs.new('NodeSocketFloat', "Y")
			nodeGroup.outputs.new('NodeSocketFloat', "Z")
			nodeGroup.outputs.new('NodeSocketFloat', "W")
		else:
			nodeGroup.interface.new_socket(name="X",description="",in_out ="OUTPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="Y",description="",in_out ="OUTPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="Z",description="",in_out ="OUTPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="W",description="",in_out ="OUTPUT", socket_type="NodeSocketFloat")
		
		nodeGroup.links.new(inNode.outputs["X"],outNode.inputs["X"])
		nodeGroup.links.new(inNode.outputs["Y"],outNode.inputs["Y"])
		nodeGroup.links.new(inNode.outputs["Z"],outNode.inputs["Z"])
		nodeGroup.links.new(inNode.outputs["W"],outNode.inputs["W"])
	
	nodeGroupNode = nodeTree.nodes.new("ShaderNodeGroup")
	nodeGroupNode.node_tree = nodeGroup
	
	return nodeGroupNode

def getBentNormalNodeGroup(nodeTree):
	if "BentNormalNodeGroup" in bpy.data.node_groups:
		nodeGroup = bpy.data.node_groups["BentNormalNodeGroup"]
	else:
		nodeGroup = bpy.data.node_groups.new(type="ShaderNodeTree", name="BentNormalNodeGroup")
		nodes = nodeGroup.nodes
		links = nodeGroup.links
		if bpy.app.version < (4,0,0):
			nodeGroup.inputs.new("NodeSocketFloat","Color")
			nodeGroup.inputs.new("NodeSocketFloat","Alpha")
		else:
			nodeGroup.interface.new_socket(name="Color",description="",in_out ="INPUT", socket_type="NodeSocketColor")
			nodeGroup.interface.new_socket(name="Alpha",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
		inNode = nodeGroup.nodes.new('NodeGroupInput')
		currentLoc = [300,0]
		separateRGBNode = nodes.new("ShaderNodeSeparateRGB")
		separateRGBNode.location = currentLoc
		currentLoc[0] += 300
		links.new(inNode.outputs["Color"],separateRGBNode.inputs["Image"])
		
		mapRangeYNode = nodes.new("ShaderNodeMapRange")
		mapRangeYNode.location = currentLoc
		mapRangeYNode.inputs["From Min"].default_value = 0.0
		mapRangeYNode.inputs["From Max"].default_value = 1.0
		mapRangeYNode.inputs["To Min"].default_value = -1.0
		mapRangeYNode.inputs["To Max"].default_value = 1.0
		
		links.new(separateRGBNode.outputs["G"],mapRangeYNode.inputs["Value"])
		
		currentLoc[0] += 300
		
		multNode0Y = nodes.new("ShaderNodeMath")
		multNode0Y.location = currentLoc
		multNode0Y.operation = "MULTIPLY"
		
		links.new(mapRangeYNode.outputs["Result"],multNode0Y.inputs[0])
		links.new(mapRangeYNode.outputs["Result"],multNode0Y.inputs[1])
		
		signNodeY = nodes.new("ShaderNodeMath")
		signNodeY.location = (currentLoc[0],currentLoc[1] - 300)
		signNodeY.operation = "SIGN"
		links.new(mapRangeYNode.outputs["Result"],signNodeY.inputs[0])
		
		currentLoc[0] += 300
		
		multNode1Y = nodes.new("ShaderNodeMath")
		multNode1Y.location = currentLoc
		multNode1Y.operation = "MULTIPLY"
		
		links.new(multNode0Y.outputs["Value"],multNode1Y.inputs[0])
		links.new(signNodeY.outputs["Value"],multNode1Y.inputs[1])
		
		currentLoc[0] += 300
		
		multNode2Y = nodes.new("ShaderNodeMath")
		multNode2Y.location = currentLoc
		multNode2Y.operation = "MULTIPLY"
		
		links.new(multNode1Y.outputs["Value"],multNode2Y.inputs[0])
		links.new(multNode1Y.outputs["Value"],multNode2Y.inputs[1])
		
		
		currentLoc[0] += 300
		
		addXYNode = nodes.new("ShaderNodeMath")
		addXYNode.location = currentLoc
		addXYNode.operation = "ADD"
		
		links.new(multNode2Y.outputs["Value"],addXYNode.inputs[0])
		
		currentLoc[0] += 300
		
		subNode = nodes.new("ShaderNodeMath")
		subNode.location = currentLoc
		subNode.operation = "SUBTRACT"
		subNode.inputs[0].default_value = 1.0
		links.new(addXYNode.outputs["Value"],subNode.inputs[1])
		
		currentLoc[0] += 300
		
		sqrRootNode = nodes.new("ShaderNodeMath")
		sqrRootNode.location = currentLoc
		sqrRootNode.operation = "SQRT"
		links.new(subNode.outputs["Value"],sqrRootNode.inputs[0])
		
		currentLoc[0] += 300
		
		combineXYZNode = nodes.new("ShaderNodeCombineXYZ")
		combineXYZNode.location = currentLoc
		links.new(multNode1Y.outputs["Value"],combineXYZNode.inputs["X"])
		links.new(sqrRootNode.outputs["Value"],combineXYZNode.inputs["Z"])
		
		currentLoc[0] += 300
		
		vectorRotateNode = nodes.new("ShaderNodeVectorRotate")
		vectorRotateNode.location = currentLoc
		vectorRotateNode.inputs["Angle"].default_value = 0.785398#45 degrees
		links.new(combineXYZNode.outputs["Vector"],vectorRotateNode.inputs["Vector"])
		
		currentLoc[0] += 300
		
		mapRangeVectorNode = nodes.new("ShaderNodeMapRange")
		mapRangeVectorNode.location = currentLoc
		mapRangeVectorNode.data_type = "FLOAT_VECTOR"
		mapRangeVectorNode.clamp = False
		mapRangeVectorNode.inputs[7].default_value = Vector((-1.0,-1.0,-1.0))
		mapRangeVectorNode.inputs[8].default_value =  Vector((1.0,1.0,1.0))
		mapRangeVectorNode.inputs[9].default_value =  Vector((0.0,0.0,0.0))
		mapRangeVectorNode.inputs[10].default_value =  Vector((1.0,1.0,1.0))
		
		links.new(vectorRotateNode.outputs["Vector"],mapRangeVectorNode.inputs["Vector"])
		
		
		currentLoc = [600,-400]
		
		mapRangeXNode = nodes.new("ShaderNodeMapRange")
		mapRangeXNode.location = currentLoc
		mapRangeXNode.inputs["From Min"].default_value = 0.0
		mapRangeXNode.inputs["From Max"].default_value = 1.0
		mapRangeXNode.inputs["To Min"].default_value = 1.0
		mapRangeXNode.inputs["To Max"].default_value = -1.0
		
		links.new(inNode.outputs["Alpha"],mapRangeXNode.inputs["Value"])
		
		currentLoc[0] += 300
		
		multNode0X = nodes.new("ShaderNodeMath")
		multNode0X.location = currentLoc
		multNode0X.operation = "MULTIPLY"
		
		links.new(mapRangeXNode.outputs["Result"],multNode0X.inputs[0])
		links.new(mapRangeXNode.outputs["Result"],multNode0X.inputs[1])
		
		signNodeX = nodes.new("ShaderNodeMath")
		signNodeX.location = (currentLoc[0],currentLoc[1] - 300)
		signNodeX.operation = "SIGN"
		links.new(mapRangeXNode.outputs["Result"],signNodeX.inputs[0])
		
		currentLoc[0] += 300
		
		multNode1X = nodes.new("ShaderNodeMath")
		multNode1X.location = currentLoc
		multNode1X.operation = "MULTIPLY"
		
		links.new(multNode0X.outputs["Value"],multNode1X.inputs[0])
		links.new(signNodeX.outputs["Value"],multNode1X.inputs[1])
		
		links.new(multNode1X.outputs["Value"],combineXYZNode.inputs["Y"])
		
		currentLoc[0] += 300
		
		multNode2X = nodes.new("ShaderNodeMath")
		multNode2X.location = currentLoc
		multNode2X.operation = "MULTIPLY"
		
		links.new(multNode1X.outputs["Value"],multNode2X.inputs[0])
		links.new(multNode1X.outputs["Value"],multNode2X.inputs[1])
		links.new(multNode2X.outputs["Value"],addXYNode.inputs[1])
		
		currentLoc[0] += 300
		
		outNode = nodeGroup.nodes.new('NodeGroupOutput')
		if bpy.app.version < (4,0,0):
			nodeGroup.outputs.new('NodeSocketColor', "Color")
			nodeGroup.outputs.new('NodeSocketFloat', "Roughness")
			nodeGroup.outputs.new('NodeSocketFloat', "BlueChannel")
			
		else:
			nodeGroup.interface.new_socket(name="Color",description="",in_out ="OUTPUT", socket_type="NodeSocketColor")
			nodeGroup.interface.new_socket(name="Roughness",description="",in_out ="OUTPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="BlueChannel",description="",in_out ="OUTPUT", socket_type="NodeSocketFloat")
		
		links.new(mapRangeVectorNode.outputs["Vector"],outNode.inputs["Color"])
		links.new(separateRGBNode.outputs["R"],outNode.inputs["Roughness"])
		links.new(separateRGBNode.outputs["B"],outNode.inputs["BlueChannel"])

	nodeGroupNode = nodeTree.nodes.new("ShaderNodeGroup")
	nodeGroupNode.node_tree = nodeGroup
	
	return nodeGroupNode

def getDualUVMappingNodeGroup(nodeTree):
	if "DualUVMappingNodeGroup" in bpy.data.node_groups:
		nodeGroup = bpy.data.node_groups["DualUVMappingNodeGroup"]
	else:
		nodeGroup = bpy.data.node_groups.new(type="ShaderNodeTree", name="DualUVMappingNodeGroup")
		nodes = nodeGroup.nodes
		links = nodeGroup.links
		if bpy.app.version < (4,0,0):
			nodeGroup.inputs.new("NodeSocketVector","UV1")
			nodeGroup.inputs.new("NodeSocketVector","UV2")
			nodeGroup.inputs.new("NodeSocketFloat","UseSecondaryUV")
			nodeGroup.inputs.new("NodeSocketFloat","OffsetX")
			nodeGroup.inputs.new("NodeSocketFloat","OffsetY")
			nodeGroup.inputs.new("NodeSocketFloat","Rotation")
			nodeGroup.inputs.new("NodeSocketFloat","Tiling")
		else:
			nodeGroup.interface.new_socket(name="UV1",description="",in_out ="INPUT", socket_type="NodeSocketVector")
			nodeGroup.interface.new_socket(name="UV2",description="",in_out ="INPUT", socket_type="NodeSocketVector")
			nodeGroup.interface.new_socket(name="UseSecondaryUV",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="OffsetX",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="OffsetY",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="Rotation",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="Tiling",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
		inNode = nodeGroup.nodes.new('NodeGroupInput')
		#inNode.outputs["UseSecondaryUV"].default_value = 0.0
		#inNode.outputs["Tiling"].default_value = 1.0
		#Setting defaults here doesn't work
		currentLoc = [300,0]
		secondaryUVClampNode = nodes.new("ShaderNodeClamp")
		secondaryUVClampNode.location = currentLoc
		links.new(inNode.outputs["UseSecondaryUV"],secondaryUVClampNode.inputs["Value"])
		
		currentLoc[0] += 300
		
		vectorMixNode = nodes.new("ShaderNodeMixRGB")
		vectorMixNode.location = currentLoc
		links.new(secondaryUVClampNode.outputs["Result"],vectorMixNode.inputs["Fac"])
		links.new(inNode.outputs["UV1"],vectorMixNode.inputs["Color1"])
		links.new(inNode.outputs["UV2"],vectorMixNode.inputs["Color2"])
		currentLoc[0] += 300
		
		locCombineNode = nodes.new("ShaderNodeCombineXYZ")
		locCombineNode.location = currentLoc
		links.new(inNode.outputs["OffsetX"],locCombineNode.inputs["X"])
		links.new(inNode.outputs["OffsetY"],locCombineNode.inputs["Y"])
		currentLoc[0] += 300
		
		rotCombineNode = nodes.new("ShaderNodeCombineXYZ")
		rotCombineNode.location = (currentLoc[0],currentLoc[1] + 300)
		links.new(inNode.outputs["Rotation"],rotCombineNode.inputs["X"])
		currentLoc[0] += 300
		
		
		mappingNode = nodes.new("ShaderNodeMapping")
		mappingNode.location = currentLoc
		links.new(vectorMixNode.outputs["Color"],mappingNode.inputs["Vector"])
		links.new(locCombineNode.outputs["Vector"],mappingNode.inputs["Location"])
		links.new(rotCombineNode.outputs["Vector"],mappingNode.inputs["Rotation"])
		links.new(inNode.outputs["Tiling"],mappingNode.inputs["Scale"])
		currentLoc[0] += 300
		
		
		outNode = nodeGroup.nodes.new('NodeGroupOutput')
		if bpy.app.version < (4,0,0):
			nodeGroup.outputs.new('NodeSocketVector', "Vector")
			
		else:
			nodeGroup.interface.new_socket(name="Vector",description="",in_out ="OUTPUT", socket_type="NodeSocketVector")
		
		links.new(mappingNode.outputs["Vector"],outNode.inputs["Vector"])
	
	nodeGroupNode = nodeTree.nodes.new("ShaderNodeGroup")
	nodeGroupNode.node_tree = nodeGroup
	
	#Set defaults

	nodeGroupNode.inputs["Tiling"].default_value = 1.0
	
	return nodeGroupNode
	

def getMHWildsSkinMappingNodeGroup(nodeTree):
	if "MHWildsSkinMappingV2" in bpy.data.node_groups:
		nodeGroup = bpy.data.node_groups["MHWildsSkinMappingV2"]
	else:
		nodeGroup = bpy.data.node_groups.new(type="ShaderNodeTree", name="MHWildsSkinMappingV2")
	
		if bpy.app.version < (4,0,0):
			nodeGroup.inputs.new("NodeSocketFloat","X")
			nodeGroup.inputs.new("NodeSocketFloat","Y")
			
		else:
			nodeGroup.interface.new_socket(name="X",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="Y",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
		
		nodes = nodeGroup.nodes
		links = nodeGroup.links
		
		inNode = nodeGroup.nodes.new('NodeGroupInput')

		currentLoc = [300,0]
		#Multiply node input values to give finer control since min and max inputs can't be set any more.
		multXNode = nodes.new("ShaderNodeMath")
		multXNode.location = [currentLoc[0],currentLoc[1]+300]
		multXNode.operation = "MULTIPLY"
		links.new(inNode.outputs["X"],multXNode.inputs[0])
		multXNode.inputs[1].default_value = 0.01
		
		multYNode = nodes.new("ShaderNodeMath")
		multYNode.location = [currentLoc[0],currentLoc[1]-300]
		multYNode.operation = "MULTIPLY"
		links.new(inNode.outputs["Y"],multYNode.inputs[0])
		multYNode.inputs[1].default_value = 0.01
		
		currentLoc[0] += 300
		
		combineXYZNode = nodes.new("ShaderNodeCombineXYZ")
		combineXYZNode.location = currentLoc
		links.new(multXNode.outputs["Value"],combineXYZNode.inputs["X"])
		links.new(multYNode.outputs["Value"],combineXYZNode.inputs["Y"])
		
		currentLoc[0] += 300
		
		mappingNode = nodes.new("ShaderNodeMapping")
		mappingNode.location = currentLoc
		links.new(combineXYZNode.outputs["Vector"],mappingNode.inputs["Location"])
		mappingNode.inputs["Scale"].default_value = (0.01,0.01,1.0)
		
		
		
		outNode = nodeGroup.nodes.new('NodeGroupOutput')
		if bpy.app.version < (4,0,0):
			nodeGroup.outputs.new('NodeSocketVector', "Vector")
			
		else:
			nodeGroup.interface.new_socket(name="Vector",description="",in_out ="OUTPUT", socket_type="NodeSocketVector")
		
		links.new(mappingNode.outputs["Vector"],outNode.inputs["Vector"])
	
	
	
	
	
	nodeGroupNode = nodeTree.nodes.new("ShaderNodeGroup")
	nodeGroupNode.node_tree = nodeGroup
	
	#Set defaults
	
	#Set skin tone closer to MHW default
	nodeGroupNode.inputs["X"].default_value = 10.0
	#nodeGroupNode.inputs["X"].min_value = 0.001
	#nodeGroupNode.inputs["X"].max_value = 0.999
	
	nodeGroupNode.inputs["Y"].default_value = 75.0
	
	#nodeGroupNode.inputs["Y"].min_value = 0.001
	#nodeGroupNode.inputs["Y"].max_value = 0.999
	
	return nodeGroupNode

def getMHWildsDetailMapNodeGroup(nodeTree):#Unfinished
	if "MHWildsDetailMapNodeGroup" in bpy.data.node_groups:
		nodeGroup = bpy.data.node_groups["MHWildsDetailMapNodeGroup"]
	else:
		nodeGroup = bpy.data.node_groups.new(type="ShaderNodeTree", name="MHWildsDetailMapNodeGroup")
		nodes = nodeGroup.nodes
		links = nodeGroup.links
		if bpy.app.version < (4,0,0):
			nodeGroup.inputs.new("NodeSocketColor","DetailMaskMap")
			nodeGroup.inputs.new("NodeSocketFloat","DetailMaskMapAlpha")
			
			nodeGroup.inputs.new("NodeSocketColor","ColorLayer_R")
			nodeGroup.inputs.new("NodeSocketColor","ColorParam_R")
			nodeGroup.inputs.new("NodeSocketColor","NormalLayer_R")
			nodeGroup.inputs.new("NodeSocketFloat","NormalParam_R")
			nodeGroup.inputs.new("NodeSocketFloat","RoughnessLayer_R")
			nodeGroup.inputs.new("NodeSocketFloat","RoughnessParam_R")
			nodeGroup.inputs.new("NodeSocketFloat","MetallicLayer_R")
			nodeGroup.inputs.new("NodeSocketFloat","MetallicParam_R")
			
			nodeGroup.inputs.new("NodeSocketColor","ColorLayer_G")
			nodeGroup.inputs.new("NodeSocketColor","ColorParam_G")
			nodeGroup.inputs.new("NodeSocketColor","NormalLayer_G")
			nodeGroup.inputs.new("NodeSocketFloat","NormalParam_G")
			nodeGroup.inputs.new("NodeSocketFloat","RoughnessLayer_G")
			nodeGroup.inputs.new("NodeSocketFloat","RoughnessParam_G")
			nodeGroup.inputs.new("NodeSocketFloat","MetallicLayer_G")
			nodeGroup.inputs.new("NodeSocketFloat","MetallicParam_G")
			
			nodeGroup.inputs.new("NodeSocketColor","ColorLayer_B")
			nodeGroup.inputs.new("NodeSocketColor","ColorParam_B")
			nodeGroup.inputs.new("NodeSocketColor","NormalLayer_B")
			nodeGroup.inputs.new("NodeSocketFloat","NormalParam_B")
			nodeGroup.inputs.new("NodeSocketFloat","RoughnessLayer_B")
			nodeGroup.inputs.new("NodeSocketFloat","RoughnessParam_B")
			nodeGroup.inputs.new("NodeSocketFloat","MetallicLayer_B")
			nodeGroup.inputs.new("NodeSocketFloat","MetallicParam_B")
			
			nodeGroup.inputs.new("NodeSocketColor","ColorLayer_A")
			nodeGroup.inputs.new("NodeSocketColor","ColorParam_A")
			nodeGroup.inputs.new("NodeSocketColor","NormalLayer_A")
			nodeGroup.inputs.new("NodeSocketFloat","NormalParam_A")
			nodeGroup.inputs.new("NodeSocketFloat","RoughnessLayer_A")
			nodeGroup.inputs.new("NodeSocketFloat","RoughnessParam_A")
			nodeGroup.inputs.new("NodeSocketFloat","MetallicLayer_A")
			nodeGroup.inputs.new("NodeSocketFloat","MetallicParam_A")
			
			nodeGroup.inputs.new("NodeSocketFloat","UseDetail")
			nodeGroup.inputs.new("NodeSocketVector","TexCoordNormal")

		else:
			nodeGroup.interface.new_socket(name="DetailMaskMap",description="",in_out ="INPUT", socket_type="NodeSocketColor")
			nodeGroup.interface.new_socket(name="DetailMaskMapAlpha",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			
			nodeGroup.interface.new_socket(name="ColorLayer_R",description="",in_out ="INPUT", socket_type="NodeSocketColor")
			nodeGroup.interface.new_socket(name="ColorParam_R",description="",in_out ="INPUT", socket_type="NodeSocketColor")
			nodeGroup.interface.new_socket(name="NormalLayer_R",description="",in_out ="INPUT", socket_type="NodeSocketColor")
			nodeGroup.interface.new_socket(name="NormalParam_R",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="RoughnessLayer_R",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="RoughnessParam_R",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="MetallicLayer_R",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="MetallicParam_R",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			
			nodeGroup.interface.new_socket(name="ColorLayer_G",description="",in_out ="INPUT", socket_type="NodeSocketColor")
			nodeGroup.interface.new_socket(name="ColorParam_G",description="",in_out ="INPUT", socket_type="NodeSocketColor")
			nodeGroup.interface.new_socket(name="NormalLayer_G",description="",in_out ="INPUT", socket_type="NodeSocketColor")
			nodeGroup.interface.new_socket(name="NormalParam_G",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="RoughnessLayer_G",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="RoughnessParam_G",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="MetallicLayer_G",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="MetallicParam_G",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			
			nodeGroup.interface.new_socket(name="ColorLayer_B",description="",in_out ="INPUT", socket_type="NodeSocketColor")
			nodeGroup.interface.new_socket(name="ColorParam_B",description="",in_out ="INPUT", socket_type="NodeSocketColor")
			nodeGroup.interface.new_socket(name="NormalLayer_B",description="",in_out ="INPUT", socket_type="NodeSocketColor")
			nodeGroup.interface.new_socket(name="NormalParam_B",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="RoughnessLayer_B",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="RoughnessParam_B",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="MetallicLayer_B",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="MetallicParam_B",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			
			nodeGroup.interface.new_socket(name="ColorLayer_A",description="",in_out ="INPUT", socket_type="NodeSocketColor")
			nodeGroup.interface.new_socket(name="ColorParam_A",description="",in_out ="INPUT", socket_type="NodeSocketColor")
			nodeGroup.interface.new_socket(name="NormalLayer_A",description="",in_out ="INPUT", socket_type="NodeSocketColor")
			nodeGroup.interface.new_socket(name="NormalParam_A",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="RoughnessLayer_A",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="RoughnessParam_A",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="MetallicLayer_A",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="MetallicParam_A",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			
			nodeGroup.interface.new_socket(name="UseDetail",description="",in_out ="INPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="TexCoordNormal",description="",in_out ="INPUT", socket_type="NodeSocketVector")
			
		inNode = nodeGroup.nodes.new('NodeGroupInput')
	
		currentLoc = [300,0]
		
		#TODO
		
		outNode = nodeGroup.nodes.new('NodeGroupOutput')
		if bpy.app.version < (4,0,0):
			nodeGroup.outputs.new('NodeSocketColor', "Color")
			nodeGroup.outputs.new('NodeSocketVector', "Normal")
			nodeGroup.outputs.new('NodeSocketFloat', "Roughness")
			nodeGroup.outputs.new('NodeSocketFloat', "Metallic")
			
		else:
			nodeGroup.interface.new_socket(name="Color",description="",in_out ="OUTPUT", socket_type="NodeSocketColor")
			nodeGroup.interface.new_socket(name="Normal",description="",in_out ="OUTPUT", socket_type="NodeSocketVector")
			nodeGroup.interface.new_socket(name="Roughness",description="",in_out ="OUTPUT", socket_type="NodeSocketFloat")
			nodeGroup.interface.new_socket(name="Metallic",description="",in_out ="OUTPUT", socket_type="NodeSocketFloat")
		
		#links.new(mappingNode.outputs["Vector"],outNode.inputs["Vector"])
	
	nodeGroupNode = nodeTree.nodes.new("ShaderNodeGroup")
	nodeGroupNode.node_tree = nodeGroup
	
	
	return nodeGroupNode
	


def addPropertyNode(prop,currentPos,node_tree):
	if prop.propName in node_tree.nodes:
		propNode = node_tree.nodes[prop.propName]
	else:
		lowerPropName = prop.propName.lower()
		if prop.propName in colorPropertySet or (prop.paramCount == 4 and ("color" in lowerPropName or "_col_" in lowerPropName) and "rate" not in lowerPropName):
			#RGBA Color
			nodeGroup = getColorNodeGroup(node_tree)
			nodeGroup.inputs["Color"].default_value = prop.propValue
			nodeGroup.inputs["Alpha"].default_value = prop.propValue[3]
			propNode = nodeGroup
		elif prop.paramCount > 1:
			#Vec4
			nodeGroup = getVec4NodeGroup(node_tree)
			nodeGroup.inputs[0].default_value = prop.propValue[0]
			nodeGroup.inputs[1].default_value = prop.propValue[1]
			nodeGroup.inputs[2].default_value = prop.propValue[2]
			nodeGroup.inputs[3].default_value = prop.propValue[3]
			propNode = nodeGroup
		else:
			propNode = node_tree.nodes.new("ShaderNodeValue")
			propNode.outputs["Value"].default_value = float(prop.propValue[0])
	
		propNode.name = prop.propName
		propNode.label = prop.propName
		propNode.location = currentPos
		currentPos[1] -= int(propNode.height*2.5)
	return propNode
class dynamicColorMixLayerNodeGroup():
	def __init__(self,nodeTree):
		self._currentOutSocket = None
		self.nodeLoc = (0,0)
		self.node_tree = nodeTree
		
	@property
	def currentOutSocket(self):
		return self._currentOutSocket
	
	@currentOutSocket.setter
	def currentOutSocket(self,value):
		self._currentOutSocket = value
		self.nodeLoc = value.node.location
	
	def addMixLayer(self,colorOutSocket,factorOutSocket = None,mixType = "MIX",mixFactor = 0.5):
		
		
		if self.currentOutSocket == None:#For the first layer added, just store the out socket since it's not being mixed with anything
			self.currentOutSocket = colorOutSocket
		else:
			mixNode = self.node_tree.nodes.new('ShaderNodeMixRGB')
			mixNode.location = (self.nodeLoc[0]+(self.currentOutSocket.node.width+100),self.nodeLoc[1])
			mixNode.blend_type = mixType
			mixNode.inputs["Fac"].default_value = mixFactor
			
			self.node_tree.links.new(self.currentOutSocket,mixNode.inputs["Color1"])
			self.node_tree.links.new(colorOutSocket,mixNode.inputs["Color2"])
			if factorOutSocket != None:
				self.node_tree.links.new(factorOutSocket,mixNode.inputs["Fac"])
			self.currentOutSocket = mixNode.outputs["Color"]

class dynamicArrayTextureSelectorNodeGroup():
	def __init__(self,nodeTree):
		self._currentOutSocket = None
		self.currentOutAlphaSocket = None
		self.nodeLoc = (0,0)
		self.node_tree = nodeTree
		self.selectorNode = None
		
	@property
	def currentOutSocket(self):
		return self._currentOutSocket
	
	@currentOutSocket.setter
	def currentOutSocket(self,value):
		self._currentOutSocket = value
		self.nodeLoc = value.node.location
	
	def addMixLayer(self,colorOutSocket,alphaOutSocket,index):
		
		outNodeLoc = colorOutSocket.node.location
		if self.currentOutSocket == None:#For the first layer added, just store the out socket since it's not being mixed with anything
			self.currentOutSocket = colorOutSocket
			self.currentOutAlphaSocket = alphaOutSocket
			selectorNode = self.node_tree.nodes.new('ShaderNodeMath')
			selectorNode.operation = "ROUND"
			selectorNode.inputs[0].default_value = 0.0
			selectorNode.name = colorOutSocket.node.name.rsplit("_",1)[0]+"_SELECTOR"
			selectorNode.label = selectorNode.name
			selectorNode.location = (outNodeLoc[0]+600,outNodeLoc[1])
			self.selectorNode = selectorNode
		else:
			
			compareNode = self.node_tree.nodes.new('ShaderNodeMath')
			compareNode.operation = "COMPARE"
			
			self.node_tree.links.new(self.selectorNode.outputs["Value"],compareNode.inputs[0])
			compareNode.inputs[1].default_value = index#Compare value	
			compareNode.inputs[2].default_value = 0.5#Epsilon
			
			
			compareNode.location = (outNodeLoc[0],outNodeLoc[1]+300)
			
			mixNode = self.node_tree.nodes.new('ShaderNodeMixRGB')
			mixNode.location = (outNodeLoc[0],outNodeLoc[1]+600)
			
			self.node_tree.links.new(self.currentOutSocket,mixNode.inputs["Color1"])
			self.node_tree.links.new(colorOutSocket,mixNode.inputs["Color2"])
			self.node_tree.links.new(compareNode.outputs["Value"],mixNode.inputs["Fac"])
			self.currentOutSocket = mixNode.outputs["Color"]
			
			mixAlphaNode = self.node_tree.nodes.new('ShaderNodeMixRGB')
			mixAlphaNode.location = (outNodeLoc[0],outNodeLoc[1]+900)
			
			self.node_tree.links.new(self.currentOutAlphaSocket,mixAlphaNode.inputs["Color1"])
			self.node_tree.links.new(alphaOutSocket,mixAlphaNode.inputs["Color2"])
			self.node_tree.links.new(compareNode.outputs["Value"],mixAlphaNode.inputs["Fac"])
			self.currentOutAlphaSocket = mixAlphaNode.outputs["Color"]

missingTexTypeDict = {
	"ALBD":(1.0,0.0,0.0,1.0),
	"ALBM":(1.0,0.0,0.0,0.0),
	"ALB":(1.0,0.0,0.0,1.0),
	"ALP":(1.0,1.0,1.0,1.0),
	"ALBA":(1.0,0.0,0.0,1.0),
	"NRMR":(.502,.502,1.0,1.0),
	"NRRT":(.502,.502,1.0,.502),
	"NRRA":(.502,.502,1.0,.502),
	"NRRC":(.502,.502,1.0,.502),
	"NRRO":(.502,.502,1.0,.502),
	"ATOS":(1.0,0.0,1.0,1.0),
	"NULLATOS":(1.0,0.0,1.0,1.0),
	"NULLWHITE":(1.0,1.0,1.0,1.0),
	"NULLBLACK":(0.0,0.0,0.0,1.0),
	"ATOC":(1.0,0.0,1.0,1.0),
	}
MAX_ARRAY_IMPORT_SIZE = 16#Blender can't handle much more than 16 mix nodes into a color node, so it gets treated as a single image node if it exceeds 16
def addImageNode(nodeTree,textureType,imageList,texturePath,currentPos):
	
	colorSpace = "sRGB" if textureType in albedoTypeSet or "alb" in texturePath.rsplit("_",1)[-1].lower() else "Non-Color"
	
	if len(imageList) == 1 or len(imageList) > MAX_ARRAY_IMPORT_SIZE:
		imageNode = nodeTree.nodes.new('ShaderNodeTexImage')
		imageNode.name = textureType
		imageNode.label = textureType
		imageNode.location = currentPos
		
		if imageList[0] != None:
			imageNode.image = imageList[0]
			#print(f"image node {textureType} path:{imageList[0].filepath}")
			
		else:
			split = os.path.splitext(os.path.split(texturePath)[1])[0].rsplit("_",1)
			texType = split[1].upper() if len(split) > 1 else split[0].upper()
	
			if f"Missing {texType}" in bpy.data.images:
				imageNode.image = bpy.data.images[f"Missing {texType}"]
			else:
				
				imageNode.image = bpy.data.images.new(
					name = f"Missing {texType}",
					width = 1,
					height = 1,
					)
				#imageNode.image.pixels = missingTexTypeDict.get(texType,(0.0,0.0,0.0,1.0))
				imageNode.image.generated_color = missingTexTypeDict.get(texType,(1.0,1.0,1.0,1.0))
	
				imageNode.image.update()
				#print(f"Created \"Missing {textureType}\" texture.")
		imageNode.image.alpha_mode = "CHANNEL_PACKED"
		imageNode.image.colorspace_settings.name = colorSpace
			
	else:
		#Create image array selector
		imageNode = getImagePassThroughNodeGroup(nodeTree)
		imageNode.name = textureType
		imageNode.label = textureType
		imageNode.location = currentPos
		currentXPos = currentPos[0] - 300
		
		if "UVMap1Node" in nodeTree.nodes:
			UVMap1Node = nodeTree.nodes["UVMap1Node"]
			nodeTree.links.new(UVMap1Node.outputs["UV"],imageNode.inputs["Vector"])
		arrayGroup = dynamicArrayTextureSelectorNodeGroup(nodeTree)
		for index,image in enumerate(imageList):
			arrayImageNode = nodeTree.nodes.new('ShaderNodeTexImage')
			arrayImageNode.name = f"ARRAY_{textureType}_{index}"
			arrayImageNode.label = f"ARRAY_{textureType}_{index}"
			arrayImageNode.location = (currentXPos,currentPos[1])
			
			arrayImageNode.image = image
			arrayImageNode.image.colorspace_settings.name = colorSpace
			nodeTree.links.new(imageNode.outputs["Vector"],arrayImageNode.inputs["Vector"])
			arrayGroup.addMixLayer(arrayImageNode.outputs["Color"],arrayImageNode.outputs["Alpha"],index)
			currentXPos -= 300
		if arrayGroup.currentOutSocket != None:
			nodeTree.links.new(arrayGroup.currentOutSocket,imageNode.inputs["Color"])
			nodeTree.links.new(arrayGroup.currentOutAlphaSocket,imageNode.inputs["Alpha"])
		del arrayGroup
	return imageNode

def newALBDNode (nodeTree,textureType,matInfo):
	imageNode = nodeTree.nodes[textureType]
	currentPos = [imageNode.location[0]+300,imageNode.location[1]]
	
	
	#matInfo["albedoNodeLayerGroup"].addMixLayer(imageNode.outputs["Color"],factorOutSocket = None,mixType = "MIX",mixFactor = 0.0)
	matInfo["albedoNodeLayerGroup"].addMixLayer(imageNode.outputs["Color"])
	matInfo["metallicNodeLayerGroup"].addMixLayer(imageNode.outputs["Alpha"])
	matInfo["isDielectric"] = True
	
	return imageNode



def newALBMNode (nodeTree,textureType,matInfo):
	imageNode = nodeTree.nodes[textureType]
	currentPos = [imageNode.location[0]+300,imageNode.location[1]]
	
	matInfo["albedoNodeLayerGroup"].addMixLayer(imageNode.outputs["Color"])
	matInfo["metallicNodeLayerGroup"].addMixLayer(imageNode.outputs["Alpha"])
	
	return imageNode
def newALBANode (nodeTree,textureType,matInfo):
	imageNode = nodeTree.nodes[textureType]
	currentPos = [imageNode.location[0]+300,imageNode.location[1]]
	
	matInfo["albedoNodeLayerGroup"].addMixLayer(imageNode.outputs["Color"],factorOutSocket = None,mixType = "MIX",mixFactor = 0.5)

	matInfo["alphaSocket"] = imageNode.outputs["Alpha"]
	return imageNode
def newALBNode (nodeTree,textureType,matInfo):
	imageNode = nodeTree.nodes[textureType]
	currentPos = [imageNode.location[0]+300,imageNode.location[1]]
	
	matInfo["albedoNodeLayerGroup"].addMixLayer(imageNode.outputs["Color"])
	
	return imageNode
def newNRMRNode (nodeTree,textureType,matInfo):
	imageNode = nodeTree.nodes[textureType]
	currentPos = [imageNode.location[0]+300,imageNode.location[1]]
	
	matInfo["normalNodeLayerGroup"].addMixLayer(imageNode.outputs["Color"])
	matInfo["roughnessNodeLayerGroup"].addMixLayer(imageNode.outputs["Alpha"])
	return imageNode
def newNAMNode (nodeTree,textureType,matInfo):
	imageNode = nodeTree.nodes[textureType]
	currentPos = [imageNode.location[0]-300,imageNode.location[1]]
	
	separateRGBNode = nodeTree.nodes.new("ShaderNodeSeparateRGB")
	separateRGBNode.location = currentPos
	nodeTree.links.new(imageNode.outputs["Color"],separateRGBNode.inputs["Image"])
	
	currentPos[0] += 300
	
	combineRGBNode = nodeTree.nodes.new("ShaderNodeCombineRGB")
	combineRGBNode.location = currentPos
	nodeTree.links.new(separateRGBNode.outputs["R"],combineRGBNode.inputs["R"])
	nodeTree.links.new(separateRGBNode.outputs["G"],combineRGBNode.inputs["G"])
	combineRGBNode.inputs["B"].default_value = 1.0
	matInfo["normalNodeLayerGroup"].addMixLayer(combineRGBNode.outputs["Image"])
	
	matInfo["alphaSocket"] = imageNode.outputs["Alpha"]
	matInfo["blenderMaterial"].shadow_method = "NONE"
	
	if "Stitch_Color" in matInfo["mPropDict"]:
		stitchColorNode = addPropertyNode(matInfo["mPropDict"]["Stitch_Color"], matInfo["currentPropPos"], nodeTree)
		
		matInfo["albedoNodeLayerGroup"].addMixLayer(stitchColorNode.outputs["Color"])
	
	if "Stitch_Scale" in matInfo["mPropDict"]:
		stitchScaleNode = addPropertyNode(matInfo["mPropDict"]["Stitch_Scale"], matInfo["currentPropPos"], nodeTree)
		if "UVMap1Node" in nodeTree.nodes:
			UVMap0Node = nodeTree.nodes["UVMap1Node"]
		else:
			UVMap0Node = nodeTree.nodes.new("ShaderNodeUVMap")
			UVMap0Node.name = "UVMap1Node"
			UVMap0Node.location = (currentPos[0]-300,currentPos[1]+300)
			UVMap0Node.uv_map = "UVMap0"
		
		mappingNode = nodeTree.nodes.new("ShaderNodeMapping")
		mappingNode.location = currentPos
		nodeTree.links.new(stitchScaleNode.outputs["Value"],mappingNode.inputs["Scale"])
		nodeTree.links.new(UVMap0Node.outputs["UV"],mappingNode.inputs["Vector"])
		
		combineNode = nodeTree.nodes.new("ShaderNodeCombineXYZ")
		combineNode.location = (currentPos[0]-300,currentPos[1])
		if "Stitch_U_offset" in matInfo["mPropDict"]:
			u_offsetNode = addPropertyNode(matInfo["mPropDict"]["Stitch_U_offset"], matInfo["currentPropPos"], nodeTree)
			
			nodeTree.links.new(u_offsetNode.outputs["Value"],combineNode.inputs["X"])
		
		if "Stitch_V_offset" in matInfo["mPropDict"]:
			v_offsetNode = addPropertyNode(matInfo["mPropDict"]["Stitch_V_offset"], matInfo["currentPropPos"], nodeTree)
			
			nodeTree.links.new(v_offsetNode.outputs["Value"],combineNode.inputs["Y"])
		
		nodeTree.links.new(combineNode.outputs["Vector"],mappingNode.inputs["Location"])
		nodeTree.links.new(mappingNode.outputs["Vector"],imageNode.inputs["Vector"])
	
	if "Stitch_Brightness" in matInfo["mPropDict"]:#TODO Fix, the brightness and contrast node isn't right
		brightConstrastNode = nodeTree.nodes.new("ShaderNodeBrightContrast")
		brightConstrastNode.location = (matInfo["albedoNodeLayerGroup"].nodeLoc[0]+200,matInfo["albedoNodeLayerGroup"].nodeLoc[1] - 200)
		stitchBrightnessNode = addPropertyNode(matInfo["mPropDict"]["Stitch_Brightness"], matInfo["currentPropPos"], nodeTree)
		brightnessAdjustNode = nodeTree.nodes.new("ShaderNodeMath")
		brightnessAdjustNode.location = addLoc(stitchBrightnessNode,(300,0))
		brightnessAdjustNode.operation = "ADD"
		nodeTree.links.new(stitchBrightnessNode.outputs["Value"],brightnessAdjustNode.inputs[0])
		brightnessAdjustNode.inputs[1].default_value = 0.0
		stitchConstrastNode = addPropertyNode(matInfo["mPropDict"]["Stitch_Contrast"], matInfo["currentPropPos"], nodeTree)
		contrastAdjustNode = nodeTree.nodes.new("ShaderNodeMath")
		contrastAdjustNode.location = addLoc(stitchConstrastNode,(300,0))
		contrastAdjustNode.operation = "ADD"
		nodeTree.links.new(stitchConstrastNode.outputs["Value"],contrastAdjustNode.inputs[0])
		brightnessAdjustNode.inputs[1].default_value = 0.0
		
		
		nodeTree.links.new(brightnessAdjustNode.outputs["Value"],brightConstrastNode.inputs["Bright"])
		nodeTree.links.new(contrastAdjustNode.outputs["Value"],brightConstrastNode.inputs["Contrast"])
		nodeTree.links.new(separateRGBNode.outputs["B"],brightConstrastNode.inputs["Color"])
		matInfo["albedoNodeLayerGroup"].addMixLayer(brightConstrastNode.outputs["Color"],mixType = "MULTIPLY",mixFactor = 1.0)
		#matInfo["albedoNodeLayerGroup"].currentOutSocket = brightConstrastNode.outputs["Color"]
	if "Stitch_Normal_Rate" in matInfo["mPropDict"]:
		stitchNormalRateNode = addPropertyNode(matInfo["mPropDict"]["Stitch_Normal_Rate"], matInfo["currentPropPos"], nodeTree)
		matInfo["normalNodeLayerGroup"].addMixLayer(stitchNormalRateNode.outputs["Value"],mixType = "MULTIPLY",mixFactor = 1.0)
	return imageNode
def newNRRTNode (nodeTree,textureType,matInfo):
	imageNode = nodeTree.nodes[textureType]
	currentPos = [imageNode.location[0]+300,imageNode.location[1]]
	
	
	nodeGroupNode = getBentNormalNodeGroup(nodeTree)
	nodeGroupNode.location = currentPos
	nodeTree.links.new(imageNode.outputs["Color"],nodeGroupNode.inputs["Color"])
	nodeTree.links.new(imageNode.outputs["Alpha"],nodeGroupNode.inputs["Alpha"])
	matInfo["normalNodeLayerGroup"].addMixLayer(nodeGroupNode.outputs["Color"])
	matInfo["roughnessNodeLayerGroup"].addMixLayer(nodeGroupNode.outputs["Roughness"])
	
	
	if textureType == "NormalRoughnessCavityMap":
		matInfo["cavityNodeLayerGroup"].addMixLayer(nodeGroupNode.outputs["BlueChannel"])
		
	elif textureType == "NormalRoughnessOcclusionMap":
		matInfo["aoNodeLayerGroup"].addMixLayer(nodeGroupNode.outputs["BlueChannel"])
	elif textureType == "NormalRoughnessAlphaMap":
		matInfo["alphaSocket"] = nodeGroupNode.outputs["BlueChannel"]
	else:
		matInfo["translucentSocket"] = nodeGroupNode.outputs["BlueChannel"]
		
	return imageNode
	
def newALPNode (nodeTree,textureType,matInfo):
	imageNode = nodeTree.nodes[textureType]
	currentPos = [imageNode.location[0]+300,imageNode.location[1]]
	
	
	bwNode = nodeTree.nodes.new('ShaderNodeRGBToBW')
	bwNode.location = currentPos
	nodeTree.links.new(imageNode.outputs["Color"],bwNode.inputs["Color"])
	matInfo["alphaSocket"] = bwNode.outputs["Val"]
	return imageNode
def newEMINode (nodeTree,textureType,matInfo):
	imageNode = nodeTree.nodes[textureType]
	currentPos = [imageNode.location[0]+300,imageNode.location[1]]
	
	matInfo["emissionColorNodeLayerGroup"].addMixLayer(imageNode.outputs["Color"])
	
	
	if "Emissive_color" in matInfo["mPropDict"]:
		emiColorNode = addPropertyNode(matInfo["mPropDict"]["Emissive_color"], matInfo["currentPropPos"], nodeTree)
		matInfo["emissionColorNodeLayerGroup"].addMixLayer(emiColorNode.outputs["Color"],mixType = "MULTIPLY",mixFactor = 1.0)
	elif "EmissiveColor" in matInfo["mPropDict"]:
		emiColorNode = addPropertyNode(matInfo["mPropDict"]["EmissiveColor"], matInfo["currentPropPos"], nodeTree)
		matInfo["emissionColorNodeLayerGroup"].addMixLayer(emiColorNode.outputs["Color"],mixType = "MULTIPLY",mixFactor = 1.0)
	emiIntensityNode = None
	if "Emissive_intensity" in matInfo["mPropDict"]:
		emiIntensityNode = addPropertyNode(matInfo["mPropDict"]["Emissive_intensity"], matInfo["currentPropPos"], nodeTree)
	elif "Emissive_Intensity" in matInfo["mPropDict"]:#I should have lower cased the prop dict
		emiIntensityNode = addPropertyNode(matInfo["mPropDict"]["Emissive_Intensity"], matInfo["currentPropPos"], nodeTree)
	elif "EmissiveIntensity" in matInfo["mPropDict"]:#I should have lower cased the prop dict
		emiIntensityNode = addPropertyNode(matInfo["mPropDict"]["EmissiveIntensity"], matInfo["currentPropPos"], nodeTree)
	if emiIntensityNode != None:
		bwNode = nodeTree.nodes.new('ShaderNodeRGBToBW')
		bwNode.location = currentPos
		bwNode.name = "BWEMINode"
		currentPos[0]+=300
		nodeTree.links.new(imageNode.outputs["Color"],bwNode.inputs[0])
		
		baseEMIMultNode = nodeTree.nodes.new('ShaderNodeMath')
		baseEMIMultNode.location = currentPos
		baseEMIMultNode.operation = "MULTIPLY"
		nodeTree.links.new(bwNode.outputs[0],baseEMIMultNode.inputs[0])
		nodeTree.links.new(emiIntensityNode.outputs["Value"],baseEMIMultNode.inputs[1])
		
		matInfo["emissionStrengthNodeLayerGroup"].addMixLayer(baseEMIMultNode.outputs["Value"],mixType = "MULTIPLY",mixFactor = 1.0)
	if "S_col_R" in matInfo["mPropDict"] and "S_col_G" in matInfo["mPropDict"] and "S_col_R_Emissive_intensity" in matInfo["mPropDict"] and "S_col_G_Emissive_intensity" in matInfo["mPropDict"]:
		RColorNode = addPropertyNode(matInfo["mPropDict"]["S_col_R"], matInfo["currentPropPos"], nodeTree)
		GColorNode = addPropertyNode(matInfo["mPropDict"]["S_col_G"], matInfo["currentPropPos"], nodeTree)
		
		RColorEmiIntensityNode = addPropertyNode(matInfo["mPropDict"]["S_col_R_Emissive_intensity"], matInfo["currentPropPos"], nodeTree)
		GColorEmiIntensityNode = addPropertyNode(matInfo["mPropDict"]["S_col_G_Emissive_intensity"], matInfo["currentPropPos"], nodeTree)
		
		if "CMMSepNode" in nodeTree.nodes:
			CMMSeparateNode = nodeTree.nodes["CMMSepNode"]
		else:
			CMMSeparateNode = nodeTree.nodes.new('ShaderNodeSeparateRGB')
			CMMSeparateNode.location = currentPos
			CMMSeparateNode.name = "CMMSepNode"
			
		RMultNode = nodeTree.nodes.new("ShaderNodeMath")
		RMultNode.operation = "MULTIPLY"
		
		nodeTree.links.new(RColorEmiIntensityNode.outputs["Value"],RMultNode.inputs[0])
		nodeTree.links.new(CMMSeparateNode.outputs["R"],RMultNode.inputs[1])
		
		GMultNode = nodeTree.nodes.new("ShaderNodeMath")
		GMultNode.operation = "MULTIPLY"
		
		StrengthAddNode = nodeTree.nodes.new("ShaderNodeMath")
		StrengthAddNode.operation = "ADD"
		
		nodeTree.links.new(RMultNode.outputs["Value"],StrengthAddNode.inputs[0])
		nodeTree.links.new(GMultNode.outputs["Value"],StrengthAddNode.inputs[1])
		
		matInfo["emissionStrengthNodeLayerGroup"].addMixLayer(StrengthAddNode.outputs["Value"],factorOutSocket = None,mixType = "ADD",mixFactor = 1.0)
		
		nodeTree.links.new(GColorEmiIntensityNode.outputs["Value"],GMultNode.inputs[0])
		nodeTree.links.new(CMMSeparateNode.outputs["G"],GMultNode.inputs[1])
		
		matInfo["emissionColorNodeLayerGroup"].addMixLayer(RColorNode.outputs["Color"],factorOutSocket = CMMSeparateNode.outputs["R"],mixType = "ADD")
		matInfo["emissionColorNodeLayerGroup"].addMixLayer(GColorNode.outputs["Color"],factorOutSocket = CMMSeparateNode.outputs["G"],mixType = "ADD")
		
		
		
	return imageNode

def newCMMNode (nodeTree,textureType,matInfo):
	imageNode = nodeTree.nodes[textureType]
	currentPos = [imageNode.location[0]+300,imageNode.location[1]]
	
	if "UseSecondaryUV_ColorLayer_MaskMap" in matInfo["mPropDict"]:
		UVMap1Node = None
		UVMap2Node = None
		if "UVMap1Node" in nodeTree.nodes:
			UVMap1Node = nodeTree.nodes["UVMap1Node"]
		if "UVMap2Node" in nodeTree.nodes:
			UVMap2Node = nodeTree.nodes["UVMap2Node"]
		if UVMap1Node != None and UVMap2Node != None:
			useSecondaryUVNode = addPropertyNode(matInfo["mPropDict"]["UseSecondaryUV_ColorLayer_MaskMap"], matInfo["currentPropPos"], nodeTree)
			
			uvMappingGroupNode = getDualUVMappingNodeGroup(nodeTree)
			uvMappingGroupNode.location = useSecondaryUVNode.location + Vector((300,0))
			nodeTree.links.new(UVMap1Node.outputs["UV"],uvMappingGroupNode.inputs["UV1"])
			nodeTree.links.new(UVMap2Node.outputs["UV"],uvMappingGroupNode.inputs["UV2"])
			nodeTree.links.new(useSecondaryUVNode.outputs["Value"],uvMappingGroupNode.inputs["UseSecondaryUV"])
			nodeTree.links.new(uvMappingGroupNode.outputs["Vector"],imageNode.inputs["Vector"])
	if "CMMSepNode" in nodeTree.nodes:
		CMMSeparateNode = nodeTree.nodes["CMMSepNode"]
	else:
		CMMSeparateNode = nodeTree.nodes.new('ShaderNodeSeparateRGB')
		CMMSeparateNode.location = currentPos
		CMMSeparateNode.name = "CMMSepNode"
	
	nodeTree.links.new(imageNode.outputs["Color"],CMMSeparateNode.inputs["Image"])
	if "S_col_R" in matInfo["mPropDict"] and "S_col_G" in matInfo["mPropDict"]:
		RColorNode = addPropertyNode(matInfo["mPropDict"]["S_col_R"], matInfo["currentPropPos"], nodeTree)
		GColorNode = addPropertyNode(matInfo["mPropDict"]["S_col_G"], matInfo["currentPropPos"], nodeTree)
		if matInfo["albedoNodeLayerGroup"] != None:
			matInfo["albedoNodeLayerGroup"].addMixLayer(RColorNode.outputs["Color"],CMMSeparateNode.outputs["R"],mixType = "MULTIPLY")
			matInfo["albedoNodeLayerGroup"].addMixLayer(GColorNode.outputs["Color"],CMMSeparateNode.outputs["G"],mixType = "MULTIPLY")
			
	elif "ColorLayer_R" in matInfo["mPropDict"] and "ColorLayer_G" in matInfo["mPropDict"] and "ColorLayer_B" in matInfo["mPropDict"] and "ColorLayer_A" in matInfo["mPropDict"]:
		RColorNode = addPropertyNode(matInfo["mPropDict"]["ColorLayer_R"], matInfo["currentPropPos"], nodeTree)
		
		
		if "Use_R" in matInfo["mPropDict"]:
			useRNode = addPropertyNode(matInfo["mPropDict"]["Use_R"], matInfo["currentPropPos"], nodeTree)
			multRNode = nodeTree.nodes.new("ShaderNodeMath")
			multRNode.location = useRNode.location + Vector((300,0))
			multRNode.operation = "MULTIPLY"
			nodeTree.links.new(useRNode.outputs["Value"],multRNode.inputs[0])
			nodeTree.links.new(CMMSeparateNode.outputs["R"],multRNode.inputs[1])
			RColorFactorSocket = multRNode.outputs["Value"]
		else:
			RColorFactorSocket = CMMSeparateNode.outputs["R"]
		
		GColorNode = addPropertyNode(matInfo["mPropDict"]["ColorLayer_G"], matInfo["currentPropPos"], nodeTree)
		
		if "Use_G" in matInfo["mPropDict"]:
			useGNode = addPropertyNode(matInfo["mPropDict"]["Use_G"], matInfo["currentPropPos"], nodeTree)
			multGNode = nodeTree.nodes.new("ShaderNodeMath")
			multGNode.location = useGNode.location + Vector((300,0))
			multGNode.operation = "MULTIPLY"
			nodeTree.links.new(useGNode.outputs["Value"],multGNode.inputs[0])
			nodeTree.links.new(CMMSeparateNode.outputs["G"],multGNode.inputs[1])
			GColorFactorSocket = multGNode.outputs["Value"]
		else:
			GColorFactorSocket = CMMSeparateNode.outputs["G"]
		
		BColorNode = addPropertyNode(matInfo["mPropDict"]["ColorLayer_B"], matInfo["currentPropPos"], nodeTree)
		
		if "Use_B" in matInfo["mPropDict"]:
			useBNode = addPropertyNode(matInfo["mPropDict"]["Use_B"], matInfo["currentPropPos"], nodeTree)
			multBNode = nodeTree.nodes.new("ShaderNodeMath")
			multBNode.location = useBNode.location + Vector((300,0))
			multBNode.operation = "MULTIPLY"
			nodeTree.links.new(useBNode.outputs["Value"],multBNode.inputs[0])
			nodeTree.links.new(CMMSeparateNode.outputs["B"],multBNode.inputs[1])
			BColorFactorSocket = multBNode.outputs["Value"]
		else:
			BColorFactorSocket = CMMSeparateNode.outputs["B"]
		
		AColorNode = addPropertyNode(matInfo["mPropDict"]["ColorLayer_A"], matInfo["currentPropPos"], nodeTree)
		
		if "Use_A" in matInfo["mPropDict"]:
			useANode = addPropertyNode(matInfo["mPropDict"]["Use_A"], matInfo["currentPropPos"], nodeTree)
			multANode = nodeTree.nodes.new("ShaderNodeMath")
			multANode.location = useANode.location + Vector((300,0))
			multANode.operation = "MULTIPLY"
			nodeTree.links.new(useANode.outputs["Value"],multANode.inputs[0])
			nodeTree.links.new(imageNode.outputs["Alpha"],multANode.inputs[1])
			AColorFactorSocket = multANode.outputs["Value"]
		else:
			AColorFactorSocket = imageNode.outputs["Alpha"]
			
		if matInfo["albedoNodeLayerGroup"] != None:
			matInfo["albedoNodeLayerGroup"].addMixLayer(RColorNode.outputs["Color"],RColorFactorSocket,mixType = "MULTIPLY")
			matInfo["albedoNodeLayerGroup"].addMixLayer(GColorNode.outputs["Color"],GColorFactorSocket,mixType = "MULTIPLY")
			matInfo["albedoNodeLayerGroup"].addMixLayer(BColorNode.outputs["Color"],BColorFactorSocket,mixType = "MULTIPLY")
			matInfo["albedoNodeLayerGroup"].addMixLayer(AColorNode.outputs["Color"],AColorFactorSocket,mixType = "MULTIPLY")
	return imageNode
def newCMASKNode (nodeTree,textureType,matInfo):
	imageNode = nodeTree.nodes[textureType]
	currentPos = [imageNode.location[0]+300,imageNode.location[1]]
	
	
	
	CMaskSeparateNode = nodeTree.nodes.new('ShaderNodeSeparateRGB')
	CMaskSeparateNode.location = currentPos
	
	nodeTree.links.new(imageNode.outputs["Color"],CMaskSeparateNode.inputs["Image"])
	
	#Fix for imported SF6 materials, this shouldn't matter in game since it gets overriden by the cmd files
	for prop in matInfo["mPropDict"].values():
		if "CustomizeRoughness" in prop.propName or "CustomizeMetal" in prop.propName:
			if prop.propValue[0] == 0.0:
				prop.propValue = [1.0]
		elif "CustomizeColor"  in prop.propName:
			if prop.propValue == [0.501960813999176, 0.501960813999176, 0.501960813999176, 1.0]:
				prop.propValue = [1.0,1.0,1.0,1.0]
	if "CustomizeColor_0" not in nodeTree.nodes:
		color0Node = addPropertyNode(matInfo["mPropDict"]["CustomizeColor_0"], matInfo["currentPropPos"], nodeTree)
		color1Node = addPropertyNode(matInfo["mPropDict"]["CustomizeColor_1"], matInfo["currentPropPos"], nodeTree)
		color2Node = addPropertyNode(matInfo["mPropDict"]["CustomizeColor_2"], matInfo["currentPropPos"], nodeTree)
		color3Node = addPropertyNode(matInfo["mPropDict"]["CustomizeColor_3"], matInfo["currentPropPos"], nodeTree)
		
		rough0Node = addPropertyNode(matInfo["mPropDict"]["CustomizeRoughness_0"], matInfo["currentPropPos"], nodeTree)
		rough1Node = addPropertyNode(matInfo["mPropDict"]["CustomizeRoughness_1"], matInfo["currentPropPos"], nodeTree)
		rough2Node = addPropertyNode(matInfo["mPropDict"]["CustomizeRoughness_2"], matInfo["currentPropPos"], nodeTree)
		rough3Node = addPropertyNode(matInfo["mPropDict"]["CustomizeRoughness_3"], matInfo["currentPropPos"], nodeTree)
		
		metal0Node = addPropertyNode(matInfo["mPropDict"]["CustomizeMetal_0"], matInfo["currentPropPos"], nodeTree)
		metal1Node = addPropertyNode(matInfo["mPropDict"]["CustomizeMetal_1"], matInfo["currentPropPos"], nodeTree)
		metal2Node = addPropertyNode(matInfo["mPropDict"]["CustomizeMetal_2"], matInfo["currentPropPos"], nodeTree)
		metal3Node = addPropertyNode(matInfo["mPropDict"]["CustomizeMetal_3"], matInfo["currentPropPos"], nodeTree)
		
		
		matInfo["albedoNodeLayerGroup"].addMixLayer(color0Node.outputs["Color"],CMaskSeparateNode.outputs["R"],mixType = "MULTIPLY")
		matInfo["albedoNodeLayerGroup"].addMixLayer(color1Node.outputs["Color"],CMaskSeparateNode.outputs["G"],mixType = "MULTIPLY")
		matInfo["albedoNodeLayerGroup"].addMixLayer(color2Node.outputs["Color"],CMaskSeparateNode.outputs["B"],mixType = "MULTIPLY")
		matInfo["albedoNodeLayerGroup"].addMixLayer(color3Node.outputs["Color"],imageNode.outputs["Alpha"],mixType = "MULTIPLY")
		
		matInfo["roughnessNodeLayerGroup"].addMixLayer(rough0Node.outputs["Value"],CMaskSeparateNode.outputs["R"],mixType = "MULTIPLY")
		matInfo["roughnessNodeLayerGroup"].addMixLayer(rough1Node.outputs["Value"],CMaskSeparateNode.outputs["G"],mixType = "MULTIPLY")
		matInfo["roughnessNodeLayerGroup"].addMixLayer(rough2Node.outputs["Value"],CMaskSeparateNode.outputs["B"],mixType = "MULTIPLY")
		matInfo["roughnessNodeLayerGroup"].addMixLayer(rough3Node.outputs["Value"],imageNode.outputs["Alpha"],mixType = "MULTIPLY")
		
		matInfo["metallicNodeLayerGroup"].addMixLayer(metal0Node.outputs["Value"],CMaskSeparateNode.outputs["R"],mixType = "MULTIPLY")
		matInfo["metallicNodeLayerGroup"].addMixLayer(metal1Node.outputs["Value"],CMaskSeparateNode.outputs["G"],mixType = "MULTIPLY")
		matInfo["metallicNodeLayerGroup"].addMixLayer(metal2Node.outputs["Value"],CMaskSeparateNode.outputs["B"],mixType = "MULTIPLY")
		matInfo["metallicNodeLayerGroup"].addMixLayer(metal3Node.outputs["Value"],imageNode.outputs["Alpha"],mixType = "MULTIPLY")
	else:#Is cmask2
		color4Node = addPropertyNode(matInfo["mPropDict"]["CustomizeColor_4"], matInfo["currentPropPos"], nodeTree)
		color5Node = addPropertyNode(matInfo["mPropDict"]["CustomizeColor_5"], matInfo["currentPropPos"], nodeTree)
		color6Node = addPropertyNode(matInfo["mPropDict"]["CustomizeColor_6"], matInfo["currentPropPos"], nodeTree)
		color7Node = addPropertyNode(matInfo["mPropDict"]["CustomizeColor_7"], matInfo["currentPropPos"], nodeTree)
	
		rough4Node = addPropertyNode(matInfo["mPropDict"]["CustomizeRoughness_4"], matInfo["currentPropPos"], nodeTree)
		rough5Node = addPropertyNode(matInfo["mPropDict"]["CustomizeRoughness_5"], matInfo["currentPropPos"], nodeTree)
		rough6Node = addPropertyNode(matInfo["mPropDict"]["CustomizeRoughness_6"], matInfo["currentPropPos"], nodeTree)
		rough7Node = addPropertyNode(matInfo["mPropDict"]["CustomizeRoughness_7"], matInfo["currentPropPos"], nodeTree)
		
		metal4Node = addPropertyNode(matInfo["mPropDict"]["CustomizeMetal_4"], matInfo["currentPropPos"], nodeTree)
		metal5Node = addPropertyNode(matInfo["mPropDict"]["CustomizeMetal_5"], matInfo["currentPropPos"], nodeTree)
		metal6Node = addPropertyNode(matInfo["mPropDict"]["CustomizeMetal_6"], matInfo["currentPropPos"], nodeTree)
		metal7Node = addPropertyNode(matInfo["mPropDict"]["CustomizeMetal_7"], matInfo["currentPropPos"], nodeTree)
		
		
		matInfo["albedoNodeLayerGroup"].addMixLayer(color4Node.outputs["Color"],CMaskSeparateNode.outputs["R"],mixType = "MULTIPLY")
		matInfo["albedoNodeLayerGroup"].addMixLayer(color5Node.outputs["Color"],CMaskSeparateNode.outputs["G"],mixType = "MULTIPLY")
		matInfo["albedoNodeLayerGroup"].addMixLayer(color6Node.outputs["Color"],CMaskSeparateNode.outputs["B"],mixType = "MULTIPLY")
		matInfo["albedoNodeLayerGroup"].addMixLayer(color7Node.outputs["Color"],imageNode.outputs["Alpha"],mixType = "MULTIPLY")
	
		matInfo["roughnessNodeLayerGroup"].addMixLayer(rough4Node.outputs["Value"],CMaskSeparateNode.outputs["R"],mixType = "MULTIPLY")
		matInfo["roughnessNodeLayerGroup"].addMixLayer(rough5Node.outputs["Value"],CMaskSeparateNode.outputs["G"],mixType = "MULTIPLY")
		matInfo["roughnessNodeLayerGroup"].addMixLayer(rough6Node.outputs["Value"],CMaskSeparateNode.outputs["B"],mixType = "MULTIPLY")
		matInfo["roughnessNodeLayerGroup"].addMixLayer(rough7Node.outputs["Value"],imageNode.outputs["Alpha"],mixType = "MULTIPLY")
		
		matInfo["metallicNodeLayerGroup"].addMixLayer(metal4Node.outputs["Value"],CMaskSeparateNode.outputs["R"],mixType = "MULTIPLY")
		matInfo["metallicNodeLayerGroup"].addMixLayer(metal5Node.outputs["Value"],CMaskSeparateNode.outputs["G"],mixType = "MULTIPLY")
		matInfo["metallicNodeLayerGroup"].addMixLayer(metal6Node.outputs["Value"],CMaskSeparateNode.outputs["B"],mixType = "MULTIPLY")
		matInfo["metallicNodeLayerGroup"].addMixLayer(metal7Node.outputs["Value"],imageNode.outputs["Alpha"],mixType = "MULTIPLY")
	return imageNode
def newATOSNode (nodeTree,textureType,matInfo):
	imageNode = nodeTree.nodes[textureType]
	currentPos = [imageNode.location[0]+300,imageNode.location[1]]
	
	
	separateNode = nodeTree.nodes.new('ShaderNodeSeparateRGB')
	separateNode.location = currentPos
	useLegacyHairUV2Occlusion = (matInfo["gameName"] in legacyUV2HairOcclusionList and "hair" in matInfo["mmtrName"].lower())
	
	#RE2 puts other masks in the alpha channel sometimes
	isMTOS = imageNode.image != None and "_mtos" in imageNode.image.filepath.lower()
	isMaskAlpha = matInfo["isMaskAlphaMMTR"]
	
	#Have to do this hack since there's no good way of telling whether the alpha channel is actually alpha with this game
	if matInfo["gameName"] == "DMC5" and (("Emissive_Intensity" in matInfo["mPropDict"] and matInfo["mPropDict"]["Emissive_Intensity"].propValue[0] != 0.0) or ("EmissiveIntensity" in matInfo["mPropDict"] and matInfo["mPropDict"]["EmissiveIntensity"].propValue[0] != 0.0) or ("Use_Emissive" in matInfo["mPropDict"] and matInfo["mPropDict"]["Use_Emissive"].propValue[0] == 1.0)):
		#TODO Set up DMC5 emission
		isMaskAlpha = True
	
	
	alphaUV2Node = None
	occlusionUV2Node = None
	cavityUV2Node = None
	makeUV2Node = False
	
	
	if "Alpha_UseSecondaryUV" in matInfo["mPropDict"]:
		makeUV2Node = True
		alphaUV2Node = addPropertyNode(matInfo["mPropDict"]["Alpha_UseSecondaryUV"], matInfo["currentPropPos"], nodeTree)
		
	if "Occlusion_UseSecondaryUV" in matInfo["mPropDict"]:
		makeUV2Node = True
		occlusionUV2Node = addPropertyNode(matInfo["mPropDict"]["Occlusion_UseSecondaryUV"], matInfo["currentPropPos"], nodeTree)
	elif "OcclusionMap_UseSecondaryUV" in matInfo["mPropDict"]:
		makeUV2Node = True
		occlusionUV2Node = addPropertyNode(matInfo["mPropDict"]["OcclusionMap_UseSecondaryUV"], matInfo["currentPropPos"], nodeTree)
	if "Cavity_UseSecondaryUV" in matInfo["mPropDict"]:
		makeUV2Node = True
		cavityUV2Node = addPropertyNode(matInfo["mPropDict"]["Cavity_UseSecondaryUV"], matInfo["currentPropPos"], nodeTree)
	currentPos[0] += 300
	nodeTree.links.new(imageNode.outputs["Color"],separateNode.inputs["Image"])
	if makeUV2Node or useLegacyHairUV2Occlusion:
		mappingNode = nodeTree.nodes.new('ShaderNodeMapping')
		mappingNode.location = currentPos
		uv2Node = nodeTree.nodes["UVMap2Node"]
		nodeTree.links.new(uv2Node.outputs["UV"],mappingNode.inputs["Vector"])
		currentPos[0] += 300
		imageNodeUV2 = nodeTree.nodes.new('ShaderNodeTexImage')
		imageNodeUV2.name = "UV2_"+textureType
		imageNodeUV2.label = "UV2_"+textureType
		imageNodeUV2.location = currentPos
		imageNodeUV2.image = imageNode.image
		nodeTree.links.new(mappingNode.outputs["Vector"],imageNodeUV2.inputs["Vector"])
		currentPos[0] += 300
		
		separateNodeUV2 = nodeTree.nodes.new('ShaderNodeSeparateRGB')
		separateNodeUV2.location = currentPos
		nodeTree.links.new(imageNodeUV2.outputs["Color"],separateNodeUV2.inputs["Image"])
		currentPos[0] += 300
		
		matInfo["translucentSocket"] = separateNode.outputs["G"]
			
		if alphaUV2Node != None:
			mixUVAlphaNode = nodeTree.nodes.new('ShaderNodeMixRGB')
			mixUVAlphaNode.location = currentPos
			nodeTree.links.new(separateNode.outputs["R"],mixUVAlphaNode.inputs["Color1"])
			nodeTree.links.new(separateNodeUV2.outputs["R"],mixUVAlphaNode.inputs["Color2"])
			nodeTree.links.new(alphaUV2Node.outputs["Value"],mixUVAlphaNode.inputs["Fac"])
			currentPos[0] += 300
			if not isMTOS and not isMaskAlpha:
				matInfo["alphaSocket"] = mixUVAlphaNode.outputs["Color"]
		else:
			if not isMTOS and not isMaskAlpha:
				matInfo["alphaSocket"] = separateNode.outputs["R"]
		
		if occlusionUV2Node != None or useLegacyHairUV2Occlusion:
			mixUVOCCNode = nodeTree.nodes.new('ShaderNodeMixRGB')
			mixUVOCCNode.location = currentPos
			nodeTree.links.new(separateNode.outputs["B"],mixUVOCCNode.inputs["Color1"])
			nodeTree.links.new(separateNodeUV2.outputs["B"],mixUVOCCNode.inputs["Color2"])
			if occlusionUV2Node != None:
				nodeTree.links.new(occlusionUV2Node.outputs["Value"],mixUVOCCNode.inputs["Fac"])
			else:
				if useLegacyHairUV2Occlusion:
					mixUVOCCNode.inputs["Fac"].default_value = 1.0
			currentPos[0] += 300
			matInfo["aoNodeLayerGroup"].addMixLayer( mixUVOCCNode.outputs["Color"])
		else:
			if matInfo["gameName"] != "SF6":#SF6 uses occlusion channel for something else
				matInfo["aoNodeLayerGroup"].addMixLayer(separateNode.outputs["B"])
		
		if cavityUV2Node != None:
			mixUVCavityNode = nodeTree.nodes.new('ShaderNodeMixRGB')
			mixUVCavityNode.location = currentPos
			nodeTree.links.new(imageNode.outputs["Alpha"],mixUVCavityNode.inputs["Color1"])
			nodeTree.links.new(imageNodeUV2.outputs["Alpha"],mixUVCavityNode.inputs["Color2"])
			nodeTree.links.new(cavityUV2Node.outputs["Value"],mixUVCavityNode.inputs["Fac"])
			currentPos[0] += 300
			matInfo["cavityNodeLayerGroup"].addMixLayer(mixUVCavityNode.outputs["Color"])
		else:
			if textureType == "AlphaTranslucentOcclusionCavityMap":
				matInfo["cavityNodeLayerGroup"].addMixLayer(imageNode.outputs["Alpha"])
	else:
		if not isMTOS and not isMaskAlpha:
			matInfo["alphaSocket"] = separateNode.outputs["R"]
		matInfo["translucentSocket"] = separateNode.outputs["G"]
		if matInfo["gameName"] != "SF6" and not useLegacyHairUV2Occlusion:#SF6 uses occlusion channel for something else
			matInfo["aoNodeLayerGroup"].addMixLayer(separateNode.outputs["B"])
		
		if textureType == "AlphaTranslucentOcclusionCavityMap":
			matInfo["cavityNodeLayerGroup"].addMixLayer(imageNode.outputs["Alpha"])
		else:
			matInfo["subsurfaceSocket"] = imageNode.outputs["Alpha"]
	
	return imageNode

def newOCTDNode (nodeTree,textureType,matInfo):
	imageNode = nodeTree.nodes[textureType]
	currentPos = [imageNode.location[0]+300,imageNode.location[1]]
	
	
	separateNode = nodeTree.nodes.new('ShaderNodeSeparateRGB')
	separateNode.location = currentPos
	currentPos[0] += 300
	nodeTree.links.new(imageNode.outputs["Color"],separateNode.inputs["Image"])
	
	
	if textureType == "OcclusionCavityTranslucentDetailMap":
		matInfo["translucentSocket"] = separateNode.outputs["B"]
	
	elif textureType == "OcclusionCavitySSSDetailMap":
		matInfo["subsurfaceSocket"] = separateNode.outputs["B"]
		
	matInfo["aoNodeLayerGroup"].addMixLayer(separateNode.outputs["R"])
	matInfo["cavityNodeLayerGroup"].addMixLayer(separateNode.outputs["G"])
	
	return imageNode
"""
def newUNKNNode (nodeTree,textureType,matInfo):
	imageNode = nodeTree.nodes.new('ShaderNodeTexImage')
	imageNode.label = textureType
	texture = bpy.data.images.get(os.path.split(texturePath)[1],None)
	if texture == None:
		imageNode.image = bpy.data.images.load(texturePath)
	else:
		imageNode.image = texture
	if "_alb" in texturePath.lower():
		imageNode.image.colorspace_settings.name = "sRGB"
	else:
		imageNode.image.colorspace_settings.name = "Non-Color"
	imageNode.image.alpha_mode = "CHANNEL_PACKED"
	imageNode.location = currentPos
	return imageNode
"""
nodeDict = {
	"ALBD":newALBDNode,
	"ALBM":newALBMNode,
	"ALBA":newALBANode,
	"ALB":newALBNode,
	"NRMR":newNRMRNode,
	"NRRT":newNRRTNode,
	"ALP":newALPNode,
	"CMM":newCMMNode,
	"CMASK":newCMASKNode,
	"EMI":newEMINode,
	"ATOS":newATOSNode,
	"OCTD":newOCTDNode,
	"NAM":newNAMNode,
	#"UNKN":newUNKNNode,
	
	}
def addTextureNode(nodeTree,nodeType,textureType,matInfo):
	#print(nodeType)
	#print(textureType)
	#print(texturePath)
	return nodeDict[nodeType](nodeTree,textureType,matInfo)
	