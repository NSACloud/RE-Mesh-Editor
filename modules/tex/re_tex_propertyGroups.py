#Author: NSA Cloud
import bpy
from bpy.props import (StringProperty,
					   BoolProperty,
					   IntProperty,
					   FloatProperty,
					   FloatVectorProperty,
					   EnumProperty,
					   PointerProperty,
					   CollectionProperty,
					   )



class PNGConversionEntryPropertyGroup(bpy.types.PropertyGroup):
	fileName: StringProperty(
		name = "File Name",
		description = "",
		default = "pngFile.png",
		)
	ddsCompressionType: EnumProperty(
		name = "Compression",
		description = "", 
		items=[ ("BC1_UNORM", "BC1 Linear", "Low quality compression, 1 bit alpha. Smaller file size. Use with non Albedo textures"),
				("BC1_UNORM_SRGB", "BC1 sRGB", "Low quality compression, 1 bit alpha. Smaller file size. Use with Albedo textures"),
				("BC7_UNORM", "BC7 Linear (Recommended)", "High quality compression, full alpha support. Use with non Albedo textures"),
				("BC7_UNORM_SRGB", "BC7 sRGB (Recommended)", "High quality compression, full alpha support. Use with Albedo textures"),
				("R8G8B8A8_UNORM", "R8G8B8A8 Linear", "Large file size. Use this for lossless non Albedo textures"),
				("R8G8B8A8_UNORM_SRGB", "R8G8B8A8 sRGB", "Large file size. Use for lossless Albedo textures"),
			  ],
		default = "BC7_UNORM",
		)

class TEX_UL_PNGConversionList(bpy.types.UIList):
	
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
		layout.label(text = item.fileName)
		layout.prop(item,"ddsCompressionType")
	def invoke(self, context, event):
		return {'PASS_THROUGH'}
	