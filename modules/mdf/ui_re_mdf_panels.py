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


class OBJECT_PT_MDFObjectModePanel(Panel):
	bl_label = "RE MDF Tools"
	bl_idname = "OBJECT_PT_mdf_tools_panel"
	bl_space_type = "VIEW_3D"   
	bl_region_type = "UI"
	bl_category = "RE MDF"   
	bl_context = "objectmode"

	@classmethod
	def poll(self,context):
		return context is not None and "HIDE_RE_MDF_EDITOR_TAB" not in context.scene

	def draw(self, context):
		layout = self.layout
		scene = context.scene
		re_mdf_toolpanel = scene.re_mdf_toolpanel
		layout.operator("re_mdf.create_mdf_collection")
		layout.label(text = "Active MDF Collection")
		layout.prop_search(re_mdf_toolpanel, "mdfCollection",bpy.data,"collections",icon = "COLLECTION_COLOR_05")
		layout.label(text = "Active Game")
		layout.prop(re_mdf_toolpanel, "activeGame")
		layout.operator("re_mdf.reindex_materials")
		layout.label(text="Material Preset")
		layout.prop(re_mdf_toolpanel, "materialPresets")
		layout.operator("re_mdf.add_preset_material")
		
		layout.operator("re_mdf.save_selected_as_preset")
		layout.operator("re_mdf.open_preset_folder")
		layout.label(text="Test MDF")
		layout.label(text = "Mesh Collection")
		layout.prop_search(re_mdf_toolpanel, "meshCollection",bpy.data,"collections",icon = "COLLECTION_COLOR_01")
		layout.label(text = "Mod Directory")
		layout.prop(re_mdf_toolpanel, "modDirectory")
		layout.operator("re_mdf.apply_mdf")
		
		
class OBJECT_PT_MDFMaterialPanel(Panel):
	bl_label = "RE MDF Material Settings"
	bl_idname = "OBJECT_PT_mdf_material_panel"
	bl_space_type = "PROPERTIES"   
	bl_region_type = "WINDOW"
	bl_category = "RE MDF Material Settings"
	bl_context = "object"

	
	@classmethod
	def poll(self,context):
		
		return context and context.object.mode == "OBJECT" and context.active_object.get("~TYPE",None) == "RE_MDF_MATERIAL" and not "HIDE_RE_MDF_EDITOR_PANEL" in context.scene

	def draw(self, context):
		layout = self.layout
		obj = context.active_object
		re_mdf_material = obj.re_mdf_material
		
		split = layout.split(factor=0.025)
		col1 = split.column()
		col2 = split.column()
		col2.label(text = f"{re_mdf_material.gameName} Material")
		split = layout.split(factor=0.01)
		col3 = split.column()
		col4 = split.column()
		col4.alignment='RIGHT'
		col4.use_property_split = True
		
		col4.prop(re_mdf_material, "materialName")
		col4.prop(re_mdf_material, "mmtrPath") 
		col4.prop(re_mdf_material, "shaderType")

class OBJECT_PT_MDFFlagsPanel(Panel):
	bl_label = "Flags"
	bl_idname = "OBJECT_PT_mdf_material_flags_panel"
	bl_parent_id = "OBJECT_PT_mdf_material_panel"  # Specify the ID of the parent panel
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_options = {'DEFAULT_CLOSED'}
	
	def draw(self, context):
		layout = self.layout
		obj = context.active_object
		flags = obj.re_mdf_material.flags
		split = layout.split(factor=0.025)#Indent list slightly to make it more clear it's a part of a sub panel
		col1 = split.column()
		col2 = split.column()
		col2.alignment='RIGHT'
		col2.prop(flags, "ver32Unknown")
		col2.prop(flags, "ver32Unknown1")
		col2.prop(flags, "ver32Unknown2")
		col2.prop(flags,"flagIntValue")
		
		col2.prop(flags,"BaseTwoSideEnable")
		col2.prop(flags,"BaseAlphaTestEnable")
		col2.prop(flags,"ShadowCastDisable")
		col2.prop(flags,"VertexShaderUsed")
		col2.prop(flags,"EmissiveUsed")
		col2.prop(flags,"TessellationEnable")
		col2.prop(flags,"EnableIgnoreDepth")
		col2.prop(flags,"AlphaMaskUsed")
		col2.prop(flags,"ForcedTwoSideEnable")
		col2.prop(flags,"TwoSideEnable")
		col2.prop(flags,"TessFactor")
		col2.prop(flags,"PhongFactor")
		col2.prop(flags,"RoughTransparentEnable")
		col2.prop(flags,"ForcedAlphaTestEnable")
		col2.prop(flags,"AlphaTestEnable")
		col2.prop(flags,"SSSProfileUsed")
		col2.prop(flags,"EnableStencilPriority")
		col2.prop(flags,"RequireDualQuaternion")
		col2.prop(flags,"PixelDepthOffsetUsed")
		col2.prop(flags,"NoRayTracing")
		

