import numpy as np
import struct
from .file_re_mesh import Matrix4x4,AABB,Sphere,CompressedSixWeightIndices

typeNameMapping = ["Position","NorTan","UV","UV2","Weight","Color"]
typeStrideDict = {
	"Position":12,
	"NorTan":8,
	"UV":4,
	"UV2":4,
	"Weight":16,
	"Color":4,
	}

def ReadPosBuffer(vertexPosBuffer,tags):
	posList = np.frombuffer(vertexPosBuffer,dtype="<3f").tolist()
	return posList

def ReadNorTanBuffer(norTanBuffer,tags):
	norTanArray = np.frombuffer(norTanBuffer,dtype="<4b")
	norTanArray = np.delete(norTanArray, 3, axis=1)
	#print(norTanArray)
	norTanArray = np.divide(norTanArray,127)
	#norTanArray = np.add(norTanArray,0.5)
	norTanList = norTanArray.tolist()
	#Slice list by even and odd to get normals and tangents
	normalList = norTanList[::2]
	tangentList = norTanList[1::2]
	#print(normalList)
	return (normalList,tangentList)

def ReadUVBuffer(uvBuffer,tags):
	#uvArray = np.frombuffer(uvBuffer,dtype="<2e",)
	uvArray = np.frombuffer(bytearray(uvBuffer),dtype="<e",)#Convert bytes to bytearray to make numpy array mutable
	#Do (1-x) to v value
	uvArray[1::2] *= -1
	uvArray[1::2] += 1
	uvArray = uvArray.reshape((-1,2))
	return uvArray.tolist()

def ReadWeightBuffer(weightBuffer,tags):
	#weightArray = np.frombuffer(weightBuffer,dtype=f"<{stride//2}B")
	weightArray = np.frombuffer(weightBuffer,dtype="<8B")
	boneIndicesList = weightArray[::2]
	if "SixWeightCompressed" in tags:
		#TODO make decompression faster, this can probably done entirely through numpy with pack and unpackbits
		#Spent too much time trying to get it to work through numpy only, gave up and used ctypes instead
		#Convert byte array to list of uint64 to be passed to bitfield
		
		
		bf = CompressedSixWeightIndices()
		uint64List = np.frombuffer(weightArray[::2].tobytes(),dtype="<Q")
		

		boneIndicesList = [(0,0,0,0,0,0,0,0)]*len(uint64List)
		#print(boneIndicesList)
		for index, value in enumerate(uint64List):
			bf.asUInt64 = value
			boneIndicesList[index] = (bf.weights.w0,bf.weights.w1,bf.weights.w2,bf.weights.w3,bf.weights.w4,bf.weights.w5,0,0)
		#print(boneIndicesArray)
	else:
		boneIndicesList = weightArray[::2].tolist()
	boneWeightsList = np.divide(weightArray[1::2],255).tolist()
	return (boneIndicesList,boneWeightsList)

def ReadColorBuffer(colorBuffer,tags):
	colorArray = np.frombuffer(colorBuffer,dtype="<4B",)
	colorArray = np.divide(colorArray,255)
	return colorArray.tolist()

def ReadFaceBuffer(faceBuffer):
	faceBuffer = np.frombuffer(faceBuffer,dtype="<3H",)
	return faceBuffer.tolist()


BufferReadDict = {
	"Position":ReadPosBuffer,
	"NorTan":ReadNorTanBuffer,
	"UV":ReadUVBuffer,
	"UV2":ReadUVBuffer,
	"Weight":ReadWeightBuffer,
	"Color":ReadColorBuffer,
	}

def ReadVertexElementBuffers(vertexElementList,vertexBuffer,tagSet):
	vertexDict = {
		"Position":None,
		"NorTan":None,
		"UV":None,
		"UV2":None,
		"Weight":None,
		"Color":None,
		}
	lastIndex = len(vertexElementList)-1
	for index,vertexElement in enumerate(vertexElementList):
		if index == lastIndex:
			#bufferEnd = len(vertexBuffer)
			bufferEnd = vertexElementList[index].posStartOffset + (vertexElement.stride * len(vertexDict["Position"]))
		else:
			bufferEnd = vertexElementList[index+1].posStartOffset
		elementName = typeNameMapping[vertexElement.typing]
		#print(f"{elementName} start {str(vertexElement.posStartOffset)} end {str(bufferEnd)} size {str(bufferEnd-vertexElement.posStartOffset)}")
		#print(elementName)
		vertexDict[elementName] = BufferReadDict[elementName](vertexBuffer[vertexElement.posStartOffset:bufferEnd],tagSet)
		
	return vertexDict

