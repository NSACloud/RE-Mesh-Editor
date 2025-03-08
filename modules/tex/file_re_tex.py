# Author: NSA Cloud & AsteriskAmpersand
from io import BytesIO
from ..gen_functions import raiseError
from ..gen_functions import read_uint, read_int, read_uint64,\
    read_float, read_short, read_ushort, read_ubyte,\
    read_unicode_string, read_byte,\
    write_uint, write_int, write_uint64, write_float,\
    write_short, write_ushort, write_ubyte, write_byte,\
    write_unicode_string
from ..gen_functions import textColors, raiseWarning, getPaddingAmount
from ..gdeflate.gdeflate import GDeflate
from .enums.game_version_enum import gameNameToTexVersionDict
from .enums.dds_bpps import ddsBpps
from .enums.tex_format_enum import texFormatToDXGIStringDict

VERSION_MHWILDS_BETA = 240701001
VERSION_MHWILDS = 241106027


def getTexVersionFromGameName(gameName):
    return gameNameToTexVersionDict.get(gameName, -1)


class TexHeader():
    def __init__(self):
        self.magic = 5784916
        self.version = 0
        self.width = 0
        self.height = 0
        self.depth = 0
        self.imageCount = 0
        self.imageMipHeaderSize = 0
        self.mipCount = 0  # Internal,calcluated from mip header size
        self.format = 0
        self.swizzleControl = -1
        self.cubemapMarker = 0
        self.unkn04 = 0
        self.unkn05 = 0
        self.null0 = 0
        # swizzle data,unused
        self.swizzleHeightDepth = 0
        self.swizzleWidth = 0
        self.null1 = 0
        self.seven = 0
        self.one = 0

        self.ddsBitsPerPixel = 0  # Internal, for reading texture data with cursed pitch

    def read(self, file):
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
        if self.version > 27 and self.version != 190820018:  # Thanks RE3
            # swizzle data,unused
            self.swizzleHeightDepth = read_ubyte(file)
            self.swizzleWidth = read_ubyte(file)
            self.null1 = read_ushort(file)
            self.seven = read_ushort(file)
            self.one = read_ushort(file)
        self.ddsBitsPerPixel = ddsBpps.get(
            texFormatToDXGIStringDict.get(self.format, "UNKNOWN"), 0)
        #self.reserved = read_uint64(file)

    def write(self, file):
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
        if self.version > 27 and self.version != 190820018:  # Thanks RE3
            write_ubyte(file, self.swizzleHeightDepth)
            write_ubyte(file, self.swizzleWidth)
            write_ushort(file, self.null1)
            write_ushort(file, self.seven)
            write_ushort(file, self.one)


class CompressedImageHeader():
    def __init__(self):
        self.imageSize = 0
        self.imageOffset = 0

    def read(self, file, expectedMipSize, width, height, ddsBPPs, currentImageDataHeaderOffset, imageDataOffset, texVersion):
        self.imageSize = read_uint(file)
        self.imageOffset = read_uint(file)

    def write(self, file):
        write_uint(file, self.imageSize)
        write_uint(file, self.imageOffset)


