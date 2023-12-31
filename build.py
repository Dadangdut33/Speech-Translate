import os
import shutil
import sys
from importlib.metadata import version as get_version

from cx_Freeze import Executable, setup

sys.setrecursionlimit(5000)


def get_env_name():
    return os.path.basename(sys.prefix)


def app_version():
    with open(os.path.join(os.path.dirname(__file__), "speech_translate/_version.py"), encoding="utf-8") as f_ver:
        return f_ver.readline().split("=")[1].strip().strip('"').strip("'")


# If you get cuda error try to remove your cuda from your system path because cx_freeze will try to include it from there
# instead of the one in the python folder
print(">> Building SpeechTranslate version", app_version())
print(">> Environment:", get_env_name())
# run build_patch.py
print(">> Running build_patch.py")
os.system("python build_patch.py")
print(">> Done")


def clear_dir(_dir):
    print(">> Clearing", _dir)
    try:
        if not os.path.exists(_dir):
            return
        if os.path.isfile(_dir):
            os.remove(_dir)
        else:
            # remove all files or folders in the dir
            for f_get in os.listdir(_dir):
                try:
                    shutil.rmtree(os.path.join(_dir, f_get))
                except Exception:
                    os.remove(os.path.join(_dir, f_get))
    except Exception as e:
        print(f">> Failed to clear {_dir} reason: {e}")


def get_whisper_version():
    ver = get_version("openai-whisper")
    print(">> Getting whisper version")
    print(">> Whisper version:", ver)
    return ver


print(">> Clearing code folder")
# clear_dir("./speech_translate/_user") # use this if base filter is updated
clear_dir("./speech_translate/_user/settings.json")
clear_dir("./speech_translate/export")
clear_dir("./speech_translate/debug")
clear_dir("./speech_translate/log")
clear_dir("./speech_translate/temp")
clear_dir("./speech_translate/assets/silero-vad/__pycache__")
print(">> Done")
print("Whisper version:", get_whisper_version())

folder_name = f"build/SpeechTranslate {app_version()} {get_env_name()}"
root = os.path.dirname(os.path.abspath(__file__))

print("ROOT:", root)
print("Assets:", os.path.abspath(os.path.join(root, "speech_translate", "assets")))

build_exe_options = {
    "excludes": ["yapf", "ruff", "cx_Freeze", "pylint", "isort"],
    "packages": ["torch", "soundfile", "sounddevice", "av", "stable_whisper", "faster_whisper", "whisper"],
    "build_exe": folder_name,
    "include_msvcr": True,
    "include_files": [(os.path.abspath(os.path.join(root, "speech_translate", "assets")), "lib/speech_translate/assets")],
}

BASE = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="SpeechTranslate",
    version=app_version(),
    description="Speech Translate",
    options={
        "build_exe": build_exe_options,
    },
    executables=[
        Executable(
            "Run.py",
            base=BASE,
            icon="speech_translate/assets/icon.ico",
            target_name="SpeechTranslate.exe",
        )
    ],
)

# check if arg is build_exe
if len(sys.argv) < 2 or sys.argv[1] != "build_exe":
    sys.exit(0)

print(">> Copying some more files...")

# we need to copy av.libs to foldername/lib because cx_freeze doesn't copy it for some reason
print(">> Copying av.libs to lib folder")
shutil.copytree(f"{get_env_name()}/Lib/site-packages/av.libs", f"{folder_name}/lib/av.libs")

# we also need to copy openai_whisper-{version}.dist-info to foldername/lib because cx_freeze doesn't copy it
print(">> Copying whisper metadata to lib folder")
shutil.copytree(
    f"{get_env_name()}/Lib/site-packages/openai_whisper-{get_whisper_version()}.dist-info",
    f"{folder_name}/lib/openai_whisper-{get_whisper_version()}.dist-info"
)

# copy LICENSE as license.txt to build folder
print(">> Creating license.txt to build folder")
with open("LICENSE", "r", encoding="utf-8") as f:
    with open(f"{folder_name}/license.txt", "w", encoding="utf-8") as f2:
        f2.write(f.read())

# copy README.md as README.txt to build folder
print(">> Creating README.txt to build folder")
with open("build/pre_install_note.txt", "r", encoding="utf-8") as f:
    with open(f"{folder_name}/README.txt", "w", encoding="utf-8") as f2:
        f2.write(f.read())

# create version.txt
print(">> Creating version.txt")
with open(f"{folder_name}/version.txt", "w", encoding="utf-8") as f:
    f.write(app_version())

# create link to repo
print(">> Creating link to repo")
with open(f"{folder_name}/homepage.url", "w", encoding="utf-8") as f:
    f.write("[InternetShortcut]\n")
    f.write("URL=https://github.com/Dadangdut33/Speech-Translate")

print(">> Opening output folder")
output_folder = os.path.abspath(folder_name)
try:
    os.startfile(output_folder)
except Exception:
    # linux
    import subprocess

    subprocess.call(["xdg-open", output_folder])
