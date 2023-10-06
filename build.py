import sys
import os
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

build_exe_options = {
    "excludes": ["yapf", "ruff"],
    "packages": ["torch", "soundfile", "sounddevice"],
    "build_exe": "build/SpeechTranslate"
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
# copy Lincese as license.txt to build folder
with open("LICENSE", "r", encoding="utf-8") as f:
    with open("build/SpeechTranslate/license.txt", "w", encoding="utf-8") as f2:
        f2.write(f.read())

# copy README.md as README.txt to build folder
with open("README.md", "r", encoding="utf-8") as f:
    with open("build/SpeechTranslate/README.txt", "w", encoding="utf-8") as f2:
        f2.write(f.read())

# create version.txt
with open("build/SpeechTranslate/version.txt", "w", encoding="utf-8") as f:
    f.write(version())

# create link to repo
with open("build/SpeechTranslate/homepage.url", "w", encoding="utf-8") as f:
    f.write("[InternetShortcut]\n")
    f.write("URL=https://github.com/Dadangdut33/Speech-Translate")

print(">> Opening output folder")
output_folder = os.path.abspath("build/SpeechTranslate")
try:
    os.startfile(output_folder)
except Exception:
    # linux
    import subprocess

    subprocess.call(["xdg-open", output_folder])
