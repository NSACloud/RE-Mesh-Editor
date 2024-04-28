#Author: NSA Cloud
#Credit to Asterisk Ampersand, code borrowed from Tex Chopper
from ..dds.file_dds import DDS,DX10_Header,DDSFile
from .file_re_tex import RE_TexFile,Tex,MipData
import math
import re

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

formatStringToDXGIDict = {
	"UNKNOWN":0,
	"R32G32B32A32TYPELESS":1,
	"R32G32B32A32FLOAT":2,
	"R32G32B32A32UINT":3,
	"R32G32B32A32SINT":4,
	"R32G32B32TYPELESS":5,
	"R32G32B32FLOAT":6,
	"R32G32B32UINT":7,
	"R32G32B32SINT":8,
	"R16G16B16A16TYPELESS":9,
	"R16G16B16A16FLOAT":10,
	"R16G16B16A16UNORM":11,
	"R16G16B16A16UINT":12,
	"R16G16B16A16SNORM":13,
	"R16G16B16A16SINT":14,
	"R32G32TYPELESS":15,
	"R32G32FLOAT":16,
	"R32G32UINT":17,
	"R32G32SINT":18,
	"R32G8X24TYPELESS":19,
	"D32FLOATS8X24UINT":20,
	"R32FLOATX8X24TYPELESS":21,
	"X32TYPELESSG8X24UINT":22,
	"R10G10B10A2TYPELESS":23,
	"R10G10B10A2UNORM":24,
	"R10G10B10A2UINT":25,
	"R11G11B10FLOAT":26,
	"R8G8B8A8TYPELESS":27,
	"R8G8B8A8UNORM":28,
	"R8G8B8A8UNORMSRGB":29,
	"R8G8B8A8UINT":30,
	"R8G8B8A8SNORM":31,
	"R8G8B8A8SINT":32,
	"R16G16TYPELESS":33,
	"R16G16FLOAT":34,
	"R16G16UNORM":35,
	"R16G16UINT":36,
	"R16G16SNORM":37,
	"R16G16SINT":38,
	"R32TYPELESS":39,
	"D32FLOAT":40,
	"R32FLOAT":41,
	"R32UINT":42,
	"R32SINT":43,
	"R24G8TYPELESS":44,
	"D24UNORMS8UINT":45,
	"R24UNORMX8TYPELESS":46,
	"X24TYPELESSG8UINT":47,
	"R8G8TYPELESS":48,
	"R8G8UNORM":49,
	"R8G8UINT":50,
	"R8G8SNORM":51,
	"R8G8SINT":52,
	"R16TYPELESS":53,
	"R16FLOAT":54,
	"D16UNORM":55,
	"R16UNORM":56,
	"R16UINT":57,
	"R16SNORM":58,
	"R16SINT":59,
	"R8TYPELESS":60,
	"R8UNORM":61,
	"R8UINT":62,
	"R8SNORM":63,
	"R8SINT":64,
	"A8UNORM":65,
	"R1UNORM":66,
	"R9G9B9E5SHAREDEXP":67,
	"R8G8B8G8UNORM":68,
	"G8R8G8B8UNORM":69,
	"BC1TYPELESS":70,
	"BC1UNORM":71,
	"BC1UNORMSRGB":72,
	"BC2TYPELESS":73,
	"BC2UNORM":74,
	"BC2UNORMSRGB":75,
	"BC3TYPELESS":76,
	"BC3UNORM":77,
	"BC3UNORMSRGB":78,
	"BC4TYPELESS":79,
	"BC4UNORM":80,
	"BC4SNORM":81,
	"BC5TYPELESS":82,
	"BC5UNORM":83,
	"BC5SNORM":84,
	"B5G6R5UNORM":85,
	"B5G5R5A1UNORM":86,
	"B8G8R8A8UNORM":87,
	"B8G8R8X8UNORM":88,
	"R10G10B10XRBIASA2UNORM":89,
	"B8G8R8A8TYPELESS":90,
	"B8G8R8A8UNORMSRGB":91,
	"B8G8R8X8TYPELESS":92,
	"B8G8R8X8UNORMSRGB":93,
	"BC6HTYPELESS":94,
	"BC6HUF16":95,
	"BC6HSF16":96,
	"BC7TYPELESS":97,
	"BC7UNORM":98,
	"BC7UNORMSRGB":99,
	"AYUV":100,
	"Y410":101,
	"Y416":102,
	"NV12":103,
	"P010":104,
	"P016":105,
	"DXGIFORMAT420OPAQUE":106,
	"YUY2":107,
	"Y210":108,
	"Y216":109,
	"NV11":110,
	"AI44":111,
	"IA44":112,
	"P8":113,
	"A8P8":114,
	"B4G4R4A4UNORM":115,
	"P208":130,
	"V208":131,
	"V408":132,
	"FORCEUINT":0xffffffff,
	}
