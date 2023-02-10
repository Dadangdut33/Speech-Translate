from speech_translate._version import __version__
from cx_Freeze import setup, Executable

build_options = {
    "packages": ["asyncio"],
    "includes": [],
    "excludes": ["pyinstaller", "cx_Freeze"],
    "include_files": [
        ("theme", "theme"),
        ("user_manual", "user_manual"),
        ("assets", "lib/assets"),
        ("LICENSE", "LICENSE.txt"),
    ],
}

import sys

# ask for console or not
console = input("Do you want to hide console window? (y/n) (default y): ").lower()
if console == "n":
    base = None
    print(">> Console window will be shown")
else:
    base = "Win32GUI" if sys.platform == "win32" else None
    print(">> Console window will be hidden")

target = Executable("Main.py", base=base, target_name="SpeechTranslate", icon="assets/logo.ico")

setup(
    name="Speech Translate",
    version=__version__,
    author="Dadangdut33",
    url="https://github.com/Dadangdut33/Speech-Translate",
    download_url="https://github.com/Dadangdut33/Speech-Translate/releases/latest",
    license="MIT",
    license_files=["LICENSE"],
    description="A Screen Translator/OCR Translator made by using Python and Tesseract",
    options={"build_exe": build_options},
    executables=[target],
)
