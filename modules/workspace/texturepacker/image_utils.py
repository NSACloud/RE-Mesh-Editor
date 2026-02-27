import numpy as np
import os
def NRRXToNRMR(NRRXArray):
    
    NRMRArray = np.empty(len(NRRXArray), dtype=np.float32)
    
    nx = NRRXArray[1::4] * 2.0 - 1.0
    ny = -(NRRXArray[3::4] * 2.0 - 1.0)
    
    nx = np.sign(nx) * (nx ** 2.0)
    ny = np.sign(ny) * (ny ** 2.0)
    
    angle = np.pi * 0.25
    cos_a = np.cos(angle)
    sin_a = np.sin(angle)
    x = nx * cos_a - ny * sin_a
    y = nx * sin_a + ny * cos_a
    
    z_sq = 1.0 - (x**2 + y**2)
    z = np.sqrt(np.clip(z_sq, 0.0, None))
    
    length = np.sqrt(x**2 + y**2 + z**2)
    x /= length
    y /= length
    z /= length
    
    x = (x + 1.0) * 0.5
    y = (y + 1.0) * 0.5
    z = (z + 1.0) * 0.5
    
    NRMRArray[0::4] = x.ravel()
    NRMRArray[1::4] = y.ravel()
    NRMRArray[2::4] = z.ravel()
    NRMRArray[3::4] = NRRXArray[0::4]
    return NRMRArray


def NRMRToNRRX(NRMRArray):
    NRMRArray = np.asarray(NRMRArray, dtype=np.float32)
    #Result is a bit brighter than the original nrrx but it's close enough that I don't think it matters much
    x = NRMRArray[0::4]
    y = NRMRArray[1::4]
    r = NRMRArray[3::4]

    x = x * 2.0 - 1.0
    y = y * 2.0 - 1.0

    cos_a = np.cos(np.deg2rad(-45))
    sin_a = np.sin(np.deg2rad(-45))

    nr_x = x * cos_a - y * sin_a
    nr_y = x * sin_a + y * cos_a

    nr_x = np.sign(nr_x) * np.sqrt(np.abs(nr_x))
    nr_y = np.sign(nr_y) * np.sqrt(np.abs(nr_y))

    nr_x = (nr_x + 1.0) * 0.5
    nr_y = (nr_y + 1.0) * 0.5

    np.clip(nr_x, 0.0, 1.0, out=nr_x)
    np.clip(nr_y, 0.0, 1.0, out=nr_y)

    NRRXArray = np.empty_like(NRMRArray)

    NRRXArray[0::4] = r
    NRRXArray[1::4] = nr_x
    NRRXArray[2::4] = 1.0
    NRRXArray[3::4] = nr_y

    return NRRXArray


