import os
import platform
import time

pip = "pip"
req = "requirements"
tempfile = req + "_temp"
# check if not windows
if platform.system() != "Windows":
    pip = "pip3"

if __name__ == "__main__":
    # ask if user want to use gpu or not
    print("-" * 100)
    print("This script will try to install the necessary packages for the project")
    use_gpu = input("Do you want to use GPU for pytorch? (y/n): ")

    # read requirements.txt save as temp
    with open(f"{req}.txt", "r") as f:
        lines = f.readlines()

        if use_gpu.lower() != "y":
            # remove line with --find-links
            lines = [line for line in lines if not line.startswith("--find-links")]

    # write temp to requirements_temp.txt
    with open(f"{tempfile}.txt", "w") as f:
        f.writelines(lines)

    timeStart = time.time()
    # install requirements
    print("-" * 100)
    print(f"Installing from {tempfile}.txt")
    os.system(f"{pip} install -r {tempfile}.txt")

    # delete temp file
    os.remove(f"{tempfile}.txt")

    print("-" * 100)
    print("Done!")
    print(f"Total time {time.time() - timeStart: .2f}")
    print("-" * 100)
    print("IF PYTORCH version is not compatible with your system, please install it manually with direction located at https://pytorch.org/")