class VisconGroup:
	def __init__(self):
		self.visconGroupNum = 0
		self.subMeshList = []
	
class LODLevel:
	def __init__(self):
		self.visconGroupList = []
		self.lodDistance = 0.0

class SubMesh:
	def __init__(self):
		self.vertexPosList = []
		self.faceList = []
		self.normalList = []
		self.tangentList = []
		self.uvList = []
		self.uv2List = []
		self.faceList = []
		self.weightList = []
		self.weightIndicesList = []
		self.colorList = []
		self.materialIndex = 0
		self.meshVertexOffset = 0#Used for determining mesh reuse
		self.isReusedMesh = False
		self.linkedSubMesh = None
		self.subMeshIndex = 0

class ParsedBone:
	def __init__(self):
		self.boneName = "BONE"
		self.boneIndex = 0
		self.parentIndex = 0
		self.nextSiblingIndex = 0
		self.nextChildIndex = 0
		self.symmetryBoneIndex = 0
		self.worldMatrix = Matrix4x4()
		self.localMatrix = Matrix4x4()
		self.inverseMatrix = Matrix4x4()
		self.boundingBox = None#Bounding box of weighted vertices
class Skeleton:
	def __init__(self):
		self.weightedBones = []
		self.boneList = []

def parseLODStructure(reMesh,targetLODList,vertexDict,usedVertexOffsetDict):
	lodList = []
	for lodGroup in targetLODList:
		lod = LODLevel()
		lod.lodDistance = lodGroup.distance
		for visconGroup in lodGroup.meshGroupList:
			group = VisconGroup()
			group.visconGroupNum = visconGroup.visconGroupID
			lastSubmeshIndex = len(visconGroup.vertexInfoList) -1
			for index,meshInfo in enumerate(visconGroup.vertexInfoList):
				#print(f"submesh {index},face count {meshInfo.faceCount},face start {meshInfo.faceStartIndex} start offset {meshInfo.faceStartIndex*2} end offset {meshInfo.faceStartIndex*2+meshInfo.faceCount*2},")
				
				if index == lastSubmeshIndex:
					bufferEnd = visconGroup.vertexInfoList[0].vertexStartIndex+visconGroup.vertexCount
				else:
					bufferEnd = visconGroup.vertexInfoList[index+1].vertexStartIndex
				submesh = SubMesh()
				submesh.materialIndex = meshInfo.materialIndex
				submesh.subMeshIndex = index
				
				if meshInfo.vertexStartIndex in usedVertexOffsetDict:
					#print(f"REUSED MESH OFFSET AT Group {str(group.visconGroupNum)} Sub{str(index)}")
					submesh.isReusedMesh = True
					submesh.linkedSubMesh = usedVertexOffsetDict[meshInfo.vertexStartIndex]
				else:
					usedVertexOffsetDict[meshInfo.vertexStartIndex] = submesh
				submesh.meshVertexOffset = meshInfo.vertexStartIndex
				
				
				if vertexDict["Position"] != None:
					submesh.vertexPosList = vertexDict["Position"][meshInfo.vertexStartIndex:bufferEnd]
				submesh.faceList = ReadFaceBuffer(reMesh.meshBufferHeader.faceBuffer[meshInfo.faceStartIndex*2:meshInfo.faceStartIndex*2+meshInfo.faceCount*2])
				if vertexDict["NorTan"] != None:
					submesh.normalList = vertexDict["NorTan"][0][meshInfo.vertexStartIndex:bufferEnd]
					submesh.tangentList = vertexDict["NorTan"][1][meshInfo.vertexStartIndex:bufferEnd]
				if vertexDict["UV"] != None:
					submesh.uvList = vertexDict["UV"][meshInfo.vertexStartIndex:bufferEnd]
				if vertexDict["UV2"] != None:
					submesh.uv2List = vertexDict["UV2"][meshInfo.vertexStartIndex:bufferEnd]
				if vertexDict["Weight"] != None:
					submesh.weightIndicesList = vertexDict["Weight"][0][meshInfo.vertexStartIndex:bufferEnd]
					submesh.weightList = vertexDict["Weight"][1][meshInfo.vertexStartIndex:bufferEnd]
				if vertexDict["Color"] != None:
					submesh.colorList = vertexDict["Color"][meshInfo.vertexStartIndex:bufferEnd]
				
				group.subMeshList.append(submesh)
			lod.visconGroupList.append(group)
		lodList.append(lod)
	return lodList
		
