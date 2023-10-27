import os
import urllib.request
from hashlib import sha256
from threading import Thread
from time import sleep, time
from tkinter import Tk, Toplevel, ttk
from typing import Union

import huggingface_hub
import requests
from faster_whisper.utils import _MODELS
from huggingface_hub.file_download import repo_folder_name

from speech_translate._path import app_icon
from speech_translate.components.custom.message import mbox
from speech_translate.custom_logging import logger
from speech_translate.globals import gc


def whisper_download_with_progress_gui(
    master: Union[Tk, Toplevel],
    cancel_func,
    after_func,
    model_name: str,
    url: str,
    download_root: str,
    in_memory: bool,
) -> Union[bytes, str, None]:
    os.makedirs(download_root, exist_ok=True)

    expected_sha256 = url.split("/")[-2]
    download_target = os.path.join(download_root, os.path.basename(url))

    if os.path.exists(download_target) and not os.path.isfile(download_target):
        raise RuntimeError(f"{download_target} exists and is not a regular file")

    if os.path.isfile(download_target):
        with open(download_target, "rb") as f:
            model_bytes = f.read()
        if sha256(model_bytes).hexdigest() == expected_sha256:
            return model_bytes if in_memory else download_target
        else:
            logger.warn(f"{download_target} exists, but the SHA256 checksum does not match; re-downloading the file")

    # Show toplevel window
    root = Toplevel(master)
    root.title("Downloading Whisper Model")
    root.transient(master)
    root.geometry("450x115")
    root.protocol("WM_DELETE_WINDOW", lambda: master.state("iconic"))  # minimize window when click close button
    root.geometry("+{}+{}".format(master.winfo_rootx() + 50, master.winfo_rooty() + 50))
    root.minsize(200, 115)
    root.maxsize(600, 180)
    try:
        root.iconbitmap(app_icon)
    except Exception:
        pass

    # flag
    paused = False

    def pause_download():
        nonlocal paused
        paused = not paused
        if paused:
            logger.info("Download paused")
            btn_pause["text"] = "Resume"
        else:
            logger.info("Download resumed")
            btn_pause["text"] = "Pause"
            update_progress_bar()  # resume progress bar update

    frame_lbl = ttk.Frame(root)
    frame_lbl.pack(side="top", fill="both", expand=True)

    status_frame = ttk.Frame(frame_lbl)
    status_frame.pack(side="top", fill="x", padx=5, pady=5)

    progress_frame = ttk.Frame(frame_lbl)
    progress_frame.pack(side="top", fill="x", padx=5, pady=5)

    btn_frame = ttk.Frame(root)
    btn_frame.pack(side="top", fill="x", padx=5, pady=5, expand=True)

    lbl_status_title = ttk.Label(status_frame, text="Status:", font="TkDefaultFont 9 bold")
    lbl_status_title.pack(side="left", padx=(5, 0), pady=5)

    lbl_status_text = ttk.Label(status_frame, text=f"Downloading {model_name} model")
    lbl_status_text.pack(side="left", padx=5, pady=5)

    btn_pause = ttk.Button(btn_frame, text="Pause", command=pause_download)
    btn_pause.pack(side="left", fill="x", padx=5, pady=5, expand=True)

    downloading = True
    with urllib.request.urlopen(url) as source, open(download_target, "wb") as output:
        buffer_size = 8192
        length = int(source.info().get("Content-Length"))
        length_in_mb = length / 1024 / 1024

        progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=300, mode="determinate")
        progress_bar.pack(side="left", fill="x", padx=5, pady=5, expand=True)

        global bytes_read
        bytes_read = 0

        def update_progress_bar():
            if downloading:
                # get how many percent of the file has been downloaded
                global bytes_read
                percent = bytes_read / length * 100
                progress_bar["value"] = percent

                # update label with mb downloaded
                mb_downloaded = bytes_read / 1024 / 1024

                if not paused:
                    lbl_status_text["text"] = (
                        f"Downloading {model_name} model ({mb_downloaded:.2f}/{length_in_mb:.2f} MB)"
                        if percent < 100 else f"Downloading {model_name} model (100%)"
                    )
                    root.after(100, update_progress_bar)
                else:
                    lbl_status_text[
                        "text"
                    ] = f"Paused downloading for {model_name} model ({bytes_read / 1024 / 1024:.2f}/{length_in_mb:.2f} MB)"

        if cancel_func:
            btn = ttk.Button(btn_frame, text="Cancel", command=cancel_func, style="Accent.TButton")
            btn.pack(side="left", fill="x", padx=5, pady=5, expand=True)

        update_progress_bar()
        while True:
            if gc.cancel_dl:
                try:
                    logger.info("Download cancelled")
                    downloading = False
                    gc.cancel_dl = False
                    root.after(1000, root.destroy)
                    mbox("Download Cancelled", f"Downloading of {model_name} model has been cancelled", 0, master)
                except Exception:
                    pass
                return

            if paused:
                # sleep for 1 second
                sleep(1)
                continue

            buffer = source.read(buffer_size)
            if not buffer:
                downloading = False
                break

            output.write(buffer)
            bytes_read += len(buffer)

        root.after(1000, root.destroy)

    model_bytes = open(download_target, "rb").read()
    if sha256(model_bytes).hexdigest() != expected_sha256:
        raise RuntimeError(
            "Model has been downloaded but the SHA256 checksum does not match. Please retry loading the model."
        )

    # all check passed, this means the model has been downloaded successfully
    # run after_func if it is not None
    logger.info("Download finished")
    if after_func:
        logger.info("Running after_func")
        Thread(target=after_func, daemon=True).start()

    # tell setting window to check model again when it open
    assert gc.sw is not None
    gc.sw.f_general.model_checked = False

    mbox("Model Downloaded Success", f"{model_name} whisper model has been downloaded successfully", 0, master)
    return model_bytes if in_memory else download_target


