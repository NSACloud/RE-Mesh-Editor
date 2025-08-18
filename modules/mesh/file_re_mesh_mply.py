#Author: NSA Cloud

from ..gen_functions import splitNativesPath,getPaddedPos,getBit,setBit,getPaddingAmount,textColors,raiseWarning,raiseError,read_uint,read_int,read_int64,read_uint64,read_float,read_short,read_ushort,read_ubyte,read_unicode_string,read_byte,write_uint,write_int,write_int64,write_uint64,write_float,write_short,write_ushort,write_ubyte,write_unicode_string,write_byte,read_string,write_string
import os
import numpy as np
import struct
from io import BytesIO
from itertools import chain
import ctypes

import time

#from .file_re_mesh import meshFileVersionToNewVersionDict,meshFileVersionToInternalVersionDict,getNearestRemapVersion

timeFormat = "%d"
#Mesh version numbers do not always increase for newer versions of the file format
#Therefore mesh versions have been remapped to new values to allow for conditional import and export changes depending on the mesh version

#Leaving gaps in case the versions in between these need to be parsed



#Games using MPLY
VERSION_DD2 = 115#file:230517984,internal:230517984
VERSION_KG = 120#file:240306278,internal:230727984
VERSION_DD2NEW = 124#file:240423143,internal:230517984
VERSION_MHWILDS = 130#file:240820143,internal:240704828



c_uint64 = ctypes.c_uint64
c_uint32 = ctypes.c_uint32
c_uint8 = ctypes.c_uint8
class ContentFlagsA_bits(ctypes.LittleEndianStructure):
	_fields_ = 	[
					("isSkinning",c_uint8,1),
					("hasJoint",c_uint8,1),
					("hasBlendShape",c_uint8,1),
					("hasVertexGroup",c_uint8,1),
					("quadEnable",c_uint8,1),
					("streamingBVH",c_uint8,1),
					("hasTertiaryUV",c_uint8,1),
					("hasVertexColor",c_uint8,1),
		
				]
	
class ContentFlagsA(ctypes.Union):
	
	_anonymous_ = ("flags",)
	_fields_ =	[
					("flags",    ContentFlagsA_bits ),
					("asUInt8", c_uint8)
				]

class ContentFlagsB_bits(ctypes.LittleEndianStructure):
	_fields_ = 	[
					("solvedOffset",c_uint8,1),
					("bufferCount",c_uint8,3),
					("useRayTracingVertexAnimation",c_uint8,1),
					("useSDF",c_uint8,1),
					("enableRebraiding",c_uint8,2),
		
				]
	
class ContentFlagsB(ctypes.Union):
	
	_anonymous_ = ("flags",)
	_fields_ =	[
					("flags",    ContentFlagsB_bits ),
					("asUInt8", c_uint8)
				]

class ClusterFlagsA_bits(ctypes.LittleEndianStructure):
	_fields_ = 	[
					("smallPos",c_uint8,1),
					("unkn1",c_uint8,1),
					("unkn2",c_uint8,1),
					("unkn3",c_uint8,1),
					("unkn4",c_uint8,1),
					("unkn5",c_uint8,1),
					("smallNormal",c_uint8,1),
					("unkn7",c_uint8,1),
		
				]
	
class ClusterFlagsA(ctypes.Union):
	
	_anonymous_ = ("flags",)
	_fields_ =	[
					("flags",    ClusterFlagsA_bits ),
					("asUInt8", c_uint8)
				]

class ClusterFlagsB_bits(ctypes.LittleEndianStructure):
	_fields_ = 	[
					("unkn0",c_uint8,1),
					("unkn1",c_uint8,1),
					("unkn2",c_uint8,1),
					("unkn3",c_uint8,1),
					("unkn4",c_uint8,1),
					("unkn5",c_uint8,1),
					("unkn6",c_uint8,1),
					("useUnknStruct",c_uint8,1),
		
				]
	
class ClusterFlagsB(ctypes.Union):
	
	_anonymous_ = ("flags",)
	_fields_ =	[
					("flags",    ClusterFlagsB_bits ),
					("asUInt8", c_uint8)
				]

