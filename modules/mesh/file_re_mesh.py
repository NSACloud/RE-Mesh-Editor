#Author: NSA Cloud
#Credit to AsteriskAmpersand for original re mesh addon that I used for reference
#Also credit to AlphaZomega for noesis re mesh plugin and re mesh 010 template

#How mesh import/export works:
#1. The mesh file is imported in it's original structure and layout in this file (file_re_mesh.py)
#2. The mesh structure is converted into an intermediary parsed format in re_mesh_parse.py
#3. The parsed mesh format is passed to blender to be imported by blender_re_mesh.py
#4. For export in blender, the mesh is checked for errors or things that otherwise wont work in the mesh format
#5. The parsed mesh format is rebuilt inside blender_re_mesh.py once it has been error checked
#6. The parsed format is passed back to file_re_mesh.py and rebuilt into a mesh structure (ParsedREMeshToREMesh())

IMPORT_BLEND_SHAPES = False#Disabled by default because it's broken at the moment.
#Set to True if you want to try to fix blend shape importing. The relevant code is in re_mesh_parse.py.
#There's something wrong with getting the amount of deltas and also the way the deltas are parsed is not correct.

#Meshes to test blend shapes with:
#MHR player face "F:\MHR_EXTRACT\extract\re_chunk_000\natives\STM\player\mod\face\pl_face000.mesh.2109148288"
#RE4R leon face "I:\RE4_EXTRACT\re_chunk_000\natives\STM\_Chainsaw\Character\ch\cha0\cha000\10\cha000_10.mesh.221108797"
#SF6 chun li body "J:\SF6_EXTRACT\re_chunk_000\natives\stm\product\model\esf\esf004\001\01\esf004_001_01.mesh.230110883"


from ..gen_functions import splitNativesPath,getPaddedPos,getBit,setBit,getPaddingAmount,textColors,raiseWarning,raiseError,read_uint,read_int,read_int64,read_uint64,read_float,read_short,read_ushort,read_ubyte,read_unicode_string,read_byte,write_uint,write_int,write_int64,write_uint64,write_float,write_short,write_ushort,write_ubyte,write_unicode_string,write_byte,read_string,write_string
import os
import numpy as np
import struct
from io import BytesIO
from itertools import chain
import ctypes

import time

timeFormat = "%d"
#Mesh version numbers do not always increase for newer versions of the file format
#Therefore mesh versions have been remapped to new values to allow for conditional import and export changes depending on the mesh version

#Leaving gaps in case the versions in between these need to be parsed
VERSION_DMC5 = 75#file:1808282334,internal:386270720
VERSION_RE2 = 80#file:1808312334,internal:386270720
VERSION_RE3 = 85#file:1902042334,internal:21011200
VERSION_RE8 = 90#file:2101050001,internal:2020091500
VERSION_RERT = 95#file:2109108288,internal:21041600
VERSION_RE7RT = 96#file:220128762,internal:21041600
VERSION_MHRSB = 100#file:2109148288,internal:21091000
VERSION_SF6 = 105#file:230110883,internal:220705151
VERSION_RE4 = 110#file:221108797,internal:220822879
VERSION_DD2 = 115#file:230517984,internal:230517984
VERSION_KG = 120#file:240306278,internal:230727984
VERSION_DD2NEW = 124#file:240423143,internal:230517984
VERSION_DR = 125#file:240424828,internal:240423829
VERSION_MHWILDS = 130#file:240820143,internal:240704828


meshFileVersionToNewVersionDict = {
	1808282334:VERSION_DMC5,
	1808312334:VERSION_RE2,
	1902042334:VERSION_RE3,
	2101050001:VERSION_RE8,
	2102020001:VERSION_RE8,#RE VERSE
	2109108288:VERSION_RERT,
	220128762:VERSION_RE7RT,
	2109148288:VERSION_MHRSB,
	230110883:VERSION_SF6,
	221108797:VERSION_RE4,
	231011879:VERSION_DD2,
	240306278:VERSION_KG,
	240423143:VERSION_DD2NEW,
	240424828:VERSION_DR,
	240820143:VERSION_MHWILDS,
	}
newVersionToMeshFileVersion = {
	VERSION_DMC5:1808282334,
	VERSION_RE2:1808312334,
	VERSION_RE3:1902042334,
	VERSION_RE8:2101050001,
	VERSION_RERT:2109108288,
	VERSION_RE7RT:220128762,
	VERSION_MHRSB:2109148288,
	VERSION_SF6:230110883,
	VERSION_RE4:221108797,
	VERSION_DD2:231011879,
	VERSION_KG:240306278,
	VERSION_DD2NEW:240423143,
	VERSION_DR:240424828,
	VERSION_MHWILDS:240820143,
	}
meshFileVersionToInternalVersionDict = {
	1808282334:386270720,#VERSION_DMC5
	1808312334:386270720,#VERSION_RE2
	1902042334:21011200,#VERSION_RE3
	2101050001:2020091500,#VERSION_RE8
	2109108288:21041600,#VERSION_RERT
	2109148288:21091000,#VERSION_MHRSB
	230110883:220705151,#VERSION_SF6
	221108797:220822879,#VERSION_RE4
	231011879:230517984,#VERSION_DD2
	240306278:230727984,#VERSION_KG
	240423143:230517984,#VERSION_DD2NEW
	240424828:240423829,#VERSION_DR
	240820143:240704828,#VERSION_MHWILDS
	}
internalVersionToMeshFileVersionDict = {
	386270720:1808282334,#VERSION_DMC5
	#386270720:1808312334,#VERSION_RE2
	21011200:1902042334,#VERSION_RE3
	2020091500:2101050001,#VERSION_RE8
	21041600:2109108288,#VERSION_RERT
	21091000:2109148288,#VERSION_MHRSB
	220705151:230110883,#VERSION_SF6
	220822879:221108797,#VERSION_RE4
	#230517984:231011879,#VERSION_DD2
	230727984:240306278,#VERSION_KG
	230517984:240423143,#VERSION_DD2NEW
	240423829:240424828,#VERSION_DR
	240704828:240820143,#VERSION_MHWILDS
	}
meshFileVersionToGameNameDict = {
	1808282334:"DMC5",#VERSION_DMC5
	1808312334:"RE2",#VERSION_RE2
	1902042334:"RE3",#VERSION_RE3
	2101050001:"RE8",#VERSION_RE8
	2102020001:"RE8",#RE VERSE
	2109108288:"RE2RT",#VERSION_RERT
	220128762:"RE7RT",#VERSION_RE7RT
	2109148288:"MHRSB",#VERSION_MHRSB
	230110883:"SF6",#VERSION_SF6
	221108797:"RE4",#VERSION_RE4
	231011879:"DD2",#VERSION_DD2
	240306278:"KG",#VERSION_KG
	240423143:"DD2",#VERSION_DD2NEW
	240424828:"DR",#VERSION_DR
	240820143:"MHWILDS",#VERSION_MHWILDS
	}

#Used for unmapped mesh versions, potentially allows for importing
def getNearestRemapVersion(meshVersion):#Returns the remapped version number of the closest mesh version
	return meshFileVersionToNewVersionDict[min(meshFileVersionToNewVersionDict.keys(), key=lambda x:abs(x-meshVersion))]

c_uint64 = ctypes.c_uint64
class CompressedSixWeightIndices_bits(ctypes.LittleEndianStructure):
	_fields_ = 	[
					("w0",c_uint64,10),
					("w1",c_uint64,10),
					("w2",c_uint64,10),
					("pad0",c_uint64,2),
					("w3",c_uint64,10),
					("w4",c_uint64,10),
					("w5",c_uint64,10),
					("pad1",c_uint64,2),
		
				]
	
class CompressedSixWeightIndices(ctypes.Union):
	
	_anonymous_ = ("weights",)
	_fields_ =	[
					("weights",    CompressedSixWeightIndices_bits ),
					("asUInt64", c_uint64)
				]

c_uint32 = ctypes.c_uint32
class CompressedBlendShapeVertexInt_bits(ctypes.LittleEndianStructure):
	_fields_ = 	[
					("x",c_uint32,11),
					("y",c_uint32,10),
					("z",c_uint32,11),
		
				]
	
class CompressedBlendShapeVertexInt(ctypes.Union):
	
	_anonymous_ = ("pos",)
	_fields_ =	[
					("pos",    CompressedBlendShapeVertexInt_bits ),
					("asUInt32", c_uint32)
				]
class Vec3():
	def __init__(self):
		self.x = 0.0
		self.y = 0.0
		self.z = 0.0
	def read(self,file):
		self.x = read_float(file)
		self.y = read_float(file)
		self.z = read_float(file)
	def write(self,file):
		write_float(file, self.x)
		write_float(file, self.y)
		write_float(file, self.z)

class Vec4():
	def __init__(self):
		self.x = 0.0
		self.y = 0.0
		self.z = 0.0
		self.w = 0.0
	def read(self,file):
		self.x = read_float(file)
		self.y = read_float(file)
		self.z = read_float(file)
		self.w = read_float(file)
	def write(self,file):
		write_float(file, self.x)
		write_float(file, self.y)
		write_float(file, self.z)
		write_float(file, self.w)
	
class Sphere():
	def __init__(self):
		self.x = 0.0
		self.y = 0.0
		self.z = 0.0
		self.r = 0.0
	def read(self,file):
		self.x = read_float(file)
		self.y = read_float(file)
		self.z = read_float(file)
		self.r = read_float(file)
	def write(self,file):
		write_float(file, self.x)
		write_float(file, self.y)
		write_float(file, self.z)
		write_float(file, self.r)

class Matrix4x4():
	def __init__(self):
		self.matrix = [[0.0,0.0,0.0,0.0],[0.0,0.0,0.0,0.0],[0.0,0.0,0.0,0.0],[0.0,0.0,0.0,0.0]]
	def read(self,file):
		self.matrix = np.frombuffer(file.read(64),dtype="<4f").tolist()
	def write(self,file):
		for row in self.matrix:
			for val in row:
				write_float(file,val)

class AABB():
	def __init__(self):
		self.min = Vec4()
		self.max = Vec4()
	def read(self,file):
		self.min.read(file)
		self.max.read(file)
	def write(self,file):
		self.min.write(file)
		self.max.write(file)
class MaterialSubdivision():
	def __init__(self):
		self.materialIndex = 0
		self.isQuad = 0
		self.vertexBufferIndex = 0
		self.padding = 0
		self.dr_unkn0 = 0
		self.faceCount = 0
		self.faceStartIndex = 0
		self.vertexStartIndex = 0
		self.streamingOffsetBytes = 0
		self.streamingPlatormSpecificOffsetBytes = 0
		self.dr_unkn1 = 0
	def read(self,file,version):
		self.materialIndex = read_ubyte(file)	
		self.isQuad = read_ubyte(file)
		self.vertexBufferIndex = read_ubyte(file)
		self.padding = read_ubyte(file)
		if version >= VERSION_DR:
			self.dr_unkn0 = read_uint(file)
		self.faceCount = read_uint(file)
		self.faceStartIndex = read_uint(file)
		self.vertexStartIndex = read_uint(file)
		if version >= VERSION_RE8:
			self.streamingOffsetBytes = read_uint(file)
			self.streamingPlatormSpecificOffsetBytes = read_uint(file)
		if version >= VERSION_DD2NEW:
			self.dr_unkn1 = read_uint(file)
	def write(self,file,version):
		write_ubyte(file, self.materialIndex)
		write_ubyte(file, self.isQuad)
		write_ubyte(file, self.vertexBufferIndex)
		write_ubyte(file, self.padding)
		if version >= VERSION_DR:
			write_uint(file, self.dr_unkn0)
		write_uint(file, self.faceCount)
		write_uint(file, self.faceStartIndex)
		write_uint(file, self.vertexStartIndex)
		if version >= VERSION_RE8:
			write_uint(file, self.streamingOffsetBytes)
			write_uint(file, self.streamingPlatormSpecificOffsetBytes)
		if version >= VERSION_DD2NEW:
			write_uint(file, self.dr_unkn1)

class MeshGroup():
	def __init__(self):
		self.visconGroupID = 0
		self.meshCount = 0
		self.null0 = 0
		self.null1 = 0
		self.null2 = 0
		self.vertexCount = 0
		self.faceCount = 0
		self.vertexInfoList = []
	def read(self,file,version):
		self.visconGroupID = read_ubyte(file)
		self.meshCount = read_ubyte(file)
		self.null0 = read_ushort(file)
		self.null1 = read_ushort(file)
		self.null2 = read_ushort(file)
		self.vertexCount = read_uint(file)
		self.faceCount = read_uint(file)
		for i in range(0,self.meshCount):
			entry = MaterialSubdivision()
			entry.read(file,version)
			self.vertexInfoList.append(entry)
	def write(self,file,version):
		write_ubyte(file, self.visconGroupID)
		write_ubyte(file, self.meshCount)
		write_ushort(file, self.null0)
		write_ushort(file, self.null1)
		write_ushort(file, self.null2)
		write_uint(file, self.vertexCount)
		write_uint(file, self.faceCount)
		for entry in self.vertexInfoList:
			entry.write(file,version)