DXGIToFormatStringDict = {
	1: 'R32G32B32A32TYPELESS',
	2: 'R32G32B32A32FLOAT',
	3: 'R32G32B32A32UINT',
	4: 'R32G32B32A32SINT',
	5: 'R32G32B32TYPELESS',
	6: 'R32G32B32FLOAT',
	7: 'R32G32B32UINT',
	8: 'R32G32B32SINT',
	9: 'R16G16B16A16TYPELESS',
	10: 'R16G16B16A16FLOAT',
	11: 'R16G16B16A16UNORM',
	12: 'R16G16B16A16UINT',
	13: 'R16G16B16A16SNORM',
	14: 'R16G16B16A16SINT',
	15: 'R32G32TYPELESS',
	16: 'R32G32FLOAT',
	17: 'R32G32UINT',
	18: 'R32G32SINT',
	19: 'R32G8X24TYPELESS',
	20: 'D32FLOATS8X24UINT',
	21: 'R32FLOATX8X24TYPELESS',
	22: 'X32TYPELESSG8X24UINT',
	23: 'R10G10B10A2TYPELESS',
	24: 'R10G10B10A2UNORM',
	25: 'R10G10B10A2UINT',
	26: 'R11G11B10FLOAT',
	27: 'R8G8B8A8TYPELESS',
	28: 'R8G8B8A8UNORM',
	29: 'R8G8B8A8UNORMSRGB',
	30: 'R8G8B8A8UINT',
	31: 'R8G8B8A8SNORM',
	32: 'R8G8B8A8SINT',
	33: 'R16G16TYPELESS',
	34: 'R16G16FLOAT',
	35: 'R16G16UNORM',
	36: 'R16G16UINT',
	37: 'R16G16SNORM',
	38: 'R16G16SINT',
	39: 'R32TYPELESS',
	40: 'D32FLOAT',
	41: 'R32FLOAT',
	42: 'R32UINT',
	43: 'R32SINT',
	44: 'R24G8TYPELESS',
	45: 'D24UNORMS8UINT',
	46: 'R24UNORMX8TYPELESS',
	47: 'X24TYPELESSG8UINT',
	48: 'R8G8TYPELESS',
	49: 'R8G8UNORM',
	50: 'R8G8UINT',
	51: 'R8G8SNORM',
	52: 'R8G8SINT',
	53: 'R16TYPELESS',
	54: 'R16FLOAT',
	55: 'D16UNORM',
	56: 'R16UNORM',
	57: 'R16UINT',
	58: 'R16SNORM',
	59: 'R16SINT',
	60: 'R8TYPELESS',
	61: 'R8UNORM',
	62: 'R8UINT',
	63: 'R8SNORM',
	64: 'R8SINT',
	65: 'A8UNORM',
	66: 'R1UNORM',
	67: 'R9G9B9E5SHAREDEXP',
	68: 'R8G8B8G8UNORM',
	69: 'G8R8G8B8UNORM',
	70: 'BC1TYPELESS',
	71: 'BC1UNORM',
	72: 'BC1UNORMSRGB',
	73: 'BC2TYPELESS',
	74: 'BC2UNORM',
	75: 'BC2UNORMSRGB',
	76: 'BC3TYPELESS',
	77: 'BC3UNORM',
	78: 'BC3UNORMSRGB',
	79: 'BC4TYPELESS',
	80: 'BC4UNORM',
	81: 'BC4SNORM',
	82: 'BC5TYPELESS',
	83: 'BC5UNORM',
	84: 'BC5SNORM',
	85: 'B5G6R5UNORM',
	86: 'B5G5R5A1UNORM',
	87: 'B8G8R8A8UNORM',
	88: 'B8G8R8X8UNORM',
	89: 'R10G10B10XRBIASA2UNORM',
	90: 'B8G8R8A8TYPELESS',
	91: 'B8G8R8A8UNORMSRGB',
	92: 'B8G8R8X8TYPELESS',
	93: 'B8G8R8X8UNORMSRGB',
	94: 'BC6HTYPELESS',
	95: 'BC6HUF16',
	96: 'BC6HSF16',
	97: 'BC7TYPELESS',
	98: 'BC7UNORM',
	99: 'BC7UNORMSRGB',
	100: 'AYUV',
	101: 'Y410',
	102: 'Y416',
	103: 'NV12',
	104: 'P010',
	105: 'P016',
	106: 'DXGIFORMAT420OPAQUE',
	107: 'YUY2',
	108: 'Y210',
	109: 'Y216',
	110: 'NV11',
	111: 'AI44',
	112: 'IA44',
	113: 'P8',
	114: 'A8P8',
	115: 'B4G4R4A4UNORM',
	130: 'P208',
	131: 'V208',
	132: 'V408',
	4294967295: 'FORCEUINT'}
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
formatStringToTexFormatDict = {
	'R32G32B32A32TYPELESS': 1,
	'R32G32B32A32FLOAT': 2,
	'R32G32B32A32UINT': 3,
	'R32G32B32A32SINT': 4,
	'R32G32B32TYPELESS': 5,
	'R32G32B32FLOAT': 6,
	'R32G32B32UINT': 7,
	'R32G32B32SINT': 8,
	'R16G16B16A16TYPELESS': 9,
	'R16G16B16A16FLOAT': 10,
	'R16G16B16A16UNORM': 11,
	'R16G16B16A16UINT': 12,
	'R16G16B16A16SNORM': 13,
	'R16G16B16A16SINT': 14,
	'R32G32TYPELESS': 15,
	'R32G32FLOAT': 16,
	'R32G32UINT': 17,
	'R32G32SINT': 18,
	'R32G8X24TYPELESS': 19,
	'D32FLOATS8X24UINT': 20,
	'R32FLOATX8X24TYPELESS': 21,
	'X32TYPELESSG8X24UINT': 22,
	'R10G10B10A2TYPELESS': 23,
	'R10G10B10A2UNORM': 24,
	'R10G10B10A2UINT': 25,
	'R11G11B10FLOAT': 26,
	'R8G8B8A8TYPELESS': 27,
	'R8G8B8A8UNORM': 28,
	'R8G8B8A8UNORMSRGB': 29,
	'R8G8B8A8UINT': 30,
	'R8G8B8A8SNORM': 31,
	'R8G8B8A8SINT': 32,
	'R16G16TYPELESS': 33,
	'R16G16FLOAT': 34,
	'R16G16UNORM': 35,
	'R16G16UINT': 36,
	'R16G16SNORM': 37,
	'R16G16SINT': 38,
	'R32TYPELESS': 39,
	'D32FLOAT': 40,
	'R32FLOAT': 41,
	'R32UINT': 42,
	'R32SINT': 43,
	'R24G8TYPELESS': 44,
	'D24UNORMS8UINT': 45,
	'R24UNORMX8TYPELESS': 46,
	'X24TYPELESSG8UINT': 47,
	'R8G8TYPELESS': 48,
	'R8G8UNORM': 49,
	'R8G8UINT': 50,
	'R8G8SNORM': 51,
	'R8G8SINT': 52,
	'R16TYPELESS': 53,
	'R16FLOAT': 54,
	'D16UNORM': 55,
	'R16UNORM': 56,
	'R16UINT': 57,
	'R16SNORM': 58,
	'R16SINT': 59,
	'R8TYPELESS': 60,
	'R8UNORM': 61,
	'R8UINT': 62,
	'R8SNORM': 63,
	'R8SINT': 64,
	'A8UNORM': 65,
	'R1UNORM': 66,
	'R9G9B9E5SHAREDEXP': 67,
	'R8G8B8G8UNORM': 68,
	'G8R8G8B8UNORM': 69,
	'BC1TYPELESS': 70,
	'BC1UNORM': 71,
	'BC1UNORMSRGB': 72,
	'BC2TYPELESS': 73,
	'BC2UNORM': 74,
	'BC2UNORMSRGB': 75,
	'BC3TYPELESS': 76,
	'BC3UNORM': 77,
	'BC3UNORMSRGB': 78,
	'BC4TYPELESS': 79,
	'BC4UNORM': 80,
	'BC4SNORM': 81,
	'BC5TYPELESS': 82,
	'BC5UNORM': 83,
	'BC5SNORM': 84,
	'B5G6R5UNORM': 85,
	'B5G5R5A1UNORM': 86,
	'B8G8R8A8UNORM': 87,
	'B8G8R8X8UNORM': 88,
	'R10G10B10XRBIASA2UNORM': 89,
	'B8G8R8A8TYPELESS': 90,
	'B8G8R8A8UNORMSRGB': 91,
	'B8G8R8X8TYPELESS': 92,
	'B8G8R8X8UNORMSRGB': 93,
	'BC6HTYPELESS': 94,
	'BC6HUF16': 95,
	'BC6HSF16': 96,
	'BC7TYPELESS': 97,
	'BC7UNORM': 98,
	'BC7UNORMSRGB': 99,
	'VIAEXTENSION': 1024,
	'ASTC4X4TYPELESS': 1025,
	'ASTC4X4UNORM': 1026,
	'ASTC4X4UNORMSRGB': 1027,
	'ASTC5X4TYPELESS': 1028,
	'ASTC5X4UNORM': 1029,
	'ASTC5X4UNORMSRGB': 1030,
	'ASTC5X5TYPELESS': 1031,
	'ASTC5X5UNORM': 1032,
	'ASTC5X5UNORMSRGB': 1033,
	'ASTC6X5TYPELESS': 1034,
	'ASTC6X5UNORM': 1035,
	'ASTC6X5UNORMSRGB': 1036,
	'ASTC6X6TYPELESS': 1037,
	'ASTC6X6UNORM': 1038,
	'ASTC6X6UNORMSRGB': 1039,
	'ASTC8X5TYPELESS': 1040,
	'ASTC8X5UNORM': 1041,
}
def TexToDDS(tex):
	dds = DDS()
	dds.header.dwSize = 124
	dds.header.dwFlags = 0x00000001 | 0x00000002 | 0x00000004 | 0x00001000 | 0x00020000 | 0x00080000 #DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT | DDSD_MIPMAPCOUNT | DDSD_LINEARSIZE
	dds.header.dwHeight = tex.header.height
	dds.header.dwWidth = tex.header.width
	dds.header.dwPitchOrLinearSize = (dds.header.dwWidth * dds.header.dwHeight * ddsBpps[texFormatToDXGIStringDict[tex.header.format]]) // 8
	dds.header.dwDepth = tex.header.depth
	dds.header.dwMipMapCount = tex.header.mipCount
	dds.header.ddpfPixelFormat.dwSize = 32
	dds.header.ddpfPixelFormat.dwFlags = 0x4#DDPF_FOURCC
	dds.header.ddpfPixelFormat.dwFourCC = 808540228#DX10
	dds.header.ddpfPixelFormat.dwRGBBitCount = 0
	dds.header.ddpfPixelFormat.dwRBitMask = 0
	dds.header.ddpfPixelFormat.dwGBitMask = 0
	dds.header.ddpfPixelFormat.dwBBitMask = 0
	dds.header.ddpfPixelFormat.dwABitMask = 0
	dds.header.ddsCaps1 = 0x00001000 | 0x00400000#DDSCAPS_TEXTURE | DDSCAPS_MIPMAP
	if tex.header.cubemapMarker != 0:
		dds.header.ddsCaps1 = dds.header.ddsCaps1 | 0x00000008#DDSCAPS_COMPLEX
		dds.header.ddsCaps2 = 0x00000200 | 0x00000400 | 0x00000800 | 0x00001000 | 0x00002000 | 0x00004000 | 0x00008000#DDSCAPS2_CUBEMAP | DDSCAPS2_CUBEMAP_POSITIVEX | DDSCAPS2_CUBEMAP_NEGATIVEX | DDSCAPS2_CUBEMAP_POSITIVEY | DDSCAPS2_CUBEMAP_NEGATIVEY | DDSCAPS2_CUBEMAP_POSITIVEZ | DDSCAPS2_CUBEMAP_NEGATIVEZ
	else:
		dds.header.ddsCaps2 = 0
	dds.header.ddsCaps3 = 0
	dds.header.ddsCaps4 = 0
	dds.header.dwReserved2 = 0
	
	dds.header.dx10Header = DX10_Header()
	dds.header.dx10Header.dxgiFormat = formatStringToDXGIDict[texFormatToDXGIStringDict[tex.header.format]]
	dds.header.dx10Header.resourceDimension = 3#D3D10_RESOURCE_DIMENSION_TEXTURE2D
	if tex.header.cubemapMarker != 0:
		dds.header.dx10Header.arraySize = tex.header.imageCount // 6
	else:
		dds.header.dx10Header.arraySize = tex.header.imageCount
	dds.header.dx10Header.miscFlags2 = 0
	dds.data = tex.GetTextureData()
	return dds

