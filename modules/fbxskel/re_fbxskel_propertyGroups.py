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



class ToggleStringPropertyGroup(bpy.types.PropertyGroup):
	enabled: BoolProperty(
		name="",
		description = "",
		default = True
	)
	name: StringProperty(
        name="",
		description = "",
	)
	
	
class FBXSKEL_UL_ObjectCheckList(bpy.types.UIList):
	
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
		layout.prop(item,"enabled")
		layout.label(text = item.name)
		
	def invoke(self, context, event):
		return {'PASS_THROUGH'}
	