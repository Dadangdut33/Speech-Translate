import whisper
import hashlib
import os
from speech_translate.components.custom.download import whisper_download_with_progress_gui

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
