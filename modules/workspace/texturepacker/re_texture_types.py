import bpy
import numpy as np
from .image_utils import NRMRToNRRX,NRRXToNRMR
#-------------------
#Texture types packing
def packALB(textureSetName,imageXRes,imageYRes,outImageName):
    #Pack ALB ----------------------------------------------
    albedoImage = bpy.data.images[f"{textureSetName}_BaseColor"]
    albedoImage.scale(imageXRes,imageYRes)
    return albedoImage
def packALBA(textureSetName,imageXRes,imageYRes,outImageName):
    #Pack ALBD ----------------------------------------------
    albedoArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    albedoImage = bpy.data.images[f"{textureSetName}_BaseColor"]
    albedoImage.scale(imageXRes,imageYRes)
    albedoImage.pixels.foreach_get(albedoArray)
    
    alphaArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    alphaImage = bpy.data.images[f"{textureSetName}_Opacity"]
    alphaImage.pixels.foreach_get(alphaArray)
    
    #outPixelArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    outPixelArray = np.copy(albedoArray)
    outPixelArray[3::4] = alphaArray[0::4]
    
    
    outImg = bpy.data.images.new(outImageName, imageXRes, imageYRes,alpha = True,is_data = False)
    outImg.alpha_mode = "CHANNEL_PACKED"
    outImg.colorspace_settings.name = "sRGB"
    outImg.pixels.foreach_set(outPixelArray)
    return outImg
def packALBD(textureSetName,imageXRes,imageYRes,outImageName):
    #Pack ALBD ----------------------------------------------
    albedoArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    albedoImage = bpy.data.images[f"{textureSetName}_BaseColor"]
    albedoImage.scale(imageXRes,imageYRes)
    albedoImage.pixels.foreach_get(albedoArray)
    
    metallicArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    metallicImage = bpy.data.images[f"{textureSetName}_Metallic"]
    metallicImage.scale(imageXRes,imageYRes)
    metallicImage.pixels.foreach_get(metallicArray)
    
    #outPixelArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    outPixelArray = np.copy(albedoArray)
    outPixelArray[3::4] = 1 - metallicArray[0::4]#Invert the metallic
    
    
    outImg = bpy.data.images.new(outImageName, imageXRes, imageYRes,alpha = True,is_data = False)
    outImg.alpha_mode = "CHANNEL_PACKED"
    outImg.colorspace_settings.name = "sRGB"
    outImg.pixels.foreach_set(outPixelArray)
    return outImg
def packALBM(textureSetName,imageXRes,imageYRes,outImageName):
    #Pack ALBD ----------------------------------------------
    albedoArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    albedoImage = bpy.data.images[f"{textureSetName}_BaseColor"]
    albedoImage.scale(imageXRes,imageYRes)
    albedoImage.pixels.foreach_get(albedoArray)
    
    metallicArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    metallicImage = bpy.data.images[f"{textureSetName}_Metallic"]
    metallicImage.scale(imageXRes,imageYRes)
    metallicImage.pixels.foreach_get(metallicArray)
    
    #outPixelArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    outPixelArray = np.copy(albedoArray)
    outPixelArray[3::4] = metallicArray[0::4]
    
    
    outImg = bpy.data.images.new(outImageName, imageXRes, imageYRes,alpha = True,is_data = False)
    outImg.alpha_mode = "CHANNEL_PACKED"
    outImg.colorspace_settings.name = "sRGB"
    outImg.pixels.foreach_set(outPixelArray)
    return outImg
def packALP(textureSetName,imageXRes,imageYRes,outImageName):
    #Pack ALP ----------------------------------------------
    alphaImage = bpy.data.images[f"{textureSetName}_Opacity"]
	
    return alphaImage
