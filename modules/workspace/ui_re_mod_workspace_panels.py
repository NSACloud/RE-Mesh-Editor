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


class OBJECT_PT_REModWorkspacePanel(Panel):
	bl_label = "RE Mod Dev Tools"
	bl_idname = "OBJECT_PT_re_mod_workspace_panel"
	bl_space_type = "VIEW_3D"   
	bl_region_type = "UI"
	bl_category = "RE Mesh"   
	bl_context = "objectmode"

	@classmethod
	def poll(self,context):
		return context is not None and "HIDE_RE_MDF_EDITOR_TAB" not in context.scene

	
	def draw(self, context):
		layout = self.layout
		obj = context.active_object
		re_modworkspace_toolpanel = context.scene.re_modworkspace_toolpanel
		layout.operator("re_mod_workspace.create_mod_workspace", icon = "WORKSPACE", text = "Create Mod Workspace" if "modWorkspace_setup" not in bpy.context.scene else "Edit Mod Workspace")
		layout.operator("re_mod_workspace.edit_modinfo", icon = "CURRENT_FILE")
		layout.operator("re_mod_workspace.open_mod_workspace", icon = "FILE_FOLDER")
		panelHeader,panelBody = layout.panel(idname = "OBJECT_PT_re_mod_workspace_porting_panel",default_closed = True)
		panelHeader.label(text="Porting Tools")
		if panelBody:
			panelBody.operator("re_mod_workspace.convert_to_re_engine", icon = "FULLSCREEN_EXIT")
			#panelBody.operator("re_mod_workspace.texture_packer", icon = "IMAGE_ZDEPTH")#Not implemented yet
		
		panelHeader,panelBody = layout.panel(idname = "OBJECT_PT_re_mod_workspace_file_tracking_panel",default_closed = True)
		panelHeader.label(text="File Tracking - ON" if context.window_manager.enableModFileTracking else "File Tracking - OFF" ,icon = "RECORD_ON" if context.window_manager.enableModFileTracking else "RECORD_OFF")
		if panelBody:
			panelBody.operator("re_mod_workspace.toggle_mod_file_tracking",icon = "TRACKER")
			panelBody.operator("re_mod_workspace.copy_mod_files_to_game_dir",icon="DUPLICATE")
			panelBody.operator("re_mod_workspace.uninstall_mod_files_from_game_dir",icon="TRASH")
			panelBody.operator("re_mod_workspace.launch_game",icon = "PLAY")
		