#Author: NSA Cloud
import os

from ..gen_functions import textColors,raiseWarning,raiseError,getPaddingAmount,read_uint,read_int,read_uint64,read_float,read_short,read_ushort,read_ubyte,read_unicode_string,read_byte,write_uint,write_int,write_uint64,write_float,write_short,write_ushort,write_ubyte,write_unicode_string,write_byte


class DX10_Header():
	def __init__(self):
		self.dxgiFormat = 0#enum
		self.resourceDimension  = 0#enum
		self.miscFlags = 0
		self.arraySize = 0
		self.miscFlags2 = 0	
		
	def read(self,file):
		self.dxgiFormat = read_uint(file)#enum
		self.resourceDimension = read_uint(file)#enum
		self.miscFlags = read_uint(file)
		self.arraySize = read_uint(file)
		self.miscFlags2 = read_uint(file)	
	
	def write(self,file):
		write_uint(file, self.dxgiFormat)
		write_uint(file, self.resourceDimension)
		write_uint(file, self.miscFlags)
		write_uint(file, self.arraySize)
		write_uint(file, self.miscFlags2)

class DDS_PixelFormat():
	def __init__(self):
		self.dwSize = 32
		self.dwFlags  = 0#enum
		self.dwFourCC = 0#enum
		self.dwRGBBitCount = 0
		self.dwRBitMask = 0	
		self.dwGBitMask = 0	
		self.dwBBitMask = 0	
		self.dwABitMask = 0	
		
	def read(self,file):
		self.dwSize = read_uint(file)
		self.dwFlags  = read_uint(file)#enum
		self.dwFourCC = read_uint(file)#enum
		self.dwRGBBitCount = read_uint(file)
		self.dwRBitMask = read_uint(file)
		self.dwGBitMask = read_uint(file)
		self.dwBBitMask = read_uint(file)
		self.dwABitMask = read_uint(file)
	
	def write(self,file):
		write_uint(file, self.dwSize)
		write_uint(file, self.dwFlags)
		write_uint(file, self.dwFourCC)
		write_uint(file, self.dwRGBBitCount)
		write_uint(file, self.dwRBitMask)
		write_uint(file, self.dwGBitMask)
		write_uint(file, self.dwBBitMask)
		write_uint(file, self.dwABitMask)

class DDSHeader():
	def __init__(self):
		self.magic = 542327876
		self.dwSize  = 0
		self.dwFlags = 0#enum
		self.dwHeight = 0
		self.dwWidth = 0
		self.dwPitchOrLinearSize = 0
		self.dwDepth = 0
		self.dwMipMapCount = 0
		self.dwReserved1 = [0]*11
		self.ddpfPixelFormat = DDS_PixelFormat()
		self.ddsCaps1 = 0#enum
		self.ddsCaps2 = 0#enum
		self.ddsCaps3 = 0
		self.ddsCaps4 = 0
		self.dwReserved2 = 0
		self.dx10Header = None	
		
	def read(self,file):
		self.magic = read_uint(file)
		if self.magic != 542327876:
			raiseError("File is not a dds file.")
		self.dwSize  = read_uint(file)
		self.dwFlags = read_uint(file)#enum
		self.dwHeight = read_uint(file)
		self.dwWidth = read_uint(file)
		self.dwPitchOrLinearSize = read_uint(file)
		self.dwDepth = read_uint(file)
		self.dwMipMapCount = read_uint(file)
		self.dwReserved1 = []
		for i in range(11):
			self.dwReserved1.append(read_uint(file))
		self.ddpfPixelFormat.read(file)
		self.ddsCaps1 = read_uint(file)#enum
		self.ddsCaps2 = read_uint(file)#enum
		self.ddsCaps3 = read_uint(file)
		self.ddsCaps4 = read_uint(file)
		self.dwReserved2 = read_uint(file)
		if self.ddpfPixelFormat.dwFourCC == 808540228:#DX10
			self.dx10Header = DX10_Header()
			self.dx10Header.read(file)
		
	def write(self,file):
		write_uint(file, self.magic)
		write_uint(file, self.dwSize)
		write_uint(file, self.dwFlags)
		write_uint(file, self.dwHeight)
		write_uint(file, self.dwWidth)
		write_uint(file, self.dwPitchOrLinearSize)
		write_uint(file, self.dwDepth)
		write_uint(file, self.dwMipMapCount)
		for entry in self.dwReserved1:
			write_uint(file,entry)
		self.ddpfPixelFormat.write(file)
		write_uint(file, self.ddsCaps1)
		write_uint(file, self.ddsCaps2)
		write_uint(file, self.ddsCaps3)
		write_uint(file, self.ddsCaps4)
		write_uint(file, self.dwReserved2)
		if self.ddpfPixelFormat.dwFourCC == 808540228 and self.dx10Header != None:#DX10
			self.dx10Header.write(file)
class DDS():
	def __init__(self):
		self.header = DDSHeader()
		self.data = bytes()
	def read(self,file):
		self.header.read(file)
		self.data = file.read()
		
	def write(self,file):
		self.header.write(file);
		file.write(self.data);
class DDSFile:
	def __init__(self):
		self.dds = DDS()
	def read(self,filePath):
		#print("Opening " + filePath)
		try:  
			file = open(filePath,"rb")
		except:
			raiseError("Failed to open " + filePath)
		self.dds.read(file)
		file.close()
			
	def write(self,filePath):
		os.makedirs(os.path.dirname(filePath),exist_ok = True)
		print("Writing " + filePath)
		try:  
			file = open(filePath,"wb")
			self.dds.write(file)
		except Exception as err:
			raiseError("Failed to write " + filePath + str(err))
		file.close()

def getDDSHeader(ddsPath):
	try:  
		file = open(ddsPath,"rb")
	except Exception as err:
		raiseError("Failed to open " + ddsPath + str(err))
	header = DDSHeader()
	header.read(file)
	file.close()
	return header