class LODGroupHeader():
	def __init__(self):
		self.count = 0
		self.vertexFormat = 0
		self.reserved = 0
		self.distance = 0
		self.offsetOffset = 0
		self.meshGroupOffsetList = []
		#padding align 16
		self.meshGroupList = []
	def read(self,file,version):
		self.count = read_ubyte(file)
		self.vertexFormat = read_ubyte(file)
		self.reserved = read_ushort(file)
		self.distance = read_float(file)
		self.offsetOffset = read_uint64(file)
		for i in range(0,self.count):
			self.meshGroupOffsetList.append(read_uint64(file))
		file.seek(getPaddedPos(file.tell(), 16))
		for i in range(0,self.count):
			entry = MeshGroup()
			entry.read(file,version)
			self.meshGroupList.append(entry)
	def write(self,file,version):
		write_ubyte(file, self.count)
		write_ubyte(file, self.vertexFormat)
		write_ushort(file, self.reserved)
		write_float(file, self.distance)
		write_uint64(file, self.offsetOffset)
		for entry in self.meshGroupOffsetList:
			write_uint64(file, entry)
		file.seek(getPaddedPos(file.tell(), 16))
		for entry in self.meshGroupList:
			entry.write(file,version)
			
class MainMeshHeader():
	def __init__(self):
		self.lodGroupCount = 0
		self.materialCount = 0
		self.uvCount = 0
		self.skinWeightCount = 18
		self.totalMeshCount = 0
		self.has32BitIndexBuffer = 0
		self.sharedLodBits = 0
		self.nullPadding = 0#PRE RE8
		self.sphere = Sphere()
		self.bbox = AABB()
		self.offsetOffset = 0
		self.lodGroupOffsetList = []
		self.lodGroupList = []
		#padding align 16
	def read(self,file,version,lodTarget = None):
		self.lodGroupCount = read_byte(file)
		self.materialCount = read_byte(file)
		self.uvCount = read_byte(file)
		self.skinWeightCount = read_byte(file)
		self.totalMeshCount = read_ushort(file)
		self.has32BitIndexBuffer = read_byte(file)
		self.sharedLodBits = read_ubyte(file)
		if version < VERSION_RE8:
			self.nullPadding = read_uint64(file)
		self.sphere.read(file)
		self.bbox.read(file)
		self.offsetOffset = read_uint64(file)
		self.lodGroupOffsetList = []
		for i in range(0,self.lodGroupCount):
			self.lodGroupOffsetList.append(read_uint64(file))
		self.lodGroupList = []
		startPos = file.tell()
		
		if lodTarget != None:
			lodTarget = abs(lodTarget)
			if lodTarget >= self.lodGroupCount:#If the chosen LOD target isn't on the mesh, use the lowest quality LOD possible
				lodTarget = self.lodGroupCount - 1
		for lodIndex, offset in enumerate(self.lodGroupOffsetList):
			if lodTarget == None or lodTarget == lodIndex:#Read only the target lod if specified
				file.seek(offset)
				entry = LODGroupHeader()
				entry.read(file,version)
				self.lodGroupList.append(entry)
		file.seek(startPos)
		file.seek(getPaddedPos(file.tell(), 16))
	def write(self,file,version):
		write_byte(file, self.lodGroupCount)
		write_byte(file, self.materialCount)
		write_byte(file, self.uvCount)
		write_byte(file, self.skinWeightCount)
		write_ushort(file, self.totalMeshCount)
		write_byte(file, self.has32BitIndexBuffer)
		write_ubyte(file, self.sharedLodBits)
		if version < VERSION_RE8:
			write_uint64(file, self.nullPadding)
		self.sphere.write(file)
		self.bbox.write(file)
		write_uint64(file, self.offsetOffset)
		for entry in self.lodGroupOffsetList:
			write_uint64(file, entry)
		file.seek(getPaddedPos(file.tell(), 16))
		for entry in self.lodGroupList:
			entry.write(file,version)

class ShadowHeader():
	def __init__(self):
		self.lodGroupCount = 0
		self.materialCount = 0
		self.uvCount = 0
		self.skinWeightCount = 18
		self.totalMeshCount = 0
		self.nullPadding = 0
		self.offsetOffset = 0
		self.null0 = 0
		self.null1 = 0
		self.null2 = 0
		self.null3 = 0
		self.null4 = 0
		self.null5 = 0
		self.lodGroupOffsetList = []
		self.lodGroupList = []
		
	def read(self,file,version):
		self.lodGroupCount = read_byte(file)
		self.materialCount = read_byte(file)
		self.uvCount = read_byte(file)
		self.skinWeightCount = read_byte(file)
		self.totalMeshCount = read_uint(file)
		if version < VERSION_RE8:
			self.nullPadding = read_uint64(file)
		self.offsetOffset = read_uint64(file)
		self.null0 = read_uint64(file)
		self.null1 = read_uint64(file)
		self.null2 = read_uint64(file)
		self.null3 = read_uint64(file)
		self.null4 = read_uint64(file)
		self.null5 = read_uint64(file)
		
		self.lodGroupOffsetList = []
		for i in range(0,self.lodGroupCount):
			self.lodGroupOffsetList.append(read_uint64(file))
		self.lodGroupList = []
		
		#Commented out because there's no reason to read it, shadow meshes can only use main mesh lods
		"""
		startPos = file.tell()
		for offset in self.lodGroupOffsetList:
			file.seek(offset)
			entry = LODGroupHeader()
			entry.read(file)
			self.lodGroupList.append(entry)
		file.seek(startPos)
		"""
		file.seek(getPaddedPos(file.tell(), 16))
	def write(self,file,version):
		#print(file.tell())
		write_byte(file, self.lodGroupCount)
		write_byte(file, self.materialCount)
		write_byte(file, self.uvCount)
		write_byte(file, self.skinWeightCount)
		write_uint(file, self.totalMeshCount)
		if version < VERSION_RE8:
			write_uint64(file, self.nullPadding)
		write_uint64(file, self.offsetOffset)
		write_uint64(file, self.null0)
		write_uint64(file, self.null1)
		write_uint64(file, self.null2)
		write_uint64(file, self.null3)
		write_uint64(file, self.null4)
		write_uint64(file, self.null5)
		for entry in self.lodGroupOffsetList:
			write_uint64(file, entry)
		file.seek(getPaddedPos(file.tell(), 16))
		
		#Shadow meshes can't have unique lods, the game will crash
		"""
		#Halfway through writing the exporter I realised lod group offsets can be shared, this is a workaround so that the lod group doesn't get written again if it shouldn't be
		currentPos = file.tell()
		#print(file.tell())
		for index,entry in enumerate(self.lodGroupList):
			if self.lodGroupOffsetList[index] >= currentPos:#If less than current pos, it's a reused offset, do not write
				#print("wrote shadow lod structure")
				entry.write(file)
		"""
#WILDS
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
		
class StreamingBufferHeaderEntry():
	def __init__(self):
		self.unkn0 = 0
		self.totalBufferSize = 0
		self.vertexBufferLength = 0
		self.mainVertexElementCount = 0
		self.vertexElementCount = 0
		self.unpaddedBufferSize = 0
		self.unpaddedBufferSize2 = 0
		self.unkn7 = 0
		self.unkn8 = 0
		self.unkn9 = 0
		self.unkn10 = 0
		self.unkn11 = 0
		self.unkn12 = 0
		self.unkn13 = 0
		self.nextBufferOffset = 0
		self.unkn15 = 0
		self.vertexBuffer = None
		self.faceBuffer = None
		self.vertexElementList = []
		
	def read(self,file):
		self.unkn0 = read_uint64(file)
		self.totalBufferSize = read_uint(file)
		self.vertexBufferLength = read_uint(file)
		self.mainVertexElementCount = read_ushort(file)
		self.vertexElementCount = read_ushort(file)
		self.unpaddedBufferSize = read_uint(file)
		self.unpaddedBufferSize2 = read_uint(file)
		self.unkn7 = read_uint(file)
		self.unkn8 = read_uint(file)
		self.unkn9 = read_uint(file)
		self.unkn10 = read_uint(file)
		self.unkn11 = read_uint(file)
		self.unkn12 = read_uint(file)
		self.unkn13 = read_uint(file)
		self.nextBufferOffset = read_uint(file)
		self.unkn15 = read_uint(file)


	def write(self,file):
		write_uint64(file, self.unkn0)
		write_uint(file, self.totalBufferSize)
		write_uint(file, self.vertexBufferLength)
		write_ushort(file, self.mainVertexElementCount)
		write_ushort(file, self.vertexElementCount)
		write_uint(file, self.unpaddedBufferSize)
		write_uint(file, self.unpaddedBufferSize2)
		write_uint(file, self.unkn7)
		write_uint(file, self.unkn8)
		write_uint(file, self.unkn9)
		write_uint(file, self.unkn10)
		write_uint(file, self.unkn11)
		write_uint(file, self.unkn12)
		write_uint(file, self.unkn13)
		write_uint(file, self.nextBufferOffset)
		write_uint(file, self.unkn15)
#

class VertexElementStruct():
	def __init__(self):
		self.typing = 0
		self.stride = 0
		self.posStartOffset = 0
	def read(self,file):
		self.typing = read_ushort(file)
		self.stride = read_ushort(file)
		self.posStartOffset = read_uint(file)
	def write(self,file):
		write_ushort(file, self.typing)
		write_ushort(file, self.stride)
		write_uint(file, self.posStartOffset)
		
