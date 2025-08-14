#Author: NSA Cloud
from modules.mesh.file_re_mesh import readREMesh,writeREMesh,ParsedREMeshToREMesh
from modules.mesh.re_mesh_parse import ParsedREMesh,Skeleton,LODLevel,VisconGroup

#Mesh plotting script


#--- Settings
#RE4 leon body
#INPUT = r"D:\EXTRACT\RE4_EXTRACT\re_chunk_000\natives\STM\_Chainsaw\Character\ch\cha0\cha000\00\cha000_00.mesh.221108797"

#SF6 streaming stage mesh
#INPUT = r"D:\EXTRACT\SF6_EXTRACT\re_chunk_000\natives\STM\Product\Environment\Props\Resource\sm3X\sm36\sm36_034_crane\sm36_034_crane_00.mesh.230110883"


#MHWilds streaming body mesh
#INPUT = r"D:\EXTRACT\MHWILDS_EXTRACT\re_chunk_000\natives\STM\Art\Model\Character\ch03\006\001\2\ch03_006_0012.mesh.241111606"

#KG MPLY stage mesh
#INPUT = r"D:\EXTRACT\KG_EXTRACT\re_chunk_000\natives\stm\environment\st\st22\st22_001\st22_001.mesh.240306278"

#MHWilds MPLY totem pole pillar mesh
#INPUT = r"D:\EXTRACT\MHWILDS_EXTRACT\re_chunk_000\natives\STM\Art\Model\StageModel\sm43\sm43_381\sm43_381_00.mesh.241111606"

#MHWilds MPLY small statue mesh
INPUT = r"D:\EXTRACT\MHWILDS_EXTRACT\re_chunk_000\natives\STM\Art\Model\StageModel\sm42\sm42_350\sm42_350_00.mesh.241111606"

allLODs = True
allGroups = True
allSubmeshes = True

maxMeshPlots = 999#Stop plotting if this amount of meshes is reached, plots can take a long time so this limits it

solid = True#Shading type

lodIndex = 0
groupIndex = 0
submeshIndex = 0

#---


from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import numpy as np

reMesh = readREMesh(INPUT)


if reMesh.meshBufferHeader != None and len(reMesh.meshBufferHeader.streamingBufferHeaderList) != 0:
	for bufferIndex,buffer in enumerate(reMesh.meshBufferHeader.streamingBufferHeaderList):
		print(f"Streaming Buffer {bufferIndex}")
		for key,value in buffer.__dict__.items():
			if key != "vertexBuffer" and key != "faceBuffer":
				print(f"\t{key}:{value}")
		for element in buffer.vertexElementList:
			for key,value in element.__dict__.items():
				print(f"\t{key}:{value}")
			print()

parseMesh = ParsedREMesh()
parseMesh.ParseREMesh(reMesh)
#print(parseMesh.mainMeshLODList[0].visconGroupList[0].subMeshList[0].faceList)

if allLODs:
	lodList = parseMesh.mainMeshLODList
else:
	lodList = [parseMesh.mainMeshLODList[lodIndex]]
plottedMeshes = 0
for lodIndex, lod in enumerate(lodList):
	
	if allGroups:
		groupList = parseMesh.mainMeshLODList[lodIndex].visconGroupList
	else:
		groupList = [parseMesh.mainMeshLODList[lodIndex].visconGroupList[groupIndex]]
	if plottedMeshes >= maxMeshPlots:
		break
	for groupIndex, group in enumerate(groupList):
		if plottedMeshes >= maxMeshPlots:
			break
		if allSubmeshes:
			submeshList = parseMesh.mainMeshLODList[lodIndex].visconGroupList[groupIndex].subMeshList
		else:
			submeshList = [parseMesh.mainMeshLODList[lodIndex].visconGroupList[groupIndex].subMeshList[submeshIndex]]
		for submeshIndex, submesh in enumerate(submeshList):
			verts = np.array(submesh.vertexPosList)
			
			
			faces = parseMesh.mainMeshLODList[lodIndex].visconGroupList[groupIndex].subMeshList[submeshIndex].faceList
			x = verts[:,0]
			y = verts[:,1]
			z = verts[:,2] * -1#Flip
			
			ax = plt.axes(projection = "3d")
			
			#Z up
			ax.plot_trisurf(x, z, y, triangles = faces, edgecolor=[[0,0,0]], linewidth=0.15, alpha= 1.0 if solid else 0.0, shade=solid)
			ax.set_title(f"LOD_{lodIndex}_Group_{groupIndex}_Sub_{submeshIndex}")
			plt.show()
			
			plottedMeshes += 1
			if plottedMeshes >= maxMeshPlots:
				break
print("done")