def generatePlaceholderMaps(textureSetName,imageXRes,imageYRes,useExistingBakes,bakeDir,fileExtension):
	import bpy
	print(f"Texture Set: {textureSetName}")
	print(f"Resolution: {imageXRes}x{imageYRes}\n")
	print("Generating Placeholder Textures...")
	
	
	imageName = f"{textureSetName}_BaseColor"
	
	generateImage = True
	bakePath = os.path.join(bakeDir,imageName+fileExtension)
	if useExistingBakes and os.path.isfile(bakePath):
		img = bpy.data.images.load(bakePath,check_existing = True)
		img.name = imageName
		
		print(f"\tLoaded existing bake for {imageName}")
		generateImage = False
	else:
		img = bpy.data.images.new(imageName,imageXRes,imageYRes,is_data = False)
		

	img.colorspace_settings.name = "sRGB"
	img.alpha_mode = "CHANNEL_PACKED"
	
	if generateImage:
		print("Generating Blank Base Color...")
		outPixelArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
		outPixelArray[0::4] = 1.0
		outPixelArray[1::4] = 1.0
		outPixelArray[2::4] = 1.0
		outPixelArray[3::4] = 1.0
		img.pixels.foreach_set(outPixelArray)
	
	generateImage = True
	imageName = f"{textureSetName}_Normal"
	bakePath = os.path.join(bakeDir,imageName+fileExtension)
	if useExistingBakes and os.path.isfile(bakePath):
		img = bpy.data.images.load(bakePath,check_existing = True)
		img.name = imageName
		print(f"\tLoaded existing bake for {imageName}")
		generateImage = False
	else:
		img = bpy.data.images.new(imageName,imageXRes,imageYRes,is_data = True)
	img.colorspace_settings.name = "Non-Color"
	img.alpha_mode = "CHANNEL_PACKED"
	
	if generateImage:
		print("Generating Blank Normal...")
		outPixelArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
		outPixelArray[0::4] = 0.5
		outPixelArray[1::4] = 0.5
		outPixelArray[2::4] = 1.0
		outPixelArray[3::4] = 1.0
		img.pixels.foreach_set(outPixelArray)
	
	
	imageName = f"{textureSetName}_Roughness"
	generateImage = True
	bakePath = os.path.join(bakeDir,imageName+fileExtension)
	if useExistingBakes and os.path.isfile(bakePath):
		img = bpy.data.images.load(bakePath,check_existing = True)
		img.name = imageName
		print(f"\tLoaded existing bake for {imageName}")
		generateImage = False
	else:
		img = bpy.data.images.new(imageName,imageXRes,imageYRes,is_data = True)
	img.colorspace_settings.name = "Non-Color"
	
	if generateImage:
		print("Generating Blank Roughness...")
		outPixelArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
		outPixelArray[0::4] = 1.0
		outPixelArray[1::4] = 1.0
		outPixelArray[2::4] = 1.0
		outPixelArray[3::4] = 1.0
		img.pixels.foreach_set(outPixelArray)

	
	imageName = f"{textureSetName}_Emissive"
	generateImage = True
	bakePath = os.path.join(bakeDir,imageName+fileExtension)
	if useExistingBakes and os.path.isfile(bakePath):
		img = bpy.data.images.load(bakePath,check_existing = True)
		img.name = imageName
		print(f"\tLoaded existing bake for {imageName}")
		generateImage = False
	else:
		img = bpy.data.images.new(imageName,imageXRes,imageYRes,is_data = True)
	img.colorspace_settings.name = "Non-Color"
	
	if generateImage:
		print("Generating Blank Emissive...")
		outPixelArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
		outPixelArray[0::4] = 0.0
		outPixelArray[1::4] = 0.0
		outPixelArray[2::4] = 0.0
		outPixelArray[3::4] = 0.0
		img.pixels.foreach_set(outPixelArray)
	
	
	imageName = f"{textureSetName}_AO"
	generateImage = True
	bakePath = os.path.join(bakeDir,imageName+fileExtension)
	if useExistingBakes and os.path.isfile(bakePath):
		img = bpy.data.images.load(bakePath,check_existing = True)
		img.name = imageName
		print(f"\tLoaded existing bake for {imageName}")
		generateImage = False
	else:
		img = bpy.data.images.new(imageName,imageXRes,imageYRes,is_data = True)
	img.colorspace_settings.name = "Non-Color"
	
	if generateImage:
		print("Generating Blank Ambient Occlusion...")
		outPixelArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
		outPixelArray[0::4] = 1.0
		outPixelArray[1::4] = 1.0
		outPixelArray[2::4] = 1.0
		outPixelArray[3::4] = 1.0
		img.pixels.foreach_set(outPixelArray)
	
	
	imageName = f"{textureSetName}_Metallic"
	generateImage = True
	bakePath = os.path.join(bakeDir,imageName+fileExtension)
	if useExistingBakes and os.path.isfile(bakePath):
		img = bpy.data.images.load(bakePath,check_existing = True)
		img.name = imageName
		print(f"\tLoaded existing bake for {imageName}")
		generateImage = False
	else:
		img = bpy.data.images.new(imageName,imageXRes,imageYRes,is_data = True)
	img.colorspace_settings.name = "Non-Color"
	
	if generateImage:
		print("Generating Blank Metallic...")
		outPixelArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
		outPixelArray[0::4] = 0.0
		outPixelArray[1::4] = 0.0
		outPixelArray[2::4] = 0.0
		outPixelArray[3::4] = 0.0
		img.pixels.foreach_set(outPixelArray)
	
	
	imageName = f"{textureSetName}_Opacity"
	generateImage = True
	bakePath = os.path.join(bakeDir,imageName+fileExtension)
	if useExistingBakes and os.path.isfile(bakePath):
		img = bpy.data.images.load(bakePath,check_existing = True)
		img.name = imageName
		print(f"\tLoaded existing bake for {imageName}")
		generateImage = False
	else:
		img = bpy.data.images.new(imageName,imageXRes,imageYRes,is_data = True)
	img.colorspace_settings.name = "Non-Color"
	
	if generateImage:
		print("Generating Blank Alpha...")
		outPixelArray = np.empty(shape = imageXRes*imageYRes*4, dtype=np.float32)
		outPixelArray[0::4] = 1.0
		outPixelArray[1::4] = 1.0
		outPixelArray[2::4] = 1.0
		outPixelArray[3::4] = 1.0
		img.pixels.foreach_set(outPixelArray)