def faster_whisper_download_with_progress_gui(master: Union[Tk, Toplevel], model_name: str, cache_dir: str, after_func):
    """Download a model from the Hugging Face Hub with a progress bar that does not show the progress, only there to show that the program is not frozen and is in fact downloading something

    Parameters
    ----------
    master : Union[Tk, Toplevel]
        Master window
    model_name : str
        The model name to download
    cache_dir : str
        The download directory
    after_func : function
        Function to run after download is finished when download is successful

    Returns
    -------
    bool
        True if download is successful, False otherwise

    Raises
    ------
    ValueError
        If model_name is not one of the official model names listed by `faster_whisper.available_models()`
    """
    logger.debug("Downloading model from Hugging Face Hub")
    os.makedirs(cache_dir, exist_ok=True)  # make cache dir if not exist

    repo_id = _MODELS.get(model_name)
    if repo_id is None:
        raise ValueError("Invalid model size '%s', expected one of: %s" % (model_name, ", ".join(_MODELS.keys())))

    storage_folder = os.path.join(cache_dir, repo_folder_name(repo_id=repo_id, repo_type="model"))
    allow_patterns = ["config.json", "model.bin", "tokenizer.json", "vocabulary.*"]
    kwargs = {"local_files_only": False, "allow_patterns": allow_patterns, "resume_download": True, "cache_dir": cache_dir}

    # Show toplevel window
    root = Toplevel(master)
    root.title("Checking Model")
    root.transient(master)
    root.geometry("450x60")
    root.protocol("WM_DELETE_WINDOW", lambda: master.state("iconic"))  # minimize window when click close button
    root.geometry("+{}+{}".format(master.winfo_rootx() + 50, master.winfo_rooty() + 50))
    root.minsize(200, 60)
    root.maxsize(500, 90)
    try:
        root.iconbitmap(app_icon)
    except Exception:
        pass

    # add label that says downloading please wait
    f1 = ttk.Frame(root)
    f1.pack(side="top", fill="x", expand=True)

    f2 = ttk.Frame(root)
    f2.pack(side="top", fill="x", expand=True)

    label = ttk.Label(f1, text="Checking please wait...")
    label.pack(side="top", padx=5, pady=5)

    # add progress bar that just goes back and forth
    progress = ttk.Progressbar(f2, orient="horizontal", length=200, mode="indeterminate")
    progress.pack(expand=True, fill="x", padx=25, pady=(5, 10))
    progress.start(15)

    after_id = None
    failed = False
    msg = ""

    def get_size(path):
        try:
            size = os.path.getsize(path)
            if size < 1024:
                return f"{size} bytes"
            elif size < pow(1024, 2):
                return f"{round(size/1024, 2)} KB"
            elif size < pow(1024, 3):
                return f"{round(size/(pow(1024,2)), 2)} MB"
            elif size < pow(1024, 4):
                return f"{round(size/(pow(1024,3)), 2)} GB"
        except Exception:
            return "Unknown file size"

    def get_file_amount(path):
        try:
            # filter out .incomplete or .lock files
            return len([name for name in os.listdir(path) if not name.endswith((".incomplete", ".lock"))])
        except Exception:
            return "Unknown"

    def run_threaded():
        nonlocal after_id, failed, msg

        root.title("Verifying Model")
        label.configure(text=f"Verifying {model_name} model please wait...")
        try:
            huggingface_hub.snapshot_download(repo_id, **kwargs)
        except (
            huggingface_hub.utils.HfHubHTTPError,
            requests.exceptions.ConnectionError,
        ) as exception:
            logger.warning(
                "An error occured while synchronizing the model %s from the Hugging Face Hub:\n%s" % (repo_id, exception)
            )
            logger.warning("Trying to load the model directly from the local cache, if it exists.")

            try:
                kwargs["local_files_only"] = True
                huggingface_hub.snapshot_download(repo_id, **kwargs)
            except Exception as e:
                failed = True
                msg = "Failed to download faster whisper model. Have tried to download the model from the Hugging Face Hub and from the local cache. Please check your internet connection and try again.\n\nError: %s" % str(
                    e
                )

    threaded = Thread(target=run_threaded, daemon=True)
    threaded.start()
    start_time = time()

    # thread.join()
    while threaded.is_alive():
        # check if 2 second have passed. Means probably downloading from the hub
        if time() - start_time > 2:
            root.title("Downloading Faster Whisper Model")
            label.configure(
                text=f"Downloading {model_name} model, {get_file_amount(storage_folder + '/' + 'blobs')}/4 files downloaded..."
            )
        sleep(0.3)

    root.destroy()
    # if not failed:
    logger.info("Download finished")

    # tell setting window to check model again when it open
    assert gc.sw is not None
    gc.sw.f_general.model_checked = False

    if success := not failed:
        # run after_func
        if after_func:
            logger.info("Running after_func")
            Thread(target=after_func, daemon=True).start()

        mbox("Model Downloaded Success", f"{model_name} faster whisper model has been downloaded successfully", 0, master)
    else:
        mbox("Model Download Failed", msg, 0, master)

    return success