class FileHeader():
	def __init__(self):
		self.magic = 1498173517
		self.version = 0
		self.fileSize = 0
		self.unknHash = 0
		self.contentFlagsA = ContentFlagsA()
		self.contentFlagsB = ContentFlagsB() #Bitflag 1000 XXXX-[GroupPivot/Floats][Blendshape][Skeleton][AABB]
		self.pad = 0
		self.wilds_unkn0 = 0
		self.stringCount = 0
		self.pad2 = 0
		self.unknOffset0 = 0
		self.unknOffset1 = 0
		self.meshletLayoutOffset = 0
		self.meshletBVHOffset = 0
		self.meshletPartsOffset = 0
		self.unknOffset2 = 0
		self.unknOffset3 = 0
		self.unknOffset4 = 0
		self.unknOffset5 = 0
		self.unknOffset6 = 0
		self.unknOffset7 = 0
		self.materialNameRemapOffset = 0
		self.unknOffset8 = 0
		self.unknOffset9 = 0
		self.stringTableOffset = 0
		self.unknOffset10 = 0
		self.streamingChunkOffset = 0
		self.gpuMeshletOffset = 0
		self.sdfPathOffset = 0
		self.sdfPath = ""
		
	def read(self,file,version):
		self.magic = read_uint(file)
		self.version = read_uint(file)
		self.fileSize = read_uint(file)
		self.unknHash = read_uint(file)
		if version >= VERSION_MHWILDS:
			
			self.wilds_unkn0 = read_uint(file)
			self.stringCount = read_ushort(file)
			self.contentFlagsA.asUInt8 = read_ubyte(file)
			self.contentFlagsB.asUInt8 = read_ubyte(file)
			self.unknOffset0 = read_uint64(file)
			self.unknOffset1 = read_uint64(file)
			self.gpuMeshletOffset = read_uint64(file)
			
			self.unknOffset2 = read_uint64(file)
			self.meshletLayoutOffset = read_uint64(file)
			self.meshletBVHOffset = read_uint64(file)
			self.meshletPartsOffset = read_uint64(file)
			self.unknOffset3 = read_uint64(file)
			self.unknOffset4 = read_uint64(file)
			self.unknOffset5 = read_uint64(file)
			self.unknOffset6 = read_uint64(file)
			self.unknOffset7 = read_uint64(file)
			self.unknOffset8 = read_uint64(file)
			self.materialNameRemapOffset = read_uint64(file)
			self.unknOffset9 = read_uint64(file)
			self.unknOffset10 = read_uint64(file)
			self.stringTableOffset = read_uint64(file)
			self.streamingChunkOffset = read_uint64(file)
			
		else:
			self.contentFlagsA.asUInt8 = read_ubyte(file)
			self.contentFlagsB.asUInt8 = read_ubyte(file)
			self.pad = read_ushort(file)
			self.stringCount = read_ushort(file)
			self.pad2 = read_ushort(file)
			self.unknOffset0 = read_uint64(file)
			self.unknOffset1 = read_uint64(file)
			self.meshletLayoutOffset = read_uint64(file)
			self.meshletBVHOffset = read_uint64(file)
			self.meshletPartsOffset = read_uint64(file)
			self.unknOffset2 = read_uint64(file)
			self.unknOffset3 = read_uint64(file)
			self.unknOffset4 = read_uint64(file)
			self.unknOffset5 = read_uint64(file)
			self.unknOffset6 = read_uint64(file)
			self.unknOffset7 = read_uint64(file)
			self.materialNameRemapOffset = read_uint64(file)
			self.unknOffset8 = read_uint64(file)
			self.unknOffset9 = read_uint64(file)
			self.stringTableOffset = read_uint64(file)
			self.unknOffset10 = read_uint64(file)
			self.streamingChunkOffset = read_uint64(file)
			self.gpuMeshletOffset = read_uint64(file)
		self.sdfPathOffset = read_uint64(file)
		currentPos = file.tell()
		if self.sdfPathOffset != 0:
			file.seek(self.sdfPathOffset)
			self.sdfPath = read_unicode_string(file)
			file.seek(currentPos)
			
	def write(self,file,version):
		pass#TODO


