#Author: NSA Cloud
import os
from io import BytesIO

from ..gen_functions import textColors,raiseWarning,raiseError,getPaddingAmount,read_uint,read_int,read_uint64,read_float,read_short,read_ushort,read_ubyte,read_unicode_string,read_byte,write_uint,write_int,write_uint64,write_float,write_short,write_ushort,write_ubyte,write_unicode_string,write_byte
from ..gdeflate.gdeflate import GDeflate



VERSION_MHWILDS = 240701001#mhwilds tex version

gameNameToTexVersionDict = {
	"DMC5":11,
	"RE2":10,
	"RE3":190820018,
	"MHR":28,
	"MHRSB":28,
	"RE8":30,
	"RE2RT":34,
	"RE3RT":34,
	"RE7RT":35,
	"RE4":143221013,
	"SF6":143230113,
	"DD2":760230703,
	"KG":231106777,
	"DR":240606151,
	"MHWILDS":240701001,
	}

ddsBpps = {
	"UNKNOWN":0,
	"R32G32B32A32TYPELESS":128,
	"R32G32B32A32FLOAT":128,
	"R32G32B32A32UINT":128,
	"R32G32B32A32SINT":128,
	"R32G32B32TYPELESS":96,
	"R32G32B32FLOAT":96,
	"R32G32B32UINT":96,
	"R32G32B32SINT":96,
	"R16G16B16A16TYPELESS":64,
	"R16G16B16A16FLOAT":64,
	"R16G16B16A16UNORM":64,
	"R16G16B16A16UINT":64,
	"R16G16B16A16SNORM":64,
	"R16G16B16A16SINT":64,
	"R32G32TYPELESS":64,
	"R32G32FLOAT":64,
	"R32G32UINT":64,
	"R32G32SINT":64,
	"R32G8X24TYPELESS":64,
	"D32FLOATS8X24UINT":64,
	"R32FLOATX8X24TYPELESS":64,
	"X32TYPELESSG8X24UINT":64,
	"R10G10B10A2TYPELESS":32,
	"R10G10B10A2UNORM":32,
	"R10G10B10A2UINT":32,
	"R11G11B10FLOAT":32,
	"R8G8B8A8TYPELESS":32,
	"R8G8B8A8UNORM":32,
	"R8G8B8A8UNORMSRGB":32,
	"R8G8B8A8UINT":32,
	"R8G8B8A8SNORM":32,
	"R8G8B8A8SINT":32,
	"R16G16TYPELESS":32,
	"R16G16FLOAT":32,
	"R16G16UNORM":32,
	"R16G16UINT":32,
	"R16G16SNORM":32,
	"R16G16SINT":32,
	"R32TYPELESS":32,
	"D32FLOAT":32,
	"R32FLOAT":32,
	"R32UINT":32,
	"R32SINT":32,
	"R24G8TYPELESS":32,
	"D24UNORMS8UINT":32,
	"R24UNORMX8TYPELESS":32,
	"X24TYPELESSG8UINT":32,
	"R8G8TYPELESS":16,
	"R8G8UNORM":16,
	"R8G8UINT":16,
	"R8G8SNORM":16,
	"R8G8SINT":16,
	"R16TYPELESS":16,
	"R16FLOAT":16,
	"D16UNORM":16,
	"R16UNORM":16,
	"R16UINT":16,
	"R16SNORM":16,
	"R16SINT":16,
	"R8TYPELESS":8,
	"R8UNORM":8,
	"R8UINT":8,
	"R8SNORM":8,
	"R8SINT":8,
	"A8UNORM":8,
	"R1UNORM":1,
	"R9G9B9E5SHAREDEXP":32,
	"R8G8B8G8UNORM":16,
	"G8R8G8B8UNORM":16,
	"B5G6R5UNORM":16,
	"B5G5R5A1UNORM":16,
	"B8G8R8A8UNORM":32,
	"B8G8R8X8UNORM":32,
	"B8G8R8A8TYPELESS":32,
	"R10G10B10XRBIASA2UNORM":32,
	"B8G8R8A8UNORMSRGB":32,
	"B8G8R8X8TYPELESS":32,
	"B8G8R8X8UNORMSRGB":32,
	"AYUV":32,
	"Y410":10,
	"Y416":16,
	"NV12":12,
	"P010":10,
	"P016":16,
	"DXGIFORMAT420OPAQUE":20,
	"YUY2":16,
	"Y210":10,
	"Y216":16,
	"NV11":11,
	"AI44":44,
	"IA44":44,
	"P8":8,
	"A8P8":16,
	"B4G4R4A4UNORM":16,
	"P208":8,
	"V208":8,
	"V408":8,
	"BC1TYPELESS":4,
	"BC1UNORM":4,
	"BC1UNORMSRGB":4,
	"BC2TYPELESS":8,
	"BC2UNORM":8,
	"BC2UNORMSRGB":8,
	"BC3TYPELESS":8,
	"BC3UNORM":8,
	"BC3UNORMSRGB":8,
	"BC4TYPELESS":4,
	"BC4UNORM":4,
	"BC4SNORM":4,
	"BC5TYPELESS":8,
	"BC5UNORM":8,
	"BC5SNORM":8,
	"BC6HTYPELESS":8,
	"BC6HUF16":8,
	"BC6HSF16":8,
	"BC7TYPELESS":8,
	"BC7UNORM":8,
	"BC7UNORMSRGB":8,
	}

