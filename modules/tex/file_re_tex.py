#Author: NSA Cloud
import os

from ..gen_functions import textColors,raiseWarning,raiseError,getPaddingAmount,read_uint,read_int,read_uint64,read_float,read_short,read_ushort,read_ubyte,read_unicode_string,read_byte,write_uint,write_int,write_uint64,write_float,write_short,write_ushort,write_ubyte,write_unicode_string,write_byte

#TODO Add support for multi image textures like RE4R's terrain textures

gameNameToTexVersionDict = {
	"DMC5":11,
	"MHR":28,
	"MHRSB":28,
	"RE8":30,
	"RE2RT":34,
	"RE3RT":34,
	"RE4":143221013,
	"SF6":143230113,
	"DD2":760230703,
	}

def getTexVersionFromGameName(gameName):
	return gameNameToTexVersionDict.get(gameName,-1)
class TexHeader():
	def __init__(self):
		self.magic = 5784916
		self.version  = 0
		self.width = 0
		self.height = 0
		self.depth = 0
		self.imageCount = 0
		self.imageMipHeaderSize = 0
		self.mipCount = 0#Internal,calcluated from mip header size
		self.format = 0
		self.swizzleControl = -1
		self.cubemapMarker = 0
		self.unkn04 = 0
		self.unkn05 = 0
		self.null0 = 0
		#swizzle data,unused
		self.swizzleHeightDepth = 0
		self.swizzleWidth = 0
		self.null1 = 0
		self.seven = 0
		self.one = 0
		
		
	def read(self,file):
		self.magic = read_uint(file)
		if self.magic != 5784916:
			raiseError("File is not a tex file.")
		self.version = read_uint(file)
		self.width = read_ushort(file)
		self.height = read_ushort(file)
		self.depth = read_ushort(file)
		self.imageCount = read_ubyte(file)
		self.imageMipHeaderSize = read_ubyte(file)
		self.mipCount = self.imageMipHeaderSize // 16
		self.format = read_uint(file)
		self.swizzleControl = read_int(file)
		self.cubemapMarker = read_uint(file)
		self.unkn04 = read_ubyte(file)
		self.unkn05 = read_ubyte(file)
		self.null0 = read_ushort(file)
		if self.version > 27:
			#swizzle data,unused
			self.swizzleHeightDepth = read_ubyte(file)
			self.swizzleWidth = read_ubyte(file)
			self.null1 = read_ushort(file)
			self.seven = read_ushort(file)
			self.one = read_ushort(file)
			
		#self.reserved = read_uint64(file)
	
	def write(self,file):
		write_uint(file, self.magic)
		write_uint(file, self.version)
		write_ushort(file, self.width)
		write_ushort(file, self.height)
		write_ushort(file, self.depth)
		write_ubyte(file, self.imageCount)
		write_ubyte(file, self.imageMipHeaderSize)
		write_uint(file, self.format)
		write_int(file, self.swizzleControl)
		write_uint(file, self.cubemapMarker)
		write_ubyte(file, self.unkn04)
		write_ubyte(file, self.unkn05)
		write_ushort(file, self.null0)
		write_ubyte(file, self.swizzleHeightDepth)
		write_ubyte(file, self.swizzleWidth)
		write_ushort(file, self.null1)
		write_ushort(file, self.seven)
		write_ushort(file, self.one)


class MipData():
	def __init__(self):
		self.mipOffset = 0
		self.compressedSize  = 0
		self.uncompressedSize = 0
		self.textureData = bytes()
	def read(self,file):

		self.mipOffset = read_uint64(file)
		self.compressedSize = read_uint(file)
		self.uncompressedSize = read_uint(file)
		currentPos = file.tell()
		file.seek(self.mipOffset)
		self.textureData = file.read(self.uncompressedSize)
		file.seek(currentPos)
		
	def write(self,file):
		write_uint64(file, self.mipOffset)
		write_uint(file, self.compressedSize)
		write_uint(file, self.uncompressedSize)

class Tex():
	def __init__(self):
		self.header = TexHeader()
		self.imageMipDataList = []
	def read(self,file):

		self.header.read(file)
		self.imageMipDataList = []
		for i in range(self.header.imageCount):
			imageMipDataListEntry = []
			for j in range(self.header.mipCount):
				mipEntry = MipData()
				mipEntry.read(file)
				imageMipDataListEntry.append(mipEntry)
			self.imageMipDataList.append(imageMipDataListEntry)
	def write(self,file):
		self.header.write(file)
		#Write mip offsets and sizes
		for mipEntryList in self.imageMipDataList:
			for mipEntry in mipEntryList:
				mipEntry.write(file)
		
		#Write mip data
		for mipEntryList in self.imageMipDataList:
			for mipEntry in mipEntryList:
				file.write(mipEntry.textureData)
	def GetTextureData(self):
		byteArray = bytearray()
		for image in self.imageMipDataList:
			for mipData in image:
				byteArray.extend(mipData.textureData)
				
		return bytes(byteArray)

class RE_TexFile:
	def __init__(self):
		self.tex = Tex()
	def read(self,filePath):
		#print("Opening " + filePath)
		try:  
			file = open(filePath,"rb")
		except:
			raiseError("Failed to open " + filePath)
		self.tex.read(file)
		file.close()
			
	def write(self,filePath):
		print("Writing " + filePath)
		try:  
			file = open(filePath,"wb")
		except:
			raiseError("Failed to open " + filePath)
		self.tex.write(file)
		file.close()