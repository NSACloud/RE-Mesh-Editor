#Author: NSA Cloud
import os

from ..gen_functions import textColors,raiseWarning,raiseError,getPaddingAmount,read_uint,read_int,read_uint64,read_float,read_short,read_ushort,read_ubyte,read_unicode_string,read_byte,write_uint,write_int,write_uint64,write_float,write_short,write_ushort,write_ubyte,write_unicode_string,write_byte
from ..hashing.pymmh3 import hash, hash_wide
import ctypes

DEBUG_MODE = False

gameNameMDFVersionDict = {
	10:"RE2",#DMC5
	13:"RE3",
	19:"RE8",
	21:"RE2RT",#RE3RT
	23:"MHRSB",
	31:"SF6",
	32:"RE4",
	40:"DD2",
	
	"DMC5":10,
	"RE2":10,
	"RE3":13,
	"RE8":19,
	"RE2RT":21,
	"RE3RT":21,
	"MHRSB":23,
	"SF6":31,
	"RE4":32,
	"DD2":40,#KG
	"KG":40,
	}
def getMDFVersionToGameName(gameName):
	return gameNameMDFVersionDict.get(gameName,-1)
class SIZEDATA():
	def __init__(self,version):
		self.HEADER_SIZE = 16
		self.MATERIAL_ENTRY_SIZE = 80
		self.TEXTURE_ENTRY_SIZE = 32
		self.PROPERTY_ENTRY_SIZE = 24
		self.PROPERTY_VALUE_SIZE = 4
		self.GPBF_ENTRY_SIZE = 16
		
		if version < 13:
			TEXTURE_ENTRY_SIZE = 24
		if version < 19:
			self.MATERIAL_ENTRY_SIZE = 64
		if version >= 31:
			self.MATERIAL_ENTRY_SIZE = 100
c_int32 = ctypes.c_int32

class MDFFlags_bits(ctypes.LittleEndianStructure):
	_fields_ = 	[
					("BaseTwoSideEnable",c_int32,1),
					("BaseAlphaTestEnable",c_int32,1),
					("ShadowCastDisable",c_int32,1),
					("VertexShaderUsed",c_int32,1),
					("EmissiveUsed",c_int32,1),
					("TessellationEnable",c_int32,1),
					("EnableIgnoreDepth",c_int32,1),
					("AlphaMaskUsed",c_int32,1),
					("ForcedTwoSideEnable",c_int32,1),
					("TwoSideEnable",c_int32,1),
					("TessFactor",c_int32,6),
					("PhongFactor",c_int32,8),
					("RoughTransparentEnable",c_int32,1),
					("ForcedAlphaTestEnable",c_int32,1),
					("AlphaTestEnable",c_int32,1),
					("SSSProfileUsed",c_int32,1),
					("EnableStencilPriority",c_int32,1),
					("RequireDualQuaternion",c_int32,1),
					("PixelDepthOffsetUsed",c_int32,1),
					("NoRayTracing",c_int32,1),
		
				]
	
class MDFFlags(ctypes.Union):
	
	_anonymous_ = ("flagValues",)
	_fields_ =	[
					("flagValues",    MDFFlags_bits ),
					("asInt32", c_int32)
				]		
def debugprint(string):
	if DEBUG_MODE:
		print(string)
class MDFHeader():
	def __init__(self):
		self.magic = 4605005
		self.version  = 1
		self.materialCount = 0
		self.reserved = 0
	def read(self,file):
		self.magic = read_uint(file)
		if self.magic != 4605005:
			raiseError("File is not an MDF file.")
		self.version = read_ushort(file)
		self.materialCount = read_ushort(file)
		file.seek(8,1)
		#self.reserved = read_uint64(file)
	def read_fast(self,file):
		file.seek(6,1)
		"""
		self.magic = read_uint(file)
		if self.magic != 4605005:
			raiseError("File is not an MDF file.")
		self.version = read_ushort(file)
		"""
		self.materialCount = read_ushort(file)
		file.seek(8,1)
		#self.reserved = read_uint64(file)
	def write(self,file):
		write_uint(file,self.magic)
		write_ushort(file,self.version)
		write_ushort(file,self.materialCount)
		file.seek(8,1)
		#write_uint64(file,self.reserved)
	def __str__(self):
		return str(self.__class__) + ": " + str(self.__dict__)