def packEMI(textureSetName,imageXRes,imageYRes,outImageName):
    #Pack EMI ----------------------------------------------
    emissionImage = bpy.data.images[f"{textureSetName}_Emissive"]
    emissionImage.scale(imageXRes,imageYRes)
    outPixelArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    emissionImage.pixels.foreach_get(outPixelArray)

    outPixelArray[3::4] = 0.0#Black out the alpha channel of emission maps, this is because mh wilds uses the alpha channel of EMI as a mask for certain things. This doesn't affect other games.
    
    
    outImg = bpy.data.images.new(outImageName, imageXRes, imageYRes,alpha = True,is_data = False)
    outImg.alpha_mode = "CHANNEL_PACKED"
    outImg.colorspace_settings.name = "sRGB"
    outImg.pixels.foreach_set(outPixelArray)
    return outImg
def packNRMR(textureSetName,imageXRes,imageYRes,outImageName):
    #Pack NRMR ----------------------------------------------
    normalArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    normalImage = bpy.data.images[f"{textureSetName}_Normal"]
    normalImage.scale(imageXRes,imageYRes)
    normalImage.pixels.foreach_get(normalArray)
    
    roughnessArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    roughnessImage = bpy.data.images[f"{textureSetName}_Roughness"]
    roughnessImage.scale(imageXRes,imageYRes)
    roughnessImage.pixels.foreach_get(roughnessArray)
    #outPixelArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    outPixelArray = np.copy(normalArray)
    outPixelArray[3::4] = roughnessArray[0::4]
    
    
    outImg = bpy.data.images.new(outImageName, imageXRes, imageYRes,alpha = True,is_data = True)
    outImg.alpha_mode = "CHANNEL_PACKED"
    outImg.colorspace_settings.name = "Non-Color"
    outImg.pixels.foreach_set(outPixelArray)
    return outImg
def packNRM(textureSetName,imageXRes,imageYRes,outImageName):
    #Pack NRM ----------------------------------------------
    normalImage = bpy.data.images[f"{textureSetName}_Normal"]
    return normalImage

def packNROC(textureSetName,imageXRes,imageYRes,outImageName):
    #Pack NROC ----------------------------------------------
    
    normalArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    normalImage = bpy.data.images[f"{textureSetName}_Normal"]
    normalImage.scale(imageXRes,imageYRes)
    normalImage.pixels.foreach_get(normalArray)
    
    roughnessArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    roughnessImage = bpy.data.images[f"{textureSetName}_Roughness"]
    roughnessImage.scale(imageXRes,imageYRes)
    roughnessImage.pixels.foreach_get(roughnessArray)
    
    aoArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    aoImage = bpy.data.images[f"{textureSetName}_AO"]
    aoImage.scale(imageXRes,imageYRes)
    aoImage.pixels.foreach_get(aoArray)
    
    normalArray[3::4] = aoArray[0::4]
    
    outPixelArray = NRMRToNRRX(normalArray)
    outPixelArray[2::4] = 1.0
    outImg = bpy.data.images.new(outImageName, imageXRes, imageYRes,alpha = True,is_data = True)
    outImg.alpha_mode = "CHANNEL_PACKED"
    outImg.colorspace_settings.name = "Non-Color"
    outImg.pixels.foreach_set(outPixelArray)
    return outImg
def packNRRT(textureSetName,imageXRes,imageYRes,outImageName):
    #Pack NRRT ----------------------------------------------
    
    normalArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    normalImage = bpy.data.images[f"{textureSetName}_Normal"]
    normalImage.scale(imageXRes,imageYRes)
    normalImage.pixels.foreach_get(normalArray)
    
    roughnessArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    roughnessImage = bpy.data.images[f"{textureSetName}_Roughness"]
    roughnessImage.scale(imageXRes,imageYRes)
    roughnessImage.pixels.foreach_get(roughnessArray)
    normalArray[3::4] = roughnessArray[0::4]
    
    outPixelArray = NRMRToNRRX(normalArray)
    outPixelArray[2::4] = 0.0
    outImg = bpy.data.images.new(outImageName, imageXRes, imageYRes,alpha = True,is_data = True)
    outImg.alpha_mode = "CHANNEL_PACKED"
    outImg.colorspace_settings.name = "Non-Color"
    outImg.pixels.foreach_set(outPixelArray)
    return outImg

