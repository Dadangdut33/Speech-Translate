import os

# Paths
dir_project: str = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__))))
dir_user: str = os.path.abspath(os.path.join(dir_project, "_user"))
dir_theme: str = os.path.abspath(os.path.join(dir_project, "theme"))
dir_temp: str = os.path.abspath(os.path.join(dir_project, "temp"))
dir_debug: str = os.path.abspath(os.path.join(dir_project, "debug"))
dir_log: str = os.path.abspath(os.path.join(dir_project, "log"))
dir_assets: str = os.path.abspath(os.path.join(dir_project, "assets"))
dir_export: str = os.path.abspath(os.path.join(dir_project, "export"))
app_icon: str = os.path.abspath(os.path.join(dir_assets, "icon.ico"))
parameters_text: str = os.path.abspath(os.path.join(dir_assets, "parameter.txt"))
ffmpeg_ps_script: str = os.path.abspath(os.path.join(dir_project, "..", "install_ffmpeg.ps1"))

# verify app_icon exist or not
if not os.path.exists(app_icon):
    app_icon_missing = True
else:
    app_icon_missing = False