def convertTexFileToDDS(texPath,outputPath):
	texFile = RE_TexFile()
	texFile.read(texPath)
	ddsFile = DDSFile()
	ddsFile.dds = TexToDDS(texFile.tex)
	ddsFile.write(outputPath)



	
#DDS To Tex
packetSize = 16
ruD = lambda x,y: (x+y-1)//y
DXT1 = "DXT1"  # 0x31545844
DXT2 = "DXT2"  # 0x32545844
DXT3 = "DXT3"  # 0x33545844
DXT4 = "DXT4"  # 0x34545844
DXT5 = "DXT5"  # 0x35545844
ATI1 = "ATI1"
ATI2 = "ATI2"
BC4U = "BC4U"
BC4S = "BC4S"
BC5U = "BC5U"
BC5S = "BC5S"
DX10 = "DX10"  # 0x30315844
CCCC = "CCCC"
NULL = "\x00\x00\x00\x00"
legacyMapping = {
    DXT1: "BC1UNORM",
    DXT2: "BC2UNORM",
    DXT3: "BC2UNORMSRGB",
    DXT4: "BC3UNORM",
    DXT5: "BC3UNORMSRGB",
    ATI1: "BC4UNORM",
    ATI2: "BC5UNORM",
    BC4U: "BC4UNORM",
    BC4S: "BC4SNORM",
    BC5U: "BC5UNORM",
    BC5S: "BC5SNORM",

}
def product(listing):
    cur = 1
    for element in listing:
        cur *= element
    return cur

