#Author: NSA Cloud
import os

from ..gen_functions import textColors,raiseWarning,raiseError,getPaddingAmount,read_uint,read_int,read_uint64,read_float,read_short,read_ushort,read_ubyte,read_unicode_string,read_byte,write_uint,write_int,write_uint64,write_float,write_short,write_ushort,write_ubyte,write_unicode_string,write_byte
from ..hashing.pymmh3 import hash_wide

DEBUG_MODE = False
class SIZEDATA():
	def __init__(self):
		self.HEADER_SIZE = 48
		self.BONE_ENTRY_SIZE = 64
		self.HASH_ENTRY_SIZE = 8
		self.PROPERTY_ENTRY_SIZE = 24
		self.PROPERTY_VALUE_SIZE = 4
		
def debugprint(string):
	if DEBUG_MODE:
		print(string)
class FBXSkelHeader():
	def __init__(self):
		self.version = 5
		self.magic = 1852599155#skln
		self.boneOffset = 48
		self.hashOffset = 0
		self.boneCount = 0
	def read(self,file):
		self.version = read_uint(file)
		self.magic = read_uint(file)
		if self.magic != 1852599155:
			raiseError("File is not an FBXSkel file.")
		file.seek(8,1)
		self.boneOffset = read_uint(file)
		file.seek(4,1)
		self.hashOffset = read_uint(file)
		file.seek(4,1)
		self.boneCount = read_uint(file)
		#self.reserved = read_uint64(file)
	def write(self,file):
		write_uint(file,self.version)
		write_uint(file,self.magic)
		file.seek(8,1)
		write_uint(file,self.boneOffset)
		file.seek(4,1)
		write_uint(file,self.hashOffset)
		file.seek(4,1)
		write_uint(file,self.boneCount)
		#write_uint64(file,self.reserved)
	def __str__(self):
		return str(self.__class__) + ": " + str(self.__dict__)

class BoneEntry():
	def __init__(self):
		self.boneNameOffset = 0
		self.boneName = "BONE_NAME"
		self.boneMMH3Hash = 0
		self.parentIndex = 0
		self.boneIndex = 0
		self.translation = (0.0,0.0,0.0)
		self.rotation = (0.0,0.0,0.0,1.0)
		self.scale = (1.0,1.0,1.0)
		self.segmentScaling = 0
	def read(self,file,version):
		self.boneNameOffset = read_uint64(file)
		debugprint(self.boneNameOffset)
		currentPos = file.tell()
		file.seek(self.boneNameOffset)
		self.boneName = read_unicode_string(file)
		file.seek(currentPos)
		self.boneMMH3Hash = read_uint(file)
		self.parentIndex = read_short(file)
		self.boneIndex = read_short(file)
		if version >= 5:
			self.rotation = (read_float(file),read_float(file),read_float(file),read_float(file))
			self.translation  = (read_float(file),read_float(file),read_float(file))
			self.scale = (read_float(file),read_float(file),read_float(file))
			self.segmentScaling = read_uint(file)
			file.seek(4,1)
		else:
			self.translation  = (read_float(file),read_float(file),read_float(file))
			file.seek(4,1)
			self.rotation = (read_float(file),read_float(file),read_float(file),read_float(file))
			self.scale = (read_float(file),read_float(file),read_float(file))
			file.seek(4,1)
		
	def write(self,file,version):
		write_uint64(file,self.boneNameOffset)
		write_uint(file,self.boneMMH3Hash)
		write_short(file,self.parentIndex)
		write_short(file,self.boneIndex)
		if version >= 5:
			write_float(file,self.rotation[0])
			write_float(file,self.rotation[1])
			write_float(file,self.rotation[2])
			write_float(file,self.rotation[3])
			write_float(file,self.translation[0])
			write_float(file,self.translation[1])
			write_float(file,self.translation[2])
			write_float(file,self.scale[0])
			write_float(file,self.scale[1])
			write_float(file,self.scale[2])
			write_uint(file,self.segmentScaling)
			file.seek(4,1)
		else:
			write_float(file,self.translation[0])
			write_float(file,self.translation[1])
			write_float(file,self.translation[2])
			file.seek(4,1)
			write_float(file,self.rotation[0])
			write_float(file,self.rotation[1])
			write_float(file,self.rotation[2])
			write_float(file,self.rotation[3])
			write_float(file,self.scale[0])
			write_float(file,self.scale[1])
			write_float(file,self.scale[2])
			file.seek(4,1)
		
	def __str__(self):
		return str(self.__class__) + ": " + str(self.__dict__)

