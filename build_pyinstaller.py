"""
Pyinstaller script to move stuff, rename, and also make a cleaner output folder
"""

import os, shutil, sys
from PyInstaller.__main__ import generate_parser, run  # type: ignore
from speech_translate._version import __version__


def run_makespec(filenames, **opts):
    print(">> Generating spec file...")
    # Split pathex by using the path separator
    temppaths = opts["pathex"][:]
    pathex = opts["pathex"] = []
    for p in temppaths:
        pathex.extend(p.split(os.pathsep))

    import PyInstaller.building.makespec # type: ignore

    spec_file = PyInstaller.building.makespec.main(filenames, **opts)
    return spec_file


def get_env_name():
    return os.path.basename(sys.prefix)


def get_base_prefix_compat():
    """Get base/real prefix, or sys.prefix if there is none."""
    return getattr(sys, "base_prefix", None) or getattr(sys, "real_prefix", None) or sys.prefix


def in_virtualenv():
    return get_base_prefix_compat() != sys.prefix


if not in_virtualenv():
    print("Please run this script in a virtual environment")
    sys.exit(1)

options = [
    "Run.py",
    "-c",  # console window. Console window cannot be hidden because it will cause error on whisper transformer logging
    "--clean",
    "--noconfirm",
    "--additional-hooks-dir=./_pyinstaller_hooks",
    "--runtime-hook=./_pyinstaller_hooks/add_lib.py",
    "--icon=./speech_translate/assets/icon.ico",
    "--add-data=./speech_translate/theme;speech_translate/theme",
    "--add-data=./speech_translate/assets;speech_translate/assets",
    "--add-data=./LICENSE.txt;.",
    f"--add-data={get_env_name()}/Lib/site-packages/whisper/assets;whisper/assets/",
    "--copy-metadata=tqdm",
    "--copy-metadata=regex",
    "--copy-metadata=requests",
    "--copy-metadata=packaging",
    "--copy-metadata=filelock",
    "--copy-metadata=numpy",
    "--copy-metadata=tokenizers",
    "--exclude-module=pyinstaller",
]

print(f"Currently running in virtual environment {get_env_name()} using python {sys.version}")
specName = f"SpeechTranslate {__version__}"
argsName = f"-n{specName}"  # name of the spec file

options.append(argsName)
# -----------------
# make spec file
parser = generate_parser()
args = parser.parse_args(options)
run_makespec(**vars(args))

# Edit spec folder
folderName = f"{specName} {get_env_name()}"
specFile = f"{specName}.spec"
spec = ""
with open(specFile, "r") as f:
    spec = f.read()
    # add recursion limit after copy_metadata
    spec = spec.replace("copy_metadata", "copy_metadata\nimport sys\nsys.setrecursionlimit(5000)", 1)
    # rename the exe file
    spec = spec.replace(f"name='{specName}'", f"name='SpeechTranslate'", 1)
    # rename the build folder name, add venv name to it
    spec = spec.replace(f"name='{specName}'", f"name='{folderName}'", 1)

# write spec file
with open(specFile, "w") as f:
    f.write(spec)

# create license.txt file
with open("LICENSE", "r") as f:
    license = f.read()
    with open("LICENSE.txt", "w") as f2:
        f2.write(license)

# run pyinstaller
run([specFile, "--noconfirm", "--clean"])

# delete license.txt file
print(">> Deleting created license.txt file")
os.remove("LICENSE.txt")

output_folder = f"dist/{folderName}"

# create lib folder in output folder
lib_folder = f"{output_folder}/lib"
os.mkdir(lib_folder)

# move all .dll .pyd files to lib folder with some whitelist
# whitelist some dll files and numpy dependencies (libopenblas)
print(">> Moving .dll files to lib folder")
dontMove = ["python3.dll", "python310.dll", "python38.dll", "python39.dll"]
for file in os.listdir(output_folder):
    if file.endswith(".dll") or file.endswith(".pyd"):
        if file not in dontMove and "libopenblas" not in file:
            shutil.move(f"{output_folder}/{file}", f"{lib_folder}/{file}")

# open folder
print(">> Opening output folder")
output_folder = os.path.abspath(output_folder)
try:
    os.startfile(output_folder)
except Exception:
    # linux
    import subprocess

    subprocess.call(["xdg-open", output_folder])