def bitCount(int32):
    return sum(((int32 >> i) & 1 for i in range(32)))
def dotDivide(vec1,vec2):
    return tuple([ruD(vl,vr) for vl,vr in zip(vec1,vec2)])
def buildFormatString(header):
    pixelFormat = header.ddpfPixelFormat
    fourCC = pixelFormat.dwFourCC
    if fourCC == 808540228:#DX10
        return DXGIToFormatStringDict[header.dx10Header.dxgiFormat]
    elif fourCC in legacyMapping:
        return legacyMapping[fourCC].replace("_", "")
    else:
        Rbc = bitCount(pixelFormat.dwRBitMask)
        Gbc = bitCount(pixelFormat.dwGBitMask)
        Bbc = bitCount(pixelFormat.dwBBitMask)
        Abc = bitCount(pixelFormat.dwABitMask)
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
BCRegex = re.compile("(BC[0-9]+H?)(.*)")
RGBRegex = re.compile("([RGBAX][0-9]+)?"*5+"(.*)")
RGBChannel = re.compile("([RGBAX])([0-9]+)")	
def formatParse(formatString):
    bc = BCRegex.match(formatString)
    if bc:
        BC,f = bc.groups()
        return (BC,4,4,f)
    rgb = RGBRegex.match(formatString)
    if rgb:
        channels = []
        bitlen = 0
        for g in rgb.groups()[:-1]:
            if g:
                c,s = RGBChannel.match(str(g)).groups()            
                channels.append((c,int(s)))
                bitlen += int(s)
        bytelen = (bitlen + 7)//8
        xpacketlen = 16//bytelen
        ypacketlen = 1
        return (channels,1,ypacketlen,rgb.groups()[-1])
    raise ValueError("Unparseable Format Error")
