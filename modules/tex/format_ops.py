# -*- coding: utf-8 -*-
"""
Created on Fri Mar  7 18:43:54 2025

@author: Asterisk
"""
import re
from .enums.legacy_mappings import legacyMapping
from .enums import dxgi_format_enum as dxgienum
from .enums import scanline_minima as scMin
from . import tex_math as tmath


AstcRegex = re.compile("(ASTC)([0-9]+)X([0-9]+)(.*)")
BCRegex = re.compile("(BC[0-9]+H?)(.*)")
RGBRegex = re.compile("([RGBAX][0-9]+)?"*5+"(.*)")
RGBChannel = re.compile("([RGBAX])([0-9]+)")

#Texture packets in dds by standard are 16 bytes long
packetSize = 16

def getBCBPP(BC):
    BC = BC.upper()
    #print("FE: "+BC)
    if "BC1" in BC: return 8
    if "BC2" in BC: return 16
    if "BC3" in BC: return 16
    if "BC4" in BC: return 8
    if "BC5" in BC: return 16
    if "BC6H" in BC: return 16
    if "BC7" in BC: return 16

def decomposeRGBFormat(rgb):
    channels = []
    bitlen = 0
    for g in rgb.groups()[:-1]:
        if g:
            c,s = RGBChannel.match(str(g)).groups()            
            channels.append((c,int(s)))
            bitlen += int(s)
    return bitlen,channels


class FormatData():
    """ Container for Format Texel Information 
    Members: 
        tx : Int
            Number of horizontal pixels per texel. Texel x dimension.
        ty : Int
            Number of vertical pixels per texel. Texel y dimension.
        bitlen : Int
            Number of bits a texel occupies.
        bytelen : Int
            Number of bytes required to store a single texel.
            If a texel bitlength is not byte aligned, then it rounds up.
        formatBase : Str
            Specifies the format family (ASTC, BC, R/G/B/A)
        formatColor : 
            Specifies the color format (Eg: BC1Unorm -> Unorm)
        scanlineMinima :
            Minimum size in bytes for a capcom scanline of the format.
    """
    def __init__(self,formatString):
        tx,ty,bl,Bl,fb,fs = _packetSizeData(formatString)
        fmin = scanlineMinima(formatString)
        self.tx = tx
        self.ty = ty
        self.bitlen = bl
        self.bytelen = Bl
        self.formatBase = fb
        self.formatColor = fs
        self.scanlineMinima = fmin
    @property
    def texelSize(self):
        return self.tx,self.ty
    @property
    def pixelPerPacket(self):
        #(packetSize*8)//bitlen*texelX,texelY
        return packetSize//self.bytelen*self.tx,self.ty
    
def _packetSizeData(formatString):
    '''X Pixel Count, Y Pixel Count, Bitcount, Bytecount'''
    astc = AstcRegex.match(formatString)
    if astc:
        ASTC,bx,by,f = astc.groups()
        return bx,by,128,128//8,ASTC,f
    bc = BCRegex.match(formatString)
    if bc:
        BC,f = bc.groups()
        lbytes = getBCBPP(BC)
        return 4,4,lbytes*8,lbytes,BC,f
    rgb = RGBRegex.match(formatString)
    if rgb:
        bitlen,channels = decomposeRGBFormat(rgb)
        bytelen = (bitlen + 7)//8
        return 1,1,bitlen,bytelen,channels,rgb.groups()[-1]

def packetSizeData(formatString):
    return FormatData(formatString)

def scanlineMinima(formatString):
    '''X Pixel Count, Y Pixel Count, Bitcount, Bytecount'''
    return scMin.formatScanlineMinima.get(formatString,256)

def buildFormatString(header):
    pixelFormat = header.ddpfPixelFormat
    fourCC = pixelFormat.dwFourCC
    if fourCC == 808540228:#DX10
        return dxgienum.DXGIToFormatStringDict[header.dx10Header.dxgiFormat]
    elif fourCC in legacyMapping:
        return legacyMapping[fourCC].replace("_", "")
    else:
        Rbc = tmath.bitCount(pixelFormat.dwRBitMask)
        Gbc = tmath.bitCount(pixelFormat.dwGBitMask)
        Bbc = tmath.bitCount(pixelFormat.dwBBitMask)
        Abc = tmath.bitCount(pixelFormat.dwABitMask)
        R = (pixelFormat.dwRBitMask, "R", "%d" % Rbc)
        G = (pixelFormat.dwGBitMask, "G", "%d" % Gbc)
        B = (pixelFormat.dwBBitMask, "B", "%d" % Bbc)
        A = (pixelFormat.dwABitMask, "A", "%d" % Abc)
        RGBA = ''.join([channel_code + bit_count for mask,
                        channel_code, bit_count in sorted([R, G, B, A]) if mask])
        knownBits = sum([Rbc, Gbc, Bbc, Abc])
        if knownBits < pixelFormat.dwRGBBitCount:
            fill = "A" if RGBA[0] == "R" else "X"
            RGBA += "%s%d" % (fill, pixelFormat.dwRGBBitCount - knownBits)
        return RGBA+"UNORM"