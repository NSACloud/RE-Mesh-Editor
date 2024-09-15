#Author: NSA Cloud
import bpy

from .gen_functions import textColors
import os
from collections import OrderedDict
from itertools import repeat
def showMessageBox(message = "", title = "Message Box", icon = 'INFO'):

	def draw(self, context):
		self.layout.label(text = message)

	bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)
	
def showErrorMessageBox(message):
	print(textColors.FAIL + "ERROR: " + message + textColors.ENDC)
	showMessageBox(message,title = "Error", icon = "ERROR")

class ContextExecuterOverride:
	def __init__(self, window, screen, area, region):
		self.window, self.screen, self.area, self.region = window, screen, area, region
		self.legacy = not hasattr(bpy.context, "temp_override")
		if self.legacy:
			self.context = bpy.context.copy()
			self.context['window'] = window
			self.context['screen'] = screen
			self.context['area'] = area
			self.context['region'] = region
		else:
			self.context = bpy.context.temp_override(window=window, screen=screen, area=area, region=region)

	def __enter__(self):
		if not self.legacy:
			self.context.__enter__()
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		if not self.legacy:
			self.context.__exit__(self, exc_type, exc_value, traceback)
		return self

class ContextScriptExecuter():

	def __init__(self, area_type, ui_type=None, script=None):
		self.area_type = area_type
		self.ui_type = ui_type if ui_type else area_type
		self.script = script

	def script_content(self, override):
		self.script(override)

	def execute_script(self):
		window = bpy.context.window
		screen = window.screen
		areas = [area for area in screen.areas if area.type == self.area_type]
		area = areas[0] if len(areas) else screen.areas[0]
		prev_ui_type = area.ui_type
		area.ui_type = self.ui_type
		regions = [region for region in area.regions if region.type == 'WINDOW']
		region = regions[0] if len(regions) else None
		with ContextExecuterOverride(window=window, screen=screen, area=area, region=region) as override:
			self.script_content(override)
		area.ui_type = prev_ui_type
		
def outlinerShowObject(objName):
	if objName in bpy.data.objects:
		obj = bpy.data.objects[objName]
		bpy.context.view_layer.objects.active = obj
		ContextScriptExecuter(
	area_type='OUTLINER',
	script=lambda override: (
		bpy.ops.outliner.show_active(override.context)
		if override.legacy
		else bpy.ops.outliner.show_active()
	)
).execute_script()


	
def operator_exists(idname):
	from bpy.ops import op_as_string
	try:
		op_as_string(idname)
		return True
	except:
		return False
	
#--------------------------------
#Node arrange by JuhaW
#https://github.com/blender/blender-addons/blob/main/node_arrange.py
class values():
	average_y = 0
	x_last = 0
	margin_x = 100
	mat_name = ""
	margin_y = 20

def outputnode_search(ntree):    # return node/None

	outputnodes = []
	for node in ntree.nodes:
		if not node.outputs:
			for input in node.inputs:
				if input.is_linked:
					outputnodes.append(node)
					break

	if not outputnodes:
		print("No output node found")
		return None
	return outputnodes

def nodes_odd(ntree, nodelist):

	nodes = ntree.nodes
	for i in nodes:
		i.select = False

	a = [x for x in nodes if x not in nodelist]
	# print ("odd nodes:",a)
	for i in a:
		i.select = True

def nodes_arrange(nodelist, level, ntree):

	parents = []
	for node in nodelist:
		parents.append(node.parent)
		node.parent = None
		ntree.nodes.update()


	#print ("nodes arrange def")
	# node x positions

	widthmax = max([x.dimensions.x for x in nodelist])
	xpos = values.x_last - (widthmax + values.margin_x) if level != 0 else 0
	#print ("nodelist, xpos", nodelist,xpos)
	values.x_last = xpos

	# node y positions
	x = 0
	y = 0

	for node in nodelist:

		if node.hide:
			hidey = (node.dimensions.y / 2) - 8
			y = y - hidey
		else:
			hidey = 0

		node.location.y = y
		y = y - values.margin_y - node.dimensions.y + hidey

		node.location.x = xpos #if node.type != "FRAME" else xpos + 1200

	y = y + values.margin_y

	center = (0 + y) / 2
	values.average_y = center - values.average_y

	#for node in nodelist:

		#node.location.y -= values.average_y

	for i, node in enumerate(nodelist):
		node.parent =  parents[i]