class MeshBufferHeader():
	def __init__(self):
		self.vertexElementOffset = 0
		self.vertexBufferOffset = 0
		self.faceBufferOffset = 0
		self.sunbreakOffset = 0
		self.vertexBufferSize = 0
		self.faceBufferSize = 0
		self.mainVertexElementCount = 0
		self.vertexElementCount = 0
		self.block2FaceBufferOffset = 0
		self.NULL = 0
		self.vertexElementSize = 0#TODO this field name is not correct
		self.unkn1 = -1
		self.sunbreakSecondUnknown = 0
		self.vertexElementList = []
		self.streamingBufferHeaderList = []#WILDS
		self.vertexBuffer = bytearray()
		self.faceBuffer = bytearray()#NOTE: Face buffer is padded to 4 byte alignment per sub mesh
		self.secondaryWeightBuffer = None#DD2 shape keys
		#SF6
		self.totalBufferSize = 0
		self.sf6unkn0 = 0
		self.streamingVertexElementOffset = 0#vectorStructSize
		self.sf6unkn2 = 0#vectorStructOffset #TODO FIX - sf6unkn2 is vertexElementStreamInfoOffset
	def read(self,file,version,streamingHeader = None,streamingBuffer = None):
		self.vertexElementOffset = read_uint64(file)
		self.vertexBufferOffset = read_uint64(file)
		if version < VERSION_SF6:
			self.faceBufferOffset = read_uint64(file)
			if version > VERSION_RE8:
				self.sunbreakOffset = read_uint64(file)
			self.vertexBufferSize = read_uint(file)
			self.faceBufferSize = read_uint(file)
			self.mainVertexElementCount = read_ushort(file)
			self.vertexElementCount = read_ushort(file)
			self.block2FaceBufferOffset = read_uint(file)
			self.NULL = read_uint(file)
			self.vertexElementSize = read_short(file)
			self.unkn1 = read_short(file)
			if version > VERSION_RE8:
				self.sunbreakSecondUnknown = read_uint64(file)
		elif version >= VERSION_SF6:
			self.sunbreakOffset = read_uint64(file)
			self.totalBufferSize = read_uint(file)
			self.vertexBufferSize = read_uint(file)
			self.faceBufferOffset = self.vertexBufferOffset + self.vertexBufferSize
			self.mainVertexElementCount = read_ushort(file)
			self.vertexElementCount = read_ushort(file)
			self.block2FaceBufferOffset = read_uint(file)
			self.faceBufferSize = self.block2FaceBufferOffset - self.vertexBufferSize
			self.NULL = read_uint(file)
			self.vertexElementSize = read_short(file)
			self.unkn1 = read_short(file)
			self.sunbreakSecondUnknown = read_uint64(file)
			self.sf6unkn0 = read_uint64(file)
			self.streamingVertexElementOffset = read_uint64(file)
			self.sf6unkn2 = read_uint64(file)
			
			
			
		if streamingHeader != None and streamingHeader.entryCount != 0 and streamingBuffer != None:
			#Made a bit of a miscalculation, this doesn't account for the fact that the vertex buffers can't just be stacked since the elements won't be grouped together correctly
			#Moved into re_mesh_parse
			
			#print("Merging streamed face buffers...")
			#print(f"Streamed buffer size {len(streamingBuffer)}")
			#elementArrayList = []
			
			for i in range(0,streamingHeader.entryCount):
				
				entry = StreamingBufferHeaderEntry()
				entry.read(file)
				streamInfo = streamingHeader.streamingInfoEntryList[i]
				#vertexBytes = streamingBuffer[streamInfo.bufferStart:streamInfo.bufferStart+entry.vertexBufferLength]
				#faceBytes = streamingBuffer[streamInfo.bufferStart+entry.vertexBufferLength:streamInfo.bufferStart+entry.unpaddedBufferSize]
				entry.vertexBuffer = streamingBuffer[streamInfo.bufferStart:streamInfo.bufferStart+entry.vertexBufferLength]
				entry.faceBuffer = streamingBuffer[streamInfo.bufferStart+entry.vertexBufferLength:streamInfo.bufferStart+entry.unpaddedBufferSize]
				#entry.faceBuffer = streamingBuffer[streamInfo.bufferStart+entry.vertexBufferLength:entry.nextBufferOffset]
				
				
				currentPos = file.tell()
				file.seek(self.streamingVertexElementOffset + i * (8*self.mainVertexElementCount))#8 is vertex element size
				
				#print(f"vertex element {i} start {file.tell()}")
				for j in range(0,self.mainVertexElementCount):
					element = VertexElementStruct()
					element.read(file)
					entry.vertexElementList.append(element)
				file.seek(currentPos)
				#self.vertexBuffer.extend(vertexBytes)
				#self.faceBuffer.extend(faceBytes)
				
				self.streamingBufferHeaderList.append(entry)
				
				#print(f"vertex range {i} {streamInfo.bufferStart}:{streamInfo.bufferStart+entry.vertexBufferLength}")
				#print(f"face range {i} {streamInfo.bufferStart+entry.vertexBufferLength}:{streamInfo.bufferStart+entry.unpaddedBufferSize}")
				
				#print(f"current vertex buffer size {i} {len(self.vertexBuffer)}")
				#print(f"current face buffer size {i} {len(self.faceBuffer)}")
				
		self.vertexElementList = []
		file.seek(self.vertexElementOffset)
		for i in range(0,self.vertexElementCount):
			entry = VertexElementStruct()
			#print(f"element {i} {file.tell()}")
			entry.read(file)
			self.vertexElementList.append(entry)
		
		file.seek(self.vertexBufferOffset)
		#print(f"Vertex buffer start {str(file.tell())}")
		self.vertexBuffer.extend(file.read(self.vertexBufferSize))
		#print(f"Vertex buffer end {str(file.tell())}")
		file.seek(self.faceBufferOffset)
		#print(f"Face buffer start {str(file.tell())}")
		self.faceBuffer.extend(file.read(self.faceBufferSize))
		
		
		if self.sunbreakOffset != 0:
			if (version == VERSION_DD2 or version == VERSION_DD2NEW):	
				#Limit this DD2 for now in case it happens to be used in other games for other things
				file.seek(self.sunbreakOffset)
				vertexCount = self.vertexElementList[1].posStartOffset // 12#Get amount of vertices from length of position buffer,pos data is 12 bytes
				self.secondaryWeightBuffer = file.read(vertexCount*16)#Weight data is 16 bytes
				print("Read DD2 secondary weight data")
		#print(f"full face buffer size {len(self.faceBuffer)}")
		#print(f"Face buffer end {str(file.tell())}")
	def write(self,file,version):
		write_uint64(file, self.vertexElementOffset)
		write_uint64(file, self.vertexBufferOffset)
		if version < VERSION_SF6:
			write_uint64(file, self.faceBufferOffset)
			if version > VERSION_RE8:
				write_uint64(file, self.sunbreakOffset)
			write_uint(file, self.vertexBufferSize)
			write_uint(file, self.faceBufferSize)
			write_ushort(file, self.mainVertexElementCount)
			write_ushort(file, self.vertexElementCount)
			write_uint(file, self.block2FaceBufferOffset)
			write_uint(file, self.NULL)
			write_short(file, self.vertexElementSize)
			write_short(file, self.unkn1)
			if version > VERSION_RE8:
				write_uint64(file, self.sunbreakSecondUnknown)
		elif version >= VERSION_SF6:
			write_uint64(file, self.sunbreakOffset)
			write_uint(file, self.totalBufferSize)
			write_uint(file, self.vertexBufferSize)
			write_ushort(file, self.mainVertexElementCount)
			write_ushort(file, self.vertexElementCount)
			write_uint(file, self.block2FaceBufferOffset)
			write_uint(file, self.NULL)
			write_short(file, self.vertexElementSize)
			write_short(file, self.unkn1)
			write_uint64(file, self.sunbreakSecondUnknown)
			write_uint64(file, self.sf6unkn0)
			write_uint64(file, self.streamingVertexElementOffset)
			write_uint64(file, self.sf6unkn2)
			
		#TODO WILDS STREAMING INFO WRITE
		for entry in self.vertexElementList:
			entry.write(file)
		file.seek(getPaddedPos(file.tell(), 16))
		file.write(self.vertexBuffer)
		file.seek(getPaddedPos(file.tell(), 16))
		file.write(self.faceBuffer)
		if self.secondaryWeightBuffer != None:
			file.seek(getPaddedPos(file.tell(), 16))
			file.write(self.secondaryWeightBuffer)

class ContentFlag():#Short bitflag in header that determines what content the mesh has Ex: Blend shapes, skeleton, etc.
	def __init__(self):
		self.bitFlag = 0
		self.hasUnknFlag16 = False
		self.hasUnknFlag10 = False
		self.hasUnknFlag8 = False#Always true on MHR
		self.hasGroupPivot = False
		self.hasBlendShape = False
		self.hasSkeleton = False
		self.hasAABB = False
	def parseBitFlag(self):
		self.hasAABB = bool(getBit(self.bitFlag,0))
		self.hasSkeleton = bool(getBit(self.bitFlag,1))
		self.hasBlendShape = bool(getBit(self.bitFlag,2))
		self.hasGroupPivot = bool(getBit(self.bitFlag,3))
		self.hasUnknFlag8 = bool(getBit(self.bitFlag,7))
		self.hasUnknFlag10 = bool(getBit(self.bitFlag,9))
		self.hasUnknFlag16 = bool(getBit(self.bitFlag,15))

		#print(f"aabb:{self.hasAABB}")
		#print(f"skeleton:{self.hasSkeleton}")
		#print(f"blendshape:{self.hasBlendShape}")
		#print(f"grouppivot:{self.hasGroupPivot}")
	def setBitFlag(self,hasUnknFlag16,hasUnknFlag10,hasUnknFlag8,hasGroupPivot,hasBlendShape,hasSkeleton,hasAABB):
		self.bitFlag = 0
		if hasAABB:
			self.bitFlag = setBit(self.bitFlag,0)
		if hasSkeleton:
			self.bitFlag = setBit(self.bitFlag,1)
		if hasBlendShape:
			self.bitFlag = setBit(self.bitFlag,2)
		if hasGroupPivot:
			self.bitFlag = setBit(self.bitFlag,3)
		if hasUnknFlag8:
			self.bitFlag = setBit(self.bitFlag,7)
		if hasUnknFlag10:
			self.bitFlag = setBit(self.bitFlag,9)
		if hasUnknFlag16:
			self.bitFlag = setBit(self.bitFlag,15)
		self.parseBitFlag()
	def read(self,file):
		self.bitFlag = read_ushort(file)
		self.parseBitFlag()
	def write(self,file):
		write_ushort(file,self.bitFlag)
	
class FileHeader():
	def __init__(self):
		self.magic = 1213416781
		self.version = 0
		self.fileSize = 0
		self.unknHash = 0
		self.contentFlag = ContentFlag() #Bitflag 1000 XXXX-[GroupPivot/Floats][Blendshape][Skeleton][AABB]
		self.nameCount = 0
		self.unkn = 0
		self.meshGroupOffset = 0
		self.shadowMeshGroupOffset = 0
		self.occlusionMeshGroupOffset = 0
		self.skeletonOffset = 0
		self.normalRecalcOffset = 0
		self.blendShapesOffset = 0
		self.aabbOffset = 0
		self.meshOffset = 0
		self.floatsOffset = 0
		self.materialNameRemapOffset = 0
		self.boneNameRemapOffset = 0
		self.blendShapeNameOffset = 0
		self.nameOffsetsOffset = 0
		
		#SF6
		self.sf6UnknCount = 0
		self.sf6unkn0 = 0
		self.sf6unkn1 = 0
		self.streamingInfoOffset = 0
		self.sf6unkn3 = 0
		self.sf6unkn4 = 0
		
		#DD2
		self.dd2HashOffset = 0
		self.verticesOffset = 0
		
		#MHWilds
		#TODO Update offset calculation for wilds meshes
		#TODO Fix write for wilds changes
		self.wilds_unkn1 = 0#TODO Clean these variables up and figure out if they're not actually new, just shifted
		self.wilds_unkn2 = 0
		self.wilds_unkn3 = 0
		self.wilds_unkn4 = 0
		self.wilds_unkn5 = 0
		self.streamingInfoOffset = 0
		
	def read(self,file,version):
		self.magic = read_uint(file)
		if self.magic != 1213416781:
			if self.magic == 1498173517:#MPLY
				raise Exception("MPLY formatted mesh files (stage meshes mostly) are not supported yet.")
			else:
				raise Exception("File is not an RE mesh file.")
		self.version = read_uint(file)
		self.fileSize = read_uint(file)
		self.unknHash = read_uint(file)
		
		
		if version < VERSION_SF6:
			self.contentFlag.read(file)
			self.nameCount = read_short(file)
			self.unkn = read_uint(file)
			self.meshGroupOffset = read_uint64(file)
			self.shadowMeshGroupOffset = read_uint64(file)
			self.occlusionMeshGroupOffset = read_uint64(file)
			self.skeletonOffset = read_uint64(file)
			self.normalRecalcOffset = read_uint64(file)
			self.blendShapesOffset = read_uint64(file)
			self.aabbOffset = read_uint64(file)
			self.meshOffset = read_uint64(file)
			self.floatsOffset = read_uint64(file)
			self.materialNameRemapOffset = read_uint64(file)
			self.boneNameRemapOffset = read_uint64(file)
			self.blendShapeNameOffset = read_uint64(file)
			self.nameOffsetsOffset = read_uint64(file)
		elif version >= VERSION_SF6 and version < VERSION_MHWILDS:
			self.contentFlag.read(file)
			self.sf6UnknCount = read_short(file)
			self.nameCount = read_short(file)
			
			self.sf6unkn3 = read_short(file)#new
			
			self.unkn = read_uint(file)
			self.sf6unkn0 = read_uint(file)#new
			self.meshGroupOffset = read_uint64(file)
			self.shadowMeshGroupOffset = read_uint64(file)
			self.occlusionMeshGroupOffset = read_uint64(file)
			self.normalRecalcOffset = read_uint64(file)
			self.blendShapesOffset = read_uint64(file)
			self.meshOffset = read_uint64(file)
			self.sf6unkn1 = read_uint64(file)#new
			
			
			
			
			self.floatsOffset = read_uint64(file)
			self.aabbOffset = read_uint64(file)
			self.skeletonOffset = read_uint64(file)
			self.materialNameRemapOffset = read_uint64(file)
			self.boneNameRemapOffset = read_uint64(file)
			self.blendShapeNameOffset = read_uint64(file)
			
			
			if version < VERSION_DD2:
				self.streamingInfoOffset = read_uint64(file)#vertex ElementOffset New with sf6
				self.nameOffsetsOffset = read_uint64(file)
			else:	
				self.nameOffsetsOffset = read_uint64(file)
				self.dd2HashOffset = read_uint64(file)
				self.streamingInfoOffset = read_uint64(file)#vertex ElementOffset New with sf6
			self.verticesOffset = read_uint64(file)#new
			self.sf6unkn4 = read_uint64(file)#new
			
		elif version >= VERSION_MHWILDS:
			self.wilds_unkn1 = read_uint(file)
			self.nameCount = read_short(file)
			self.contentFlag.read(file)
			self.sf6UnknCount = read_short(file)
			
			self.wilds_unkn2 = read_uint(file)
			self.wilds_unkn3 = read_uint(file)
			self.wilds_unkn4 = read_uint(file)
			self.wilds_unkn5 = read_short(file)
				
			self.verticesOffset = read_uint64(file)
			self.meshGroupOffset = read_uint64(file)
			self.shadowMeshGroupOffset = read_uint64(file)
			self.occlusionMeshGroupOffset = read_uint64(file)
			self.normalRecalcOffset = read_uint64(file)
			self.blendShapesOffset = read_uint64(file)
			self.meshOffset = read_uint64(file)
			self.sf6unkn1 = read_uint64(file)#new
			
			
			
			
			self.floatsOffset = read_uint64(file)
			self.aabbOffset = read_uint64(file)
			self.skeletonOffset = read_uint64(file)
			self.materialNameRemapOffset = read_uint64(file)
			self.boneNameRemapOffset = read_uint64(file)
			self.blendShapeNameOffset = read_uint64(file)
			self.nameOffsetsOffset = read_uint64(file)
			self.streamingInfoOffset = read_uint64(file)#new with wilds
			self.sf6unkn4 = read_uint64(file)#new
			
	def write(self,file,version):
		write_uint(file, self.magic)
		write_uint(file, self.version)
		write_uint(file, self.fileSize)
		write_uint(file, self.unknHash)
		
		
		if version < VERSION_SF6:
			self.contentFlag.write(file)
			write_short(file, self.nameCount)
			write_uint(file, self.unkn)
			write_uint64(file, self.meshGroupOffset)
			write_uint64(file, self.shadowMeshGroupOffset)
			write_uint64(file, self.occlusionMeshGroupOffset)
			write_uint64(file, self.skeletonOffset)
			write_uint64(file, self.normalRecalcOffset)
			write_uint64(file, self.blendShapesOffset)
			write_uint64(file, self.aabbOffset)
			write_uint64(file, self.meshOffset)
			write_uint64(file, self.floatsOffset)
			write_uint64(file, self.materialNameRemapOffset)
			write_uint64(file, self.boneNameRemapOffset)
			write_uint64(file, self.blendShapeNameOffset)
			write_uint64(file, self.nameOffsetsOffset)
		elif version >= VERSION_SF6 and version < VERSION_MHWILDS:
			self.contentFlag.write(file)
			write_short(file, self.sf6UnknCount)
			write_short(file, self.nameCount)
			write_short(file, self.sf6unkn3)#new
			write_uint(file, self.unkn)
			write_uint(file, self.sf6unkn0)#new
			write_uint64(file, self.meshGroupOffset)
			write_uint64(file, self.shadowMeshGroupOffset)
			write_uint64(file, self.occlusionMeshGroupOffset)
			write_uint64(file, self.normalRecalcOffset)
			write_uint64(file, self.blendShapesOffset)
			write_uint64(file, self.meshOffset)
			write_uint64(file, self.sf6unkn1)#new
			
			write_uint64(file, self.floatsOffset)
			write_uint64(file, self.aabbOffset)
			write_uint64(file, self.skeletonOffset)
			write_uint64(file, self.materialNameRemapOffset)
			write_uint64(file, self.boneNameRemapOffset)
			write_uint64(file, self.blendShapeNameOffset)
			if version < VERSION_DD2:
				write_uint64(file, self.streamingInfoOffset)#new
				write_uint64(file, self.nameOffsetsOffset)
			else:
				write_uint64(file, self.nameOffsetsOffset)
				write_uint64(file, self.dd2HashOffset)
				write_uint64(file, self.streamingInfoOffset)#new
				
			write_uint64(file, self.verticesOffset)#new
			write_uint64(file, self.sf6unkn4)#new
		elif version >= VERSION_MHWILDS:
			write_uint(file, self.wilds_unkn1)
			write_short(file, self.nameCount)
			self.contentFlag.write(file)
			write_short(file, self.sf6UnknCount)
			write_uint(file, self.wilds_unkn2)
			write_uint(file, self.wilds_unkn3)
			write_uint(file, self.wilds_unkn4)
			write_short(file, self.wilds_unkn5)
			write_uint64(file, self.verticesOffset)
			write_uint64(file, self.meshGroupOffset)
			write_uint64(file, self.shadowMeshGroupOffset)
			write_uint64(file, self.occlusionMeshGroupOffset)
			write_uint64(file, self.normalRecalcOffset)
			write_uint64(file, self.blendShapesOffset)
			write_uint64(file, self.meshOffset)
			write_uint64(file, self.sf6unkn1)
			write_uint64(file, self.floatsOffset)
			write_uint64(file, self.aabbOffset)
			write_uint64(file, self.skeletonOffset)
			write_uint64(file, self.materialNameRemapOffset)
			write_uint64(file, self.boneNameRemapOffset)
			write_uint64(file, self.blendShapeNameOffset)
			write_uint64(file, self.nameOffsetsOffset)
			write_uint64(file, self.streamingInfoOffset)
			write_uint64(file, self.sf6unkn4)