texFormatToDXGIStringDict = {
		1:"R32G32B32A32TYPELESS",
		2:"R32G32B32A32FLOAT",
		3:"R32G32B32A32UINT",
		4:"R32G32B32A32SINT",
		5:"R32G32B32TYPELESS",
		6:"R32G32B32FLOAT",
		7:"R32G32B32UINT",
		8:"R32G32B32SINT",
		9:"R16G16B16A16TYPELESS",
		0XA:"R16G16B16A16FLOAT",
		0XB:"R16G16B16A16UNORM",
		0XC:"R16G16B16A16UINT",
		0XD:"R16G16B16A16SNORM",
		0XE:"R16G16B16A16SINT",
		0XF:"R32G32TYPELESS",
		0X10:"R32G32FLOAT",
		0X11:"R32G32UINT",
		0X12:"R32G32SINT",
		0X13:"R32G8X24TYPELESS",
		0X14:"D32FLOATS8X24UINT",
		0X15:"R32FLOATX8X24TYPELESS",
		0X16:"X32TYPELESSG8X24UINT",
		0X17:"R10G10B10A2TYPELESS",
		0X18:"R10G10B10A2UNORM",
		0X19:"R10G10B10A2UINT",
		0X1A:"R11G11B10FLOAT",
		0X1B:"R8G8B8A8TYPELESS",
		0X1C:"R8G8B8A8UNORM",
		0X1D:"R8G8B8A8UNORMSRGB",
		0X1E:"R8G8B8A8UINT",
		0X1F:"R8G8B8A8SNORM",
		0X20:"R8G8B8A8SINT",
		0X21:"R16G16TYPELESS",
		0X22:"R16G16FLOAT",
		0X23:"R16G16UNORM",
		0X24:"R16G16UINT",
		0X25:"R16G16SNORM",
		0X26:"R16G16SINT",
		0X27:"R32TYPELESS",
		0X28:"D32FLOAT",
		0X29:"R32FLOAT",
		0X2A:"R32UINT",
		0X2B:"R32SINT",
		0X2C:"R24G8TYPELESS",
		0X2D:"D24UNORMS8UINT",
		0X2E:"R24UNORMX8TYPELESS",
		0X2F:"X24TYPELESSG8UINT",
		0X30:"R8G8TYPELESS",
		0X31:"R8G8UNORM",
		0X32:"R8G8UINT",
		0X33:"R8G8SNORM",
		0X34:"R8G8SINT",
		0X35:"R16TYPELESS",
		0X36:"R16FLOAT",
		0X37:"D16UNORM",
		0X38:"R16UNORM",
		0X39:"R16UINT",
		0X3A:"R16SNORM",
		0X3B:"R16SINT",
		0X3C:"R8TYPELESS",
		0X3D:"R8UNORM",
		0X3E:"R8UINT",
		0X3F:"R8SNORM",
		0X40:"R8SINT",
		0X41:"A8UNORM",
		0X42:"R1UNORM",
		0X43:"R9G9B9E5SHAREDEXP",
		0X44:"R8G8B8G8UNORM",
		0X45:"G8R8G8B8UNORM",
		0X46:"BC1TYPELESS",
		0X47:"BC1UNORM",
		0X48:"BC1UNORMSRGB",
		0X49:"BC2TYPELESS",
		0X4A:"BC2UNORM",
		0X4B:"BC2UNORMSRGB",
		0X4C:"BC3TYPELESS",
		0X4D:"BC3UNORM",
		0X4E:"BC3UNORMSRGB",
		0X4F:"BC4TYPELESS",
		0X50:"BC4UNORM",
		0X51:"BC4SNORM",
		0X52:"BC5TYPELESS",
		0X53:"BC5UNORM",
		0X54:"BC5SNORM",
		0X55:"B5G6R5UNORM",
		0X56:"B5G5R5A1UNORM",
		0X57:"B8G8R8A8UNORM",
		0X58:"B8G8R8X8UNORM",
		0X59:"R10G10B10XRBIASA2UNORM",
		0X5A:"B8G8R8A8TYPELESS",
		0X5B:"B8G8R8A8UNORMSRGB",
		0X5C:"B8G8R8X8TYPELESS",
		0X5D:"B8G8R8X8UNORMSRGB",
		0X5E:"BC6HTYPELESS",
		0X5F:"BC6HUF16",
		0X60:"BC6HSF16",
		0X61:"BC7TYPELESS",
		0X62:"BC7UNORM",
		0X63:"BC7UNORMSRGB",
		0X400:"VIAEXTENSION",
		0X401:"ASTC4X4TYPELESS",
		0X402:"ASTC4X4UNORM",
		0X403:"ASTC4X4UNORMSRGB",
		0X404:"ASTC5X4TYPELESS",
		0X405:"ASTC5X4UNORM",
		0X406:"ASTC5X4UNORMSRGB",
		0X407:"ASTC5X5TYPELESS",
		0X408:"ASTC5X5UNORM",
		0X409:"ASTC5X5UNORMSRGB",
		0X40A:"ASTC6X5TYPELESS",
		0X40B:"ASTC6X5UNORM",
		0X40C:"ASTC6X5UNORMSRGB",
		0X40D:"ASTC6X6TYPELESS",
		0X40E:"ASTC6X6UNORM",
		0X40F:"ASTC6X6UNORMSRGB",
		0X410:"ASTC8X5TYPELESS",
		0X411:"ASTC8X5UNORM",
		0X412:"ASTC8X5UNORMSRGB",
		0X413:"ASTC8X6TYPELESS",
		0X414:"ASTC8X6UNORM",
		0X415:"ASTC8X6UNORMSRGB",
		0X416:"ASTC8X8TYPELESS",
		0X417:"ASTC8X8UNORM",
		0X418:"ASTC8X8UNORMSRGB",
		0X419:"ASTC10X5TYPELESS",
		0X41A:"ASTC10X5UNORM",
		0X41B:"ASTC10X5UNORMSRGB",
		0X41C:"ASTC10X6TYPELESS",
		0X41D:"ASTC10X6UNORM",
		0X41E:"ASTC10X6UNORMSRGB",
		0X41F:"ASTC10X8TYPELESS",
		0X420:"ASTC10X8UNORM",
		0X421:"ASTC10X8UNORMSRGB",
		0X422:"ASTC10X10TYPELESS",
		0X423:"ASTC10X10UNORM",
		0X424:"ASTC10X10UNORMSRGB",
		0X425:"ASTC12X10TYPELESS",
		0X426:"ASTC12X10UNORM",
		0X427:"ASTC12X10UNORMSRGB",
		0X428:"ASTC12X12TYPELESS",
		0X429:"ASTC12X12UNORM",
		0X42A:"ASTC12X12UNORMSRGB",
		0X7FFFFFFF:"FORCEUINT"
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
		
		self.ddsBitsPerPixel = 0#Internal, for reading texture data with cursed pitch
		
	def read(self,file):
		self.magic = read_uint(file)
		if self.magic != 5784916:
			raiseError("File is not a tex file.")
		self.version = read_uint(file)
		self.width = read_ushort(file)
		self.height = read_ushort(file)
		self.depth = read_ushort(file)
		if self.version > 11 and self.version != 190820018:
			self.imageCount = read_ubyte(file)
			self.imageMipHeaderSize = read_ubyte(file)
			self.mipCount = self.imageMipHeaderSize // 16
		else:
			self.mipCount = read_ubyte(file)
			self.imageCount = read_ubyte(file)
		self.format = read_uint(file)
		self.swizzleControl = read_int(file)
		self.cubemapMarker = read_uint(file)
		self.unkn04 = read_ubyte(file)
		self.unkn05 = read_ubyte(file)
		self.null0 = read_ushort(file)
		if self.version > 27 and self.version != 190820018:#Thanks RE3
			#swizzle data,unused
			self.swizzleHeightDepth = read_ubyte(file)
			self.swizzleWidth = read_ubyte(file)
			self.null1 = read_ushort(file)
			self.seven = read_ushort(file)
			self.one = read_ushort(file)
		self.ddsBitsPerPixel = ddsBpps.get(texFormatToDXGIStringDict.get(self.format,"UNKNOWN"),0)
		#self.reserved = read_uint64(file)
	
	def write(self,file):
		write_uint(file, self.magic)
		write_uint(file, self.version)
		write_ushort(file, self.width)
		write_ushort(file, self.height)
		write_ushort(file, self.depth)
		if self.version > 11 and self.version != 190820018:
			write_ubyte(file, self.imageCount)
			write_ubyte(file, self.imageMipHeaderSize)
		else:
			write_ubyte(file, self.mipCount)
			write_ubyte(file, self.imageCount)
			
		write_uint(file, self.format)
		write_int(file, self.swizzleControl)
		write_uint(file, self.cubemapMarker)
		write_ubyte(file, self.unkn04)
		write_ubyte(file, self.unkn05)
		write_ushort(file, self.null0)
		if self.version > 27 and self.version != 190820018:#Thanks RE3
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
		
		#WILDS
		self.imageSize = 0
		self.imageOffset = 0
		
		self.textureData = bytearray()
	def read(self,file,expectedMipSize,width,height,ddsBPPs,currentImageDataHeaderOffset,imageDataOffset,texVersion):

		self.mipOffset = read_uint64(file)
		self.compressedSize = read_uint(file)
		self.uncompressedSize = read_uint(file)
		currentPos = file.tell()
		file.seek(self.mipOffset)
		#print(f"mip offset {self.mipOffset}")
		#print(f"{file.tell()}")
		endSize = self.uncompressedSize
		
		mipData = None#BytesIO for uncompressed texture data
		
		if texVersion >= VERSION_MHWILDS:
			file.seek(currentImageDataHeaderOffset)
			self.imageSize = read_uint(file)
			self.imageOffset = read_uint(file)
			
			file.seek(imageDataOffset + self.imageOffset)
			rawImageData = file.read(self.imageSize)

			# Check if it's GDeflate compressed by the [0x04, 0xFB] header until we figure
			# out if there is a flag somewhere else.
			if len(rawImageData) >= 2 and rawImageData[0] == 0x04 and rawImageData[1] == 0xFB:
				#print("Decompressing MH Wilds texture with GDeflate")
				decompressor = GDeflate()
				mipData = BytesIO(decompressor.decompress(rawImageData, num_workers=4))

			else:
				#print("MH Wilds texture without GDeflate header - assuming uncompressed.")
				mipData = BytesIO(rawImageData)
			
			endSize = mipData.getbuffer().nbytes
			#print(f"Decompressed data size: {endSize}")
			#print(f"Specified size: {self.uncompressedSize}")
			

		#print(f"expected mip size: {expectedMipSize}\nactual mip size: {self.uncompressedSize}")
		if endSize != expectedMipSize:
			if mipData == None:
				mipData = BytesIO(file.read(self.uncompressedSize))
			#print(f"{width},{height}")
			if ddsBPPs == 4 or ddsBPPs == 8:
				texelSize = 4
			else:
				texelSize = ddsBPPs // 8
			
			if ddsBPPs != 0:
				bitAmount = (width * ddsBPPs)
				pad = 8 - bitAmount if bitAmount < 8 else 0
				#if not bitAmount % 8 == 0:
					#raise ValueError("Data is not byte aligned")
				byteReadLength = (bitAmount//8+pad) * texelSize
				#print(f"byteReadLength: {byteReadLength}")
				
			else:
				raise ValueError("Unsupported DXGI Format")
			
			currentOffset = 0
			seekAmount = self.compressedSize - byteReadLength
			#print(f"seekAmount: {seekAmount}")
			#print(f"endSize: {endSize}")
			#tempFile = open(r"D:\Modding\Monster Hunter Wilds\texDataTest\tempData"+str(currentImageDataHeaderOffset),"wb")
			#tempFile.write(mipData.getvalue())
			#tempFile.close()
			while currentOffset != endSize:
				#print(f"current block offset {file.tell()}")
				self.textureData.extend(mipData.read(byteReadLength))
				mipData.seek(seekAmount,1)
				currentOffset += self.compressedSize
				if currentOffset > endSize:
					raise Exception("Texture Data Read Past Bounds")
				#print(f"end block offset {file.tell()}")
			#print(f"end mip read offset {file.tell()}")
			
			mipData.close()
			
		else:
			
			if mipData != None:
				self.textureData = mipData.getvalue()
				mipData.close()
			else:
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
		self.imageHeaderList = []#WILDS
	def read(self,file):

		self.header.read(file)
		self.imageMipDataList = []
		currentOverallMipIndex = 0
		currentImageDataHeaderOffset = file.tell() + (self.header.mipCount * self.header.imageCount ) * 16#16 is mip header size
		imageDataOffset = currentImageDataHeaderOffset +  (self.header.mipCount * self.header.imageCount ) * 8#8 is image data header size
		for i in range(self.header.imageCount):
			imageMipDataListEntry = []
			currentXSize = self.header.width
			currentYSize = self.header.height
			#expectedMipSize = ((currentXSize * currentYSize) * self.header.ddsBitsPerPixel) // 8
			for j in range(self.header.mipCount):
				mipEntry = MipData()
				mipX = max(self.header.width >> j, 1)
				mipY = max(self.header.height >> j, 1)
				mipBitSize = (mipX*mipY) * self.header.ddsBitsPerPixel
				pad = 8 - mipBitSize if mipBitSize < 8 else 0
				expectedMipSize = (mipBitSize + pad) // 8
				mipEntry.read(file,expectedMipSize,mipX,mipY,self.header.ddsBitsPerPixel,currentImageDataHeaderOffset,imageDataOffset,self.header.version)
				imageMipDataListEntry.append(mipEntry)
				currentImageDataHeaderOffset += 8#8 is image data header size
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
	def GetTextureData(self,imageIndex):
		byteArray = bytearray()
		
		
		#for image in self.imageMipDataList:
		image = self.imageMipDataList[imageIndex]
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