class MeshletHeader():
	def __init__(self):
		self.minAABB = (0.0,0.0,0.0)
		self.lodNum = 0
		self.loadedLod = 0
		self.residentLod = 0
		self.undefined = 0
		self.maxAABB = (0.0,0.0,0.0)
		self.validLodBits = 0
		self.lodClustersOffset = [0,0,0,0,0,0,0,0]
		self.lodFactor = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
		self.bindlessGeometryOffset = [0,0,0,0,0,0,0,0]
	def read(self,file):
		self.minAABB = (read_float(file),read_float(file),read_float(file))
		self.lodNum = read_ubyte(file)
		self.loadedLod = read_ubyte(file)
		self.residentLod = read_ubyte(file)
		self.undefined = read_ubyte(file)
		self.maxAABB = (read_float(file),read_float(file),read_float(file))
		self.validLodBits = read_uint(file)
		self.lodClustersOffset = [read_uint(file),read_uint(file),read_uint(file),read_uint(file),read_uint(file),read_uint(file),read_uint(file),read_uint(file)]
		self.lodFactor = [read_float(file),read_float(file),read_float(file),read_float(file),read_float(file),read_float(file),read_float(file),read_float(file)]
		self.bindlessGeometryOffset = [read_uint(file),read_uint(file),read_uint(file),read_uint(file),read_uint(file),read_uint(file),read_uint(file),read_uint(file)]
		

	def write(self,file):
		pass#TODO


class MeshletLayout():
	def __init__(self):
		self.gpuMeshletOffset = 0
		self.meshletHeader = MeshletHeader()
		self.wilds_unkn0 = 0
		self.wilds_unkn1 = 0
		self.gpuDataSize = 0
		self.unkn = 0
		self.gpuMeshletHeader = MeshletHeader()
	def read(self,file,version):
		self.gpuMeshletOffset = read_uint64(file)
		self.meshletHeader.read(file)
		if version >= VERSION_MHWILDS:
			self.wilds_unkn0 = read_uint64(file)
			self.wilds_unkn1 = read_uint64(file)
		self.gpuDataSize = read_uint(file)
		self.unkn = read_uint(file)
		currentPos = file.tell()
		file.seek(self.gpuMeshletOffset)
		self.gpuMeshletHeader.read(file)
		file.seek(currentPos)
	def write(self,file):
		pass#TODO

class MeshletCompactedClusterHeaderBitField_bits(ctypes.LittleEndianStructure):
	_fields_ = 	[
					("vertexCount",c_uint64,8),
					("indexCount",c_uint64,9),
					("no_rt",c_uint64,1),
					("alpha_test",c_uint64,1),
					("transparent",c_uint64,1),
					("positionCompressLevel",c_uint64,2),
					("pad",c_uint64,1),
					("materialId",c_uint64,8),
					("partsId",c_uint64,8),
					("aabbCenterOffset",c_uint64,24),
		
				]
	
class MeshletCompactedClusterHeaderBitField(ctypes.Union):
	
	_anonymous_ = ("fields",)
	_fields_ =	[
					("fields",    MeshletCompactedClusterHeaderBitField_bits ),
					("asUInt64", c_uint64)
				]

class MeshletCompactedClusterHeader():
	def __init__(self):
		self.bitfield = MeshletCompactedClusterHeaderBitField()
		self.vertexOffsetBytes = 0
		self.indexOffsetBytes = 0

	def read(self,file):
		self.bitfield.asUInt64 = read_uint64(file)
		#print("Cluster Info")
		#for field in self.bitfield.fields._fields_:
		    #print(field[0], getattr(self.bitfield.fields, field[0]))
		self.vertexOffsetBytes = read_uint(file)
		self.indexOffsetBytes = read_uint(file)

	def write(self,file):
		pass#TODO

class QuantizeAABBCenter():
	def __init__(self):
		self.X = 0
		self.Y = 0
		self.Z = 0

	def read(self,file):
		self.X = read_ushort(file)
		self.Y = read_ushort(file)
		self.Z = read_ushort(file)

	def write(self,file):
		pass#TODO