class Property():
	def __init__(self):
		self.propNameOffset = 0
		self.unicodeMMH3Hash = 0
		self.asciiMMH3Hash = 0
		self.paramCount = 0
		self.propDataOffset = 0
		self.propName = "MDFProp"
		self.propValue = []
		self.padding = 0#To account for SF6's weird spacing between mmtrs properties
	def read(self,file,matPropertyDataOffset,version):
		self.propNameOffset = read_uint64(file)
		self.unicodeMMH3Hash = read_uint(file)
		self.asciiMMH3Hash = read_uint(file)
		if version >= 13:
			self.propDataOffset = read_int(file)
			self.paramCount = read_int(file)
		else:
			self.paramCount = read_int(file)
			self.propDataOffset = read_int(file)
		currentPos = file.tell()
		file.seek(self.propNameOffset)
		self.propName = read_unicode_string(file)
		file.seek(matPropertyDataOffset+self.propDataOffset)
		for i in range(0,self.paramCount):
			self.propValue.append(read_float(file))
		file.seek(currentPos)
		debugprint(self)
	def write(self,file,version):
		write_uint64(file,self.propNameOffset)
		write_uint(file,self.unicodeMMH3Hash)
		write_uint(file,self.asciiMMH3Hash)
		if version >= 13:
			write_int(file,self.propDataOffset)
			write_int(file,self.paramCount)
		else:
			write_int(file,self.paramCount)
			write_int(file,self.propDataOffset)
	def __str__(self):
		return str(self.__class__) + ": " + str(self.__dict__)

class TextureBinding():
	def __init__(self):
		self.textureTypeOffset = 0
		self.unicodeMMH3Hash = 0
		self.asciiMMH3Hash = 0
		self.texturePathOffset = 0
		self.textureType = ""
		self.texturePath = ""

	def read(self,file,version):
		self.textureTypeOffset = read_uint64(file)
		self.unicodeMMH3Hash = read_uint(file)
		self.asciiMMH3Hash = read_uint(file)
		self.texturePathOffset = read_uint64(file)
		currentPos = file.tell()
		file.seek(self.textureTypeOffset)
		self.textureType = read_unicode_string(file)
		file.seek(self.texturePathOffset)
		self.texturePath = read_unicode_string(file)
		file.seek(currentPos)
		if version >= 13:
			file.seek(8,1)
		debugprint(self)
	def write(self,file,version):
		write_uint64(file,self.textureTypeOffset)
		write_uint(file,self.unicodeMMH3Hash)
		write_uint(file,self.asciiMMH3Hash)
		write_uint64(file,self.texturePathOffset)
		if version >= 13:
			file.seek(8,1)
	def __str__(self):
		return str(self.__class__) + ": " + str(self.__dict__)

class MMTRSData():
	def __init__(self):
		self.offsetList = []
		self.indexDataList = []

	def read(self,file):
		#Amount of offsets always seems to be 8, nothing indicates count
		for i in range(0,8):
			self.offsetList.append(read_uint64(file))
		for offset in self.offsetList:
			file.seek(offset)
			indexCount = read_uint(file)
			indexList = []
			for i in range(0,indexCount):
				indexList.append(read_uint(file))
			self.indexDataList.append(indexList)
		debugprint(self)
	def write(self,file):
		for offset in self.offsetList:
			write_uint64(file, offset)
		for indexList in self.indexDataList:
			write_uint(file,len(indexList))
			for index in indexList:
				write_uint(file,index)
	def __str__(self):
		return str(self.__class__) + ": " + str(self.__dict__)

