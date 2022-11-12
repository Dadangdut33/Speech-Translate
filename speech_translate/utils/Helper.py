import os
import subprocess


modelSelectDict = {"Tiny (~32x speed)": "tiny", "Base (~16x speed)": "base", "Small (~6x speed)": "small", "Medium (~2x speed)": "medium", "Large (1x speed)": "large"}
modelKeys = list(modelSelectDict.keys())
modelValues = list(modelSelectDict.values())


def upFirstCase(string):
    return string[0].upper() + string[1:]

def startFile(filename):
    """
    Open a folder or file in the default application.
    """
    try:
        os.startfile(filename)
    except FileNotFoundError:
        print("Cannot find the file specified.")
    except Exception:
        try:
            subprocess.Popen(['xdg-open', filename])
        except FileNotFoundError:
            print("Cannot open the file specified.")
        except Exception as e:
            print("Error: " + str(e))