class IndexNormalRecalc():
	def __init__(self):
		self.index = 0
		self.left = 0
		self.right = 0
	def read(self,file):
		self.index = read_ushort(file)
		self.left = read_ubyte(file)
		self.right = read_ubyte(file)
	def write(self,file):
		write_ushort(file, self.index)
		write_ubyte(file, self.left)
		write_ubyte(file, self.right)

class NormalRecalc():
	def __init__(self):
		self.blockCount = 0
		self.dataOffset = 0
		self.nextOffset = 0
		self.null = 0
		self.vertexOffset = 0
		self.faceOffset = 0
		#padding align 16
		self.vertexDataList = []
		#padding align 16
		self.faceDataList = []
		
		
	def read(self,file,vertexCount,faceCount):
		self.blockCount = read_uint(file)
		self.dataOffset = read_uint64(file)
		self.nextOffset = read_short(file)
		self.null = read_short(file)
		self.vertexOffset = read_uint(file)
		self.faceOffset = read_uint64(file)
		file.seek(getPaddedPos(file.tell(), 16))
		for i in range(0,vertexCount):
			entry = IndexNormalRecalc()
			entry.read(file)
			self.vertexDataList.append(entry)
		file.seek(getPaddedPos(file.tell(), 16))
		for i in range(0,faceCount):
			entry = IndexNormalRecalc()
			entry.read(file)
			self.faceDataList.append(entry)
		
	def write(self,file):
		write_uint(file, self.blockCount)
		write_uint64(file, self.dataOffset)
		write_short(file, self.nextOffset)
		write_short(file, self.null)
		write_uint(file, self.vertexOffset)
		write_uint64(file, self.faceOffset)
		file.seek(getPaddedPos(file.tell(), 16))#TODO FIX WRITE
		for entry in self.vertexDataList:
			entry.write(file)
		file.seek(getPaddedPos(file.tell(), 16))#TODO FIX WRITE
		for entry in self.faceDataList:
			entry.write(file)

class BlendSubMesh():
	def __init__(self):
		self.subMeshVertexStartIndex = 0
		self.vertOffset = 0
		self.vertCount = 0
		self.paramUnkn3 = 0
		
	def read(self,file):
		self.subMeshVertexStartIndex = read_uint(file)
		self.vertOffset = read_uint(file)
		self.vertCount = read_uint(file)
		self.paramUnkn3 = read_uint(file)
		
	def write(self,file):
		write_uint(file, self.subMeshVertexStartIndex)
		write_uint(file, self.vertOffset)
		write_uint(file, self.vertCount)
		write_uint(file, self.paramUnkn3)

class BlendTarget():
	def __init__(self):
		self.subMeshVertexStartIndex = 0
		self.vertCount = 0
		self.blendSSIndex = 0
		self.blendShapeNum = 0
		self.deltaOffset = 0
		
		#sf6 changes
		self.unkn0 = 0
		self.subMeshEntryCount = 0
		self.unkn2 = 0
		self.subMeshEntryOffset = 0
		self.subMeshEntryList = []
		
		
	def read(self,file,version):
		if version < VERSION_SF6:
			self.subMeshVertexStartIndex = read_uint(file)
			self.vertCount = read_uint(file)
			self.blendSSIndex = read_ushort(file)
			self.blendShapeNum = read_ushort(file)
			self.deltaOffset = read_uint(file)
		else:
			self.blendSSIndex = read_ushort(file)
			self.blendShapeNum = read_ushort(file)
			self.unkn0 = read_ushort(file)
			self.subMeshEntryCount = read_ubyte(file)
			self.unkn2 = read_ubyte(file)
			self.subMeshEntryOffset = read_uint64(file)
			currentPos = file.tell()
			file.seek(self.subMeshEntryOffset)
			for i in range(0,self.subMeshEntryCount):
				subMeshEntry = BlendSubMesh()
				subMeshEntry.read(file)
				self.subMeshEntryList.append(subMeshEntry)
			
			file.seek(currentPos)
		
	def write(self,file,version):#TODO FIX WRITE
		write_uint64(file, self.count)
		write_uint64(file, self.mainOffset)
		write_uint64(file, self.zero)
		write_uint64(file, self.hash)
		for entry in self.blendShapeOffsetList:
			write_uint64(file,entry)
		
		for entry in self.blendShapeList:#TODO FIX WRITE
			entry.write(file)

class BlendShapeData():
	def __init__(self):
		self.targetCount = 1
		self.typing = 0
		self.unknFlag = 0
		self.padding1 = 0
		self.padding2 = 0
		self.dataOffset = 0#[Target count]
		self.aabbOffset = 0
		self.blendSOffset = 0
		self.blendSSOffset = 0
		self.blendTargetList = []
		self.aabbList = [AABB()]
		self.blendS = [0,0,0,0]
		self.blendSSList = []
	def read(self,file,version):
		self.targetCount = read_ushort(file)
		self.typing = read_ushort(file)
		self.unknFlag = read_uint(file)
		self.padding1 = read_uint(file)
		self.padding2 = read_uint(file)
		self.dataOffset = read_uint64(file)#[Target count]
		self.aabbOffset = read_uint64(file)
		self.blendSOffset = read_uint64(file)
		self.blendSSOffset = read_uint64(file)
		file.seek(self.dataOffset)
		for i in range(0,self.targetCount):
			blendTargetEntry = BlendTarget()
			blendTargetEntry.read(file,version)
			self.blendTargetList.append(blendTargetEntry)
		file.seek(self.aabbOffset)#TODO FIX WRITE
		self.aabbList.clear()
		for i in range(0,self.targetCount):
			aabbEntry = AABB()
			aabbEntry.read(file)
			self.aabbList.append(aabbEntry)
		self.blendS = [read_int(file),read_int(file),read_int(file)]
		self.blendSSList = []
		for blendTarget in self.blendTargetList:
			for i in range(0,blendTarget.blendShapeNum):
				self.blendSSList.append(read_int(file))
	def write(self,file):#TODO FIX WRITE
		write_ushort(file, self.targetCount)
		write_ushort(file, self.typing)
		write_uint(file, self.unknFlag)
		write_uint(file, self.padding1)
		write_uint(file, self.padding2)
		write_uint64(file, self.dataOffset)
		write_uint64(file, self.aabbOffset)
		write_uint64(file, self.blendSOffset)
		write_uint64(file, self.blendSSOffset)
		write_uint(file, self.vertOffset)
		write_uint(file, self.vertCount)
		write_ushort(file, self.visconTarget)
		write_ushort(file,self.blendShapeCount)
		self.aabb.write(file)
		for entry in self.blendS:
			write_int(file,entry)
		for entry in self.blendSSList:
			write_int(file,entry)

class BlendShapeHeader():
	def __init__(self):
		self.count = 0
		self.mainOffset = 0
		self.zero = 0
		self.hash = 0
		self.blendShapeOffsetList = []
		self.blendShapeList = []	
		#TODO Blend shapes are different in wilds, fix
		
	def read(self,file,version):
		self.count = read_uint64(file)
		if version < VERSION_MHWILDS:
			self.mainOffset = read_uint64(file)
			self.zero = read_uint64(file)
		else:
			self.zero = read_uint64(file)
			self.mainOffset = read_uint64(file)
		self.hash = read_uint64(file)
		self.blendShapeOffsetList = []
		for i in range(0,self.count):
			self.blendShapeOffsetList.append(read_uint64(file))
		self.blendShapeList = []
		currentPos = file.tell()
		for i in range(0,self.count):
			file.seek(self.blendShapeOffsetList[i])
			entry = BlendShapeData()
			entry.read(file,version)
			self.blendShapeList.append(entry)
		file.seek(currentPos)
		
	def write(self,file,version):
		write_uint64(file, self.count)
		write_uint64(file, self.mainOffset)
		write_uint64(file, self.zero)
		write_uint64(file, self.hash)
		for entry in self.blendShapeOffsetList:
			write_uint64(file,entry)
		
		for entry in self.blendShapeList:#TODO FIX WRITE
			entry.write(file,version)

class BoneAABBGroup():
	def __init__(self):
		self.count = 0
		self.offset = 0
		self.bboxList = []
		#padding align 16
		
	def read(self,file):
		self.count = read_uint64(file)
		self.offset = read_uint64(file)
		self.bboxList = []	
		for i in range(0,self.count):
			entry = AABB()
			entry.read(file)
			self.bboxList.append(entry)
		file.seek(getPaddedPos(file.tell(), 16))
	def write(self,file):
		write_uint64(file, self.count)
		write_uint64(file, self.offset)
		for entry in self.bboxList:#TODO FIX WRITE
			entry.write(file)
		file.seek(getPaddedPos(file.tell(), 16))

class Bone():
	def __init__(self):
		self.boneIndex = 0
		self.boneParent = 0
		self.boneSibling = 0
		self.boneChild = 0
		self.boneSymmetric = 0
		self.useSecondaryWeight = 0
		self.padding0 = 0
		self.padding1 = 0
	def read(self,file):
		self.boneIndex = read_ushort(file)
		self.boneParent = read_short(file)
		self.boneSibling = read_short(file)
		self.boneChild = read_short(file)
		self.boneSymmetric = read_short(file)
		self.useSecondaryWeight = read_short(file)
		self.padding0 = read_short(file)
		self.padding1 = read_short(file)
	def write(self,file):
		write_ushort(file, self.boneIndex)
		write_short(file, self.boneParent)
		write_short(file, self.boneSibling)
		write_short(file, self.boneChild)
		write_short(file, self.boneSymmetric)
		write_short(file, self.useSecondaryWeight)
		write_short(file, self.padding0)
		write_short(file, self.padding1)

