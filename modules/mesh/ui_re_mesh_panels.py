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

class OBJECT_PT_MeshObjectModePanel(Panel):
	bl_label = "RE Mesh Tools"
	bl_idname = "OBJECT_PT_mesh_tools_panel"
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
		layout.operator("re_mesh.create_mesh_collection")
		layout.operator("re_mesh.rename_meshes")
		layout.operator("re_mesh.delete_loose")
		#TODO add solve repeated uvs again
		#layout.operator("re_mesh.solve_repeated_uvs")
		layout.operator("re_mesh.remove_zero_weight_vertex_groups")
		layout.operator("re_mesh.limit_total_normalize")
		layout.operator("re_mesh.batch_exporter")
		
class OBJECT_PT_MeshArmatureToolsPanel(Panel):
	bl_label = "Armature Tools"
	bl_idname = "OBJECT_PT_mesh_armature_tools_panel"
	bl_parent_id = "OBJECT_PT_mesh_tools_panel"  # Specify the ID of the parent panel
	bl_space_type = "VIEW_3D"   
	bl_region_type = "UI"
	bl_category = "RE Mesh"   
	bl_options = {'DEFAULT_CLOSED'}
	
	def draw(self, context):
		layout = self.layout
		obj = context.active_object
		re_mdf_toolpanel = context.scene.re_mdf_toolpanel
		layout.operator("re_fbxskel.link_armature_bones")
		layout.operator("re_fbxskel.clear_bone_linkages")	
class OBJECT_PT_REAssetExtensionPanel(Panel):
	bl_label = "RE Asset Extensions"
	bl_idname = "OBJECT_PT_re_asset_extension_panel"
	bl_space_type = "VIEW_3D"  
	bl_region_type = "UI"
	bl_category = "RE Mesh"   
	bl_context = "objectmode"

	@classmethod
	def poll(self,context):
		return context is not None and "HIDE_RE_MDF_EDITOR_TAB" not in context.scene

	def draw(self, context):
		layout = self.layout
		scene = context.scene
		if hasattr(bpy.types, "OBJECT_PT_re_pak_panel"):
			try:
				layout.operator("re_asset.create_pak_patch")
			except:
				pass
		if hasattr(bpy.types, "RE_ASSET_OT_unpack_mod_pak"):
			try:
				layout.operator("re_asset.unpack_mod_pak")
			except:
				pass
			
		if hasattr(bpy.types, "RE_ASSET_OT_batch_mdf_updater"):
			
			try:
				layout.operator("re_asset.blender_mdf_updater")
				layout.operator("re_asset.batch_mdf_updater")
			except:
				pass
		
		if hasattr(bpy.types, "RE_ASSET_OT_batch_rsz_updater"):
			try:
				layout.operator("re_asset.batch_rsz_updater")
			except:
				pass
		else:
			layout.label(text="Update RE Asset Library for more options.")
				