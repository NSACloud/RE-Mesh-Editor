# Author: NSA Cloud & AsteriskAmpersand
# Credit to Asterisk Ampersand, code borrowed from Tex Chopper
from ..dds.file_dds import DDS, DX10_Header, DDSFile, getDDSHeader

from .file_re_tex import RE_TexFile, MipData, CompressedImageHeader
from ..gen_functions import raiseWarning
from ..gdeflate.gdeflate import GDeflate, GDeflateCompressionLevel, GDeflateError
from ..ddsconv.directx.texconv import Texconv, unload_texconv
from .enums import tex_format_enum as texenum
from .enums import dxgi_format_enum as dxgienum
from .enums.dds_bpps import ddsBpps
from . import tex_math as tmath
from . import format_ops
import os

VERSION_MHWILDS_BETA = 240701001
VERSION_MHWILDS = 241106027


def TexToDDS(tex, imageIndex):
    """ Generates a DDS file from the 'imageIndex'th image in the tex file"""
    dds = DDS()
    dds.header.dwSize = 124
    # DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT | DDSD_MIPMAPCOUNT | DDSD_LINEARSIZE
    dds.header.dwFlags = 0x00000001 | 0x00000002 | 0x00000004 | 0x00001000 | 0x00020000 | 0x00080000
    dds.header.dwHeight = tex.header.height
    dds.header.dwWidth = tex.header.width
    bpps = ddsBpps[texenum.texFormatToDXGIStringDict[tex.header.format]]
    dds.header.dwPitchOrLinearSize = (
        dds.header.dwWidth * dds.header.dwHeight * bpps) // 8
    #dds.header.dwDepth = tex.header.depth
    dds.header.dwDepth = tex.header.depth
    dds.header.dwMipMapCount = tex.header.mipCount
    dds.header.ddpfPixelFormat.dwSize = 32
    dds.header.ddpfPixelFormat.dwFlags = 0x4  # DDPF_FOURCC
    dds.header.ddpfPixelFormat.dwFourCC = 808540228  # DX10
    dds.header.ddpfPixelFormat.dwRGBBitCount = 0
    dds.header.ddpfPixelFormat.dwRBitMask = 0
    dds.header.ddpfPixelFormat.dwGBitMask = 0
    dds.header.ddpfPixelFormat.dwBBitMask = 0
    dds.header.ddpfPixelFormat.dwABitMask = 0
    dds.header.ddsCaps1 = 0x00001000 | 0x00400000  # DDSCAPS_TEXTURE | DDSCAPS_MIPMAP
    if tex.header.cubemapMarker != 0:
        dds.header.ddsCaps1 = dds.header.ddsCaps1 | 0x00000008  # DDSCAPS_COMPLEX
        # DDSCAPS2_CUBEMAP | DDSCAPS2_CUBEMAP_POSITIVEX | DDSCAPS2_CUBEMAP_NEGATIVEX | DDSCAPS2_CUBEMAP_POSITIVEY | DDSCAPS2_CUBEMAP_NEGATIVEY | DDSCAPS2_CUBEMAP_POSITIVEZ | DDSCAPS2_CUBEMAP_NEGATIVEZ
        dds.header.ddsCaps2 = 0x00000200 | 0x00000400 | 0x00000800 | 0x00001000 | 0x00002000 | 0x00004000 | 0x00008000
    else:
        dds.header.ddsCaps2 = 0
    dds.header.ddsCaps3 = 0
    dds.header.ddsCaps4 = 0
    dds.header.dwReserved2 = 0

    dds.header.dx10Header = DX10_Header()
    dds.header.dx10Header.dxgiFormat = dxgienum.formatStringToDXGIDict[
        texenum.texFormatToDXGIStringDict[tex.header.format]]
    # D3D10_RESOURCE_DIMENSION_TEXTURE2D
    dds.header.dx10Header.resourceDimension = 3
    """ Image Arrays are exported as multiple files, hence this is commented out
    if tex.header.cubemapMarker != 0:
        dds.header.dx10Header.arraySize = tex.header.imageCount // 6
    else:
        dds.header.dx10Header.arraySize = tex.header.imageCount
    """
    dds.header.dx10Header.arraySize = 1
    dds.header.dx10Header.miscFlags2 = 0
    dds.data = tex.GetTextureData(imageIndex)
    return dds


