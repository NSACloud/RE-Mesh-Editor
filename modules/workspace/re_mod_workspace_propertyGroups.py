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

from ..mdf.re_mdf_presets import reloadPresets
		
class ModWorkspaceToolPanelPropertyGroup(bpy.types.PropertyGroup):
	
	enableModFileTracking: BoolProperty(
		name = "Mod File Tracking",
		description="When enabled, any changes made to files in the modOutput directory will automatically be copied to the game directory.\nThis allows for quick testing of changes while in game.\nRE Asset Library must be installed and the asset library for the game must be set up",
		default = False,
		
		)
def getMaterialPresets(self,context):
	return reloadPresets(context.scene.get("modWorkspace_gameName","UNKN"))
class ConvertedMaterialEntryPropertyGroup(bpy.types.PropertyGroup):
	
	oldMaterialName: StringProperty(
		name = "Old Material Name",
		description="",
		default = "oldMaterialName",
		)
	newMaterialName: StringProperty(
		name = "New Material Name",
		description="This is the name that will be used by the RE Engine material.\nName must be only alphanumeric characters and hyphens/underscores",
		default = "newMaterialName",
		)
	
	textureSetName: StringProperty(
		name = "Texture Set Name",
		description="Set the name of the texture set for this material.\nExample: Material_00 would result in:\nMaterial_00_ALBD.tex\nMaterial_00_NRRO.tex\nMaterial_00_ATOS.tex\netc.",
		default = "newTextureSet",
		)
	
	imageXRes: IntProperty(
		name = "X Resolution",
		description="Resolution must be a power of two (256,512,1024,2048,etc.)",
		default = 1024,
		min = 256,
		max = 4096,
		)
	imageYRes: IntProperty(
		name = "Y Resolution",
		description="Resolution must be a power of two (256,512,1024,2048,etc.)",
		default = 1024,
		min = 256,
		max = 4096,
		)
	materialPreset: EnumProperty(
		name = "Material Preset",
		description="Choose which preset material to convert this material into.\nThis determines what texture maps the material will use and the properties the material will have",
		items = getMaterialPresets
		)
	bakeAO: BoolProperty(
		name = "Bake Ambient Occlusion (Slow)",
		description="Bake ambient occlusion texture, this may give mixed results. You may want to use the original ambient occlusion texture if you have one.\nThis may take a very long time to bake depending on your specs and quality of the model",
		default = True,
		)
	uv2AOBake: BoolProperty(
		name = "Bake AO to UV2",
		description="Bakes ambient occlusion using the second uv map if present. AO is baked to UV2 for hair in certain games",
		default = False,
		)
	
class REMOD_UL_MaterialConversionList(bpy.types.UIList):
	
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
				
			split = layout.split(factor = .6)
			if item.oldMaterialName in bpy.data.materials:
				if bpy.data.materials[item.oldMaterialName].preview != None:
					icon = bpy.data.materials[item.oldMaterialName].preview.icon_id
			else:
				print(f"Material doesnt exist: {item.oldMaterialName}")
				icon = "NONE"
			col = split.column()
			col.label(text=item.oldMaterialName,icon_value=icon)
			col = split.column()

			col.prop(item,"materialPreset",text = "")
			
			
	# Disable double-click to rename
	def invoke(self, context, event):
		return {'PASS_THROUGH'}
