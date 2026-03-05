# Made by tek.dev if ur gonna skid at least give credits

import sys
import os
import time
import threading
from ctypes import windll, byref, Structure, wintypes
import ctypes
import requests
try:
    from pymem import Pymem
    from pymem.process import list_processes
    import dearpygui.dearpygui as dpg
except ImportError as e:
    print(f"Missing dependency: {e}")
    input("Press Enter to exit...")
    sys.exit(1)

PID = -1
baseAddr = None
pm = Pymem()
offsets = {}
injected = False
speed_enabled = False
speed_value = 50.0

def DRP(address):
    try:
        return int.from_bytes(pm.read_bytes(address, 8), "little")
    except:
        return 0

def ReadRobloxString(expected_address):
    try:
        string_count = pm.read_int(expected_address + 0x10)
        if string_count > 15:
            ptr = DRP(expected_address)
            return pm.read_string(ptr, string_count)
        return pm.read_string(expected_address, string_count)
    except:
        return ""

def GetClassName(instance):
    try:
        ptr = pm.read_longlong(instance + 0x18)
        ptr = pm.read_longlong(ptr + 0x8)
        fl = pm.read_longlong(ptr + 0x18)
        if fl == 0x1F:
            ptr = pm.read_longlong(ptr)
        return ReadRobloxString(ptr)
    except:
        return ""

def GetChildren(instance):
    if not instance: return []
    children = []
    try:
        start = DRP(instance + int(offsets['Children'], 16))
        if start == 0: return []
        end = DRP(start + 8)
        current = DRP(start)
        for _ in range(2000):
            if current == end: break
            children.append(pm.read_longlong(current))
            current += 0x10
    except: pass
    return children

def FindFirstChildOfClass(instance, class_name):
    for child in GetChildren(instance):
        if GetClassName(child) == class_name:
            return child
    return 0

def attach_to_roblox():
    global PID, baseAddr, pm, injected
    for proc in list_processes():
        if proc.szExeFile.decode() == "RobloxPlayerBeta.exe":
            try:
                pm.open_process_from_id(proc.th32ProcessID)
                PID = proc.th32ProcessID
                for module in pm.list_modules():
                    if module.name == "RobloxPlayerBeta.exe":
                        baseAddr = module.lpBaseOfDll
                        injected = True
                        return True
            except: pass
    return False

def speed_loop():
    global speed_enabled, speed_value, injected, baseAddr
    while True:
        if speed_enabled and injected and baseAddr:
            try:
                fakeDatamodel = pm.read_longlong(baseAddr + int(offsets['FakeDataModelPointer'], 16))
                dataModel = pm.read_longlong(fakeDatamodel + int(offsets['FakeDataModelToDataModel'], 16))
                plrsAddr = FindFirstChildOfClass(dataModel, 'Players')
                lpAddr = pm.read_longlong(plrsAddr + int(offsets['LocalPlayer'], 16))
                lpChar = pm.read_longlong(lpAddr + int(offsets['ModelInstance'], 16))
                
                if lpChar:
                    humanoid = FindFirstChildOfClass(lpChar, 'Humanoid')
                    if humanoid:
                        check_offset = int(offsets['WalkSpeedCheck'], 16)
                        value_offset = int(offsets['WalkSpeed'], 16)
                        pm.write_float(humanoid + check_offset, float('inf'))
                        pm.write_float(humanoid + value_offset, float(speed_value))
            except: pass
        time.sleep(0.01)

def on_attach():
    if attach_to_roblox():
        dpg.set_value("status_text", "Status: Attached")
        dpg.configure_item("status_text", color=(100, 255, 100))
    else:
        dpg.set_value("status_text", "Status: Not Found")
        dpg.configure_item("status_text", color=(255, 100, 100))

def drag_viewport(sender, app_data):
    if dpg.get_mouse_pos(local=True)[1] < 40:
        pos = dpg.get_viewport_pos()
        dpg.set_viewport_pos([pos[0] + app_data[1], pos[1] + app_data[2]])

if __name__ == "__main__":
    try:
        offsets = requests.get('https://offsets.ntgetwritewatch.workers.dev/offsets.json').json()
    except: sys.exit(1)

    threading.Thread(target=speed_loop, daemon=True).start()

    dpg.create_context()
    
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (12, 12, 14, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (20, 20, 22, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Button, (45, 45, 120, 200))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (60, 60, 150, 255))
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 12)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 15, 15)

    with dpg.theme() as close_btn_theme:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (180, 50, 50, 150))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (220, 50, 50, 255))

    with dpg.handler_registry():
        dpg.add_mouse_drag_handler(button=dpg.mvMouseButton_Left, callback=drag_viewport)

    with dpg.window(label="Goon Cheat Base", width=320, height=220, no_resize=True, no_collapse=True, no_move=True, no_title_bar=True, tag="MainWin"):
        with dpg.group(horizontal=True):
            dpg.add_text("GOON BASE", color=(120, 120, 255))
            dpg.add_spacer(width=165)
            dpg.add_button(label="X", width=30, height=20, callback=lambda: os._exit(0), tag="close_btn")
            dpg.bind_item_theme("close_btn", close_btn_theme)
        
        dpg.add_separator()
        dpg.add_spacer(height=10)
        
        dpg.add_button(label="ATTACH TO ROBLOX", callback=on_attach, width=-1, height=45)
        dpg.add_spacer(height=10)
        
        with dpg.group(horizontal=True):
            dpg.add_checkbox(label="ENABLE SPEED", callback=lambda s, a: globals().update(speed_enabled=a))
            dpg.add_spacer(width=10)

        dpg.add_slider_float(label="", default_value=50.0, min_value=16.0, max_value=300.0, callback=lambda s, a: globals().update(speed_value=a), width=-1)
        
        dpg.add_spacer(height=10)
        dpg.add_separator()
        dpg.add_text("Status: Idle", tag="status_text", color=(150, 150, 150))

    dpg.bind_theme(global_theme)
    dpg.create_viewport(title="Goon Cheat Base", width=320, height=220, resizable=False, decorated=False, always_on_top=True)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("MainWin", True)
    dpg.start_dearpygui()
    dpg.destroy_context()
