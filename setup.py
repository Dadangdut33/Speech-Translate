import os
import platform
import time


def install_requirements():
    os.system("pip install -r requirements.txt")


def uninstall_torch():
    os.system("pip uninstall torch")


def install_torch():
    # if mac
    if platform.system() == "Darwin":
        os.system("pip install pytorch torchvision torchaudio -c pytorch")
    else:  # windows and linux
        os.system("pip install pytorch torchvision torchaudio pytorch-cuda=11.7 -c pytorch -c nvidia")


if __name__ == "__main__":
    # ask if user want to use gpu or not
    print("-" * 100)
    print("This script will try to install the necessary packages for the project")
    use_gpu = input("Do you want to use GPU for pytorch? (y/n): ")

    timeStart = time.time()
    # install requirements
    print("-" * 100)
    print("Installing from requirements.txt")
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
