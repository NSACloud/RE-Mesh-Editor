import bpy

from bpy.types import (Panel,
					   Menu,
					   Operator,
					   PropertyGroup,
					   )


class OBJECT_PT_TexConversionPanel(Panel):
	bl_label = "RE Tex Conversion"
	bl_idname = "OBJECT_PT_tex_tools_panel"
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
		
		layout.operator("re_tex.convert_tex_dds_files")
		
		layout.label(text = "Convert Image Directory")
		layout.prop(re_mdf_toolpanel, "textureDirectory")
		layout.operator("re_tex.convert_tex_directory")
		#layout.prop(re_mdf_toolpanel, "createStreamingTextures")
		layout.prop(re_mdf_toolpanel, "openConvertedFolder")
		layout.operator("re_tex.copy_converted_tex")
		
		if hasattr(bpy.types, "OBJECT_PT_re_pak_panel"):
			try:
				layout.operator("re_asset.create_pak_patch")
			except:
				pass