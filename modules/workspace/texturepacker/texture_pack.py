import bpy
import os

from .re_texture_types import getTexturePacker

def packTextures(textureSetName,textureTypeList,imageXRes,imageYRes,outDir,fileFormat,fileExt):
    #PACKING-----------------------------------------------------------------------------
	print("\tPacking Textures...")
	#textureTypeList = ["ALBD","ALBM","NRMR","NRRT","NRRC","NRRO","ATOS","ATOC","ALP"]
	for textureType in textureTypeList:
		#Pack ALBD ----------------------------------------------
		outImageName = f"{textureSetName}_{textureType}"
		outFilePath = os.path.join(outDir,outImageName+fileExt)
		packer = getTexturePacker(textureType)
		outImg = packer(textureSetName,imageXRes,imageYRes,outImageName)
		outImg.file_format = fileFormat
		outImg.filepath_raw = outFilePath
		outImg.save()
		print(f"\tSaved {outFilePath}")