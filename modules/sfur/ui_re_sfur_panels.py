import bpy

from bpy.types import (Panel,
					   Menu,
					   Operator,
					   PropertyGroup,
					   )


def tag_redraw(context, space_type="PROPERTIES", region_type="WINDOW"):
	for window in context.window_manager.windows:
		for area in window.screen.areas:
			if area.spaces[0].type == space_type:
				for region in area.regions:
					if region.type == region_type:
						region.tag_redraw()

		
class OBJECT_PT_SFurObjectModePanel(Panel):
	bl_label = "RE SFur Tools"
	bl_idname = "OBJECT_PT_sfur_tools_panel"
	bl_space_type = "VIEW_3D"   
	bl_region_type = "UI"
	bl_category = "RE Mesh"   
	bl_context = "objectmode"
	bl_options = {'DEFAULT_CLOSED'}
	
	@classmethod
	def poll(self,context):
		return context is not None and "HIDE_RE_MDF_EDITOR_TAB" not in context.scene

	def draw(self, context):
		layout = self.layout
		scene = context.scene
		re_mdf_toolpanel = scene.re_mdf_toolpanel
		layout.operator("re_sfur.create_sfur_collection",icon = "COLLECTION_NEW")
		layout.label(text = "Active SFur Collection")
		layout.prop_search(re_mdf_toolpanel, "sFurCollection",bpy.data,"collections",icon = "COLLECTION_COLOR_08")
		layout.operator("re_sfur.add_sfur_entry")
		layout.operator("re_sfur.reindex_entries")
		#layout.operator("re_sfur.apply_sfur")
		
		
		
class OBJECT_PT_SFurEntryPanel(Panel):
	bl_label = "RE Shell Fur Settings"
	bl_idname = "OBJECT_PT_sfur_entry_panel"
	bl_space_type = "PROPERTIES"   
	bl_region_type = "WINDOW"
	bl_category = "RE Shell Fur Settings"
	bl_context = "object"

	
	@classmethod
	def poll(self,context):
		
		return context and context.object.mode == "OBJECT" and context.active_object.get("~TYPE",None) == "RE_SFUR_ENTRY" and not "HIDE_RE_MDF_EDITOR_PANEL" in context.scene

	def draw(self, context):
		layout = self.layout
		obj = context.active_object
		re_sfur_data = obj.re_sfur_data
		layout.label(icon = "ERROR",text="Fur effects are not shown in Blender yet.")
		layout.label(text="Using EMV Engine to tweak fur parameters while in game is advised.")
		split = layout.split(factor=0.025)
		col1 = split.column()
		col2 = split.column()
		split = layout.split(factor=0.01)
		col3 = split.column()
		col4 = split.column()
		col4.alignment='RIGHT'
		col4.use_property_split = True
		
		col4.separator()
		col4.prop(re_sfur_data, "materialName")
		col4.prop(re_sfur_data, "groomingTexturePath")
		col4.prop(re_sfur_data, "shellCount")
		col4.prop(re_sfur_data, "shellThinType")
		col4.prop(re_sfur_data, "groomingTexCoordType")
		col4.prop(re_sfur_data, "shellHeight",slider = True)
		col4.prop(re_sfur_data, "bendRate",slider = True)
		col4.prop(re_sfur_data, "bendRootRate",slider = True)
		col4.prop(re_sfur_data, "normalTransformRate",slider = True)
		col4.prop(re_sfur_data, "stiffness",slider = True)
		col4.prop(re_sfur_data, "stiffnessDistribution",slider = True)
		col4.prop(re_sfur_data, "springCoefficient",slider = True)
		col4.prop(re_sfur_data, "damping",slider = True)
		col4.prop(re_sfur_data, "gravityForceScale",slider = True)
		col4.prop(re_sfur_data, "directWindForceScale",slider = True)
		col4.prop(re_sfur_data, "isForceTwoSide")
		col4.prop(re_sfur_data, "isForceAlphaTest")
		col4.prop(re_sfur_data, "unknownFlag")