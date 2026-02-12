#Author: NSA Cloud
import os

from ..gen_functions import textColors,raiseWarning,raiseError,getPaddingAmount,read_uint,read_int,read_uint64,read_float,read_short,read_ushort,read_ubyte,read_unicode_string,read_byte,write_uint,write_int,write_uint64,write_float,write_short,write_ushort,write_ubyte,write_unicode_string,write_byte

class SIZEDATA():
	def __init__(self,version):
		self.SFUR_ENTRY_SIZE = 72
		if version < 5:
			self.SFUR_ENTRY_SIZE = 80
		

class SFurHeader():
	def __init__(self):
		self.magic = 1381320275#sfur
		self.version = 5
		self.matCount = 0
		self.unkn = 0
		self.tblOffset = 0
		self.offsetList = []
	def read(self,file):
		self.magic = read_uint(file)
		if self.magic != 1381320275:
			raiseError("File is not an SFur file.")
		self.version = read_uint(file)
		self.matCount = read_uint(file)
		self.unkn = read_uint(file)
		self.tblOffset = read_uint64(file)
		self.offsetList.clear()
		for i in range(0,self.matCount):
			self.offsetList.append(read_uint64(file))
	def write(self,file):
		write_uint(file,self.magic)
		write_uint(file,self.version)
		write_uint(file,self.matCount)
		write_uint(file,self.unkn)
		write_uint64(file,self.tblOffset)
		for entry in self.offsetList:
			write_uint64(file,entry)
	def __str__(self):
		return str(self.__class__) + ": " + str(self.__dict__)

class SFurEntry():
	def __init__(self):
		self.shellCount = 0
		self.shellThinType = 0
		self.groomingTexCoordType = 0
		self.shellHeight = 0.0
		self.bendRate = 0.0
		self.bendRootRate = 0.0
		self.normalTransformRate = 0.0
		self.stiffness = 0.0
		self.stiffnessDistribution = 0.0
		self.springCoefficient = 0.0
		self.damping = 0.0
		self.gravityForceScale = 0.0
		self.directWindForceScale = 0.0
		self.isForceTwoSide = False
		self.isForceAlphaTest = False
		self.padding = 0
		self.unknOffset = 0#Version 4 only?
		self.materialNameOffset = 0
		self.materialName = "MATERIAL_NAME"
		self.groomingTexturePathOffset = 0
		self.groomingTexturePath = ""
		
		
	def read(self,file,version):
		self.shellCount = read_uint(file)
		self.shellThinType = read_uint(file)
		self.groomingTexCoordType = read_uint(file)
		self.shellHeight = read_float(file)
		self.bendRate = read_float(file)
		self.bendRootRate = read_float(file)
		self.normalTransformRate = read_float(file)
		self.stiffness = read_float(file)
		self.stiffnessDistribution = read_float(file)
		self.springCoefficient = read_float(file)
		self.damping = read_float(file)
		self.gravityForceScale = read_float(file)
		self.directWindForceScale = read_float(file)
		self.isForceTwoSide = bool(read_ubyte(file))
		self.isForceAlphaTest = bool(read_ubyte(file))
		self.padding = read_ushort(file)
		if version < 5:#WILDS
			self.unknOffset = read_uint64(file)
		self.materialNameOffset = read_uint64(file)
		self.groomingTexturePathOffset = read_uint64(file)
		currentPos = file.tell()
		file.seek(self.materialNameOffset)
		self.materialName = read_unicode_string(file)
		file.seek(self.groomingTexturePathOffset)
		self.groomingTexturePath = read_unicode_string(file)
		file.seek(currentPos)
	def write(self,file,version):
		write_uint(file, self.shellCount)
		write_uint(file, self.shellThinType)
		write_uint(file, self.groomingTexCoordType)
		write_float(file, self.shellHeight)
		write_float(file, self.bendRate)
		write_float(file, self.bendRootRate)
		write_float(file, self.normalTransformRate)
		write_float(file, self.stiffness)
		write_float(file, self.stiffnessDistribution)
		write_float(file, self.springCoefficient)
		write_float(file, self.damping)
		write_float(file, self.gravityForceScale)
		write_float(file, self.directWindForceScale)
		write_ubyte(file, int(self.isForceTwoSide))
		write_ubyte(file, int(self.isForceAlphaTest))
		write_ushort(file, self.padding)
		if version < 5:#WILDS
			write_uint64(file, self.unknOffset)
		write_uint64(file, self.materialNameOffset)
		write_uint64(file, self.groomingTexturePathOffset)
		
	def __str__(self):
		return str(self.__class__) + ": " + str(self.__dict__)


