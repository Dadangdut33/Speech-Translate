import sys
import os
import shutil
from cx_Freeze import setup, Executable

sys.setrecursionlimit(5000)


def get_env_name():
    return os.path.basename(sys.prefix)


def version():
    with open(os.path.join(os.path.dirname(__file__), "speech_translate/_version.py")) as f:
        return f.readline().split("=")[1].strip().strip('"').strip("'")


# If you get cuda error try to remove your cuda from your system path because cx_freeze will try to include it from there
# instead of the one in the python folder
print(">> Building SpeechTranslate version", version())
print(">> Environment:", get_env_name())


def clear_dir(dir):
    print(">> Clearing", dir)
    try:
        if not os.path.exists(dir):
            return
        if os.path.isdir(dir):
            for f in os.listdir(dir):
                os.remove(os.path.join(dir, f))

            # remove the folder
            os.rmdir(dir)
        else:
            os.remove(dir)
    except Exception as e:
        print(f">> Failed to clear {dir} reason: {e}")


def get_whisper_version_from_requirements_txt():
    with open("requirements.txt", "r", encoding="utf-8") as f:
        for line in f.readlines():
            if line.startswith("openai-whisper"):
                return line.split("==")[1].strip()


print(">> Clearing code folder")
clear_dir("./speech_translate/_user")
clear_dir("./speech_translate/export")
clear_dir("./speech_translate/debug")
clear_dir("./speech_translate/log")
clear_dir("./speech_translate/temp")
print(">> Done")
print("Whisper version:", get_whisper_version_from_requirements_txt())

folder_name = f"build/SpeechTranslate {version()} {get_env_name()}"

build_exe_options = {
    "excludes": ["yapf", "ruff"],
    "packages": ["torch", "soundfile", "sounddevice", "av", "stable_whisper", "faster_whisper", "whisper"],
    "build_exe": folder_name
}

base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="SpeechTranslate",
    version=version(),
    description="Speech Translate",
    options={
        "build_exe": build_exe_options,
    },
    executables=[
        Executable(
            "Run.py",
            base=base,
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
    f"{get_env_name()}/Lib/site-packages/openai_whisper-{get_whisper_version_from_requirements_txt()}.dist-info",
    f"{folder_name}/lib/openai_whisper-{get_whisper_version_from_requirements_txt()}.dist-info"
)

# copy Lincese as license.txt to build folder
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
    f.write(version())

# copy install_ffmpeg.ps1 to build folder
print(">> Copying install_ffmpeg.ps1 to build folder")
shutil.copyfile("install_ffmpeg.ps1", f"{folder_name}/install_ffmpeg.ps1")
shutil.copyfile("install_ffmpeg.ps1", f"{folder_name}/lib/install_ffmpeg.ps1")

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