def packNRRC(textureSetName,imageXRes,imageYRes,outImageName):
    #Pack NRRC ----------------------------------------------
    
    normalArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    normalImage = bpy.data.images[f"{textureSetName}_Normal"]
    normalImage.scale(imageXRes,imageYRes)
    normalImage.pixels.foreach_get(normalArray)
    
    roughnessArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    roughnessImage = bpy.data.images[f"{textureSetName}_Roughness"]
    roughnessImage.scale(imageXRes,imageYRes)
    roughnessImage.pixels.foreach_get(roughnessArray)
    normalArray[3::4] = roughnessArray[0::4]
    
    outPixelArray = NRMRToNRRX(normalArray)
    outPixelArray[2::4] = 1.0
    outImg = bpy.data.images.new(outImageName, imageXRes, imageYRes,alpha = True,is_data = True)
    outImg.alpha_mode = "CHANNEL_PACKED"
    outImg.colorspace_settings.name = "Non-Color"
    outImg.pixels.foreach_set(outPixelArray)
    return outImg

def packNRRA(textureSetName,imageXRes,imageYRes,outImageName):
    #Pack NRRA ----------------------------------------------
    
    normalArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    normalImage = bpy.data.images[f"{textureSetName}_Normal"]
    normalImage.scale(imageXRes,imageYRes)
    normalImage.pixels.foreach_get(normalArray)
    
    roughnessArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    roughnessImage = bpy.data.images[f"{textureSetName}_Roughness"]
    roughnessImage.scale(imageXRes,imageYRes)
    roughnessImage.pixels.foreach_get(roughnessArray)
    normalArray[3::4] = roughnessArray[0::4]
    
    alphaArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    alphaImage = bpy.data.images[f"{textureSetName}_Opacity"]
    alphaImage.scale(imageXRes,imageYRes)
    alphaImage.pixels.foreach_get(alphaArray)
	
    outPixelArray = NRMRToNRRX(normalArray)
    outPixelArray[2::4] = alphaArray[0::4]
    outImg = bpy.data.images.new(outImageName, imageXRes, imageYRes,alpha = True,is_data = True)
    outImg.alpha_mode = "CHANNEL_PACKED"
    outImg.colorspace_settings.name = "Non-Color"
    outImg.pixels.foreach_set(outPixelArray)
    return outImg

def packNRRO(textureSetName,imageXRes,imageYRes,outImageName):
    #Pack NRRO ----------------------------------------------
    
    normalArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    normalImage = bpy.data.images[f"{textureSetName}_Normal"]
    normalImage.scale(imageXRes,imageYRes)
    normalImage.pixels.foreach_get(normalArray)
    
    roughnessArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    roughnessImage = bpy.data.images[f"{textureSetName}_Roughness"]
    roughnessImage.scale(imageXRes,imageYRes)
    roughnessImage.pixels.foreach_get(roughnessArray)
    
    aoArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    aoImage = bpy.data.images[f"{textureSetName}_AO"]
    aoImage.scale(imageXRes,imageYRes)
    aoImage.pixels.foreach_get(aoArray)
    
    normalArray[3::4] = roughnessArray[0::4]
    
    outPixelArray = NRMRToNRRX(normalArray)
    outPixelArray[2::4] = aoArray[0::4]
    outImg = bpy.data.images.new(outImageName, imageXRes, imageYRes,alpha = True,is_data = True)
    outImg.alpha_mode = "CHANNEL_PACKED"
    outImg.colorspace_settings.name = "Non-Color"
    outImg.pixels.foreach_set(outPixelArray)
    return outImg

