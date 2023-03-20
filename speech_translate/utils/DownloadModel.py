import whisper
import hashlib
import threading
import os
import urllib.request
import tkinter as tk
from tkinter import ttk
from typing import Union
from speech_translate.Logging import logger
from speech_translate.Globals import gClass
from speech_translate._path import app_icon
from speech_translate.components.custom.MBox import Mbox

# ----------------------------------------------------------------------
def do_nothing_on_close() -> None:
    pass

def whisper_download_with_progress_gui(master: Union[tk.Tk, tk.Toplevel], cancel_func, after_func, model_name: str, url: str, download_root: str, in_memory: bool) -> Union[bytes, str, None]:
    os.makedirs(download_root, exist_ok=True)

    expected_sha256 = url.split("/")[-2]
    download_target = os.path.join(download_root, os.path.basename(url))

    if os.path.exists(download_target) and not os.path.isfile(download_target):
        raise RuntimeError(f"{download_target} exists and is not a regular file")

    if os.path.isfile(download_target):
        with open(download_target, "rb") as f:
            model_bytes = f.read()
        if hashlib.sha256(model_bytes).hexdigest() == expected_sha256:
            return model_bytes if in_memory else download_target
        else:
            logger.warn(f"{download_target} exists, but the SHA256 checksum does not match; re-downloading the file")

    # Show toplevel window
    root = tk.Toplevel(master)
    root.title("Downloading Model")
    root.transient(master)
    root.geometry("400x150")
    root.wm_attributes("-topmost", True)
    root.protocol("WM_DELETE_WINDOW", do_nothing_on_close)
    root.geometry("+{}+{}".format(master.winfo_rootx() + 50, master.winfo_rooty() + 50))
    try:
        root.iconbitmap(app_icon)
    except:
        pass

    mf = ttk.Frame(root)
    mf.pack(side=tk.TOP, fill=tk.BOTH, padx=5, pady=5, expand=True)
    
    lbl = ttk.Label(mf, text=f"Current Task: Downloading {model_name} model")
    lbl.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5, expand=True)

    downloading = True
    with urllib.request.urlopen(url) as source, open(download_target, "wb") as output:
        buffer_size = 8192
        length = int(source.info().get("Content-Length"))
        length_in_mb = length / 1024 / 1024

        progress_bar = ttk.Progressbar(mf, orient='horizontal', length=300, mode='determinate')
        progress_bar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5, expand=True)

        global bytes_read
        bytes_read = 0

        def update_progress_bar():
            if downloading:
                # get how many percent of the file has been downloaded
                global bytes_read
                percent = bytes_read / length * 100
                progress_bar['value'] = percent

                # update label with mb downloaded
                mb_downloaded = bytes_read / 1024 / 1024
                lbl['text'] = f"Current Task: Downloading {model_name} model ({mb_downloaded:.2f}MB/{length_in_mb:.2f}MB)" if percent < 100 else f"Current Task: Downloading {model_name} model (100%)"

                root.after(100, update_progress_bar)

        if cancel_func:
            btn = ttk.Button(mf, text="Cancel", command=cancel_func)
            btn.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5, expand=True)

        update_progress_bar()
        while True:
            buffer = source.read(buffer_size)
            if not buffer:
                downloading = False
                break

            if gClass.cancel_dl:
                gClass.cancel_dl = False
                Mbox("Download Cancelled", f"Downloading of {model_name} model has been cancelled", 0, master)
                root.after(1000, root.destroy)
                return

            output.write(buffer)
            bytes_read += len(buffer)
            
        root.after(1000, root.destroy)

    model_bytes = open(download_target, "rb").read()
    if hashlib.sha256(model_bytes).hexdigest() != expected_sha256:
        raise RuntimeError("Model has been downloaded but the SHA256 checksum does not not match. Please retry loading the model.")

    if after_func:
        threading.Thread(target=after_func, daemon=True).start()

    Mbox("Model Downloaded Success", f"{model_name} model has been downloaded successfully", 0, master)
    return model_bytes if in_memory else download_target

# donwload function
def download_model(model_name, root_win=None, cancel_func=None, after_func=None, download_root=None, in_memory=False):
    """Download a model from the official model repository

    Parameters
    ----------
    model_name : str
        one of the official model names listed by `whisper.available_models()`
    download_root: str
        path to download the model files; by default, it uses "~/.cache/whisper"
    in_memory: bool
        whether to preload the model weights into host memory

    Returns
    -------
    model_bytes : bytes
        the model checkpoint as a byte string
    """
    if download_root is None:
        download_root = os.getenv("XDG_CACHE_HOME", os.path.join(os.path.expanduser("~"), ".cache", "whisper"))

    if model_name not in whisper._MODELS:
        raise RuntimeError(f"Model {model_name} not found; available models = {whisper.available_models()}")
    
    if root_win is None:
        return whisper._download(whisper._MODELS[model_name], download_root, in_memory)
    else:
        return whisper_download_with_progress_gui(root_win, cancel_func, after_func, model_name, whisper._MODELS[model_name], download_root, in_memory)


# check if model is already downloaded
def check_model(model_name, download_root=None):
    """Check if a model is already downloaded

    Parameters
    ----------
    model_name : str
        one of the official model names listed by `whisper.available_models()`
    download_root: str
        path to download the model files; by default, it uses "~/.cache/whisper"

    Returns
    -------
    bool
        True if the model is already downloaded
    """
    if download_root is None:
        download_root = os.getenv("XDG_CACHE_HOME", os.path.join(os.path.expanduser("~"), ".cache", "whisper"))

    if model_name not in whisper._MODELS:
        raise RuntimeError(f"Model {model_name} not found; available models = {whisper.available_models()}")

    return os.path.exists(os.path.join(download_root, model_name + ".pt"))


# verify downloaded model sha
def verify_model(model_name, download_root=None):
    """Verify the SHA256 checksum of a downloaded model

    Parameters
    ----------
    model_name : str
        one of the official model names listed by `whisper.available_models()`
    download_root: str
        path to download the model files; by default, it uses "~/.cache/whisper"

    Returns
    -------
    bool
        True if the model is already downloaded
    """
    if download_root is None:
        download_root = os.getenv("XDG_CACHE_HOME", os.path.join(os.path.expanduser("~"), ".cache", "whisper"))

    if model_name not in whisper._MODELS:
        raise RuntimeError(f"Model {model_name} not found; available models = {whisper.available_models()}")

    model_file = os.path.join(download_root, model_name + ".pt")
    if not os.path.exists(model_file):
        return False

    expected_sha256 = whisper._MODELS[model_name].split("/")[-2]

    model_bytes = open(model_file, "rb").read()
    return hashlib.sha256(model_bytes).hexdigest() == expected_sha256


# get default download root
def get_default_download_root():
    """Get the default download root

    Returns
    -------
    str
        the default download root
    """
    return os.getenv("XDG_CACHE_HOME", os.path.join(os.path.expanduser("~"), ".cache", "whisper"))
