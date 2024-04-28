#Author: NSA Cloud
import bpy
import os
from..gen_functions import raiseWarning
from .re_tex_utils import convertTexFileToDDS
def loadTex(texPath,outputPath,texConv,reloadCachedTextures):
	ddsPath = os.path.splitext(outputPath)[0]+".dds"
	blenderImage = None
	if os.path.isfile(outputPath) and not reloadCachedTextures:
		blenderImage = bpy.data.images.load(outputPath,check_existing = True)
	if blenderImage == None:
		#Convert tex to dds
		convertTexFileToDDS(texPath, ddsPath)
		
		texConv.convert_to_tif(ddsPath,out = os.path.dirname(outputPath),verbose=False)
		if os.path.isfile(outputPath):
			blenderImage = bpy.data.images.load(outputPath,check_existing = False)
		try:
			os.remove(ddsPath)
		except:
			raiseWarning("Could not delete temporary dds file: {ddsPath}")
	return blenderImage