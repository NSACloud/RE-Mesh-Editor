'''Constants for DXGI formats

Notes:
    - Official document for DXGI formats
      https://docs.microsoft.com/en-us/windows/win32/api/dxgiformat/ne-dxgiformat-dxgi_format
    - Official repo for DDS
      https://github.com/microsoft/DirectXTex
'''
from enum import IntEnum


class DXGI_FORMAT(IntEnum):
    """Enum for DDS format."""
    UNKNOWN = 0
    R32G32B32A32_TYPELESS = 1
    R32G32B32A32_FLOAT = 2
    R32G32B32A32_UINT = 3
    R32G32B32A32_SINT = 4
    R32G32B32_TYPELESS = 5
    R32G32B32_FLOAT = 6
    R32G32B32_UINT = 7
    R32G32B32_SINT = 8
    R16G16B16A16_TYPELESS = 9
    R16G16B16A16_FLOAT = 10
    R16G16B16A16_UNORM = 11
    R16G16B16A16_UINT = 12
    R16G16B16A16_SNORM = 13
    R16G16B16A16_SINT = 14
    R32G32_TYPELESS = 15
    R32G32_FLOAT = 16
    R32G32_UINT = 17
    R32G32_SINT = 18
    R32G8X24_TYPELESS = 19
    D32_FLOAT_S8X24_UINT = 20
    R32_FLOAT_X8X24_TYPELESS = 21
    X32_TYPELESS_G8X24_UINT = 22
    R10G10B10A2_TYPELESS = 23
    R10G10B10A2_UNORM = 24
    R10G10B10A2_UINT = 25
    R11G11B10_FLOAT = 26
    R8G8B8A8_TYPELESS = 27
    R8G8B8A8_UNORM = 28
    R8G8B8A8_UNORM_SRGB = 29
    R8G8B8A8_UINT = 30
    R8G8B8A8_SNORM = 31
    R8G8B8A8_SINT = 32
    R16G16_TYPELESS = 33
    R16G16_FLOAT = 34
    R16G16_UNORM = 35
    R16G16_UINT = 36
    R16G16_SNORM = 37
    R16G16_SINT = 38
    R32_TYPELESS = 39
    D32_FLOAT = 40
    R32_FLOAT = 41
    R32_UINT = 42
    R32_SINT = 43
    R24G8_TYPELESS = 44
    D24_UNORM_S8_UINT = 45
    R24_UNORM_X8_TYPELESS = 46
    X24_TYPELESS_G8_UINT = 47
    R8G8_TYPELESS = 48
    R8G8_UNORM = 49
    R8G8_UINT = 50
    R8G8_SNORM = 51
    R8G8_SINT = 52
    R16_TYPELESS = 53
    R16_FLOAT = 54
    D16_UNORM = 55
    R16_UNORM = 56
    R16_UINT = 57
    R16_SNORM = 58
    R16_SINT = 59
    R8_TYPELESS = 60
    R8_UNORM = 61
    R8_UINT = 62
    R8_SNORM = 63
    R8_SINT = 64
    A8_UNORM = 65
    R1_UNORM = 66
    R9G9B9E5_SHAREDEXP = 67
    R8G8_B8G8_UNORM = 68
    G8R8_G8B8_UNORM = 69
    BC1_TYPELESS = 70
    BC1_UNORM = 71
    BC1_UNORM_SRGB = 72
    BC2_TYPELESS = 73
    BC2_UNORM = 74
    BC2_UNORM_SRGB = 75
    BC3_TYPELESS = 76
    BC3_UNORM = 77
    BC3_UNORM_SRGB = 78
    BC4_TYPELESS = 79
    BC4_UNORM = 80
    BC4_SNORM = 81
    BC5_TYPELESS = 82
    BC5_UNORM = 83
    BC5_SNORM = 84
    B5G6R5_UNORM = 85
    B5G5R5A1_UNORM = 86
    B8G8R8A8_UNORM = 87
    B8G8R8X8_UNORM = 88
    R10G10B10_XR_BIAS_A2_UNORM = 89
    B8G8R8A8_TYPELESS = 90
    B8G8R8A8_UNORM_SRGB = 91
    B8G8R8X8_TYPELESS = 92
    B8G8R8X8_UNORM_SRGB = 93
    BC6H_TYPELESS = 94
    BC6H_UF16 = 95
    BC6H_SF16 = 96
    BC7_TYPELESS = 97
    BC7_UNORM = 98
    BC7_UNORM_SRGB = 99
    AYUV = 100
    Y410 = 101
    Y416 = 102
    NV12 = 103
    P010 = 104
    P016 = 105
    OPAQUE_420 = 106
    YUY2 = 107
    Y210 = 108
    Y216 = 109
    NV11 = 110
    AI44 = 111
    IA44 = 112
    P8 = 113
    A8P8 = 114
    B4G4R4A4_UNORM = 115
    P208 = 130
    V208 = 131
    V408 = 132
    A4B4G4R4_UNORM = 191

    # non-official formats
    ASTC_4X4_TYPELESS = 133
    ASTC_4X4_UNORM = 134

    @classmethod
    def is_valid_format(cls, fmt_name):
        return fmt_name in cls._member_names_

    @staticmethod
    def get_signed(fmt):
        name = fmt.name
        name_split = name.split("_")
        num_type = name_split[-1]

        new_num_types = {
            "UNORM": "SNORM",
            "UINT": "SINT"
        }

        if num_type in new_num_types:
            name = "_".join(name_split[:-1] + new_num_types[num_type])
        else:
            return fmt

        if DXGI_FORMAT.is_valid_format(name):
            return DXGI_FORMAT[name]
        else:
            return fmt