class GPBFEntry():
	def __init__(self):
		self.nameOffset = 0
		self.nameUTF16Hash = 0
		self.nameUTF8Hash = 0
		self.name = ""

	def read(self,file):
		self.nameOffset = read_uint64(file)
		self.nameUTF16Hash = read_uint(file)
		self.nameUTF8Hash = read_uint(file)
		currentPos = file.tell()
		file.seek(self.nameOffset)
		self.name = read_unicode_string(file)
		file.seek(currentPos)
		debugprint(self)
	def write(self,file):
		write_uint64(file,self.nameOffset)
		write_uint(file,self.nameUTF16Hash)
		write_uint(file,self.nameUTF8Hash)
		
	def __str__(self):
		return str(self.__class__) + ": " + str(self.__dict__)

class Material():
	def __init__(self):
		self.matNameOffset = 0
		self.matNameHash = 0
		self.propBlockSize = 0
		self.propertyCount = 0
		self.textureCount = 0
		self.GPBFBufferNameCount = 0
		self.GPBFBufferPathCount = 0
		self.shaderType = 0
		self.ver32Unkn0 = 0		
		self.flags = MDFFlags()
		self.ver32Unkn1 = 0
		self.ver32Unkn2 = 0
		self.propHeadersOffset = 0
		self.texHeadersOffset = 0
		self.GPUBufferOffset = 0
		self.propDataOffset = 0
		self.mmtrPathOffset = 0
		self.ver32MMTRSDataOffset = 0#Actually version 31 but sf6 support was added retroactively
		self.ver32Unkn4 = 0
		self.materialName = ""
		self.mmtrPath = ""
		self.textureList = []
		self.propertyList = []
		self.mmtrsData = None
		self.gpbfBufferNameList = []
		self.gpbfBufferPathList = []
		
	def getPropertyDict(self):
		return {prop.propName : prop for prop in self.propertyList}
	def read(self,file,version):
		self.matNameOffset = read_uint64(file)
		debugprint("matNameOffset:"+str(self.matNameOffset))
		self.matNameHash = read_uint(file)
		debugprint("matNameHash:"+str(self.matNameHash))
		self.propBlockSize = read_int(file)
		self.propertyCount = read_int(file)
		self.textureCount = read_int(file)
		if version >= 19:
			self.GPBFBufferNameCount = read_int(file)
			self.GPBFBufferPathCount = read_int(file)
		self.shaderType = read_int(file)
		debugprint("shaderType:"+str(self.shaderType))
		if version >= 31:
			self.ver32Unkn0 = read_int(file)
			debugprint("ver32Unkn0:"+str(self.ver32Unkn0))
		self.flags.asInt32 = read_int(file)
			
		debugprint("flags:"+str(self.flags.asInt32))
		if version >= 31:
			self.ver32Unkn1 = read_int(file)
			debugprint("ver32Unkn1:"+str(self.ver32Unkn1))
			self.ver32Unkn2 = read_int(file)
			debugprint("ver32Unkn2:"+str(self.ver32Unkn2))
		self.propHeadersOffset = read_uint64(file)
		self.texHeadersOffset = read_uint64(file)
		if version >= 19:
			self.GPUBufferOffset = read_uint64(file)
		self.propDataOffset = read_uint64(file)
		self.mmtrPathOffset = read_uint64(file)
		if version >= 31:
			self.ver32MMTRSDataOffset = read_int(file)
			self.ver32Unkn4 = read_int(file)
		currentPos = file.tell()
		if self.ver32MMTRSDataOffset != 0:
			file.seek(self.ver32MMTRSDataOffset)
			self.mmtrsData = MMTRSData()
			self.mmtrsData.read(file)
		file.seek(self.matNameOffset)
		self.materialName = read_unicode_string(file)
		file.seek(self.mmtrPathOffset)
		self.mmtrPath = read_unicode_string(file)
		debugprint(self)
		
		if self.GPBFBufferNameCount > 0:
			file.seek(self.GPUBufferOffset)
			self.gpbfBufferNameList.clear()
			self.gpbfBufferPathList.clear()
			for i in range(0,self.GPBFBufferNameCount):
				
				gpbfBufferNameEntry = GPBFEntry()
				gpbfBufferNameEntry.read(file)
				self.gpbfBufferNameList.append(gpbfBufferNameEntry)
				gpbfBufferPathEntry = GPBFEntry()
				gpbfBufferPathEntry.read(file)
				self.gpbfBufferPathList.append(gpbfBufferPathEntry)
		
		file.seek(self.texHeadersOffset)
		self.textureList = []
		for i in range(0,self.textureCount):
			textureEntry = TextureBinding()
			textureEntry.read(file,version)
			debugprint(textureEntry)
			self.textureList.append(textureEntry)
		file.seek(self.propHeadersOffset)
		self.propertyList = []
		#Get padding size of properties for SF6
		lastPropEndPos = 0
		for i in range(0,self.propertyCount):
			
			propertyEntry = Property()
			propertyEntry.read(file,self.propDataOffset,version)
			propertyEntry.padding = propertyEntry.propDataOffset - lastPropEndPos
			#print(f"{propertyEntry.propName} - {propertyEntry.padding}")
			lastPropEndPos = propertyEntry.propDataOffset + 4*(propertyEntry.paramCount)
			
			debugprint(propertyEntry)
			self.propertyList.append(propertyEntry)
		file.seek(currentPos)
		debugprint(self)
	def read_fast(self,file,version):
		self.matNameOffset = read_uint64(file)
		file.seek(12,1)
		#self.matNameHash = read_uint(file)
		#self.propBlockSize = read_int(file)
		#self.propertyCount = read_int(file)
		self.textureCount = read_int(file)
		file.seek(24,1)
		if version >= 31:
			file.seek(12,1)
		#self.flags.read(file)
		#self.shaderType = read_int(file)
		#self.propHeadersOffset = read_uint64(file)
		self.texHeadersOffset = read_uint64(file)
		#self.GPUBufferOffset = read_uint64(file)
		#self.propDataOffset = read_uint64(file)
		#self.mmtrPathOffset = read_uint64(file)
		currentPos = file.tell()+24
		if version >= 31:
			currentPos += 8
		file.seek(self.matNameOffset)
		self.materialName = read_unicode_string(file)
		#file.seek(self.mmtrPathOffset)
		#self.mmtrPath = read_unicode_string(file)
		#debugprint(self)
		file.seek(self.texHeadersOffset)
		self.textureList = []
		for i in range(0,self.textureCount):
			textureEntry = TextureBinding()
			textureEntry.read(file)
			debugprint(textureEntry)
			self.textureList.append(textureEntry)
		"""
		file.seek(self.propHeadersOffset)
		self.propertyList = []
		for i in range(0,self.propertyCount):
			propertyEntry = Property()
			propertyEntry.read(file)
			debugprint(propertyEntry)
			self.propertyList.append(propertyEntry)
		"""
		file.seek(currentPos)
	def write(self,file,version):
		write_uint64(file, self.matNameOffset)
		write_uint(file, self.matNameHash)
		write_int(file, self.propBlockSize)
		write_int(file, self.propertyCount)
		write_int(file, self.textureCount)
		if version >= 19:
			write_int(file,self.GPBFBufferNameCount)
			write_int(file,self.GPBFBufferPathCount)
		write_int(file, self.shaderType)
		if version >= 31:
			write_int(file, self.ver32Unkn0)
		
		write_int(file,self.flags.asInt32)
		if version >= 31:
			write_int(file, self.ver32Unkn1)
			write_int(file, self.ver32Unkn2)
		write_uint64(file, self.propHeadersOffset)
		write_uint64(file, self.texHeadersOffset)
		if version >= 19:
			write_uint64(file, self.GPUBufferOffset)
		write_uint64(file, self.propDataOffset)
		write_uint64(file, self.mmtrPathOffset)
		if version >= 31:
			write_int(file, self.ver32MMTRSDataOffset)#Write mmtrs data later
			write_int(file, self.ver32Unkn4)
	def __str__(self):
		return str(self.__class__) + ": " + str(self.__dict__)
		