class OBJECT_PT_MDFMaterialPropertyListPanel(Panel):
	bl_label = "Property List"
	bl_idname = "OBJECT_PT_mdf_material_proplist_panel"
	bl_parent_id = "OBJECT_PT_mdf_material_panel"  # Specify the ID of the parent panel
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'

	def draw(self, context):
		layout = self.layout
		obj = context.active_object
		re_mdf_material = obj.re_mdf_material
		
		split = layout.split(factor=0.025)#Indent list slightly to make it more clear it's a part of a sub panel
		col1 = split.column()
		col2 = split.column()
		col2.label(text = f"Property Count: {str(len(obj.re_mdf_material.propertyList_items))}")
		col2.template_list(
			listtype_name = "MESH_UL_MDFPropertyList", 
			list_id = "",
			dataptr = re_mdf_material,
			propname = "propertyList_items",
			active_dataptr = re_mdf_material, 
			active_propname = "propertyList_index",
			rows = 6,
			type='DEFAULT'
			)
		
class OBJECT_PT_MDFMaterialTextureBindingListPanel(Panel):
	bl_label = "Texture Bindings"
	bl_idname = "OBJECT_PT_mdf_material_texturebindinglist_panel"
	bl_parent_id = "OBJECT_PT_mdf_material_panel"  # Specify the ID of the parent panel
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'

	def draw(self, context):
		layout = self.layout
		obj = context.active_object
		re_mdf_material = obj.re_mdf_material
		split = layout.split(factor=0.025)#Indent list slightly to make it more clear it's a part of a sub panel
		col1 = split.column()
		col2 = split.column()
		col2.label(text = f"Texture Binding Count: {str(len(obj.re_mdf_material.textureBindingList_items))}")
		col2.template_list(
			listtype_name = "MESH_UL_MDFTextureBindingList", 
			list_id = "",
			dataptr = re_mdf_material,
			propname = "textureBindingList_items",
			active_dataptr = re_mdf_material, 
			active_propname = "textureBindingList_index",
			rows = 6,
			type='DEFAULT'
			)
class OBJECT_PT_MDFMaterialMMTRSIndexListPanel(Panel):
	bl_label = "MMTRS Data"
	bl_idname = "OBJECT_PT_mdf_material_mmtrsindexlist_panel"
	bl_parent_id = "OBJECT_PT_mdf_material_panel"  # Specify the ID of the parent panel
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_options = {'DEFAULT_CLOSED'}
	@classmethod
	def poll(self,context):
		return context.active_object != None and len(context.active_object.re_mdf_material.mmtrsData_items) != 0
	
	def draw(self, context):
		layout = self.layout
		obj = context.active_object
		re_mdf_material = obj.re_mdf_material
		split = layout.split(factor=0.025)#Indent list slightly to make it more clear it's a part of a sub panel
		col1 = split.column()
		col2 = split.column()
		col2.label(text = f"Do not change these unless you know what you're doing.")
		col2.label(text = f"Index Count: {str(len(obj.re_mdf_material.mmtrsData_items))}")
		col2.template_list(
			listtype_name = "MESH_UL_MDFMMTRSDataList", 
			list_id = "",
			dataptr = re_mdf_material,
			propname = "mmtrsData_items",
			active_dataptr = re_mdf_material, 
			active_propname = "mmtrsData_index",
			rows = 8,
			type='DEFAULT'
			)

class OBJECT_PT_MDFMaterialGPBFDataListPanel(Panel):
	bl_label = "GPBF Data"
	bl_idname = "OBJECT_PT_mdf_material_gpbfdatalist_panel"
	bl_parent_id = "OBJECT_PT_mdf_material_panel"  # Specify the ID of the parent panel
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_options = {'DEFAULT_CLOSED'}
	@classmethod
	def poll(self,context):
		return context.active_object != None and len(context.active_object.re_mdf_material.gpbfData_items) != 0
	
	def draw(self, context):
		layout = self.layout
		obj = context.active_object
		re_mdf_material = obj.re_mdf_material
		split = layout.split(factor=0.025)#Indent list slightly to make it more clear it's a part of a sub panel
		col1 = split.column()
		col2 = split.column()
		col2.label(text = f"Do not change these unless you know what you're doing.")
		col2.label(text = f"Index Count: {str(len(obj.re_mdf_material.gpbfData_items))}")
		col2.template_list(
			listtype_name = "MESH_UL_MDFGPBFDataList", 
			list_id = "",
			dataptr = re_mdf_material,
			propname = "gpbfData_items",
			active_dataptr = re_mdf_material, 
			active_propname = "gpbfData_index",
			rows = 3,
			type='DEFAULT'
			)	