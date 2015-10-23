# provides file dialog functions
# uses "module as a singleton" approach to remember the default directory

import wx, os
import wx.lib.agw.multidirdialog as MDD

# setup a default path
default_dir = os.path.abspath(os.path.join(os.getcwd(), os.path.pardir, 'data/'))
if not os.path.exists(default_dir):
    default_dir = os.getcwd()
default_dir=""
# opens a dialog to save a file
def save_file_dialog(message="Save File", file_types="*.*", default_file=""):
    global default_dir

    dlg = wx.FileDialog(None, message, default_dir, default_file, file_types, wx.SAVE | wx.FD_OVERWRITE_PROMPT)
    path = None
    if dlg.ShowModal() == wx.ID_OK:
        path = dlg.GetPath()
        default_dir = os.path.dirname(path)

    dlg.Destroy()
    return path


# opens a dialog to choose a single file
def open_file_dialog(message="Open File", file_types="*.*"):
    global default_dir

    dlg = wx.FileDialog(None, message, default_dir, "", file_types, wx.OPEN | wx.FD_FILE_MUST_EXIST)
    path = None
    if dlg.ShowModal() == wx.ID_OK:
        path = dlg.GetPath()
        default_dir = os.path.dirname(path)

    dlg.Destroy()
    return path


# opens a dialog to choose multiple files
def open_multiple_files_dialog(message="Open Files", file_type="*.*"):
    default_dir=""

    dlg = wx.FileDialog(None, message, default_dir, "", file_type, wx.OPEN | wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST)
    path = None
    file_names = None
    if dlg.ShowModal() == wx.ID_OK:
        path = dlg.GetPath()
        if path is not None:
            file_names = [os.path.join(os.path.dirname(path.encode('ascii')), f.encode('ascii')) for f in dlg.GetFilenames()]
            default_dir = os.path.dirname(path)

    dlg.Destroy()
    return file_names


# opens a dialog to choose a directory
def open_dir_dialog(message="Select a Folder"):
    global default_dir
    dlg = wx.DirDialog(None, message, default_dir)
    path = None
    if dlg.ShowModal() == wx.ID_OK:
        path = dlg.GetPath()
        default_dir = path

    dlg.Destroy()
    return path

def open_multiple_dir_dialog(message,default):
    dlg=MDD.MultiDirDialog(None,message=message,defaultPath=default,agwStyle=MDD.DD_MULTIPLE | MDD.DD_DIR_MUST_EXIST)
    dirs=None
    if dlg.ShowModal() == wx.ID_OK:
        dirs = dlg.GetPaths()
    dlg.Destroy()
    return dirs

def open_single_dir_dialog(message,default):
    global default_dir
    dlg = wx.DirDialog(None, message, default)
    #dlg=MDD.MultiDirDialog(None,message=message,defaultPath=default,agwStyle=MDD.DD_NEW_DIR_BUTTON)
    dir=None
    if dlg.ShowModal() == wx.ID_OK:
        dir = dlg.GetPath()
        default_dir=dir
    dlg.Destroy()
    return dir

# TODO: Simple Figure Dialog App to feed into parsers