def nodes_iterate(ntree, arrange=True):

	nodeoutput = outputnode_search(ntree)
	if nodeoutput is None:
		#print ("nodeoutput is None")
		return None
	a = []
	a.append([])
	for i in nodeoutput:
		a[0].append(i)


	level = 0

	while a[level]:
		a.append([])

		for node in a[level]:
			inputlist = [i for i in node.inputs if i.is_linked]

			if inputlist:

				for input in inputlist:
					for nlinks in input.links:
						node1 = nlinks.from_node
						a[level + 1].append(node1)

			else:
				pass

		level += 1

	del a[level]
	level -= 1

	#remove duplicate nodes at the same level, first wins
	for x, nodes in enumerate(a):
		a[x] = list(OrderedDict(zip(a[x], repeat(None))))

	#remove duplicate nodes in all levels, last wins
	top = level
	for row1 in range(top, 1, -1):
		for col1 in a[row1]:
			for row2 in range(row1-1, 0, -1):
				for col2 in a[row2]:
					if col1 == col2:
						a[row2].remove(col2)
						break

	"""
	for x, i in enumerate(a):
		print (x)
		for j in i:
			print (j)
		#print()
	"""
	"""
	#add node frames to nodelist
	frames = []
	print ("Frames:")
	print ("level:", level)
	print ("a:",a)
	for row in range(level, 0, -1):

		for i, node in enumerate(a[row]):
			if node.parent:
				print ("Frame found:", node.parent, node)
				#if frame already added to the list ?
				frame = node.parent
				#remove node
				del a[row][i]
				if frame not in frames:
					frames.append(frame)
					#add frame to the same place than node was
					a[row].insert(i, frame)

	pprint.pprint(a)
	"""
	#return None
	########################################



	if not arrange:
		nodelist = [j for i in a for j in i]
		nodes_odd(ntree, nodelist=nodelist)
		return None

	########################################

	levelmax = level + 1
	level = 0
	values.x_last = 0

	while level < levelmax:

		values.average_y = 0
		nodes = [x for x in a[level]]
		#print ("level, nodes:", level, nodes)
		nodes_arrange(nodes, level, ntree)

		level = level + 1

	return None

def nodes_center(ntree):

	bboxminx = []
	bboxmaxx = []
	bboxmaxy = []
	bboxminy = []

	for node in ntree.nodes:
		if not node.parent:
			bboxminx.append(node.location.x)
			bboxmaxx.append(node.location.x + node.dimensions.x)
			bboxmaxy.append(node.location.y)
			bboxminy.append(node.location.y - node.dimensions.y)

	# print ("bboxminy:",bboxminy)
	bboxminx = min(bboxminx)
	bboxmaxx = max(bboxmaxx)
	bboxminy = min(bboxminy)
	bboxmaxy = max(bboxmaxy)
	center_x = (bboxminx + bboxmaxx) / 2
	center_y = (bboxminy + bboxmaxy) / 2
	'''
	print ("minx:",bboxminx)
	print ("maxx:",bboxmaxx)
	print ("miny:",bboxminy)
	print ("maxy:",bboxmaxy)

	print ("bboxes:", bboxminx, bboxmaxx, bboxmaxy, bboxminy)
	print ("center x:",center_x)
	print ("center y:",center_y)
	'''

	x = 0
	y = 0

	for node in ntree.nodes:

		if not node.parent:
			node.location.x -= center_x
			node.location.y += -center_y

def arrangeNodeTree(ntree,margin_x = 100,margin_y = 20,centerNodes = True):

#TODO Fix, blender doesn't initialize node dimensions unless the shader editor is open	

	values.margin_x = margin_x
	values.margin_y = margin_y

	ntree.nodes.update()
	#first arrange nodegroups
	n_groups = []
	for i in ntree.nodes:
		if i.type == 'GROUP':
			n_groups.append(i)

	while n_groups:
		j = n_groups.pop(0)
		nodes_iterate(j.node_tree)
		for i in j.node_tree.nodes:
			if i.type == 'GROUP':
				n_groups.append(i)

	nodes_iterate(ntree)

	# arrange nodes + this center nodes together
	if centerNodes:
		nodes_center(ntree)
#--------------------------------