class MipData():
    def __init__(self):
        self.mipOffset = 0
        self.scanlineLength = 0
        self.uncompressedSize = 0

        # WILDS
        self.imageSize = 0
        self.imageOffset = 0

        self.textureData = None

    def storeTrimmed(self, source, target, scanlineLength, dataLength, endSize):
        """
        Parameters
        ----------
        source : BytesIO
            Raw untrimmed texture data
        target : BytesIO
            Buffer to write the trimmed texture data to
        scanlineLength : int
            Length in bytes of scanline as specified by the file
        dataLength : int
            Length in bytes of a single row of pixels
        endSize : int
            Final size of the texture as specified by the file

        Raises
        ------
        BufferError 
            If texture is read past expected bounds
        """
        currentOffset = 0
        seekAmount = scanlineLength - dataLength
        #print(f"seekAmount: {seekAmount}")
        #print(f"endSize: {endSize}")
        #tempFile = open(r"D:\Modding\Monster Hunter Wilds\texDataTest\tempData"+str(currentImageDataHeaderOffset),"wb")
        # tempFile.write(mipData.getvalue())
        # tempFile.close()
        while currentOffset != endSize:
            #print(f"current block offset {file.tell()}")
            target.extend(source.read(dataLength))
            source.seek(seekAmount, 1)
            currentOffset += scanlineLength
            if currentOffset > endSize:
                raise BufferError("Texture Data Read Past Bounds")
            #print(f"end block offset {file.tell()}")
        #print(f"end mip read offset {file.tell()}")
        source.close()
        return target

    def calculateLineBytelength(self, ddsBPPs, width):
        """
        Parameters
        ----------
        ddsBPPs : Int
            Bytes per pixel of the compression format used in the file
        width : Int
            Texture width in pixels

        Returns
        ----------
        lineBytelength : Int
            Number of bytes expected per horizontal pixel line

        Raises
        ------
        ValueError
            DXGI Format lacking a known bytes per pixel value
        """
        # print(f"{width},{height}")
        if ddsBPPs == 4 or ddsBPPs == 8:
            texelSize = 4
        else:
            texelSize = ddsBPPs // 8

        if ddsBPPs != 0:
            bitAmount = (width * ddsBPPs)
            pad = 8 - bitAmount if bitAmount < 8 else 0
            # if not bitAmount % 8 == 0:
            #raise ValueError("Data is not byte aligned")
            byteReadLength = (bitAmount//8+pad) * texelSize
            #print(f"byteReadLength: {byteReadLength}")
        else:
            raise ValueError("Unsupported DXGI Format")
        return byteReadLength

    def uncompressGdeflate(self, file, headerOffset, imageOffset):
        """
        Parameters
        ----------
        file : BytesIO
            Tex file being read
        headerOffset : Int
            Offset from the start of the file to the current Compressed Data Header
        imageOffset : Int
            Offset form the start of the file to the start of Texture information

        Returns
        ----------
        mipData : BytesIO
            Uncompressed texture data
        """

        file.seek(headerOffset)
        self.imageSize = read_uint(file)
        self.imageOffset = read_uint(file)

        file.seek(imageOffset + self.imageOffset)
        rawImageData = file.read(self.imageSize)

        # Check if it's GDeflate compressed by the [0x04, 0xFB] header until we figure
        # out if there is a flag somewhere else.
        if len(rawImageData) >= 2 and rawImageData[0] == 0x04 and rawImageData[1] == 0xFB:
            #print("Decompressing MH Wilds texture with GDeflate")
            decompressor = GDeflate()
            mipData = BytesIO(decompressor.decompress(
                rawImageData, num_workers=4))

        else:
            #print("MH Wilds texture without GDeflate header - assuming uncompressed.")
            mipData = BytesIO(rawImageData)

        #print(f"Decompressed data size: {endSize}")
        #print(f"Specified size: {self.uncompressedSize}")
        return mipData

    def read(self, file, expectedMipSize, dimensions, ddsBPPs,
             currentImageDataHeaderOffset, imageDataOffset,
             texVersion):
        """
        Parameters
        ----------
        file : BytesIO
            Tex file being read
        expectedMipSize : Int
            Expected size in bytes of the final texture buffer (x * y * z * bytesPerPixel)
        dimensions : Int[3]
            Height, Width and Depth of Image
        ddsBPPs : Int
            Bytes per pixel of the compression format used in the file
        currentImageDataHeaderOffset : Int
            Offset from the start of the file to the current Compressed Data Header
        imageDataOffset : Int
            Offset form the start of the file to the start of Texture information
        texVersion : Int
            RE Engine Texture format Version
        """
        width, height, depth = dimensions
        self.mipOffset = read_uint64(file)
        self.scanlineLength = read_uint(file)
        self.uncompressedSize = read_uint(file)
        self.textureData = bytearray()
        currentPos = file.tell()
        file.seek(self.mipOffset)
        #print(f"mip offset {self.mipOffset}")
        # print(f"{file.tell()}")
        endSize = self.uncompressedSize
        mipData = None  # BytesIO for uncompressed texture data

        if texVersion == VERSION_MHWILDS or texVersion == VERSION_MHWILDS_BETA:
            mipData = self.uncompressGdeflate(file,
                currentImageDataHeaderOffset, imageDataOffset)
            endSize = mipData.getbuffer().nbytes

        #print(f"expected mip size: {expectedMipSize}\nactual mip size: {self.uncompressedSize}")
        if endSize != expectedMipSize:
            if mipData == None:
                mipData = BytesIO(file.read(self.uncompressedSize))
            lineBytelength = self.calculateLineBytelength(ddsBPPs, width)
            self.storeTrimmed(mipData, self.textureData,
                              self.scanlineLength, lineBytelength,
                              expectedMipSize)
        else:
            if mipData != None:
                self.textureData = mipData.getvalue()
                mipData.close()
            else:
                self.textureData = file.read(self.uncompressedSize)

        file.seek(currentPos)

    def write(self, file):
        write_uint64(file, self.mipOffset)
        write_uint(file, self.scanlineLength)
        write_uint(file, self.uncompressedSize)


class Tex():
    def __init__(self):
        self.header = TexHeader()
        self.imageMipDataList = []
        self.imageHeaderList = []  # WILDS

    def read(self, file):
        self.header.read(file)
        self.imageMipDataList = []
        currentOverallMipIndex = 0
        currentImageDataHeaderOffset = file.tell() + \
            (self.header.mipCount * self.header.imageCount) * \
            16  # 16 is mip header size
        imageDataOffset = currentImageDataHeaderOffset +  \
            (self.header.mipCount * self.header.imageCount) * \
            8  # 8 is compression data header size
        for i in range(self.header.imageCount):
            imageMipDataListEntry = []
            currentXSize = self.header.width
            currentYSize = self.header.height
            #expectedMipSize = ((currentXSize * currentYSize) * self.header.ddsBitsPerPixel) // 8
            for j in range(self.header.mipCount):
                mipEntry = MipData()
                mipX = max(self.header.width >> j, 1)
                mipY = max(self.header.height >> j, 1)
                mipZ = max(self.header.depth >> j, 1)
                mipBitSize = (mipX*mipY*mipZ) * self.header.ddsBitsPerPixel
                pad = 8 - mipBitSize if mipBitSize < 8 else 0
                expectedMipSize = (mipBitSize + pad) // 8
                mipEntry.read(file, expectedMipSize, (mipX, mipY, mipZ),
                              self.header.ddsBitsPerPixel, currentImageDataHeaderOffset,
                              imageDataOffset, self.header.version)
                imageMipDataListEntry.append(mipEntry)
                currentImageDataHeaderOffset += 8  # 8 is image data header size
            self.imageMipDataList.append(imageMipDataListEntry)

    def write(self, file):
        self.header.write(file)
        # Write mip offsets and sizes
        for mipEntryList in self.imageMipDataList:
            for mipEntry in mipEntryList:
                mipEntry.write(file)

        # Write compressed image headers, wilds
        for imageHeader in self.imageHeaderList:
            imageHeader.write(file)

        # Write mip data
        for mipEntryList in self.imageMipDataList:
            for mipEntry in mipEntryList:
                file.write(mipEntry.textureData)

    def GetTextureData(self, imageIndex):
        byteArray = bytearray()
        # for image in self.imageMipDataList:
        image = self.imageMipDataList[imageIndex]
        for mipData in image:
            byteArray.extend(mipData.textureData)
        return bytes(byteArray)


class RE_TexFile:
    def __init__(self):
        self.tex = Tex()

    def read(self, filePath):
        #print("Opening " + filePath)
        try:
            file = open(filePath, "rb")
        except:
            raiseError("Failed to open " + filePath)
        self.tex.read(file)
        file.close()

    def write(self, filePath):
        print("Writing " + filePath)
        try:
            file = open(filePath, "wb")
        except:
            raiseError("Failed to open " + filePath)
        self.tex.write(file)
        file.close()