class Skeleton():
	def __init__(self):
		self.boneCount = 0
		self.remapCount = 0
		self.NULL = 0
		self.boneHeaderOffset = 0
		self.boneLocalMatrixOffset = 0
		self.boneWorldMatrixOffset = 0
		self.boneInverseMatrixOffset = 0
		self.boneRemapList = []
		#padding align 16
		self.boneInfoList = []
		#padding align 16
		self.localMatList = []
		self.worldMatList = []
		self.inverseMatList = []
	def read(self,file):
		self.boneCount = read_uint(file)
		self.remapCount = read_uint(file)
		self.NULL = read_uint64(file)
		self.boneHeaderOffset = read_uint64(file)
		self.boneLocalMatrixOffset = read_uint64(file)
		self.boneWorldMatrixOffset = read_uint64(file)
		self.boneInverseMatrixOffset = read_uint64(file)
		self.boneRemapList = []
		for i in range(0,self.remapCount):
			self.boneRemapList.append(read_ushort((file)))
		file.seek(getPaddedPos(file.tell(), 16))
		self.boneInfoList = []
		for i in range(0,self.boneCount):
			entry = Bone()
			entry.read(file)
			self.boneInfoList.append(entry)
		file.seek(getPaddedPos(file.tell(), 16))
		localMatList = []
		for i in range(0,self.boneCount):
			entry = Matrix4x4()
			entry.read(file)
			self.localMatList.append(entry)
		worldMatList = []
		for i in range(0,self.boneCount):
			entry = Matrix4x4()
			entry.read(file)
			self.worldMatList.append(entry)
		inverseMatList = []
		for i in range(0,self.boneCount):
			entry = Matrix4x4()
			entry.read(file)
			self.inverseMatList.append(entry)
	def write(self,file):
		write_uint(file, self.boneCount)
		write_uint(file, self.remapCount)
		write_uint64(file, self.NULL)
		write_uint64(file, self.boneHeaderOffset)
		write_uint64(file, self.boneLocalMatrixOffset)
		write_uint64(file, self.boneWorldMatrixOffset)
		write_uint64(file, self.boneInverseMatrixOffset)
		for entry in self.boneRemapList:
			write_ushort(file,entry)
		file.seek(getPaddedPos(file.tell(), 16))
		for entry in self.boneInfoList:
			entry.write(file)
		for entry in self.localMatList:
			entry.write(file)
		for entry in self.worldMatList:
			entry.write(file)
		for entry in self.inverseMatList:
			entry.write(file)