def convertTexFileToDDS(texPath, outputPath):
    texFile = RE_TexFile()
    texFile.read(texPath)

    texInfo = {"isArray": texFile.tex.header.imageCount >
               1, "arrayNum": texFile.tex.header.imageCount}
    if texFile.tex.header.imageCount == 1:
        ddsFile = DDSFile()
        ddsFile.dds = TexToDDS(texFile.tex, 0)
        ddsFile.write(outputPath)
    else:
        digitCount = len(str(texFile.tex.header.imageCount))
        #print("TEX ARRAY FOUND")
        newOutPathRoot = os.path.splitext(outputPath)[0] + " #ARRAY_"
        for i in range(texFile.tex.header.imageCount):
            newOutputPath = f"{newOutPathRoot}{str(i).zfill(digitCount)}.dds"
            ddsFile = DDSFile()
            ddsFile.dds = TexToDDS(texFile.tex, i)
            ddsFile.write(newOutputPath)
            #print(f"Wrote {newOutputPath}")
    return texInfo


def makeTexHeader(texVersion, ddsHeader, imageCount):
    newTexFile = RE_TexFile()
    texHeader = newTexFile.tex.header
    texHeader.version = texVersion
    texHeader.width = ddsHeader.dwWidth
    texHeader.height = ddsHeader.dwHeight
    texHeader.depth = ddsHeader.dwDepth
    texHeader.imageCount = imageCount
    texHeader.mipCount = ddsHeader.dwMipMapCount  # For DMC5/RE2
    texHeader.imageMipHeaderSize = ddsHeader.dwMipMapCount << 4
    #texHeader.imageCount = (ddsHeader.dwMipMapCount << 12) | imageCount
    #print(f"imageCount {imageCount}")
    #print(f"dwMipMapCount {ddsHeader.dwMipMapCount}")
    #print(f"tex image count {texHeader.imageCount}")
    texHeader.formatString = format_ops.buildFormatString(ddsHeader)
    texHeader.format = texenum.formatStringToTexFormatDict[texHeader.formatString]
    cubemap = (ddsHeader.ddsCaps2 & 0x00000200 != 0)*1  # DDSCAPS2_CUBEMAP
    texHeader.cubemapMarker = cubemap * 4
    return newTexFile


def padding(image, ddsSl, capSl, linecount):
    result = b''
    for ix in range(linecount):
        imgData = image[ix*ddsSl:(ix+1)*ddsSl]
        pad = b'\x00'*(capSl-ddsSl)
        result += imgData + pad
    return result


def packageTextures(ddsHeader, ddsList, compress, formatData):
    """Pads and compresses textures aas needed, stores information relative to their size for header generation"""
    compressor = GDeflate()
    miptex = []
    offset = 0
    for dds in ddsList:
        mips = []
        minima = formatData.scanlineMinima
        #print(f"image {tex}")
        for mip in range(ddsHeader.dwMipMapCount):
            x, y = tmath.ruD(ddsHeader.dwWidth, 2 **
                             mip), tmath.ruD(ddsHeader.dwHeight, 2**mip)
            z = tmath.ruD(ddsHeader.dwDepth, 2**mip)
            xcount, ycount = tmath.ruD(
                x, formatData.tx), tmath.ruD(y, formatData.ty)
            mpacketSize = tmath.ruD(format_ops.packetSize, round(
                tmath.product(tmath.dotDivide(formatData.pixelPerPacket, formatData.texelSize))))
            # texelSize = packetTexelPacking and mTexelSize = tx,ty
            bytelen = xcount*ycount*z*mpacketSize
            mipmap = dds.data[offset:offset+bytelen]
            capcomScanline = tmath.ruNX(xcount*mpacketSize, minima)
            ddsScanline = mpacketSize * xcount
            paddedMipmap = padding(mipmap, ddsScanline,
                                   capcomScanline, ycount*z)
            uncompressedSize = capcomScanline * ycount
            if x * y >= 64 and compress:
                try:
                    compressedPaddedMipmap = compressor.compress(
                        paddedMipmap, GDeflateCompressionLevel.BEST_RATIO)
                    s = compressor.get_uncompressed_size(compressedPaddedMipmap)
                    if len(compressedPaddedMipmap) > s:
                        compressedPaddedMipmap = paddedMipmap
                except GDeflateError:
                    compressedPaddedMipmap = paddedMipmap
            else:
                compressedPaddedMipmap = paddedMipmap
            mipData = compressedPaddedMipmap, uncompressedSize, len(
                compressedPaddedMipmap), capcomScanline
            parsel = (mipData, (xcount, ycount))
            mips.append(parsel)
            offset += bytelen
            #assert len(parsel[0]) == bytelen
        miptex.append(mips)
    return miptex