class ClusterEntry():
	def __init__(self):
		self.headerCount = 0
		self.unkn0 = 0
		self.unkn1 = 0

	def read(self,file):
		self.headerCount = read_ushort(file)
		self.unkn0 = read_ubyte(file)
		self.unkn1 = read_ubyte(file)

	def write(self,file):
		pass#TODO

class MeshletBVH():
	def __init__(self):
		self.gpuClusterHeadersOffset = 0
		self.gpuClusterQuantizeOffset = 0
		self.offset = (0.0,0.0,0.0)
		self.scale = 0
		self.clusterEntryList = []
		self.clusterOffsetList = []
		self.meshletBVHOffsetList = []
		self.clusterHeaderLODList = []
		self.quantizeAABBLODList = []
		

	def read(self,file):
		self.gpuClusterHeadersOffset = read_uint64(file)
		self.gpuClusterQuantizeOffset = read_uint64(file)
		self.offset = (read_float(file),read_float(file),read_float(file))
		self.scale = read_float(file)
		for _ in range(0,8):
			entry = ClusterEntry()
			entry.read(file)
			self.clusterEntryList.append(entry)
		for _ in range(0,8):
			self.clusterOffsetList.append(read_uint(file))
		for _ in range(0,8):
			self.meshletBVHOffsetList.append(read_uint(file))
		currentPos = file.tell()
		for index, entry in enumerate(self.clusterEntryList):
			if entry.headerCount != 0:
				file.seek(self.clusterOffsetList[index] + self.gpuClusterHeadersOffset)
				lodList = []
				for _ in range(0,entry.headerCount):
					headerEntry = MeshletCompactedClusterHeader()
					headerEntry.read(file)
					lodList.append(headerEntry)
				self.clusterHeaderLODList.append(lodList)
				#print(f"lod {index}")
				#print(f"cluster count {len(lodList)}")
		
		if self.gpuClusterQuantizeOffset != 0:	
			file.seek(self.gpuClusterQuantizeOffset)
			for entry in self.clusterEntryList:
				if entry.headerCount != 0:
					lodList = []
					for _ in range(0,entry.headerCount):
						aabbCenterEntry = QuantizeAABBCenter()
						aabbCenterEntry.read(file)
						lodList.append(aabbCenterEntry)
					self.quantizeAABBLODList.append(lodList)
		file.seek(currentPos)
		
	def write(self,file):
		pass#TODO


class MeshletPartsLayout():
	def __init__(self):
		self.partIndicesOffset = 0
		self.partsNum = 0
		self.reserve = 0
		self.partIndicesList = []

	def read(self,file):
		self.partIndicesOffset = read_uint64(file)
		self.partsNum = read_uint(file)
		self.reserve = read_uint(file)
		currentPos = file.tell()
		file.seek(self.partIndicesOffset)
		for _ in range(0,self.partsNum):
			self.partIndicesList.append(read_ubyte(file))
		file.seek(currentPos)
				
	def write(self,file):
		pass#TODO




class StreamingInfoEntry():
	def __init__(self):
		self.bufferStart = 0
		self.bufferLength = 0
	def read(self,file):
		self.bufferStart = read_uint(file)
		self.bufferLength = read_uint(file)

	def write(self,file):
		write_uint(file, self.bufferStart)
		write_uint(file, self.bufferLength)

class StreamingInfo():
	def __init__(self):
		self.entryCount = 0
		self.unkn1 = 0
		self.entryOffset = 0
		self.streamingInfoEntryList = []
	def read(self,file):
		self.entryCount = read_uint(file)
		self.unkn1 = read_uint(file)
		self.entryOffset = read_uint64(file)
		
		currentPos = file.tell()
		file.seek(self.entryOffset)
		for i in range(0,self.entryCount):
			entry = StreamingInfoEntry()
			entry.read(file)
			self.streamingInfoEntryList.append(entry)
		file.seek(currentPos)
	def write(self,file):
		write_uint(file, self.entryCount)
		write_uint(file, self.unkn1)
		write_uint64(file, self.entryOffset)