class SFurFile():
	def __init__(self):
		
		self.header = SFurHeader()
		self.furEntryList = []
		self.stringList = []#Used during writing
	def read(self,file):
		self.header.read(file)
		for entryOffset in self.header.offsetList:
			file.seek(entryOffset)
			entry = SFurEntry()
			entry.read(file,self.header.version)
			self.furEntryList.append(entry)
		
	def gatherStrings(self):
		stringOffsetDict = {}
		currentStringOffset = 0
		for entry in self.furEntryList: 
			if stringOffsetDict.get(entry.materialName,None) == None:
				stringOffsetDict[entry.materialName] = currentStringOffset
				currentStringOffset += len(entry.materialName)*2+2
			if stringOffsetDict.get(entry.groomingTexturePath,None) == None:
				stringOffsetDict[entry.groomingTexturePath] = currentStringOffset
				currentStringOffset += len(entry.groomingTexturePath)*2+2
		return stringOffsetDict
	def recalculateHashesAndOffsets(self,stringOffsetDict):
		
		self.header.matCount = len(self.furEntryList)
		
		self.header.tblOffset = 24
		
		furEntrySize = self.sizeData.SFUR_ENTRY_SIZE * len(self.furEntryList)
		
		currentEntryOffset = self.header.tblOffset + (self.header.matCount * 8)
		stringTableOffset = currentEntryOffset + furEntrySize
		self.header.offsetList.clear()
		for entry in self.furEntryList:
			entry.materialNameOffset = stringOffsetDict[entry.materialName] + stringTableOffset
			entry.groomingTexturePathOffset = stringOffsetDict[entry.groomingTexturePath] + stringTableOffset
			self.header.offsetList.append(currentEntryOffset)
			currentEntryOffset += self.sizeData.SFUR_ENTRY_SIZE
			
		for string in stringOffsetDict.keys():
			self.stringList.append(string)
	def write(self,file,version):
		self.header.version = version
		self.sizeData = SIZEDATA(version)
		stringOffsetDict = self.gatherStrings()
		self.recalculateHashesAndOffsets(stringOffsetDict)
		self.header.write(file)
		
		print("Writing Fur Entries")
			
		for index,offset in enumerate(self.header.offsetList):
			file.seek(offset)
			furEntry = self.furEntryList[index]
			furEntry.write(file,self.header.version)
		print("Writing Strings")
		for string in self.stringList:
			write_unicode_string(file, string)
def readSFur(filepath):
	print(textColors.OKCYAN + "__________________________________\nSFur read started." + textColors.ENDC)
	print("Opening " + filepath)
	try:  
		file = open(filepath,"rb")
	except:
		raiseError("Failed to open " + filepath)
	sFurFile = SFurFile()
	sFurFile.read(file)
	file.close()
	print(textColors.OKGREEN + "__________________________________\nSFur read finished." + textColors.ENDC)
	return sFurFile
def writeSFur(sFurFile,filepath):
	print(textColors.OKCYAN + "__________________________________\nSFur write started." + textColors.ENDC)
	print("Opening " + filepath)
	try:
		file = open(filepath,"wb")
	except:
		raiseError("Failed to open " + filepath)
	try:
		version = int(os.path.splitext(filepath)[1].replace(".",""))
	except:
		raiseWarning("No number extension found on SFur file, defaulting to version 5")
		version = 5
	sFurFile.write(file,version)
	file.close()
	print(textColors.OKGREEN + "__________________________________\nSFur write finished." + textColors.ENDC)