class FloatData():
	def __init__(self):
		self.bufferSize = 0
		self.offset = 0
		self.unknDataList = []
		
	def read(self,file):
		self.count = read_uint64(file)
		self.offset = read_uint64(file)
		self.unknDataList = []
		startPos = file.tell()
		file.seek(self.offset)
		for i in range(0,self.bufferSize//12):
			entry = Vec3()
			entry.read(file)
			self.unknDataList.append(entry)
		file.seek(startPos)
	def write(self,file):
		write_uint64(file, self.count)
		write_uint64(file, self.offset)
		startPos = file.tell()
		file.seek(self.offset)
		for entry in self.unknDataList:#TODO FIX WRITE
			entry.write(file)
		file.seek(startPos)
class REMesh():
	def __init__(self):
		self.meshVersion = 0
		self.fileHeader = FileHeader()
		self.lodHeader = None
		self.shadowHeader = None
		self.occlusionHeader = None
		self.skeletonHeader = None
		self.normalRecalcHeader = None
		self.blendShapeHeader = None
		self.boneBoundingBoxHeader = None
		self.streamingInfoHeader = None#WILDS
		self.streamingBuffer = None#WILDS
		self.meshBufferHeader = None
		self.floatsHeader = None
		self.rawNameOffsetList = []
		self.rawNameList = []
		self.materialNameRemapList = []
		self.boneNameRemapList = []
		self.blendShapeNameRemapList = []
	def read(self,file,version,lodTarget = None,streamingBuffer = None):#LOD target is an int that determines what lod level to import, the rest get ignored
		self.streamingBuffer = streamingBuffer
		if streamingBuffer != None:
			lodTarget = None#Disable lod target optimization since all lods are needed	
		self.fileHeader.read(file,version)
		
		if self.fileHeader.meshGroupOffset:
			file.seek(self.fileHeader.meshGroupOffset)
			self.lodHeader = MainMeshHeader()
			self.lodHeader.read(file,version,lodTarget)
			
		if self.fileHeader.shadowMeshGroupOffset and lodTarget == None:
			file.seek(self.fileHeader.shadowMeshGroupOffset)
			self.shadowHeader = ShadowHeader()
			self.shadowHeader.read(file,version)
		
		if self.fileHeader.occlusionMeshGroupOffset and lodTarget == None:
			file.seek(self.fileHeader.occlusionMeshGroupOffset)
			self.occlusionHeader = LODGroupHeader()
			self.occlusionHeader.read(file,version)
		
		if self.fileHeader.skeletonOffset:
			file.seek(self.fileHeader.skeletonOffset)
			self.skeletonHeader = Skeleton()
			self.skeletonHeader.read(file)
		#TODO - Normal recalc is changed or offset is different in mhwilds
		"""
		if self.fileHeader.normalRecalcOffset:
			file.seek(self.fileHeader.normalRecalcOffset)
			self.normalRecalcHeader = NormalRecalc()
			self.normalRecalcHeader.read(file,sum([i.vertexCount for i in self.lodHeader.lodGroupList[0].meshGroupList]),sum([i.faceCount for i in self.lodHeader.lodGroupList[0].meshGroupList]))
		"""
		if self.fileHeader.blendShapesOffset and IMPORT_BLEND_SHAPES:
			file.seek(self.fileHeader.blendShapesOffset)
			self.blendShapeHeader = BlendShapeHeader()
			self.blendShapeHeader.read(file,version)
		
		if self.fileHeader.aabbOffset:
			file.seek(self.fileHeader.aabbOffset)
			self.boneBoundingBoxHeader = BoneAABBGroup()
			self.boneBoundingBoxHeader.read(file)
		
		if version >= VERSION_SF6:
			if self.fileHeader.streamingInfoOffset:
				file.seek(self.fileHeader.streamingInfoOffset)
				self.streamingInfoHeader = StreamingInfo()
				self.streamingInfoHeader.read(file)
				if self.streamingInfoHeader.entryCount != 0 and streamingBuffer == None:
					raiseError("The corresponding streaming mesh file is missing. Cannot import mesh.\nCheck that you're using the most up to date list file when extracting files.")
					raise Exception("Streaming mesh file is missing. Check that you're using the most up to date list file when extracting game files.")
		if self.fileHeader.meshOffset:
			file.seek(self.fileHeader.meshOffset)
			self.meshBufferHeader = MeshBufferHeader()
			self.meshBufferHeader.read(file,version,self.streamingInfoHeader,streamingBuffer)
				
		if self.fileHeader.floatsOffset:
			file.seek(self.fileHeader.floatsOffset)
			self.floatsHeader = FloatData()
			self.floatsHeader.read(file)
		
		if self.fileHeader.nameOffsetsOffset:
			file.seek(self.fileHeader.nameOffsetsOffset)
			for i in range(0,self.fileHeader.nameCount):
				self.rawNameOffsetList.append(read_uint64(file))
			
			for offset in self.rawNameOffsetList:
				file.seek(offset)
				self.rawNameList.append(read_string(file))
				
		if self.fileHeader.materialNameRemapOffset and self.lodHeader != None:
			file.seek(self.fileHeader.materialNameRemapOffset)
			for i in range(0,self.lodHeader.materialCount):
				self.materialNameRemapList.append(read_ushort(file))
				
		if self.fileHeader.boneNameRemapOffset and self.skeletonHeader != None:
			file.seek(self.fileHeader.boneNameRemapOffset)
			for i in range(0,self.skeletonHeader.boneCount):
				self.boneNameRemapList.append(read_ushort(file))
		
		if self.fileHeader.blendShapeNameOffset and self.blendShapeHeader != None:
			file.seek(self.fileHeader.blendShapeNameOffset)
			blendNameCount = self.fileHeader.nameCount - len(self.materialNameRemapList) - len(self.boneNameRemapList)
			#for i in range(0,sum([blendShape.blendShapeCount for blendShape in self.blendShapeHeader.blendShapeList])):
			for i in range(0,blendNameCount):
				self.blendShapeNameRemapList.append(read_ushort(file))
	def write(self,file,version):
		self.fileHeader.write(file,version)
		
		if self.fileHeader.meshGroupOffset:
			if self.fileHeader.meshGroupOffset != file.tell():
				print(f"ERROR IN OFFSET CALCULATION - meshGroupOffset - expected {self.fileHeader.meshGroupOffset}, actual {file.tell()}")
			self.lodHeader.write(file,version)
	
		if self.fileHeader.shadowMeshGroupOffset:
			if self.fileHeader.shadowMeshGroupOffset != file.tell():
				print(f"ERROR IN OFFSET CALCULATION - shadowMeshGroupOffset - expected {self.fileHeader.shadowMeshGroupOffset}, actual {file.tell()}")
			self.shadowHeader.write(file,version)
		
		if self.fileHeader.skeletonOffset:
			if self.fileHeader.skeletonOffset != file.tell():
				print(f"ERROR IN OFFSET CALCULATION - skeletonOffset - expected {self.fileHeader.skeletonOffset}, actual {file.tell()}")
			self.skeletonHeader.write(file)
		
		if self.fileHeader.materialNameRemapOffset and self.fileHeader.materialNameRemapOffset != file.tell():
			print(f"ERROR IN OFFSET CALCULATION - materialNameRemapOffset - expected {self.fileHeader.materialNameRemapOffset}, actual {file.tell()}")
		for entry in self.materialNameRemapList:
			write_ushort(file,entry)
			
		file.seek(getPaddedPos(file.tell(), 16))
		if self.fileHeader.boneNameRemapOffset and self.fileHeader.boneNameRemapOffset != file.tell():
			print(f"ERROR IN OFFSET CALCULATION - boneNameRemapOffset - expected {self.fileHeader.boneNameRemapOffset}, actual {file.tell()}")
		for entry in self.boneNameRemapList:
			write_ushort(file,entry)
		
		file.seek(getPaddedPos(file.tell(), 16))
		if self.fileHeader.blendShapeNameOffset and self.fileHeader.blendShapeNameOffset != file.tell():
			print(f"ERROR IN OFFSET CALCULATION - boneNameRemapOffset - expected {self.fileHeader.blendShapeNameOffset}, actual {file.tell()}")
		for entry in self.blendShapeNameRemapList:
			write_ushort(file,entry)
		
		file.seek(getPaddedPos(file.tell(), 16))
		
		if self.fileHeader.nameOffsetsOffset and self.fileHeader.nameOffsetsOffset != file.tell():
			print(f"ERROR IN OFFSET CALCULATION - nameOffsetsOffset - expected {self.fileHeader.nameOffsetsOffset}, actual {file.tell()}")
		
		for offset in self.rawNameOffsetList:
			write_uint64(file,offset)
		file.seek(getPaddedPos(file.tell(), 16))
		
		for name in self.rawNameList:
			write_string(file, name)
			
		file.seek(getPaddedPos(file.tell(), 16))
		
		if self.fileHeader.aabbOffset:
			if self.fileHeader.aabbOffset != file.tell():
				print(f"ERROR IN OFFSET CALCULATION - aabbOffset - expected {self.fileHeader.aabbOffset}, actual {file.tell()}")
			self.boneBoundingBoxHeader.write(file)
		
		if self.fileHeader.meshOffset:
			if self.fileHeader.meshOffset != file.tell():
				print(f"ERROR IN OFFSET CALCULATION - meshOffset - expected {self.fileHeader.meshOffset}, actual {file.tell()}")
			self.meshBufferHeader.write(file,version)	
		
		file.write(b'\x00'*getPaddingAmount(file.tell(),16))#Write end of file padding
		if self.fileHeader.fileSize != file.tell():
			print(f"ERROR IN OFFSET CALCULATION - fileSize - expected {self.fileHeader.fileSize}, actual {file.tell()}")
#List to buffer conversions

def WriteToVertexPosBuffer(bufferStream,vertexPosList):
	data = struct.pack(f'{len(vertexPosList)*3}f', *chain.from_iterable(vertexPosList))
	bufferStream.write(data)

def WriteToNorTanBuffer(bufferStream,normalArray,tangentArray):
	vertexCount = len(normalArray)
	normalArray = np.floor(np.multiply(normalArray,127))
	normalArray = np.insert(normalArray, 3, np.zeros(vertexCount,np.dtype("<b")),axis=1)
	norTanArray = np.empty((vertexCount*2,4), dtype=np.dtype("<b"))
	norTanArray[::2] = normalArray
	norTanArray[1::2] = tangentArray
	#print(norTanArray)
	
	
	bufferStream.write(norTanArray.tobytes())
	
#Old method of calculating tangents, slow

def WriteToNorTanBufferOld(bufferStream,normalList,vertexPosList,uvList,faceList):
	
	vertexCount = len(vertexPosList)
	faceCount = len(faceList)
	normalArray = np.array(normalList)
	tangentArray = np.zeros((vertexCount,4),dtype="int8")
	#print(tangentArray)
	tan1Array = np.zeros((vertexCount*2,3),dtype="float")
	#print(tan1Array)
	tan2Array = np.zeros((vertexCount*2,3),dtype="float")
	for face in faceList:
		v1 = vertexPosList[face[0]]
		v2 = vertexPosList[face[1]]
		v3 = vertexPosList[face[2]]
		
		w1 = uvList[face[0]]
		w2 = uvList[face[1]]
		w3 = uvList[face[2]]
		
		x1 = v2[0] - v1[0]
		x2 = v3[0] - v1[0]
		y1 = v2[1] - v1[1]
		y2 = v3[1] - v1[1]
		z1 = v2[2] - v1[2]
		z2 = v3[2] - v1[2]
		
		s1 = w2[0] - w1[0]
		s2 = w3[0] - w1[0]
		t1 = w2[1] - w1[1]
		t2 = w3[1] - w1[1]
		
		div = (s1 * t2 - s2 * t1)
		r = 1.0
		if div != 0.0:
			r = 1.0 / div
		sdir = [(t2 * x1 - t1 * x2) * r, (t2 * y1 - t1 * y2) * r, (t2 * z1 - t1 * z2) * r]
		tdir = [(s1 * x2 - s2 * x1) * r, (s1 * y2 - s2 * y1) * r, (s1 * z2 - s2 * z1) * r]
		tan1Array[face[0]] += sdir
		tan1Array[face[1]] += sdir
		tan1Array[face[2]] += sdir
		
		tan2Array[face[0]] += tdir
		tan2Array[face[1]] += tdir
		tan2Array[face[2]] += tdir
		
	for i in range(vertexCount):
		n = normalArray[i]
		t = tan1Array[i]
		TN = t - n * (np.dot(n,t))
		norm = np.linalg.norm(TN)
		#print(norm)
		if norm != 0.0:
			TN /= norm
		#print(f"TN : {TN}")
		TNW = np.dot(np.cross(n,t),tan2Array[i])
		if TNW < 0.0:
			TNW = -128 
		else: 
			TNW = 127
		
		tangentArray[i][0] = TN[0]*127
		tangentArray[i][1] = TN[1]*127
		tangentArray[i][2] = TN[2]*127
		tangentArray[i][3] = TNW
	normalArray = np.multiply(normalArray,127)
	normalArray = np.floor(normalArray)
	normalArray = np.insert(normalArray, 3, np.zeros(vertexCount,np.dtype("<b")),axis=1)
	norTanArray = np.empty((vertexCount*2,4), dtype=np.dtype("<b"))
	norTanArray[::2] = normalArray
	norTanArray[1::2] = tangentArray
	#print(norTanArray)
	
	
	bufferStream.write(norTanArray.tobytes())

def WriteToUVBuffer(bufferStream,uvList):
	uvArray = np.array(uvList,dtype = np.dtype("<e"))
	uvArray = uvArray.flatten()
	uvArray[1::2] *= -1
	uvArray[1::2] += 1
	#print(uvArray)
	bufferStream.write(uvArray.tobytes())

def WriteToWeightBuffer(bufferStream,boneWeightsList,boneIndicesList,isSixWeight):
	
	if isSixWeight:
		#TODO Do bitfield work in numpy
		bf = CompressedSixWeightIndices()
		uint64Array = np.empty((len(boneWeightsList),1), dtype=np.dtype("<Q"))
		for index in range(len(boneIndicesList)):
			#print(f"boneIndicesList: {boneIndicesList[index]}")
			bf.weights.w0 = boneIndicesList[index][0]
			bf.weights.w1 = boneIndicesList[index][1]
			bf.weights.w2 = boneIndicesList[index][2]
			bf.weights.pad0 = 0
			bf.weights.w3 = boneIndicesList[index][3]
			bf.weights.w4 = boneIndicesList[index][4]
			bf.weights.w5 = boneIndicesList[index][5]
			bf.weights.pad1 = 0
			uint64Array[index] = bf.asUInt64
			#print(f"bitfield: {[bf.weights.w0,bf.weights.w1,bf.weights.w2,bf.weights.w3,bf.weights.w4,bf.weights.w5]}")
			#print(f"uint64: {uint64Array[index]}\n")
		boneIndicesArray = uint64Array.view(dtype = "<B")#.byteswap(inplace=True)
		#print(boneIndicesArray)
	else:
		boneIndicesArray = boneIndicesList.astype("<B")
	
	
	
	boneWeightsArray = np.array(boneWeightsList)
	
	#Clean Weights
	#boneWeightsArray = np.round(boneWeightsArray,decimals=4)
	#MIN_FLOAT_VALUE = 0.01
	#boneWeightsArray = np.where(((boneWeightsArray != 0) & (boneWeightsArray < MIN_FLOAT_VALUE)),0.0,boneWeightsArray)
	
	#boneWeightsArray = np.round(boneWeightsArray,decimals = 2)
	weightSums = np.sum(boneWeightsArray,axis = 1,dtype = np.float32)
	#print(weightSums)
	#Normalize weights to 1.0
	with np.errstate(divide='ignore', invalid='ignore'):
	    boneWeightsArray = boneWeightsArray / weightSums[:,None]
	    boneWeightsArray[weightSums == 0] = 0
	boneWeightsArray = np.multiply(boneWeightsArray,255)
	boneWeightsArray = np.round(boneWeightsArray)
	diffSums = 255.0 - np.sum(boneWeightsArray,axis = 1,dtype = np.float32)
	#print(diffSums)
	#for i in range(len(boneWeightsArray)):
		#print(f"{boneWeightsArray[i]}, difference: {diffSums[i]}")
	
	#Add difference of 255 to the largest value of each row in weight array
	boneWeightsArray[np.arange(boneWeightsArray.shape[0]), np.argmax(boneWeightsArray, axis=1)] += diffSums
	#boneWeightsArray[:, 0] += diffSums
	boneWeightsArray = boneWeightsArray.astype("<B")
	
	if (255 - np.sum(boneWeightsArray,axis = 1,dtype = np.int32) != 0).any():
		raiseWarning("Non normalized weights detected on sub mesh! Weights may not behave as expected in game!")
	
	#Set zero weight bone indices to 0
	#boneIndicesArray = np.where(boneWeightsArray == 0,0,boneIndicesArray)
	
	weightArray = np.empty((len(boneWeightsList)*2,8), dtype=np.dtype("<B"))
	weightArray[::2] = boneIndicesArray
	weightArray[1::2] = boneWeightsArray
	#print(weightArray)
	bufferStream.write(weightArray.tobytes())
	
def WriteToColorBuffer(bufferStream,colorList):
	colorArray = np.array(colorList,dtype = np.float32)
	colorArray = np.multiply(colorArray,255)
	colorArray = colorArray.astype(dtype=">B")
	#print(colorArray)
	bufferStream.write(colorArray.tobytes())
def WriteToFaceBuffer(bufferStream,faceList):
	data = struct.pack(f'{len(faceList)*3}H', *chain.from_iterable(faceList))
	
	if (len(data))%4 != 0:#Align face buffer to 4 bytes per submesh
		data += b'\x00\x00'
	bufferStream.write(data)
def WriteToIntFaceBuffer(bufferStream,faceList):
	data = struct.pack(f'{len(faceList)*3}I', *chain.from_iterable(faceList))
	
	#if (len(data))%4 != 0:#Align face buffer to 4 bytes per submesh
		#data += b'\x00\x00\x00\x00'
	bufferStream.write(data)

class sizeData:
	def __init__(self,version):
		self.MESH_HEADER_SIZE = 128
		if version >= VERSION_SF6:
			self.MESH_HEADER_SIZE = 168
		if version >= VERSION_DD2:
			self.MESH_HEADER_SIZE = 176
		self.LOD_HEADER_OFFSET_LIST_OFFSET = 64#Offset from start of lod header to offset list
		self.LOD_GROUP_HEADER_OFFSET_LIST_OFFSET = 16#Offset from start of lod group to offset list	
		self.MESH_GROUP_SIZE = 16
		self.MATERIAL_SUBDIVISION_SIZE = 24
		self.SKELETON_REMAP_TABLE_OFFSET = 48
		self.BONE_INFO_ENTRY_SIZE = 16
		self.MATRIX_SIZE = 64
		self.AABB_OFFSET = 16
		self.AABB_SIZE = 32
		self.VERTEX_ELEMENT_OFFSET = 64
		self.STREAMING_HEADER_SIZE = 16#WILDS
		if version < VERSION_RE8:
			self.LOD_HEADER_OFFSET_LIST_OFFSET = 72
			self.MATERIAL_SUBDIVISION_SIZE = 16
		
		if version <= VERSION_RE8:
			self.VERTEX_ELEMENT_OFFSET = 48
		if version >= VERSION_SF6:
			self.VERTEX_ELEMENT_OFFSET = 80
		
		
		if version >= VERSION_DD2NEW:
			self.MATERIAL_SUBDIVISION_SIZE = 28
			
		if version >= VERSION_DR:
			self.MATERIAL_SUBDIVISION_SIZE = 32
		self.VERTEX_ELEMENT_SIZE = 8

def ParsedREMeshToREMesh(parsedMesh,meshVersion):
	print(f"Mesh Version:{meshVersion}")
	version = meshFileVersionToNewVersionDict.get(meshVersion,getNearestRemapVersion(meshVersion)) 
	print(f"Remapped Version:{version}")
	sd = sizeData(version)
	currentOffset = 0
	currentVertexIndex = 0
	currentFaceIndex = 0
	
	#totalTangentGenerationTime = 0.0#For benchmarking the time it takes tangents to calculate
	
	#Buffers
	vertexPosBuffer = BytesIO()
	norTanBuffer = BytesIO()
	UVBuffer = BytesIO()
	UV2Buffer = BytesIO()
	weightBuffer = BytesIO()
	colorBuffer = BytesIO()
	faceBuffer = BytesIO()
	extraWeightBuffer = BytesIO()#MH Wilds extended weight buffer
	secondaryWeightBuffer = BytesIO()#DD2 shapekey
	
	parsedSubMeshToSubMeshDataDict = dict()
	
	reMesh = REMesh()
	
	reMesh.fileHeader.version = meshFileVersionToInternalVersionDict.get(meshVersion,getNearestRemapVersion(meshVersion))
	#TODO Fix shadow mesh export, causes game to crash. It seems shadow meshes can't have unique lods, even if the sub mesh offsets are still shared. They might only be able to use the existing full lods from the main mesh
	#parsedMesh.shadowMeshLODList.clear()
	
	#Main Meshes
	if parsedMesh.mainMeshLODList != []:
		reMesh.fileHeader.meshGroupOffset = sd.MESH_HEADER_SIZE
		reMesh.lodHeader = MainMeshHeader()
		reMesh.lodHeader.lodGroupCount = len(parsedMesh.mainMeshLODList)
		reMesh.lodHeader.materialCount = len(parsedMesh.materialNameList)
		reMesh.lodHeader.bbox = parsedMesh.boundingBox
		reMesh.lodHeader.sphere = parsedMesh.boundingSphere
		for viscon in parsedMesh.mainMeshLODList[0].visconGroupList:
			reMesh.lodHeader.totalMeshCount += len(viscon.subMeshList)
		reMesh.lodHeader.skinWeightCount = 18
		if version == VERSION_SF6:
			reMesh.lodHeader.skinWeightCount = 9
		if parsedMesh.bufferHasUV2:#This is wrong, uv count is determined by something else. However uv count is unused by the game so it doesn't really matter
			reMesh.lodHeader.uvCount = 2
		else:
			reMesh.lodHeader.uvCount = 1
		if parsedMesh.bufferHasIntFaces:
			reMesh.lodHeader.has32BitIndexBuffer = 1
		reMesh.lodHeader.offsetOffset = sd.MESH_HEADER_SIZE+sd.LOD_HEADER_OFFSET_LIST_OFFSET
		
		#currentOffset = LOD Group 0 offset
		currentOffset = reMesh.lodHeader.offsetOffset + 8*reMesh.lodHeader.lodGroupCount + getPaddingAmount(reMesh.lodHeader.offsetOffset+(8*reMesh.lodHeader.lodGroupCount),16)
		
		#SF6 uses six weights with higher possible bone index values
		isSixWeight = version == VERSION_SF6 or version == VERSION_MHWILDS
		
		#Main Meshes
		#TODO Move lod parsing into a function and call it for both main and shadow mesh
		for lod in parsedMesh.mainMeshLODList:
			reMesh.lodHeader.lodGroupOffsetList.append(currentOffset)
			lodGroupHeader = LODGroupHeader()
			lodGroupHeader.count = len(lod.visconGroupList)
			lodGroupHeader.distance = lod.lodDistance
			currentOffset += sd.LOD_GROUP_HEADER_OFFSET_LIST_OFFSET
			lodGroupHeader.offsetOffset = currentOffset
			#Viscon 0 Offset
			currentOffset = lodGroupHeader.offsetOffset + 8*lodGroupHeader.count + getPaddingAmount(lodGroupHeader.offsetOffset+(8*lodGroupHeader.count),16)
			for viscon in lod.visconGroupList:
				lodGroupHeader.meshGroupOffsetList.append(currentOffset)
				#print(f"viscon {viscon.visconGroupNum} offset: {str(currentOffset)}")
				meshGroup = MeshGroup()
				meshGroup.visconGroupID = viscon.visconGroupNum
				meshGroup.meshCount = len(viscon.subMeshList)
				for parsedSubMesh in viscon.subMeshList:
					subMesh = MaterialSubdivision()
					subMesh.materialIndex = parsedSubMesh.materialIndex
					subMesh.faceCount = len(parsedSubMesh.faceList) * 3
					if parsedMesh.bufferHasIntFaces:
						paddedFaceCount = subMesh.faceCount
					else:
						paddedFaceCount = getPaddedPos(subMesh.faceCount, 2)
					meshGroup.faceCount += paddedFaceCount
					
					vertCount = len(parsedSubMesh.vertexPosList)
					meshGroup.vertexCount += vertCount
					parsedSubMeshToSubMeshDataDict[parsedSubMesh] = subMesh
					if not parsedSubMesh.isReusedMesh:
						subMesh.faceStartIndex = currentFaceIndex
						subMesh.vertexStartIndex = currentVertexIndex
						currentVertexIndex += vertCount
						currentFaceIndex += paddedFaceCount
						#TODO Add vertices and faces to buffers
						WriteToVertexPosBuffer(vertexPosBuffer,parsedSubMesh.vertexPosList)
						
						#tangentGenerationStartTime = time.time()
						WriteToNorTanBuffer(norTanBuffer, parsedSubMesh.normalList,parsedSubMesh.tangentList)
						#WriteToNorTanBufferOld(norTanBuffer, parsedSubMesh.normalList,parsedSubMesh.vertexPosList,parsedSubMesh.uvList,parsedSubMesh.faceList)
						#totalTangentGenerationTime +=  (time.time() - tangentGenerationStartTime)
						
						#Copy uv1 to uv2 if buffer has uv2, but the mesh only has 1 uv
						if parsedMesh.bufferHasUV2 and parsedSubMesh.uv2List is None:
							parsedSubMesh.uv2List = parsedSubMesh.uvList
						
						
						WriteToUVBuffer(UVBuffer,parsedSubMesh.uvList)
						if parsedSubMesh.uv2List is not None:
							WriteToUVBuffer(UV2Buffer,parsedSubMesh.uv2List)
						
						if len(parsedSubMesh.weightIndicesList) != 0 and len(parsedSubMesh.weightIndicesList) == len(parsedSubMesh.weightList):
							WriteToWeightBuffer(weightBuffer,parsedSubMesh.weightList,parsedSubMesh.weightIndicesList,isSixWeight)
						
						if parsedMesh.bufferHasExtraWeight and len(parsedSubMesh.extraWeightIndicesList) != 0 and len(parsedSubMesh.extraWeightIndicesList) == len(parsedSubMesh.extraWeightList):
							WriteToWeightBuffer(extraWeightBuffer,parsedSubMesh.extraWeightList,parsedSubMesh.extraWeightIndicesList,isSixWeight)
						
						#DD2 shapekeys
						if len(parsedSubMesh.secondaryWeightIndicesList) != 0 and len(parsedSubMesh.secondaryWeightIndicesList) == len(parsedSubMesh.secondaryWeightList):
							WriteToWeightBuffer(secondaryWeightBuffer,parsedSubMesh.secondaryWeightList,parsedSubMesh.secondaryWeightIndicesList,isSixWeight)
						
						
						#Add vertex color if it's missing and other meshes have it
						if parsedMesh.bufferHasColor and parsedSubMesh.colorList is None:
							parsedSubMesh.colorList = [(255,255,255,255)]*len(parsedSubMesh.vertexPosList)
						
						if parsedSubMesh.colorList is not None:
							WriteToColorBuffer(colorBuffer,parsedSubMesh.colorList)
						if parsedMesh.bufferHasIntFaces:
							WriteToIntFaceBuffer(faceBuffer,parsedSubMesh.faceList)
						else:
							WriteToFaceBuffer(faceBuffer,parsedSubMesh.faceList)
					else:
						linkedMeshData = parsedSubMeshToSubMeshDataDict[parsedSubMesh.linkedSubMesh]
						subMesh.faceStartIndex = linkedMeshData.faceStartIndex
						subMesh.vertexStartIndex = linkedMeshData.vertexStartIndex
						#TODO Get linked mesh offset for reused meshes
						#Make dict of offset key to tuple of vertexstartindex and facestartindex
						#meshOffsetDict[parsedSubMesh.linkedMesh][0]
					meshGroup.vertexInfoList.append(subMesh)
				currentOffset += sd.MESH_GROUP_SIZE + meshGroup.meshCount*sd.MATERIAL_SUBDIVISION_SIZE
				
				lodGroupHeader.meshGroupList.append(meshGroup)
			reMesh.lodHeader.lodGroupList.append(lodGroupHeader)
	#print(f"Tangent calculation took {timeFormat%(totalTangentGenerationTime * 1000)} ms.")
	#Shadow Meshes
	
	if parsedMesh.shadowMeshLinkedLODList != []:
		reMesh.fileHeader.shadowMeshGroupOffset = currentOffset
		reMesh.shadowHeader = ShadowHeader()
		reMesh.shadowHeader.skinWeightCount = 18
		reMesh.shadowHeader.lodGroupCount = len(parsedMesh.shadowMeshLinkedLODList)
		reMesh.shadowHeader.materialCount = reMesh.lodHeader.materialCount
		reMesh.shadowHeader.totalMeshCount = reMesh.lodHeader.totalMeshCount
		
		if parsedMesh.bufferHasUV2:
			reMesh.shadowHeader.uvCount = 2
		else:
			reMesh.shadowHeader.uvCount = 1
		reMesh.shadowHeader.offsetOffset = reMesh.fileHeader.shadowMeshGroupOffset+sd.LOD_HEADER_OFFSET_LIST_OFFSET
		
		for linkedLOD in parsedMesh.shadowMeshLinkedLODList:
			mainMeshLODIndex = parsedMesh.mainMeshLODList.index(linkedLOD)
			reMesh.shadowHeader.lodGroupOffsetList.append(reMesh.lodHeader.lodGroupOffsetList[mainMeshLODIndex])
		
		#currentOffset = LOD Group 0 offset
		currentOffset = getPaddedPos(reMesh.shadowHeader.offsetOffset + 8*reMesh.shadowHeader.lodGroupCount,16)
	#It turns out shadow meshes can only use existing lods from the main mesh so this was pointless
	"""
	if parsedMesh.shadowMeshLODList != []:
		reMesh.fileHeader.shadowMeshGroupOffset = currentOffset
		reMesh.shadowHeader = ShadowHeader()
		reMesh.shadowHeader.skinWeightCount = 18
		reMesh.shadowHeader.lodGroupCount = len(parsedMesh.shadowMeshLODList)
		reMesh.shadowHeader.materialCount = len(parsedMesh.materialNameList)
		for viscon in parsedMesh.shadowMeshLODList[0].visconGroupList:
			reMesh.shadowHeader.totalMeshCount += len(viscon.subMeshList)
		if parsedMesh.bufferHasUV2:
			reMesh.shadowHeader.uvCount = 2
		else:
			reMesh.shadowHeader.uvCount = 1
		reMesh.shadowHeader.offsetOffset = reMesh.fileHeader.shadowMeshGroupOffset+sd.LOD_HEADER_OFFSET_LIST_OFFSET
		
		#currentOffset = LOD Group 0 offset
		currentOffset = getPaddedPos(reMesh.shadowHeader.offsetOffset + 8*reMesh.shadowHeader.lodGroupCount,16)
		
		for lod in parsedMesh.shadowMeshLODList:
			reMesh.shadowHeader.lodGroupOffsetList.append(currentOffset)
			lodGroupHeader = LODGroupHeader()
			lodGroupHeader.count = len(lod.visconGroupList)
			lodGroupHeader.distance = lod.lodDistance
			currentOffset += sd.LOD_GROUP_HEADER_OFFSET_LIST_OFFSET
			lodGroupHeader.offsetOffset = currentOffset
			#Viscon 0 Offset
			currentOffset = lodGroupHeader.offsetOffset + 8*lodGroupHeader.count + getPaddingAmount(lodGroupHeader.offsetOffset+(8*lodGroupHeader.count),16)
			
			for viscon in lod.visconGroupList:
				lodGroupHeader.meshGroupOffsetList.append(currentOffset)
				#print(f"viscon {viscon.visconGroupNum} offset: {str(currentOffset)}")
				meshGroup = MeshGroup()
				meshGroup.visconGroupID = viscon.visconGroupNum
				meshGroup.meshCount = len(viscon.subMeshList)
				for parsedSubMesh in viscon.subMeshList:
					subMesh = MaterialSubdivision()
					parsedSubMeshToSubMeshDataDict[parsedSubMesh] = subMesh
					subMesh.materialIndex = parsedSubMesh.materialIndex
					subMesh.faceCount = len(parsedSubMesh.faceList) * 3
					paddedFaceCount = getPaddedPos(subMesh.faceCount, 2)
					meshGroup.faceCount += paddedFaceCount
					
					vertCount = len(parsedSubMesh.vertexPosList)
					meshGroup.vertexCount += vertCount
					if not parsedSubMesh.isReusedMesh:
						subMesh.faceStartIndex = currentFaceIndex
						subMesh.vertexStartIndex = currentVertexIndex
						currentVertexIndex += vertCount
						currentFaceIndex += paddedFaceCount
						#TODO Add vertices and faces to buffers
						WriteToVertexPosBuffer(vertexPosBuffer,parsedSubMesh.vertexPosList)
						WriteToNorTanBuffer(norTanBuffer, parsedSubMesh.normalList,parsedSubMesh.vertexPosList,parsedSubMesh.uvList,parsedSubMesh.faceList)
						WriteToUVBuffer(UVBuffer,parsedSubMesh.uvList)
						if parsedSubMesh.uv2List != []:
							WriteToUVBuffer(UV2Buffer,parsedSubMesh.uv2List)
						if parsedSubMesh.weightIndicesList != [] and parsedSubMesh.weightList != []:
							WriteToWeightBuffer(weightBuffer,parsedSubMesh.weightList,parsedSubMesh.weightIndicesList)
						if parsedSubMesh.colorList != []:
							WriteToColorBuffer(colorBuffer,parsedSubMesh.colorList)
						
						WriteToFaceBuffer(faceBuffer,parsedSubMesh.faceList)
					else:
						linkedMeshData = parsedSubMeshToSubMeshDataDict[parsedSubMesh.linkedSubMesh]
						subMesh.faceStartIndex = linkedMeshData.faceStartIndex
						subMesh.vertexStartIndex = linkedMeshData.vertexStartIndex
						#TODO Get linked mesh offset for reused meshes
						#Make dict of offset key to tuple of vertexstartindex and facestartindex
						#meshOffsetDict[parsedSubMesh.linkedMesh][0]
					meshGroup.vertexInfoList.append(subMesh)
				currentOffset += sd.MESH_GROUP_SIZE + meshGroup.meshCount*sd.MATERIAL_SUBDIVISION_SIZE
				
				lodGroupHeader.meshGroupList.append(meshGroup)
			reMesh.shadowHeader.lodGroupList.append(lodGroupHeader)	
	"""
	#Skeleton / AABB
	if parsedMesh.skeleton != None:
		reMesh.fileHeader.skeletonOffset = currentOffset
		reMesh.skeletonHeader = Skeleton()
		reMesh.skeletonHeader.boneCount = len(parsedMesh.skeleton.boneList)
		reMesh.skeletonHeader.remapCount = len(parsedMesh.skeleton.weightedBones)
		
		
		#Do AABB struct while looping through bones
		if reMesh.skeletonHeader.remapCount > 0:
			reMesh.boneBoundingBoxHeader = BoneAABBGroup()
			reMesh.boneBoundingBoxHeader.count = reMesh.skeletonHeader.remapCount
		for boneIndex, parsedBone in enumerate(parsedMesh.skeleton.boneList):
			if parsedBone.boneName in parsedMesh.skeleton.weightedBones:
				reMesh.skeletonHeader.boneRemapList.append(boneIndex)
				if parsedBone.boundingBox != None and reMesh.boneBoundingBoxHeader != None:
					reMesh.boneBoundingBoxHeader.bboxList.append(parsedBone.boundingBox)
			reMesh.skeletonHeader.localMatList.append(parsedBone.localMatrix)
			reMesh.skeletonHeader.worldMatList.append(parsedBone.worldMatrix)
			reMesh.skeletonHeader.inverseMatList.append(parsedBone.inverseMatrix)
			
			bone = Bone()
			bone.boneIndex = boneIndex
			bone.boneParent = parsedBone.parentIndex
			bone.boneSibling = parsedBone.nextSiblingIndex
			bone.boneChild = parsedBone.nextChildIndex
			bone.boneSymmetric = parsedBone.symmetryBoneIndex
			bone.useSecondaryWeight = parsedBone.useSecondaryWeight
			reMesh.skeletonHeader.boneInfoList.append(bone)
		
		reMesh.skeletonHeader.boneHeaderOffset = getPaddedPos(reMesh.fileHeader.skeletonOffset + sd.SKELETON_REMAP_TABLE_OFFSET + 2*reMesh.skeletonHeader.remapCount,16)
		reMesh.skeletonHeader.boneLocalMatrixOffset = reMesh.skeletonHeader.boneHeaderOffset + reMesh.skeletonHeader.boneCount * sd.BONE_INFO_ENTRY_SIZE
		reMesh.skeletonHeader.boneWorldMatrixOffset = reMesh.skeletonHeader.boneLocalMatrixOffset + reMesh.skeletonHeader.boneCount * sd.MATRIX_SIZE
		reMesh.skeletonHeader.boneInverseMatrixOffset = reMesh.skeletonHeader.boneWorldMatrixOffset + reMesh.skeletonHeader.boneCount * sd.MATRIX_SIZE
		
		currentOffset = reMesh.skeletonHeader.boneInverseMatrixOffset + reMesh.skeletonHeader.boneCount * sd.MATRIX_SIZE
	#Name lists and remaps
	currentNameIndex = 0
	for index,materialName in enumerate(parsedMesh.materialNameList):
		reMesh.rawNameList.append(materialName)
		reMesh.materialNameRemapList.append(index)
	currentNameIndex += len(reMesh.rawNameList)
	if parsedMesh.skeleton != None:
		for bone in parsedMesh.skeleton.boneList:
			reMesh.rawNameList.append(bone.boneName)
			reMesh.boneNameRemapList.append(currentNameIndex)
			currentNameIndex += 1
	#TODO Blend Shape Names Remap
	
	reMesh.fileHeader.materialNameRemapOffset = currentOffset
	currentOffset = getPaddedPos(currentOffset + (len(reMesh.materialNameRemapList)*2), 16)
	if parsedMesh.skeleton != None:
		reMesh.fileHeader.boneNameRemapOffset = currentOffset
		currentOffset = getPaddedPos(currentOffset + (len(reMesh.boneNameRemapList)*2), 16)
	
	reMesh.fileHeader.nameOffsetsOffset = currentOffset
	currentOffset = getPaddedPos(currentOffset + (len(reMesh.rawNameList)*8), 16)#Get the position after all string offsets
	for name in reMesh.rawNameList:
		reMesh.rawNameOffsetList.append(currentOffset)
		currentOffset += len(name.encode('utf-8'))+1
	reMesh.fileHeader.nameCount = len(reMesh.rawNameList)
	currentOffset = getPaddedPos(currentOffset, 16)
	#AABB
	if reMesh.boneBoundingBoxHeader != None:
		reMesh.fileHeader.aabbOffset = currentOffset
		reMesh.boneBoundingBoxHeader.offset = currentOffset + sd.AABB_OFFSET
		currentOffset += sd.AABB_OFFSET + reMesh.boneBoundingBoxHeader.count * sd.AABB_SIZE
		
	#Mesh Buffer
	reMesh.fileHeader.meshOffset = currentOffset
	
	
	reMesh.meshBufferHeader = MeshBufferHeader()
	reMesh.meshBufferHeader.vertexBuffer = bytearray()
	currentBufferOffset = 0
	if vertexPosBuffer.tell() != 0:
		vertexElement = VertexElementStruct()
		vertexElement.posStartOffset = currentBufferOffset
		vertexElement.typing = 0
		vertexElement.stride = 12
		currentBufferOffset+=vertexPosBuffer.tell()
		reMesh.meshBufferHeader.vertexElementList.append(vertexElement)
		reMesh.meshBufferHeader.vertexBuffer.extend(vertexPosBuffer.getvalue())

	if norTanBuffer.tell() != 0:
		vertexElement = VertexElementStruct()
		vertexElement.posStartOffset = currentBufferOffset
		vertexElement.typing = 1
		vertexElement.stride = 8
		currentBufferOffset+=norTanBuffer.tell()
		reMesh.meshBufferHeader.vertexElementList.append(vertexElement)
		reMesh.meshBufferHeader.vertexBuffer.extend(norTanBuffer.getvalue())

	if UVBuffer.tell() != 0:
		vertexElement = VertexElementStruct()
		vertexElement.posStartOffset = currentBufferOffset
		vertexElement.typing = 2
		vertexElement.stride = 4
		currentBufferOffset+=UVBuffer.tell()
		reMesh.meshBufferHeader.vertexElementList.append(vertexElement)
		reMesh.meshBufferHeader.vertexBuffer.extend(UVBuffer.getvalue())

	if UV2Buffer.tell() != 0:
		vertexElement = VertexElementStruct()
		vertexElement.posStartOffset = currentBufferOffset
		vertexElement.typing = 3
		vertexElement.stride = 4
		currentBufferOffset+=UV2Buffer.tell()
		reMesh.meshBufferHeader.vertexElementList.append(vertexElement)
		reMesh.meshBufferHeader.vertexBuffer.extend(UV2Buffer.getvalue())

	if weightBuffer.tell() != 0:
		vertexElement = VertexElementStruct()
		vertexElement.posStartOffset = currentBufferOffset
		vertexElement.typing = 4
		vertexElement.stride = 16
		currentBufferOffset+=weightBuffer.tell()
		reMesh.meshBufferHeader.vertexElementList.append(vertexElement)
		reMesh.meshBufferHeader.vertexBuffer.extend(weightBuffer.getvalue())
			
	
	if colorBuffer.tell() != 0:
		#print("Added color buffer")
		vertexElement = VertexElementStruct()
		vertexElement.posStartOffset = currentBufferOffset
		vertexElement.typing = 5
		vertexElement.stride = 4
		currentBufferOffset+=colorBuffer.tell()
		reMesh.meshBufferHeader.vertexElementList.append(vertexElement)
		reMesh.meshBufferHeader.vertexBuffer.extend(colorBuffer.getvalue())

	if extraWeightBuffer.tell() != 0:
		vertexElement = VertexElementStruct()
		vertexElement.posStartOffset = currentBufferOffset
		vertexElement.typing = 7
		vertexElement.stride = 16
		currentBufferOffset+=extraWeightBuffer.tell()
		reMesh.meshBufferHeader.vertexElementList.append(vertexElement)
		reMesh.meshBufferHeader.vertexBuffer.extend(extraWeightBuffer.getvalue())
		
	reMesh.meshBufferHeader.faceBuffer = faceBuffer.getvalue()
	#print(len(reMesh.meshBufferHeader.faceBuffer))
	reMesh.meshBufferHeader.vertexElementCount = len(reMesh.meshBufferHeader.vertexElementList)
	reMesh.meshBufferHeader.mainVertexElementCount = reMesh.meshBufferHeader.vertexElementCount
	reMesh.meshBufferHeader.vertexElementOffset = reMesh.fileHeader.meshOffset + sd.VERTEX_ELEMENT_OFFSET
	reMesh.meshBufferHeader.vertexBufferOffset = getPaddedPos(reMesh.meshBufferHeader.vertexElementOffset +  reMesh.meshBufferHeader.vertexElementCount * sd.VERTEX_ELEMENT_SIZE,16)
	
	#TODO check on this, padding vertex buffer size might cause issues in some games
	reMesh.meshBufferHeader.vertexBufferSize = getPaddedPos(currentBufferOffset,16)
	reMesh.meshBufferHeader.faceBufferOffset = getPaddedPos(reMesh.meshBufferHeader.vertexBufferOffset + reMesh.meshBufferHeader.vertexBufferSize,16)
	reMesh.meshBufferHeader.faceBufferSize = faceBuffer.tell()
	
	#Content Flags
	unknFlag16 = False#Bit index 15
	unknFlag10 = False#Bit index 9
	
	
	if version < VERSION_SF6:
		reMesh.meshBufferHeader.vertexElementSize = 31872
		reMesh.meshBufferHeader.block2FaceBufferOffset = reMesh.meshBufferHeader.faceBufferSize
	
		
	if version >= VERSION_SF6:
		reMesh.fileHeader.sf6UnknCount = 84
		reMesh.meshBufferHeader.vertexElementSize = 27104
		reMesh.fileHeader.verticesOffset = reMesh.meshBufferHeader.vertexBufferOffset
		reMesh.fileHeader.streamingInfoOffset =  reMesh.fileHeader.meshOffset + sd.VERTEX_ELEMENT_OFFSET - 16
		reMesh.meshBufferHeader.block2FaceBufferOffset = reMesh.meshBufferHeader.vertexBufferSize + reMesh.meshBufferHeader.faceBufferSize
		reMesh.meshBufferHeader.NULL = reMesh.meshBufferHeader.block2FaceBufferOffset
		reMesh.meshBufferHeader.totalBufferSize = getPaddedPos(reMesh.meshBufferHeader.block2FaceBufferOffset,16)
		unknFlag16 = True
		unknFlag10 = True
	
	if version == VERSION_SF6:
		reMesh.fileHeader.sf6UnknCount = 6
		reMesh.fileHeader.unknHash = 3407096719	
	
	
	currentOffset = getPaddedPos(reMesh.meshBufferHeader.faceBufferOffset + reMesh.meshBufferHeader.faceBufferSize,16)
	if version >= VERSION_DD2:	
		if parsedMesh.bufferHasSecondaryWeight:
			reMesh.meshBufferHeader.sunbreakOffset = reMesh.meshBufferHeader.vertexBufferOffset + reMesh.meshBufferHeader.totalBufferSize
			
			reMesh.meshBufferHeader.secondaryWeightBuffer = secondaryWeightBuffer.getvalue()
			reMesh.meshBufferHeader.sunbreakSecondUnknown = len(reMesh.meshBufferHeader.secondaryWeightBuffer)
			currentOffset = reMesh.meshBufferHeader.sunbreakOffset + len(reMesh.meshBufferHeader.secondaryWeightBuffer)
	reMesh.fileHeader.fileSize = currentOffset
	
	
	
	reMesh.fileHeader.contentFlag.setBitFlag(unknFlag16,unknFlag10,hasUnknFlag8 = True, hasGroupPivot = reMesh.floatsHeader != None, hasBlendShape = reMesh.blendShapeHeader != None, hasSkeleton = reMesh.skeletonHeader != None, hasAABB = reMesh.boneBoundingBoxHeader != None)
	vertexPosBuffer.close()
	norTanBuffer.close()
	UVBuffer.close()
	UV2Buffer.close()
	weightBuffer.close()
	colorBuffer.close()
	extraWeightBuffer.close()
	faceBuffer.close()
	secondaryWeightBuffer.close()
				
	return reMesh
#---RE MESH IO FUNCTIONS---#

def readREMesh(filepath,lodTarget = None):
	print("Opening " + filepath)
	try:  
		file = open(filepath,"rb",buffering=8192)
	except:
		raiseError("Failed to open " + filepath)
	try:
		meshVersion = int(os.path.splitext(filepath)[1].replace(".",""))
	except:
		print("Unable to read mesh version from file path, assuming MHRSB")
		meshVersion = 2109148288#MHRSB
	version = meshFileVersionToNewVersionDict.get(meshVersion,getNearestRemapVersion(meshVersion))
	if meshVersion not in meshFileVersionToNewVersionDict:
		raiseWarning(f"Mesh Version ({str(meshVersion)}) not supported! Attempting import...")
		print(f"Nearest Remap Version: {str(version)} ({meshFileVersionToGameNameDict[newVersionToMeshFileVersion[version]]})")
	
	streamingBuffer = None#WILDS
	#if version >= VERSION_MHWILDS:
		
	#Precheck to see if user imported a headerless streaming mesh
	magic = read_uint(file)
	if magic != 1213416781 and "streaming" in filepath:
		raiseError("Attempted to import a streaming mesh file. Streaming mesh files cannot be imported directly.\nImport the mesh file that has same path and name that's not in the streaming folder.")
		raise Exception("Streaming meshes can't be imported directly. Import the non streaming mesh instead.")
	file.seek(0)
	
	if version >= VERSION_SF6:
		paths = splitNativesPath(filepath)
		if paths != None:#Returns none if path does not contain a natives folder
			rootPath = paths[0]#The path to the natives\STM folder from the root
			nativesPath = paths[1]#The path to the file inside the natives\STM folder
			streamingMeshPath = os.path.join(rootPath,"streaming",nativesPath)
			if os.path.isfile(streamingMeshPath):
				
				try:  
					streamFile = open(streamingMeshPath,"rb")
					streamingBuffer = streamFile.read()
					streamFile.close()
					print(f"Loaded {len(streamingBuffer)} bytes from streaming mesh at {streamingMeshPath}")
				except:
					raiseError("Failed to open " + filepath)
		
	reMeshFile = REMesh()
	reMeshFile.meshVersion = meshVersion
	reMeshFile.read(file,version,lodTarget,streamingBuffer)
	file.close()
	return reMeshFile
def writeREMesh(reMeshFile,filepath):
	print("Writing to " + filepath)
	try:
		file = open(filepath,"wb",buffering=8192)
	except:
		raiseError("Failed to open " + filepath)
	try:
		meshVersion = int(os.path.splitext(filepath)[1].replace(".",""))
	except:
		print("Unable to read mesh version from file path, assuming MHRSB")
		meshVersion = 2109148288#MHRSB
	version = newVersionToMeshFileVersion.get(meshVersion,getNearestRemapVersion(meshVersion))
	reMeshFile.meshVersion = meshVersion
	reMeshFile.write(file,version)
	file.close()

