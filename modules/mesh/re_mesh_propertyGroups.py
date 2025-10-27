#Author: NSA Cloud
import bpy
import os
from bpy.props import (StringProperty,
					   BoolProperty,
					   IntProperty,
					   FloatProperty,
					   FloatVectorProperty,
					   EnumProperty,
					   PointerProperty,
					   CollectionProperty,
					   )


def update_relPathToAbs(self,context):
	try:
		if "//" in self.path:
			#print("updated path")
			self.path = os.path.realpath(bpy.path.abspath(self.path))
	except:
		pass
	if self.path == "" or self.path.count(".") < 2:#Check if path is empty or if number extension is missing
		self.invalid = True
	else:
		self.invalid = False
class ExporterNodePropertyGroup(bpy.types.PropertyGroup):
	name: StringProperty(
        name="",
		description = "",
	)
	icon: StringProperty(
        name="",
		description = "",
	)
	enabled: BoolProperty(
		name="",
		description = "",
		default = True,

	)
	show: BoolProperty(
		name="",
		description = "",
		default = True
	)
	hasChild: BoolProperty(
		name="",
		description = "",
		default = False
	)
	expand: BoolProperty(
		name="",
		description = "",
		default = True
	)
	
	parentName: StringProperty(
		name="",
		description = "",
		default = ""
	)
	hierarchyLevel: IntProperty(
		name="",
		description = "",
		default = 0
	)
	exportType: StringProperty(
        name="",
		description = "",
		default = ""
	)
	path: StringProperty(
        name="",
		subtype="FILE_PATH",
		description = "Path to where to export the file to",
		update = update_relPathToAbs
	)
	invalid: BoolProperty(
		name="",
		description = "",
		default = False
	)

	#mesh operator arguments
	
	exportAllLODs : BoolProperty(
	   name = "Export All LODs",
	   description = "Export all LODs. If disabled, only LOD0 will be exported. Note that LODs meshes must be grouped inside a collection for each level and that collection must be contained in another collection. See a mesh with LODs imported for reference on how it should look. A target collection must also be set",
	   default = True)
	exportBlendShapes : BoolProperty(
	   name = "Export Blend Shapes",
	   description = "Exports blend shapes from mesh if present",
	   default = True)
	rotate90 : BoolProperty(
	   name = "Convert Z Up To Y Up",
	   description = "Rotates objects 90 degrees for export. Leaving this option enabled is recommended",
	   default = True)
	autoSolveRepeatedUVs : BoolProperty(
	   name = "Auto Solve Repeated UVs",
	   description = "Splits connected UV islands if present. The mesh format does not allow for multiple uvs assigned to a vertex.\nNOTE: This will modify the object and may slightly increase time taken to export",
	   default = True)
	preserveSharpEdges : BoolProperty(
	   name = "Split Sharp Edges",
	   description = "Edge splits all edges marked as sharp to preserve them on the exported mesh.\nNOTE: This will modify the exported mesh",
	   default = False)
	useBlenderMaterialName : BoolProperty(
	   name = "Use Blender Material Names",
	   description = "If left unchecked, the exporter will get the material names to be used from the end of each object name. For example, if a mesh is named LOD_0_Group_0_Sub_0__Shirts_Mat, the material name is Shirts_Mat. If this option is enabled, the material name will instead be taken from the first material assigned to the object",
	   default = False)
	preserveBoneMatrices : BoolProperty(
	   name = "Preserve Bone Matrices",
	   description = "Export using the original matrices of the imported bones. Note that this option only applies armatures imported with this addon. Any newly added bones will have new matrices calculated",
	   default = False)
	exportBoundingBoxes : BoolProperty(
	   name = "Export Bounding Boxes",
	   description = "Exports the original bounding boxes from the \"Import Bounding Boxes\" import option. New bounding boxes will be generated for any bones that do not have them",
	   default = False)
	
	
class MESH_UL_REExporterList(bpy.types.UIList):
	
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
				
			row = layout.row()
			if not item.hasChild and item.invalid:
				row.alert = True
			col1 = row.column()
			#col1.prop(item,"expand")
			col1.alignment = "RIGHT"
			col1.label(text="      |    "*item.hierarchyLevel if item.hierarchyLevel != 0 else " ")
			if not item.hasChild:
				col2 = row.column()
				col2.prop(item,"enabled")
			col3 = row.column()
			col3.label(icon = item.icon,text=item.name)
			col4 = row.column()
			
	# Disable double-click to rename
	def invoke(self, context, event):
		return {'PASS_THROUGH'}