class HashEntry():
	def __init__(self):
		self.mmh3Hash = 0
		self.boneIndex = 0
	def read(self,file):
		self.mmh3Hash = read_uint(file)
		self.boneIndex = read_uint(file)
	def write(self,file):
		write_uint(file,self.mmh3Hash)
		write_uint(file,self.boneIndex)
		
	def __str__(self):
		return str(self.__class__) + ": " + str(self.__dict__)

class FBXSkelFile():
	def __init__(self):
		self.sizeData = SIZEDATA()
		self.header = FBXSkelHeader()
		self.boneEntryList = []
		self.boneHashList = []#Sorted by hash value
		self.stringList = []#Used during writing
	def read(self,file):
		self.header.read(file)
		debugprint(self.header)
		file.seek(self.header.boneOffset)
		for i in range(0,self.header.boneCount):
			entry = BoneEntry()
			entry.read(file,self.header.version)
			debugprint(entry)
			self.boneEntryList.append(entry)
		file.seek(self.header.hashOffset)
		for i in range(0,self.header.boneCount):
			entry = HashEntry()
			entry.read(file)
			self.boneHashList.append(entry)
		
	def gatherStrings(self):
		stringOffsetDict = {}
		currentStringOffset = 0
		for bone in self.boneEntryList: 
			if stringOffsetDict.get(bone.boneName,None) == None:
				stringOffsetDict[bone.boneName] = currentStringOffset
				currentStringOffset += len(bone.boneName)*2+2
		return stringOffsetDict
	def recalculateHashesAndOffsets(self,stringOffsetDict):
		self.header.boneCount = len(self.boneEntryList)
		
		boneEntriesSize = self.sizeData.BONE_ENTRY_SIZE * len(self.boneEntryList)
		self.header.hashOffset = self.sizeData.HEADER_SIZE + boneEntriesSize
		
		stringTableOffset = self.header.hashOffset + (self.header.boneCount * self.sizeData.HASH_ENTRY_SIZE)
		for bone in self.boneEntryList:
			bone.boneMMH3Hash = hash_wide(bone.boneName)
			bone.boneNameOffset = stringOffsetDict[bone.boneName] + stringTableOffset
		self.boneHashList = []
		for index,boneEntry in enumerate(self.boneEntryList):
			hashEntry = HashEntry()
			hashEntry.mmh3Hash = boneEntry.boneMMH3Hash
			hashEntry.boneIndex = index
			self.boneHashList.append(hashEntry)
		self.boneHashList.sort(key=lambda x: x.mmh3Hash)
		
	def write(self,file,version):
		self.header.version = version
		stringOffsetDict = self.gatherStrings()
		self.recalculateHashesAndOffsets(stringOffsetDict)
		self.header.write(file)
		file.seek(self.header.boneOffset)
		print("Writing Bone Entries")
		for boneEntry in self.boneEntryList:
			debugprint(boneEntry)
			boneEntry.write(file,self.header.version)
		#Loop to write texture entries
		print("Writing Bone Hashes")
		for hashEntry in self.boneHashList:
			hashEntry.write(file)
		#Loop to write property headers
		print("Writing Bone Strings")
		for boneEntry in self.boneEntryList:
			write_unicode_string(file, boneEntry.boneName)
def readFBXSkel(filepath):
	print(textColors.OKCYAN + "__________________________________\nFBXSkel read started." + textColors.ENDC)
	print("Opening " + filepath)
	try:  
		file = open(filepath,"rb")
	except:
		raiseError("Failed to open " + filepath)
	fbxSkelFile = FBXSkelFile()
	fbxSkelFile.read(file)
	file.close()
	print(textColors.OKGREEN + "__________________________________\nFBXSkel read finished." + textColors.ENDC)
	return fbxSkelFile
def writeFBXSkel(fbxSkelFile,filepath):
	print(textColors.OKCYAN + "__________________________________\nFBXSkel write started." + textColors.ENDC)
	print("Opening " + filepath)
	try:
		file = open(filepath,"wb")
	except:
		raiseError("Failed to open " + filepath)
	try:
		version = int(os.path.splitext(filepath)[1].replace(".",""))
	except:
		raiseWarning("No number extension found on FBXSkel file, defaulting to version 5")
		version = 5
	fbxSkelFile.write(file,version)
	file.close()
	print(textColors.OKGREEN + "__________________________________\nFBXSkel write finished." + textColors.ENDC)