COMPRESSED_POS_DATA_STRIDE = 6
NORTAN_STRIDE = 8
UV_STRIDE = 4
COLOR_STRIDE = 4

class ClusterInfo():
	def __init__(self):
		self.posX = 0.0#Controls postion of meshlet, this value is the same across all meshlets in the file, likely used to move the model to the origin.
		self.posY = 0.0
		self.posZ = 0.0
		self.vertexCount = 0
		self.faceCount = 0
		self.unkn0 = 0#Sometimes 1
		self.unkn1 = 0
		self.relPosX = 0
		self.unknVal0 = 0
		self.relPosY = 0
		self.unknVal1 = 0
		self.relPosZ = 0
		self.unknVal2 = 0
		self.flagsA = ClusterFlagsA()
		self.flagsB = ClusterFlagsB()
		self.unkn5A = 0
		self.unkn5B = 0#Stays same throughout whole file, but different across files
		
		self.faceBuffer = bytes()
		self.vertexBuffer = bytes()
		
	def read(self,file,contentFlagsA):
		self.posX = read_float(file)#AABB center maybe
		self.posY = read_float(file)
		self.posZ = read_float(file)
		self.vertexCount = read_ubyte(file)
		self.faceCount = read_ubyte(file)
		self.unkn0 = read_ubyte(file)
		self.unkn1 = read_ubyte(file)
		self.relPosX = read_ushort(file)
		self.unknVal0 = read_ushort(file)#Bounding box length/height/width maybe
		self.relPosY = read_ushort(file)
		self.unknVal1 = read_ushort(file)#Bounding box length/height/width maybe
		self.relPosZ = read_ushort(file)
		self.unknVal2 = read_ushort(file)#Bounding box length/height/width maybe
		self.relPos = (self.relPosX/65535,self.relPosY/65535,self.relPosZ/65535)
		self.flagsA.asUInt8 = read_ubyte(file)
		self.flagsB.asUInt8 = read_ubyte(file)
		self.unkn5A = read_ubyte(file)
		self.unkn5B = read_ubyte(file)
		
		self.faceBuffer = file.read(self.faceCount*3)#Faces are streamed from streaming mesh, max of 128 faces for non streaming
		
		print(self.vertexCount)
		print(self.faceCount)
		
		#Skip padding
		file.seek(getPaddedPos(file.tell(), 4))
		
		print(f"vert start {file.tell()}")
		self.posBuffer = file.read(self.vertexCount*COMPRESSED_POS_DATA_STRIDE)
		#Skip padding again after pos since the stride isn't divisible by 4 
		file.seek(getPaddedPos(file.tell(), 4))
		if self.flagsA.flags.smallNormal:
			self.normalBuffer = file.read(self.vertexCount*4)
		else:
			self.normalBuffer = file.read(self.vertexCount*8)
		#TODO
		if self.flagsB.flags.useUnknStruct:
			self.unknStructBuffer = file.read(12)
		else:
			self.unknStructBuffer = None
		#This structure varies in size, it's either 12 bytes or 16 bytes and I haven't found what indicates which struct to use yet
			
		self.uvBuffer = file.read(self.vertexCount*UV_STRIDE)
		if contentFlagsA.hasVertexColor:
			self.colorBuffer = file.read(self.vertexCount*COLOR_STRIDE)
		else:
			self.colorBuffer = None
		
	def write(self,file):
		pass

class ClusterLODEntry():
	def __init__(self):
		self.entryCount = 0
		self.entryOffsetList = []
		self.entryList = []
	def read(self,file,startOffset,contentFlagsA):
		self.entryCount = read_uint(file)
		
		for i in range(0,self.entryCount):
			self.entryOffsetList.append(read_uint(file))
		for offset in self.entryOffsetList:
			#print(offset)
			file.seek(startOffset+offset)
			entry = ClusterInfo()
			entry.read(file,contentFlagsA)
			self.entryList.append(entry)

class ClusterInfoLayout():
	def __init__(self):
		self.lodList = []
	def read(self,file,startOffset,LODOffsetList,contentFlagsA):
		
		for offset in LODOffsetList:
			if offset != 0:
				file.seek(startOffset + offset)
				entry = ClusterLODEntry()
				entry.read(file,startOffset,contentFlagsA)
				self.lodList.append(entry)
			
	def write(self,file):
		pass