def getBCBPP(BC):
    BC = BC.upper()
    if "BC1" in BC:
        return 8
    if "BC2" in BC:
        return 16
    if "BC3" in BC:
        return 16
    if "BC4" in BC:
        return 8
    if "BC5" in BC:
        return 16
    if "BC6H" in BC:
        return 16
    if "BC7" in BC:
        return 16
def formatTexelParse(formatString):
   
    bc = BCRegex.match(formatString)
    if bc:
        BC,f = bc.groups()
        hcount = 16//getBCBPP(BC)
        return (BC,4*hcount,4,f)
    rgb = RGBRegex.match(formatString)
    if rgb:
        channels = []
        bitlen = 0
        for g in rgb.groups()[:-1]:
            if g:
                c,s = RGBChannel.match(str(g)).groups()            
                channels.append((c,int(s)))
                bitlen += int(s)
        bytelen = (bitlen + 7)//8
        xpacketlen = 16//bytelen
        ypacketlen = 1
        return (channels,xpacketlen,ypacketlen,rgb.groups()[-1])
    raise ValueError("Unparseable Format Error")

def getTexFileFromDDS(dds,texVersion,streamingFlag = False):
	ddsHeader = dds.header
	
	newTexFile = RE_TexFile()
	texHeader = newTexFile.tex.header
	texHeader.version = texVersion
	texHeader.width = ddsHeader.dwWidth
	texHeader.height = ddsHeader.dwHeight
	texHeader.depth = 1
	
	cubemap = (ddsHeader.ddsCaps2 & 0x00000200 != 0)*1#DDSCAPS2_CUBEMAP
	
	imageCount = 1 if not ddsHeader.ddpfPixelFormat.dwFourCC == 808540228 else ddsHeader.dx10Header.arraySize * (6 if cubemap else 1)
	texHeader.imageCount = imageCount
	texHeader.imageMipHeaderSize = ddsHeader.dwMipMapCount * 16
	#texHeader.imageCount = (ddsHeader.dwMipMapCount << 12) | imageCount
	#print(f"imageCount {imageCount}")
	#print(f"dwMipMapCount {ddsHeader.dwMipMapCount}")
	#print(f"tex image count {texHeader.imageCount}")
	formatString = buildFormatString(ddsHeader)
	texHeader.format = formatStringToTexFormatDict[formatString]
	texHeader.cubemapMarker = cubemap * 4
	_, mtx, mty, _ = formatParse(formatString)
	_, tx, ty, _ = formatTexelParse(formatString)
	_, ptx, pty, _ = formatTexelParse(formatString)
	
	texelSize = (tx, ty)
	mTexelSize = (mtx, mty)
	packetTexelSize = ptx, pty
	
	superBlockSize = (0,0)
	
	miptex = []
	offset = 0
	for tex in range(imageCount):
		mips = []
		for mip in range(ddsHeader.dwMipMapCount):
			xcount, ycount = ruD(
				ruD(ddsHeader.dwWidth, 2**mip), mtx), ruD(ruD(ddsHeader.dwHeight, 2**mip), mty)
			mpacketSize = ruD(packetSize, round(
				product(dotDivide(texelSize, mTexelSize))))
			bytelen = xcount*ycount*mpacketSize
			parsel = (dds.data[offset:offset+bytelen], (xcount, ycount))
			mips.append(parsel)
			offset += bytelen
			assert len(parsel[0]) == bytelen
		miptex.append(mips)
	
	stride = 0x10
	base = (8 if texVersion >= 28 else 0) + 0x20 + stride*imageCount*ddsHeader.dwMipMapCount
	tex = []
	headers = []
	for texture in miptex:
		#mips = []
		textureHeaders = []
		imageMipDataListEntry = []
		for mip, (data, texelCount) in enumerate(texture):
			correction = 1 + 1 *("BC1" in formatString or "BC4" in formatString)
			uncompressedSize = len(data)
			tx, ty = texelCount
			mpacketSize = ruD(packetSize, round(
				product(dotDivide(texelSize, mTexelSize))))
			scanlineSize = tx*mpacketSize
			mipEntry = MipData()
			mipEntry.mipOffset = base
			mipEntry.uncompressedSize = uncompressedSize
			mipEntry.compressedSize = scanlineSize
			mipEntry.textureData = data
			base += uncompressedSize
			imageMipDataListEntry.append(mipEntry)
		newTexFile.tex.imageMipDataList.append(imageMipDataListEntry)
	
	return newTexFile

def DDSToTex(ddsPath,texVersion,outPath,streamingFlag = False):
	ddsFile = DDSFile()
	ddsFile.read(ddsPath)
	texFile = getTexFileFromDDS(ddsFile.dds,texVersion,streamingFlag)
	texFile.write(outPath)