def storeTextures(ddsHeader, texFile, miptex, compress):
    texHeader = texFile.tex.header
    texVersion = texHeader.version
    imageCount = len(miptex)
    mipCount = ddsHeader.dwMipMapCount
    mipstride = 0x10
    baseHeader = (8 if texVersion >= 28 and texVersion != 190820018 else 0) + 0x20
    mipbase = baseHeader + mipstride*imageCount*mipCount
    offset = 0x0
    mipoffset = 0x0
    tex = []
    for texture in miptex:
        mips = []
        mipHeaders = []
        for mip, (mipData, texelCount) in enumerate(texture):
            mipmap, uncompressedSize, compressedSize, scanlineSize = mipData
            tx, ty = texelCount
            mips.append(mipmap)
            mipEntry = MipData()
            mipEntry.mipOffset = mipbase+mipoffset
            mipEntry.uncompressedSize = uncompressedSize
            mipEntry.scanlineLength = scanlineSize
            mipEntry.textureData = mipmap
            mipHeaders.append(mipEntry)
            if compress:
                imageHeader = CompressedImageHeader()
                imageHeader.imageOffset = offset
                imageHeader.imageSize = compressedSize
                texFile.tex.imageHeaderList.append(imageHeader)
            offset += compressedSize
            mipoffset += uncompressedSize
        tex.append(mips)
        texFile.tex.imageMipDataList.append(mipHeaders)
    return texFile


def getTexFileFromDDS(ddsList, texVersion, streamingFlag=False):
    ddsHeader = ddsList[0].header
    isGDeflate = texVersion == VERSION_MHWILDS or texVersion == VERSION_MHWILDS_BETA
    newTexFile = makeTexHeader(texVersion, ddsHeader, len(ddsList))
    formatData = format_ops.packetSizeData(newTexFile.tex.header.formatString)
    miptex = packageTextures(ddsHeader, ddsList, isGDeflate, formatData)
    return storeTextures(ddsHeader, newTexFile, miptex, isGDeflate)


def DDSToTex(ddsPathList, texVersion, outPath, streamingFlag=False):

    if len(ddsPathList) == 1:
        ddsFile = DDSFile()
        ddsFile.read(ddsPathList[0])
        texFile = getTexFileFromDDS([ddsFile.dds], texVersion, streamingFlag)
        texFile.write(outPath)
    else:  # Array texture
        baseHeader = getDDSHeader(ddsPathList[0])
        # Preparse dds files to make sure they have the same height,width,format and mip count as the first
        valid = True
        fixDDSMipList = []  # Force mip counts to match first dds in array
        for ddsPath in ddsPathList:

            currentHeader = getDDSHeader(ddsPath)
            if currentHeader.dwWidth != baseHeader.dwWidth:
                raiseWarning(
                    f"{os.path.split(ddsPath)[1]} - Width does not match first array texture.")
                valid = False
            if currentHeader.dwHeight != baseHeader.dwHeight:
                raiseWarning(
                    f"{os.path.split(ddsPath)[1]} - Height does not match first array texture.")
                valid = False
            if currentHeader.dwMipMapCount != baseHeader.dwMipMapCount:
                raiseWarning(
                    f"{os.path.split(ddsPath)[1]} - Mipmap count does not match first array texture.")
                fixDDSMipList.append(ddsPath)
                #valid = False
            if currentHeader.dx10Header == None:
                raiseWarning(
                    f"{os.path.split(ddsPath)[1]} - DX10 header is missing, save the DDS file using Photoshop with the Intel DDS plugin.")
                valid = False
            else:
                if baseHeader.dx10Header != None:
                    if currentHeader.dx10Header.dxgiFormat != baseHeader.dx10Header.dxgiFormat:
                        raiseWarning(
                            f"{os.path.split(ddsPath)[1]} - DDS format ({dxgienum.DXGIToFormatStringDict.get(currentHeader.dx10Header.dxgiFormat)}) does not match first array texture ({dxgienum.DXGIToFormatStringDict.get(baseHeader.dx10Header.dxgiFormat)}).")
                        valid = False

        if valid:
            if fixDDSMipList != []:
                texConv = Texconv()
                for fixPath in fixDDSMipList:
                    print(f"Fixing mip count on {os.path.split(fixPath)[1]}")
                    texConv.fix_mip_count(fixPath, os.path.split(
                        fixPath)[0], baseHeader.dwMipMapCount)
                unload_texconv()

            ddsList = []
            for ddsPath in ddsPathList:
                ddsFile = DDSFile()
                ddsFile.read(ddsPath)
                ddsList.append(ddsFile.dds)

            texFile = getTexFileFromDDS(ddsList, texVersion, streamingFlag)
            texFile.write(outPath)