class ParsedREMesh:
	def __init__(self):
		self.skeleton = None
		self.mainMeshLODList = []
		#self.shadowMeshLODList = []#Commented out because shadow meshes can only reuse lods from main mesh
		self.shadowMeshLinkedLODList = []#
		self.occlusionMeshLODList = []
		self.nameList = []
		self.boneNameRemapList = []
		self.materialNameList = []
		self.boundingSphere = Sphere()
		self.boundingBox = AABB()
		self.bufferHasPosition = False
		self.bufferHasNorTan = False
		self.bufferHasUV = False
		self.bufferHasUV2 = False
		self.bufferHasWeight = False
		self.bufferHasColor = False
	def ParseREMesh(self,reMesh,importOptions = {"importAllLOD":True,"importShadowMesh":True,"importOcclusionMesh":True,"importBlendShapes":True}):
		vertexDict = None
		usedVertexOffsetDict = dict()
		lodOffsetDict = dict()#Used for linking shadow mesh lods to main mesh lods
		self.nameList = reMesh.rawNameList
		self.boneNameRemapList = reMesh.boneNameRemapList
		self.materialRemapList = reMesh.materialNameRemapList
		#Parse Skeleton
		for remapIndex in reMesh.materialNameRemapList:
			self.materialNameList.append(reMesh.rawNameList[remapIndex])
		if reMesh.skeletonHeader != None:
			self.skeleton = Skeleton()
			self.skeleton.weightedBones = []
			
			for remapIndex in reMesh.skeletonHeader.boneRemapList:
				self.skeleton.weightedBones.append(reMesh.rawNameList[reMesh.boneNameRemapList[remapIndex]])
			
			weightedBoneIndex = 0
			for i in range(reMesh.skeletonHeader.boneCount):
				#print(i)
				bone = ParsedBone()
				bone.boneName = reMesh.rawNameList[reMesh.boneNameRemapList[i]]
				bone.boneIndex = i
				bone.parentIndex = reMesh.skeletonHeader.boneInfoList[i].boneParent
				bone.nextSiblingIndex = reMesh.skeletonHeader.boneInfoList[i].boneSibling
				bone.nextChildIndex = reMesh.skeletonHeader.boneInfoList[i].boneChild
				bone.symmetryBoneIndex = reMesh.skeletonHeader.boneInfoList[i].boneSymmetric
				bone.worldMatrix = reMesh.skeletonHeader.worldMatList[i]
				bone.localMatrix = reMesh.skeletonHeader.localMatList[i]
				bone.inverseMatrix = reMesh.skeletonHeader.inverseMatList[i]
				
				if bone.boneName in self.skeleton.weightedBones:
					bone.boundingBox = reMesh.boneBoundingBoxHeader.bboxList[weightedBoneIndex]
					weightedBoneIndex += 1
				self.skeleton.boneList.append(bone)
			
		#Parse Vertex Buffer
		if reMesh.meshBufferHeader != None:
			tags = set()
			if reMesh.fileHeader.version == 220705151:#Street Fighter 6 internal version
				tags.add("SixWeightCompressed")#Add tag to parse compressed weights
			vertexDict = ReadVertexElementBuffers(reMesh.meshBufferHeader.vertexElementList, reMesh.meshBufferHeader.vertexBuffer,tags)
		#Parse Main Meshes
		if reMesh.lodHeader != None and vertexDict != None:
			self.boundingSphere = reMesh.lodHeader.sphere
			self.boundingBox = reMesh.lodHeader.bbox
			self.mainMeshLODList = parseLODStructure(reMesh,reMesh.lodHeader.lodGroupList,vertexDict,usedVertexOffsetDict)
			for i in range(len(self.mainMeshLODList)):
				lodOffsetDict[reMesh.lodHeader.lodGroupOffsetList[i]] = self.mainMeshLODList[i]
		if reMesh.shadowHeader != None and vertexDict != None:
			for offset in reMesh.shadowHeader.lodGroupOffsetList:
				if offset in lodOffsetDict:
					self.shadowMeshLinkedLODList.append(lodOffsetDict[offset])
				else:#This shouldn't happen
					print("ERROR: Shadow mesh has unique lod offsets, cannot import")
			#self.shadowMeshLODList = parseLODStructure(reMesh,reMesh.shadowHeader.lodGroupList,vertexDict,usedVertexOffsetDict)
		
		#TODO Add occlusion mesh