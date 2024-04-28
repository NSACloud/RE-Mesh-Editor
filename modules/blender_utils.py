#Author: NSA Cloud
import bpy

from .gen_functions import textColors
import os

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