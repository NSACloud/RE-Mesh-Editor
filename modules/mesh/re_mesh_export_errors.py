from ..gen_functions import textColors
def addErrorToDict(errorDict,errorType,objectName):
	if errorType in errorDict:
		errorDict[errorType]["count"] += 1
		if objectName != None:
			errorDict[errorType]["objectSet"].add(objectName)
		
	else:
		if objectName != None:
			errorDict[errorType] = {"count":1,"objectSet":set([objectName])}
		else:
			errorDict[errorType] = {"count":1,"objectSet":set()}
		
errorInfoDict = {
"NoMeshesInCollection":"""No Meshes In Collection
No meshes were found in the target collection.
	
HOW TO FIX:
_______________
	
Specify a target collection in the export options that contains meshes, or leave it blank and move your meshes and armature into the Scene Collection.
""",

"MoreThanOneArmature":"""More Than One Armature
More than one armature was found in the target collection. Only one armature can be present in a mesh collection. 
	
HOW TO FIX:
_______________
	
Move the extra armature into another collection or delete it. 
""",
"NoMaterialOnSubMesh":"""No Material On Sub Mesh
A mesh has no material assigned to it. All meshes must have one material assigned to them.
	
HOW TO FIX:
_______________
	
Specify an MDF material name on the end of the object name separated by two underscores. See example, here the material name is "pl1000_Body_Mat".

Example Object Name: LOD_0_Group_0_Sub_0__pl1000_Body_Mat
""",

"MoreThanOneMaterialOnSubMesh":"""More Than One Material On Sub Mesh
A mesh has more than one material assigned to it. All meshes must have only one material assigned to them.
	
HOW TO FIX:
_______________
	
Select the listed mesh in edit mode, press A to select all vertices. Then press P > Material to split the mesh by it's materials.
""",

"NoUVMapOnSubMesh":"""No UV Map On Sub Mesh
A mesh has no UV map. All meshes require at least one uv map.
	
HOW TO FIX:
_______________
	
Create a UV map.
""",

"NoVerticesOnSubMesh":"""No Vertices On Sub Mesh
A mesh has no vertices. All meshes must have at least 3 vertices and 1 face.
	
HOW TO FIX:
_______________
	
Delete the listed mesh.
""",

"NoFacesOnSubMesh":"""No Faces On Sub Mesh
A mesh has no faces. All meshes must have at least 3 vertices and 1 face.
	
HOW TO FIX:
_______________
	
Delete the listed mesh.
""",

"LooseVerticesOnSubMesh":"""Loose Vertices On Sub Mesh
A mesh has loose vertices with no faces assigned.
	
HOW TO FIX:
_______________
	
Select the listed mesh in edit mode, press A to select all vertices. In the menu bar at the top, select > Mesh > Clean Up > Delete Loose.

OR

Press the "Delete Loose" button in RE Toolbox to delete loose vertices on all meshes.
""",

"NonTriangulatedFace":"""Non Triangulated Faces
A mesh has non triangulated faces. All faces must be triangulated.
	
HOW TO FIX:
_______________
	
Select the listed mesh in edit mode, press A to select all vertices. Press Ctrl + T to triangulate faces.

OR

Press the "Triangulate Meshes" button in RE Toolbox to triangulate all meshes.
""",
"MultipleUVsAssignedToVertex":"""Multiple UVs Assigned To Vertex
A mesh has multiple uvs assigned to a single vertex.
	
HOW TO FIX:
_______________
	
Select the listed mesh in edit mode, switch to edge select mode.
Press A to select all edges,then press F3 to search for and select "Seams From Islands".
Select an edge that is marked red on the mesh, then press Shift > G > Seam. 
Press V to rip the vertices and then press Esc so that the vertices stay in the same location.

OR

Press the "Solve Repeated UVs" button in RE Toolbox to do this process automatically.
""",
"MaxVerticesExceeded":"""Max Vertices Exceeded On Sub Mesh
A mesh exceeded the limit of 65535 vertices.
	
HOW TO FIX:
_______________
	
Separate parts of the mesh into more sub meshes.

OR

Use the decimate modifier to reduce mesh quality.
""",
"MaxFacesExceeded":"""Max Faces Exceeded On Sub Mesh
A mesh exceeded the limit of 4294967295 faces.
	
HOW TO FIX:
_______________
	
Reconsider the life choices that led you to decide to try to export a mesh with 4 million faces.
""",

"MaxWeightsPerVertexExceeded":"""Max Weights Per Vertex Exceeded On Sub Mesh
A vertex has more the maximum of 8 (or 6 for SF6) weights assigned to it.
	
HOW TO FIX:
_______________
	
Limit total weights to 8 in weight paint mode and normalize all weights from the Weights menu.

OR

Use the "Limit Total and Normalize All Weights" button in RE Toolbox.

""",

"NoBonesOnArmature":"""No Bones on Armature
The armature in the target collection has no bones.
	
HOW TO FIX:
_______________
	
Import a valid armature from an existing mesh file.
""",
"NoWeightsOnMesh":"""No Weights on Sub Mesh
A mesh has an armature, but no weights assigned to bones.
	
HOW TO FIX:
_______________
	
Add a new vertex group and weight it to a bone on the armature in weight paint mode.
""",
"MaxWeightedBonesExceeded":"""Max Weighted Bones Exceeded
The mesh exceeded the limit of 256 bones with weights assigned to them.
	
HOW TO FIX:
_______________
	
Reduce the amount of chain bones on the armature.
""",
	}
	
def printErrorDict(errorDict):
	print(f"\n{textColors.FAIL}Unable to export mesh. {len(errorDict)} error(s) were found that need to be fixed.{textColors.ENDC}\n")
	for index, errorType in enumerate(sorted(errorDict.keys())):
		count = errorDict[errorType]["count"]
		objectSet = errorDict[errorType]["objectSet"]
		errorInfo = errorInfoDict[errorType]
		nameListString = ""
		if objectSet:
			nameListString = f"\nObjects with this error ({str(len(objectSet))}):\n"
			for name in sorted(list(objectSet)):
				nameListString += "["+name +"]\n"
		print(f"{textColors.FAIL}ERROR ({str(index+1)} / {len(errorDict)}): {str(count)} instance(s) of {errorInfo}{nameListString}\n__________________________________{textColors.ENDC}")