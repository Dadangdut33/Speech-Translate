import os
import platform
import time

pip = "pip"
req = "requirements"
# check if not windows
if platform.system() != "Windows":
    pip = "pip3"
    req = "requirements_notwindows"


def install_requirements():
    os.system(f"{pip} install -r {req}.txt")


def uninstall_torch():
    os.system(f"{pip} uninstall -y torch")


def install_torch():
    if platform.system() == "Darwin": # if mac
        os.system(f"{pip} install torch torchvision torchaudio")
    elif platform.system() == "Linux":
        os.system(f"{pip} install torch torchvision torchaudio")
    elif platform.system() == "Windows":
        os.system(f"{pip} install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu117")
    else:
        print("Unknown OS, please install torch manually by visting https://pytorch.org/")


if __name__ == "__main__":
    # ask if user want to use gpu or not
    print("-" * 100)
    print("This script will try to install the necessary packages for the project")
    use_gpu = input("Do you want to use GPU for pytorch? (y/n): ")

    timeStart = time.time()
    # install requirements
    print("-" * 100)
    print(f"Installing from {req}.txt")
    install_requirements()

    if use_gpu.lower() == "y":
        # uninstall torch
        print("-" * 100)
        print("Uninstalling torch")
        uninstall_torch()

        # install torch
        print("-" * 100)
        print("Installing torch")
        install_torch()

    print("-" * 100)
    print("Done!")
    print(f"Total time {time.time() - timeStart: .2f}")
