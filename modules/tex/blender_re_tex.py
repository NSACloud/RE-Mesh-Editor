#Author: NSA Cloud
import bpy
import os
from..gen_functions import raiseWarning,wildCardFileSearchList
from .file_re_tex import getTexVersionFromGameName
from .re_tex_utils import DDSToTex,convertTexFileToDDS
DELETE_DDS = True
BLENDER_MAX_IMAGE_ARRAY_SIZE = 16#Blender can't handle much more mix nodes than this
def loadTex(texPath,outputPath,texConv,reloadCachedTextures,useDDS):
	ddsPath = os.path.splitext(outputPath)[0]+".dds"
	if useDDS:
		outputPath = ddsPath
	blenderImageList = None
	if not reloadCachedTextures and os.path.isfile(outputPath):
		blenderImageList = [bpy.data.images.load(outputPath,check_existing = True)]
	
	
	if blenderImageList == None:
		blenderImageList = []
		#Check if there's an array texture extracted
		foundArrayTexture = False
		if not reloadCachedTextures:
			resultList = wildCardFileSearchList(os.path.splitext(outputPath)[0]+ " #ARRAY_*")
			#print("test")
			#print(resultList)
			for result in sorted(resultList):
				if result.endswith(".dds" if useDDS else ".tif"):
					foundArrayTexture = True
					#print(f"Found existing array texture {result}")
					blenderImageList.append(bpy.data.images.load(result,check_existing = True)) 
			
		
		if not foundArrayTexture:#Convert array tex
			texInfo = convertTexFileToDDS(texPath, ddsPath)
			if texInfo["arrayNum"] > BLENDER_MAX_IMAGE_ARRAY_SIZE:
				arrayMaxExceeded = True
				print(f"Array size of {os.path.split(texPath)[1]} exceeds the max limit of {str(BLENDER_MAX_IMAGE_ARRAY_SIZE)} images, importing only the first array image.")
			else:
				arrayMaxExceeded = False
			if texInfo["isArray"] and not arrayMaxExceeded:
				digitCount = 2
				if texInfo["arrayNum"] > 99:
					digitCount = 3
				elif texInfo["arrayNum"] > 999:#Highest possible image count is technically 4095 but I'm going to pretend nobody will try to make something that unholy
					digitCount = 4
				#print("TEX ARRAY FOUND")
				newDDSPathRoot = os.path.splitext(ddsPath)[0]+ " #ARRAY_"
				print(f"Converting array texture: {texPath}")
				for i in range(texInfo["arrayNum"]):
					newDDSPath = f"{newDDSPathRoot}{str(i).zfill(digitCount)}.dds"
					newOutputPath = f"{newDDSPathRoot}{str(i).zfill(digitCount)}.tif"
					
					if not useDDS:
						texConv.convert_to_tif(newDDSPath,out = os.path.dirname(newOutputPath),verbose=False)
					else:
						newOutputPath = newDDSPath
					
					
					if os.path.isfile(newOutputPath):
						blenderImageList.append(bpy.data.images.load(newOutputPath,check_existing = not reloadCachedTextures))
					if not useDDS:
						try:
							os.remove(newDDSPath)
						except:
							raiseWarning("Could not delete temporary dds file: {newDDSPath}")
			else:#Convert single image tex
				if arrayMaxExceeded:
					digitCount = 2
					if texInfo["arrayNum"] > 99:
						digitCount = 3
					elif texInfo["arrayNum"] > 999:#Highest possible image count is technically 4095 but I'm going to pretend nobody will try to make something that unholy
						digitCount = 4
					#print("TEX ARRAY FOUND")
					ddsPath = f"{os.path.splitext(ddsPath)[0]} #ARRAY_{str(0)*digitCount}.dds"
				if not useDDS:
					texConv.convert_to_tif(ddsPath,out = os.path.dirname(outputPath),verbose=False)
				if os.path.isfile(outputPath):
					blenderImageList = [bpy.data.images.load(outputPath,check_existing = not reloadCachedTextures)]
					#print(blenderImageList)
				if not useDDS:
					try:
						os.remove(ddsPath)
					except:
						raiseWarning("Could not delete temporary dds file: {ddsPath}")
	return blenderImageList

supportedImageExtensionsSet = set([".png",".tga",".tif"])#Not implemented yet

def convertTexDDSList (fileNameList,inDir,outDir,gameName,createStreamingTex = False):
	ddsConversionList = []
	ddsArrayConversionDict = {}
	texConversionList = []
	texVersion = 28
	
	conversionCount = 0
	failCount = 0
	
	#gameName = bpy.context.scene.re_mdf_toolpanel.activeGame
	if gameName != -1 and getTexVersionFromGameName(gameName) != -1:
		texVersion = getTexVersionFromGameName(gameName)
	for fileName in fileNameList:
		fullPath = os.path.join(inDir,fileName)
		if os.path.isfile(fullPath):
			if fileName.lower().endswith(".dds"):
				if " #ARRAY_" in fileName:
					split = fileName.split(" #ARRAY_")
					if split[0] in ddsArrayConversionDict:
						ddsArrayConversionDict[split[0]].append(os.path.join(os.path.join(inDir,fileName)))
					else:
						ddsArrayConversionDict[split[0]] = [os.path.join(os.path.join(inDir,fileName))]
				else:
					path = os.path.join(inDir,fileName)
					ddsConversionList.append(path)
					print(str(path))
			elif ".tex." in fileName.lower():
				path = os.path.join(inDir,fileName)
				texConversionList.append(path)
		elif os.path.splitext(fileName)[1] in supportedImageExtensionsSet:
			pass#TODO			
	
	if ddsConversionList != [] or ddsArrayConversionDict != {}:
		os.makedirs(outDir,exist_ok = True)
		
		#Single Texture Conversion
		for ddsPath in ddsConversionList:
			texPath = os.path.join(outDir,os.path.splitext(os.path.split(ddsPath)[1])[0])+f".tex.{str(texVersion)}"
			print(str(texPath))
			DDSToTex([ddsPath],texVersion,texPath,streamingFlag = False)#TODO Streaming
			conversionCount += 1
		
		
		#Array Texture Conversion
		for key in ddsArrayConversionDict.keys():
			ddsPathList = sorted(ddsArrayConversionDict[key])
			#print(key)
			#print(ddsPathList)
			texPath = os.path.join(outDir,key+f".tex.{str(texVersion)}")
			DDSToTex(ddsPathList,texVersion,texPath,streamingFlag = False)#TODO Streaming
			conversionCount += 1
	
	if texConversionList != []:
		os.makedirs(outDir,exist_ok = True)
		for texPath in texConversionList:
			try:
				convertTexFileToDDS(texPath,texPath.split(".tex.")[0]+".dds")
				conversionCount += 1
			except Exception as err:
				print(f"Failed to convert {texPath} - {str(err)}")
				failCount += 1
	return (conversionCount,failCount)