class REMeshMPLY():
	def __init__(self):
		self.isMPLY = True
		self.meshVersion = 0
		self.fileHeader = FileHeader()
		self.meshletLayout = MeshletLayout()
		self.meshletBVH = MeshletBVH()
		self.meshletPartsLayout = MeshletPartsLayout()
		
		self.rawNameOffsetList = []
		self.rawNameList = []
		self.materialNameRemapList = []
		self.streamingInfoHeader = None
		self.clusterInfoLayout = None
		
		#Unused, only here for compatibility with existing mesh code
		self.lodHeader = None
		self.shadowHeader = None
		self.skeletonHeader = None
		self.meshBufferHeader = None
		self.boneNameRemapList = []

	def read(self,file,version,lodTarget = None,streamingBuffer = None):#LOD target is an int that determines what lod level to import, the rest get ignored
		self.streamingBuffer = streamingBuffer
		if streamingBuffer != None:
			lodTarget = None#Disable lod target optimization since all lods are needed	
		self.fileHeader.read(file,version)
		if self.fileHeader.meshletLayoutOffset:
			file.seek(self.fileHeader.meshletLayoutOffset)
			self.meshletLayout.read(file,version)
			
		if self.fileHeader.meshletBVHOffset:
			file.seek(self.fileHeader.meshletBVHOffset)
			self.meshletBVH.read(file)
			
		if self.fileHeader.meshletPartsOffset:
			file.seek(self.fileHeader.meshletPartsOffset)
			self.meshletPartsLayout.read(file)
		
		#if self.fileHeader.materialNameRemapOffset:
			#file.seek(self.fileHeader.materialNameRemapOffset)
			#for _ in range(0,self.fileHeader.stringCount):
				#self.materialNameRemapList.append(read_ushort(file))
		if self.fileHeader.stringCount:
			file.seek(self.fileHeader.stringTableOffset)
			for _ in range(0,self.fileHeader.stringCount):
				self.rawNameOffsetList.append(read_uint64(file))
			
			for offset in self.rawNameOffsetList:
				file.seek(offset)
				self.rawNameList.append(read_string(file))
		if self.fileHeader.streamingChunkOffset:	
			file.seek(self.fileHeader.streamingChunkOffset)
			self.streamingInfoHeader = StreamingInfo()
			self.streamingInfoHeader.read(file)
			if self.streamingInfoHeader.entryCount != 0 and streamingBuffer == None:
				raise Exception("Streaming file associated with mesh is missing, can't import.")
		if self.fileHeader.gpuMeshletOffset and self.meshletLayout.gpuDataSize != 0:
			
			self.clusterInfoLayout = ClusterInfoLayout()
			self.clusterInfoLayout.read(file, self.meshletLayout.gpuMeshletOffset, self.meshletLayout.gpuMeshletHeader.lodClustersOffset,self.fileHeader.contentFlagsA.flags)
			
			#file.seek(self.fileHeader.gpuMeshletOffset)
			#self.gpuData = file.read(self.meshletLayout.gpuDataSize)
		
		#for field in self.fileHeader.contentFlagsA.flags._fields_:
		    #print(field[0], getattr(self.fileHeader.contentFlagsA.flags, field[0]))
			
		
	def write(self,file,version):
		pass#TODO
		
class sizeData:
	def __init__(self,version):
		pass#TODO
		#self.MESH_HEADER_SIZE = 128
		#if version >= VERSION_SF6:
			#self.MESH_HEADER_SIZE = 168

def ParsedREMeshToREMeshMPLY(parsedMesh,meshVersion):
	print(f"Mesh Version:{meshVersion}")
	version = meshFileVersionToNewVersionDict.get(meshVersion,getNearestRemapVersion(meshVersion)) 
	print(f"Remapped Version:{version}")
	sd = sizeData(version)
	currentOffset = 0
	currentVertexIndex = 0
	currentFaceIndex = 0
	
	#TODO
	
	
	return reMeshMPLY