def int_to_byte(n):
    return n.to_bytes(1, byteorder="little")


# For detecting DXGI from fourCC
FOURCC_TO_DXGI = [
    [[b'DXT1'], DXGI_FORMAT.BC1_UNORM],
    [[b'DXT2', b'DXT3'], DXGI_FORMAT.BC2_UNORM],
    [[b'DXT4', b'DXT5'], DXGI_FORMAT.BC3_UNORM],
    [[b'ATI1', b'BC4U', b'3DC1'], DXGI_FORMAT.BC4_UNORM],
    [[b'ATI2', b'BC5U', b'3DC2'], DXGI_FORMAT.BC5_UNORM],
    [[b'BC4S'], DXGI_FORMAT.BC4_SNORM],
    [[b'BC5S'], DXGI_FORMAT.BC5_SNORM],
    [[b'BC6H'], DXGI_FORMAT.BC6H_UF16],
    [[b'BC7L', b'BC7'], DXGI_FORMAT.BC7_UNORM],
    [[b'RGBG'], DXGI_FORMAT.R8G8_B8G8_UNORM],
    [[b'GRGB'], DXGI_FORMAT.G8R8_G8B8_UNORM],
    [[b'YUY2', b'UYVY'], DXGI_FORMAT.YUY2],
    [[int_to_byte(36)], DXGI_FORMAT.R16G16B16A16_UNORM],
    [[int_to_byte(110)], DXGI_FORMAT.R16G16B16A16_SNORM],
    [[int_to_byte(111)], DXGI_FORMAT.R16_FLOAT],
    [[int_to_byte(112)], DXGI_FORMAT.R16G16_FLOAT],
    [[int_to_byte(113)], DXGI_FORMAT.R16G16B16A16_FLOAT],
    [[int_to_byte(114)], DXGI_FORMAT.R32_FLOAT],
    [[int_to_byte(115)], DXGI_FORMAT.R32G32_FLOAT],
    [[int_to_byte(116)], DXGI_FORMAT.R32G32B32A32_FLOAT]
]


# Used to detect DXGI format from DDS_PIXELFORMAT
BITMASK_TO_DXGI = [
    [[0x00ff0000, 0x0000ff00, 0x000000ff, 0xff000000], DXGI_FORMAT.B8G8R8A8_UNORM],
    [[0x00ff0000, 0x0000ff00, 0x000000ff, 0], DXGI_FORMAT.B8G8R8X8_UNORM],
    [[0x000000ff, 0x0000ff00, 0x00ff0000, 0xff000000], DXGI_FORMAT.R8G8B8A8_UNORM],
    [[0x3ff00000, 0x000ffc00, 0x000003ff, 0xc0000000], DXGI_FORMAT.R10G10B10A2_UNORM],
    [[0x0000ffff, 0xffff0000, 0, 0], DXGI_FORMAT.R16G16_UNORM],
    [[0xffffffff, 0, 0, 0], DXGI_FORMAT.R32_FLOAT],
    [[0x7c00, 0x03e0, 0x001f, 0x8000], DXGI_FORMAT.B5G5R5A1_UNORM],
    [[0xf800, 0x07e0, 0x001f, 0], DXGI_FORMAT.B5G6R5_UNORM],
    [[0x0f00, 0x00f0, 0x000f, 0xf000], DXGI_FORMAT.B4G4R4A4_UNORM],
    [[0x00ff, 0, 0, 0xff00], DXGI_FORMAT.R8G8_UNORM],
    [[0xffff, 0, 0, 0], DXGI_FORMAT.R16_UNORM],
    [[0xff, 0, 0, 0], DXGI_FORMAT.R8_UNORM],
    [[0, 0, 0, 0xff], DXGI_FORMAT.A8_UNORM]
]
