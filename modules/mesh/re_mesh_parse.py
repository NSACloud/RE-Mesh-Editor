import numpy as np
import struct
from .file_re_mesh import Matrix4x4,AABB,Sphere,CompressedSixWeightIndices,CompressedBlendShapeVertexInt

typeNameMapping = ["Position","NorTan","UV","UV2","Weight","Color"]
typeStrideDict = {
	"Position":12,
	"NorTan":8,
	"UV":4,
	"UV2":4,
	"Weight":16,
	"Color":4,
	}

blendShapeNameMapping =["BlendShapeByte","BlendShapeShort"]
blendShapeStrideDict = {
	"BlendShapeByte":4,
	"BlendShapeShort":8,
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

def ReadBlendShapeByteBuffer(blendShapeBuffer,tags):
	blendShapeIntArray = np.frombuffer(blendShapeBuffer,dtype="<L")
	
	blendShapeArray = np.empty((len(blendShapeIntArray),3),dtype = "<f")
	bf = CompressedBlendShapeVertexInt()
	
	for index, value in enumerate(blendShapeIntArray):
		bf.asUInt32 = value
		blendShapeArray[index] = np.asarray((bf.pos.x,bf.pos.y,bf.pos.z))
	
	#print(blendShapeArray)
	"""
	blendShapeArray = np.frombuffer(blendShapeBuffer,dtype="<4b",)
	normalizingArray = None
	for index,delta in enumerate(blendShapeArray):#Hack, still trying to figure out how to get the deltas to be correct
		if delta[3] == 127:#Find the value of a delta with no change and subtract that from all deltas
			normalizingArray = blendShapeArray[index]
			break
	#blendShapeFloatArray = np.empty((len(blendShapeBuffer)//4), dtype=np.dtype("<3f"))
	
	
	
	blendShapeArray = blendShapeArray.astype("float32")
	blendShapeArray = blendShapeArray / blendShapeArray[:,3][:,np.newaxis]
	blendShapeArray = np.delete(blendShapeArray, 3, axis=1)#Remove 4th column
	
	if normalizingArray is not None:
		normalizingArray = normalizingArray.astype("float32")
		normalizingArray = normalizingArray / 127
		normalizingArray = np.delete(normalizingArray, 3, axis=0)#Remove 4th column
		#print(normalizingArray)
		blendShapeArray = blendShapeArray - np.tile(normalizingArray,(len(blendShapeArray),1))
	#print(blendShapeFloatArray)
	#blendShapeArray = np.where(blendShapeArray < 0,blendShapeArray / 128, blendShapeArray / 127)
	"""
	"""
	#TODO Do this through numpy
	
	for index, entry in enumerate(blendShapeArray):
		blendShapeFloatArray[index][0] = blendShapeArray[index][0] / (127 + 1 * (blendShapeArray[index][0] < 0))
		blendShapeFloatArray[index][1] = blendShapeArray[index][1] / (127 + 1 * (blendShapeArray[index][1] < 0))
		blendShapeFloatArray[index][2] = blendShapeArray[index][2] / (127 + 1 * (blendShapeArray[index][2] < 0))
		print(blendShapeFloatArray[index])
		#blendShapeFloatArray[index][3] = blendShapeArray[index][3] / (127 + 1 * (blendShapeArray[index][3] < 0))
	"""
	return blendShapeArray

def ReadBlendShapeShortBuffer(blendShapeBuffer,tags):
	blendShapeArray = np.frombuffer(blendShapeBuffer,dtype="<4H",)
	#blendShapeFloatArray = np.empty((len(blendShapeBuffer)//8), dtype=np.dtype("<3f"))
	blendShapeArray = np.delete(blendShapeArray, 3, axis=1)#Remove 4th column
	blendShapeArray = blendShapeArray.astype("float32")
	
	blendShapeArray = np.where(blendShapeArray < 0,blendShapeArray / 32768, blendShapeArray / 32767)
	"""
	#TODO Do this through numpy
	for index, entry in enumerate(blendShapeArray):
		blendShapeFloatArray[index][0] = blendShapeArray[index][0] / (32767 + 1 * (blendShapeArray[index][0] < 0))
		blendShapeFloatArray[index][1] = blendShapeArray[index][1] / (32767 + 1 * (blendShapeArray[index][1] < 0))
		blendShapeFloatArray[index][2] = blendShapeArray[index][2] / (32767 + 1 * (blendShapeArray[index][2] < 0))
		#blendShapeFloatArray[index][3] = blendShapeArray[index][3] / (32767 + 1 * (blendShapeArray[index][3] < 0))
	"""
	return blendShapeArray

BlendShapeBufferReadDict = {
	"BlendShapeByte":ReadBlendShapeByteBuffer,
	"BlendShapeShort":ReadBlendShapeShortBuffer,
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
	importedElementsSet = set()
	for index,vertexElement in enumerate(vertexElementList):
		if index == lastIndex:
			#bufferEnd = len(vertexBuffer)
			bufferEnd = vertexElementList[index].posStartOffset + (vertexElement.stride * len(vertexDict["Position"]))
		else:
			bufferEnd = vertexElementList[index+1].posStartOffset
		elementName = typeNameMapping[vertexElement.typing]
		#print(f"{elementName} start {str(vertexElement.posStartOffset)} end {str(bufferEnd)} size {str(bufferEnd-vertexElement.posStartOffset)}")
		#print(elementName)

		if elementName not in importedElementsSet:#Prevent importing of doubled vertex element entries present on some meshes
			#I suspect the doubled vertex elements are for when the shadow meshes have their own unique LODs
			#TODO Make shadowVertexDict
			if "shadowLOD" not in tagSet:#Skip reading the first vertex element entry of a type if reading unique shadow LOD
				vertexDict[elementName] = BufferReadDict[elementName](vertexBuffer[vertexElement.posStartOffset:bufferEnd],tagSet)
			importedElementsSet.add(elementName)
		elif "shadowLOD" in tagSet:
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
		self.blendShapeList = []

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

class BlendShape:
	def __init__(self):
		self.blendShapeName = "newBlendShape"
		self.deltas = []

def parseLODStructure(reMesh,targetLODList,vertexDict,usedVertexOffsetDict, blendShapeBuffer = None):
	lodList = []
	currentBlendShapeOffset = 0
	blendShapeDict = {}
	for lodIndex, lodGroup in enumerate(targetLODList):
		
		#BLEND SHAPES - LOD level
		if reMesh.blendShapeHeader != None and len(reMesh.blendShapeHeader.blendShapeList) > lodIndex:
			blendShapeLODData = reMesh.blendShapeHeader.blendShapeList[lodIndex]
		else:
			blendShapeLODData = None
		
		#BLEND SHAPES - submesh
		currentBlendShapeNameIndex = 0
		currentBlendDeltaOffset = 0
		if blendShapeLODData != None:
			blendShapeTags = set()#Unused currently but there if needed in the future
			#identifier = [reMesh.lodHeader.lodGroupOffsetList[lodIndex]]
			print(f"LOD Index {str(lodIndex)}")
			bufferType = blendShapeNameMapping[blendShapeLODData.typing]
			bufferStride = blendShapeStrideDict[bufferType]
			
			#endOffset = currentBlendShapeOffset + (blendShapeLODData.vertCount*bufferStride)
			
			#blendShapeDeltas = BlendShapeBufferReadDict[bufferType](blendShapeBuffer[currentBlendShapeOffset:endOffset],tags = blendShapeTags)
			
			#TODO Get slice containing only current LOD, currently parses whole buffer for each LOD
			blendShapeDeltas = BlendShapeBufferReadDict[bufferType](blendShapeBuffer,tags = blendShapeTags)
			
			#print(f"Delta Vert Count {str(len(blendShapeDeltas))}")
			#(f"Delta Length {str(endOffset-currentBlendShapeOffset)}")
			#currentBlendShapeOffset = endOffset
			
			
			
			currentDeltaOffset = 0
			#TODO - Blend shape vertex count can span across meshes, add list of vertex ranges for every sub mesh
			for blendTargetIndex,blendTarget in enumerate(blendShapeLODData.blendTargetList):
				
				if blendShapeLODData.typing == 0:
					step_size_x = (blendShapeLODData.aabbList[blendTargetIndex].max.x - blendShapeLODData.aabbList[blendTargetIndex].min.x) / (2 ** 11 - 1)
					step_size_y = (blendShapeLODData.aabbList[blendTargetIndex].max.y - blendShapeLODData.aabbList[blendTargetIndex].min.y) / (2 ** 10 - 1)
					step_size_z = (blendShapeLODData.aabbList[blendTargetIndex].max.z - blendShapeLODData.aabbList[blendTargetIndex].min.z) / (2 ** 11 - 1)
				else:
					step_size_x = (blendShapeLODData.aabbList[blendTargetIndex].max.x - blendShapeLODData.aabbList[blendTargetIndex].min.x) / (2 ** 16 - 1)
					step_size_y = (blendShapeLODData.aabbList[blendTargetIndex].max.y - blendShapeLODData.aabbList[blendTargetIndex].min.y) / (2 ** 16 - 1)
					step_size_z = (blendShapeLODData.aabbList[blendTargetIndex].max.z - blendShapeLODData.aabbList[blendTargetIndex].min.z) / (2 ** 16 - 1)
				
				for blendNameIndex in range(0,blendTarget.blendShapeNum):
					blendShapeName = reMesh.rawNameList[reMesh.blendShapeNameRemapList[currentBlendShapeNameIndex+blendNameIndex]]
					
					#print(blendShapeEntry.blendShapeName)
					if blendTarget.subMeshEntryCount != 0:#If Version >= SF6
						for subMeshEntry in blendTarget.subMeshEntryList:
							
							blendShapeEntry = BlendShape()
							blendShapeEntry.blendShapeName = blendShapeName
							blendShapeEntry.deltas = blendShapeDeltas[currentBlendDeltaOffset:currentBlendDeltaOffset+subMeshEntry.vertCount]
							blendShapeEntry.deltas[:,0] *= step_size_x
							blendShapeEntry.deltas[:,1] *= step_size_y
							blendShapeEntry.deltas[:,2] *= step_size_z
							
							#blendShapeEntry.deltas[:,0] -= blendShapeLODData.aabbList[blendTargetIndex].max.x
							#blendShapeEntry.deltas[:,1] -= blendShapeLODData.aabbList[blendTargetIndex].max.y
							#blendShapeEntry.deltas[:,2] -= blendShapeLODData.aabbList[blendTargetIndex].max.z
							
							currentBlendDeltaOffset += subMeshEntry.vertCount
							if subMeshEntry.subMeshVertexStartIndex in blendShapeDict:
								blendShapeDict[subMeshEntry.subMeshVertexStartIndex].append(blendShapeEntry)
							else:
								blendShapeDict[subMeshEntry.subMeshVertexStartIndex] = [blendShapeEntry]
							#blendShapeList.append(blendShapeEntry)
							#blendShapeDict[subMeshEntry.subMeshVertexStartIndex] = blendShapeList
						
					else:
						blendShapeEntry = BlendShape()
						blendShapeEntry.blendShapeName = blendShapeName
						blendShapeEntry.deltas = blendShapeDeltas[currentBlendDeltaOffset:currentBlendDeltaOffset+blendTarget.vertCount]
						
						blendShapeEntry.deltas[:,0] *= step_size_x
						blendShapeEntry.deltas[:,1] *= step_size_y
						blendShapeEntry.deltas[:,2] *= step_size_z
						
						currentBlendDeltaOffset += blendTarget.vertCount
						if blendTarget.subMeshVertexStartIndex in blendShapeDict:
							blendShapeDict[blendTarget.subMeshVertexStartIndex].append(blendShapeEntry)
						else:
							blendShapeDict[blendTarget.subMeshVertexStartIndex] = [blendShapeEntry]
							
				currentBlendShapeNameIndex += blendTarget.blendShapeNum
				
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
				#print(f"{meshInfo.faceStartIndex*2} - {meshInfo.faceStartIndex*2+meshInfo.faceCount*2}")
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
				
				if blendShapeLODData != None:
					"""
					vertexCount = len(vertexDict["Position"])
					for blendShapeIndex in range(0,blendShapeLODData.blendShapeCount):
						
						blendShapeEntry = BlendShape()
						blendShapeEntry.blendShapeName = reMesh.rawNameList[reMesh.blendShapeNameRemapList[blendShapeIndex]]
						
						meshVertStart = meshInfo.vertexStartIndex
						meshVertEnd = bufferEnd
						
						blendShapeVertStart = blendShapeLODData.vertOffset
						blendShapeVertEnd = blendShapeLODData.vertOffset + blendShapeLODData.vertCount
						
						if meshVertStart < blendShapeVertEnd and meshVertEnd > blendShapeVertStart:
							blendShapeEntry.deltas = [(0, 0, 0) for i in range(meshVertStart, blendShapeVertStart)]
							for ix in range(max(meshVertStart, blendShapeVertStart), min(meshVertEnd, blendShapeVertEnd)):
								blendShapeEntry.deltas.append(blendShapeDeltas[ix-blendShapeVertStart])
								
							for ix in range(meshVertEnd, blendShapeVertEnd):
								blendShapeEntry.deltas.append((0, 0, 0))
						else:
							blendShapeEntry.deltas = []
						#blendShapeEntry.deltas = blendShapeDeltas[currentDeltaOffset:currentDeltaOffset+vertexCount].tolist()
						#print(len(blendShapeEntry.deltas))
						#print(blendShapeEntry.blendShapeName)
						#print(blendShapeEntry.deltas)
						submesh.blendShapeList.append(blendShapeEntry)
				#blendShapeDict[identifier] = shapeList
				"""
				if meshInfo.vertexStartIndex in blendShapeDict:
					submesh.blendShapeList.extend(blendShapeDict[meshInfo.vertexStartIndex])
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
			if reMesh.meshVersion == 230110883:#Street Fighter 6 mesh version
				tags.add("SixWeightCompressed")#Add tag to parse compressed weights
			#if duplicate in vertexelementlist, add shadowLOD tag
			
			vertexDict = ReadVertexElementBuffers(reMesh.meshBufferHeader.vertexElementList, reMesh.meshBufferHeader.vertexBuffer,tags)
			#TODO
			#tags.add("shadowLOD")
			#shadowVertexDict = ReadVertexElementBuffers(reMesh.meshBufferHeader.vertexElementList, reMesh.meshBufferHeader.vertexBuffer,tags)
		#Parse Blend Shapes
		vertexCount = len(vertexDict["Position"])
		lastElement = reMesh.meshBufferHeader.vertexElementList[-1]
		blendShapeStartPos = lastElement.posStartOffset + vertexCount * lastElement.stride
		blendShapeBuffer = reMesh.meshBufferHeader.vertexBuffer[blendShapeStartPos:]
		if reMesh.blendShapeHeader != None:
			
			print(f"blendShape buffer start pos {str(reMesh.meshBufferHeader.vertexBufferOffset+blendShapeStartPos)}")
			
				
				
		#Parse Main Meshes
		if reMesh.lodHeader != None and vertexDict != None:
			self.boundingSphere = reMesh.lodHeader.sphere
			self.boundingBox = reMesh.lodHeader.bbox
			self.mainMeshLODList = parseLODStructure(reMesh,reMesh.lodHeader.lodGroupList,vertexDict,usedVertexOffsetDict,blendShapeBuffer)
			for i in range(len(self.mainMeshLODList)):
				lodOffsetDict[reMesh.lodHeader.lodGroupOffsetList[i]] = self.mainMeshLODList[i]
		if reMesh.shadowHeader != None and vertexDict != None:
			for offset in reMesh.shadowHeader.lodGroupOffsetList:
				if offset in lodOffsetDict:
					self.shadowMeshLinkedLODList.append(lodOffsetDict[offset])
				else:#This shouldn't happen
					#Update: it does :/
					#RE3_EXTRACT\re_chunk_000\natives\stm\escape\character\enemy\em9200\mesh\em9200.mesh.2109108288
					#TODO Add unique shadow mesh LOD importing
					print("ERROR: Shadow mesh has unique lod offsets, cannot import")
			#self.shadowMeshLODList = parseLODStructure(reMesh,reMesh.shadowHeader.lodGroupList,vertexDict,usedVertexOffsetDict)
		
		#TODO Add occlusion mesh