def packATOS(textureSetName,imageXRes,imageYRes,outImageName):
    #Pack ATOS ----------------------------------------------
    alphaArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    alphaImage = bpy.data.images[f"{textureSetName}_Opacity"]
    alphaImage.scale(imageXRes,imageYRes)
    alphaImage.pixels.foreach_get(alphaArray)
    
    aoArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    aoImage = bpy.data.images[f"{textureSetName}_AO"]
    aoImage.scale(imageXRes,imageYRes)
    aoImage.pixels.foreach_get(aoArray)
    outPixelArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    outPixelArray[0::4] = alphaArray[0::4]
    outPixelArray[1::4] = 1.0
    outPixelArray[2::4] = aoArray[0::4]
    outPixelArray[3::4] = 1.0
    
    
    outImg = bpy.data.images.new(outImageName, imageXRes, imageYRes,alpha = True,is_data = True)
    outImg.alpha_mode = "CHANNEL_PACKED"
    outImg.colorspace_settings.name = "Non-Color"
    outImg.pixels.foreach_set(outPixelArray)
    return outImg
def packOCMA(textureSetName,imageXRes,imageYRes,outImageName):
    #Pack OCMA ----------------------------------------------
    alphaArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    alphaImage = bpy.data.images[f"{textureSetName}_Opacity"]
    alphaImage.scale(imageXRes,imageYRes)
    alphaImage.pixels.foreach_get(alphaArray)
    
    aoArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    aoImage = bpy.data.images[f"{textureSetName}_AO"]
    aoImage.scale(imageXRes,imageYRes)
    aoImage.pixels.foreach_get(aoArray)
    outPixelArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    outPixelArray[0::4] = aoArray[0::4]
    outPixelArray[1::4] = 1.0
    outPixelArray[2::4] = 1.0
    outPixelArray[3::4] = alphaArray[0::4]
    
    
    outImg = bpy.data.images.new(outImageName, imageXRes, imageYRes,alpha = True,is_data = True)
    outImg.alpha_mode = "CHANNEL_PACKED"
    outImg.colorspace_settings.name = "Non-Color"
    outImg.pixels.foreach_set(outPixelArray)
    return outImg

def packSCOT(textureSetName,imageXRes,imageYRes,outImageName):
    #Pack SCOT ----------------------------------------------
    
    aoArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    aoImage = bpy.data.images[f"{textureSetName}_AO"]
    aoImage.scale(imageXRes,imageYRes)
    aoImage.pixels.foreach_get(aoArray)
    outPixelArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
    outPixelArray[0::4] = 1.0
    outPixelArray[1::4] = 1.0
    outPixelArray[0::4] = aoArray[0::4]
    outPixelArray[3::4] = 0.0
    
    
    outImg = bpy.data.images.new(outImageName, imageXRes, imageYRes,alpha = True,is_data = True)
    outImg.alpha_mode = "CHANNEL_PACKED"
    outImg.colorspace_settings.name = "Non-Color"
    outImg.pixels.foreach_set(outPixelArray)
    return outImg
#-------------------

texTypeDict = {
	"alb":packALB,
	"alba":packALBA,
	"albd":packALBD,
	"albm":packALBM,
	"alp":packALP,
	"atoc":packATOS,
	"atos":packATOS,
	"acot":packATOS,
	"emi":packEMI,
	"nrm":packNRM,
	"nrmr":packNRMR,
	"nroc":packNROC,
	"nroe":packNROC,
	"nrof":packNROC,
	"nrrt":packNRRT,
	"nrrc":packNRRC,
	"nrrm":packNRRC,
	"nrro":packNRRO,
	"nrra":packNRRA,
	"ocma":packOCMA,
	"ocnm":packOCMA,
	"scot":packSCOT,
	}


def getTexturePacker(texType):
	return texTypeDict[texType.lower()]#If you get an error here and you're on the latest version, please report what material presets you used