class MDFFile():
	def __init__(self):
		self.fileVersion = 0#Internal
		self.sizeData = None
		self.Header = MDFHeader()
		self.materialList = []
		self.stringList = []#Used during writing
	def read(self,file,version):
		self.Header.read(file)
		debugprint(self.Header)
		for i in range(0,self.Header.materialCount):
			materialEntry = Material()
			materialEntry.read(file,version)
			debugprint(materialEntry)
			self.materialList.append(materialEntry)
		
	def read_fast(self,file,version):
		self.Header.read_fast(file)
		debugprint(self.Header)
		for i in range(0,self.Header.materialCount):
			materialEntry = Material()
			materialEntry.read_fast(file,version)
			debugprint(materialEntry)
			self.materialList.append(materialEntry)
	
	def getMaterialDict(self):
		return {material.materialName: material for material in self.materialList}
	
	def recalculateHashesAndOffsets(self,version):
		self.Header.materialCount = len(self.materialList)
		self.sizeData = SIZEDATA(version)
		materialEntriesSize = self.sizeData.MATERIAL_ENTRY_SIZE * len(self.materialList)
		textureEntriesSize = 0
		propertyEntriesSize = 0
		gpbfEntriesSize = 0
		
		propDataBlockOffsetList = []
		propHeaderOffsetList = []
		texHeaderOffsetList = []
		gpbfOffsetList = []
		currentPropDataBlockOffset = 0
		currentPropHeaderOffset = 0
		currentTexHeaderOffset = 0
		currentMMTRSOffset = 0
		
		for material in self.materialList:
			textureEntriesSize += len(material.textureList) * self.sizeData.TEXTURE_ENTRY_SIZE
			propertyEntriesSize += len(material.propertyList) * self.sizeData.PROPERTY_ENTRY_SIZE
			gpbfEntriesSize += len(material.gpbfBufferNameList) * 2 * self.sizeData.GPBF_ENTRY_SIZE
			material.matNameHash = hash_wide(material.materialName)
			material.propBlockSize = 0
			material.textureCount = len(material.textureList)
			material.propertyCount = len(material.propertyList)
			currentPropOffset = 0
			
			propHeaderOffsetList.append(currentPropHeaderOffset)
			currentPropHeaderOffset += material.propertyCount * self.sizeData.PROPERTY_ENTRY_SIZE
			
			texHeaderOffsetList.append(currentTexHeaderOffset)
			currentTexHeaderOffset += material.textureCount * self.sizeData.TEXTURE_ENTRY_SIZE
			for prop in material.propertyList:
				currentPropSize = len(list(prop.propValue))*self.sizeData.PROPERTY_VALUE_SIZE
				prop.propDataOffset = currentPropOffset + prop.padding
				currentPropOffset += currentPropSize + prop.padding
				prop.paramCount = len(list(prop.propValue))
				prop.asciiMMH3Hash = hash(prop.propName)
				prop.unicodeMMH3Hash = hash_wide(prop.propName)
			material.propBlockSize = currentPropOffset + getPaddingAmount(currentPropOffset, 16)
			propDataBlockOffsetList.append(currentPropDataBlockOffset)
			currentPropDataBlockOffset += material.propBlockSize
			for texture in material.textureList:
				texture.asciiMMH3Hash = hash(texture.textureType)
				texture.unicodeMMH3Hash = hash_wide(texture.textureType)
		
		materialEntryStartOffset = self.sizeData.HEADER_SIZE
		textureEntryStartOffset = materialEntryStartOffset + materialEntriesSize
		propertyEntryStartOffset = textureEntryStartOffset + textureEntriesSize
		
		currentGPBFOffset = propertyEntryStartOffset + propertyEntriesSize
		stringTableStartOffset = propertyEntryStartOffset + propertyEntriesSize + gpbfEntriesSize
		
		#Get string offsets
		currentStringOffset = stringTableStartOffset
		#Get all material names and mmtr paths first
		for material in self.materialList:
			material.matNameOffset = currentStringOffset
			self.stringList.append(material.materialName)
			currentStringOffset += len(material.materialName)*2+2
			
			material.mmtrPathOffset = currentStringOffset
			self.stringList.append(material.mmtrPath)
			currentStringOffset += len(material.mmtrPath)*2+2
		#Get texture types and paths next
		textureOffsetDict = {}#Property names have to share offsets or the game will crash
		
		for material in self.materialList:
			for texture in material.textureList:
				if textureOffsetDict.get(texture.textureType,None) != None:
					texture.textureTypeOffset = textureOffsetDict[texture.textureType]
				else:
					textureOffsetDict[texture.textureType] = currentStringOffset
					texture.textureTypeOffset = currentStringOffset
					self.stringList.append(texture.textureType)
					currentStringOffset += len(texture.textureType)*2+2
				
				if textureOffsetDict.get(texture.texturePath,None) != None:
					texture.texturePathOffset = textureOffsetDict[texture.texturePath]
				else:
					textureOffsetDict[texture.texturePath] = currentStringOffset
					texture.texturePathOffset = currentStringOffset
					self.stringList.append(texture.texturePath)
					currentStringOffset += len(texture.texturePath)*2+2
		#Lastly get property names
		propNameOffsetDict = {}#Property names have to share offsets or the game will crash
		for material in self.materialList:
			for prop in material.propertyList:
				if propNameOffsetDict.get(prop.propName,None) != None:
					prop.propNameOffset = propNameOffsetDict[prop.propName]
				else:
					prop.propNameOffset = currentStringOffset
					propNameOffsetDict[prop.propName] = currentStringOffset
					self.stringList.append(prop.propName)
					currentStringOffset += len(prop.propName)*2+2
		if gpbfEntriesSize != 0:
			gpbfNameOffsetDict = {}
			for material in self.materialList:
				material.GPBFBufferNameCount = len(material.gpbfBufferNameList)
				material.GPBFBufferPathCount = material.GPBFBufferNameCount
				material.GPUBufferOffset = currentGPBFOffset
				currentGPBFOffset += ((material.GPBFBufferNameCount*2) * self.sizeData.GPBF_ENTRY_SIZE)
				for entry in material.gpbfBufferNameList:
					entry.nameUTF16Hash = hash_wide(entry.name)
					entry.nameUTF8Hash = hash(entry.name)
					if gpbfNameOffsetDict.get(entry.name,None) != None:
						entry.nameOffset = gpbfNameOffsetDict[entry.name]
					else:
						entry.nameOffset = currentStringOffset
						gpbfNameOffsetDict[entry.name] = currentStringOffset
						self.stringList.append(entry.name)
						currentStringOffset += len(entry.name)*2+2
				for entry in material.gpbfBufferPathList:
					if gpbfNameOffsetDict.get(entry.name,None) != None:
						entry.nameOffset = gpbfNameOffsetDict[entry.name]
					else:
						entry.nameOffset = currentStringOffset
						gpbfNameOffsetDict[entry.name] = currentStringOffset
						self.stringList.append(entry.name)
						currentStringOffset += len(entry.name)*2+2
		#stringTableSize = list(stringOffsetDict.items())[-1][1] + len(list(stringOffsetDict.items())[-1][0])*2 +2
		#stringTableSize = stringTableSize + getPaddingAmount(stringTableStartOffset+stringTableSize, 16)
		
		
		propDataStartOffset = currentStringOffset + getPaddingAmount(currentStringOffset, 16)

		#Loop through materials again now that the offsets have been gathered
		for index, material in enumerate(self.materialList):
			#print(propDataBlockOffsetList[index])
			material.propHeadersOffset = propertyEntryStartOffset + propHeaderOffsetList[index]
			material.texHeadersOffset = textureEntryStartOffset + texHeaderOffsetList[index]
			if material.GPUBufferOffset == 0:
				material.GPUBufferOffset = currentGPBFOffset
			material.propDataOffset = propDataStartOffset + propDataBlockOffsetList[index]
			
		currentMMTRSOffset = currentPropDataBlockOffset + propDataStartOffset
		for material in self.materialList:
			if material.mmtrsData != None:
				material.ver32MMTRSDataOffset = currentMMTRSOffset
				currentMMTRIndexListOffset =  currentMMTRSOffset + 8 * 8
				material.mmtrsData.offsetList.clear()
				for i in range(0,8):
					material.mmtrsData.offsetList.append(currentMMTRIndexListOffset)
					currentMMTRIndexListOffset +=  4 + 4 * len(material.mmtrsData.indexDataList[i])
				currentMMTRSOffset = currentMMTRIndexListOffset
	def write(self,file,version):
		
		
		self.recalculateHashesAndOffsets(version)
		self.Header.write(file)
		#It would be more faster and more efficient to write everything to buffers instead of looping again for each entry type but this is fast enough so ¯\_(ツ)_/¯
		#Loop to write material entries
		print("Writing Material Entries")
		for material in self.materialList:
			#print(material)
			material.write(file,version)
		#Loop to write texture entries
		print("Writing Texture Headers")
		for material in self.materialList:
			file.seek(material.texHeadersOffset)
			for texture in material.textureList:
				texture.write(file,version)
		#Loop to write property headers
		print("Writing Property Headers")
		for material in self.materialList:
			file.seek(material.propHeadersOffset)
			for prop in material.propertyList:
				prop.write(file,version)
		#Loop to write GPBF
		for material in self.materialList:
			file.seek(material.GPUBufferOffset)
			for i in range(0,material.GPBFBufferNameCount):
				material.gpbfBufferNameList[i].write(file)
				material.gpbfBufferPathList[i].write(file)
		#Write string table
		print("Writing Strings")
		"""
		for string in sorted(list(stringOffsetDict.items()),key = lambda item: item[1]):
			write_unicode_string(file, string[0])
		"""
		for string in self.stringList:
			write_unicode_string(file, string)
		#Clear string list after writing
		self.stringList = []
		#Loop over materials one last time to write property values
		
		print("Writing Property Values")
		for material in self.materialList:
			for prop in material.propertyList:
				file.seek(material.propDataOffset + prop.propDataOffset)
				for value in list(prop.propValue):
					write_float(file,value)
					
		
		for material in self.materialList:
			if material.mmtrsData != None:
				file.seek(material.ver32MMTRSDataOffset)
				#print(material.mmtrsData)
				material.mmtrsData.write(file)
def readMDF(filepath):
	#print(textColors.OKCYAN + "__________________________________\nMDF read started." + textColors.ENDC)
	print("Opening " + filepath)
	try:  
		file = open(filepath,"rb")
	except:
		raiseError("Failed to open " + filepath)
	#try:
	version = int(os.path.splitext(filepath)[1].replace(".",""))
	#except:
		#raiseWarning("No number extension found on mdf file, defaulting to version 23")
		#version = 23
	mdfFile = MDFFile()
	mdfFile.fileVersion = version
	mdfFile.read(file,version)
	file.close()
	#print(textColors.OKGREEN + "__________________________________\nMDF read finished." + textColors.ENDC)
	return mdfFile
def readMDFFast(filepath):
	#print(textColors.OKCYAN + "__________________________________\nMDF read started." + textColors.ENDC)
	print("Opening " + filepath)
	try:  
		file = open(filepath,"rb")
	except:
		raiseError("Failed to open " + filepath)
	try:
		version = int(os.path.splitext(filepath)[1].replace(".",""))
	except:
		raiseWarning("No number extension found on mdf file, defaulting to version 23")
		version = 23
	mdfFile = MDFFile()
	debugprint("File Version "+str(version))
	mdfFile.read_fast(file,version)
	file.close()
	#print(textColors.OKGREEN + "__________________________________\nMDF read finished." + textColors.ENDC)
	return mdfFile
def writeMDF(mdfFile,filepath):
	#print(textColors.OKCYAN + "__________________________________\nMDF write started." + textColors.ENDC)
	print("Opening " + filepath)
	try:
		file = open(filepath,"wb")
	except:
		raiseError("Failed to open " + filepath)
	try:
		version = int(os.path.splitext(filepath)[1].replace(".",""))
	except:
		raiseWarning("No number extension found on mdf file, defaulting to version 23")
		version = 23
	mdfFile.write(file,version)
	file.close()
	#print(textColors.OKGREEN + "__________________________________\nMDF write finished." + textColors.ENDC)
