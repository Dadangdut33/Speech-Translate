import os
import hashlib
import time
import urllib.request
import tkinter as tk
import threading
from tkinter import ttk
from typing import Union
from speech_translate.custom_logging import logger
from speech_translate.globals import gc
from speech_translate._path import app_icon
from speech_translate.components.custom.message import mbox


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
    root.geometry("450x150")
    root.protocol("WM_DELETE_WINDOW", lambda: master.state("iconic")) # minimize window when click close button
    root.geometry("+{}+{}".format(master.winfo_rootx() + 50, master.winfo_rooty() + 50))
    try:
        root.iconbitmap(app_icon)
    except:
        pass

    # flag
    paused = False
    def pause_download():
        nonlocal paused
        paused = not paused
        if paused:
            logger.info("Download paused")
            btn_pause['text'] = "Resume"
        else:
            logger.info("Download resumed")
            btn_pause['text'] = "Pause"
            update_progress_bar() # resume progress bar update

    mf = ttk.Frame(root)
    mf.pack(side="top", fill="both", padx=5, pady=5, expand=True)

    status_frame = ttk.Frame(mf)
    status_frame.pack(side="top", fill="x", padx=5, pady=5, expand=True)

    btn_frame = ttk.Frame(mf)
    btn_frame.pack(side="bottom", fill="x", padx=5, pady=5, expand=True)
    
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

        progress_bar = ttk.Progressbar(mf, orient='horizontal', length=300, mode='determinate')
        progress_bar.pack(side="top", fill="x", padx=5, pady=5, expand=True)

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

                if not paused:
                    lbl_status_text['text'] = f"Downloading {model_name} model ({mb_downloaded:.2f}/{length_in_mb:.2f} MB)" if percent < 100 else f"Downloading {model_name} model (100%)"
                    root.after(100, update_progress_bar)
                else:
                    lbl_status_text['text'] = f"Paused downloading for {model_name} model ({bytes_read / 1024 / 1024:.2f}/{length_in_mb:.2f} MB)"

        if cancel_func:
            btn = ttk.Button(btn_frame, text="Cancel", command=cancel_func, style="Accent.TButton")
            btn.pack(side="left", fill="x", padx=5, pady=5, expand=True)

        update_progress_bar()
        while True:
            if gc.cancel_dl:
                logger.info("Download cancelled")
                downloading = False
                gc.cancel_dl = False
                root.after(1000, root.destroy)
                mbox("Download Cancelled", f"Downloading of {model_name} model has been cancelled", 0, master)
                return

            if paused:
                # sleep for 1 second
                time.sleep(1)
                continue

            buffer = source.read(buffer_size)
            if not buffer:
                downloading = False
                break

            output.write(buffer)
            bytes_read += len(buffer)
            
        root.after(1000, root.destroy)

    model_bytes = open(download_target, "rb").read()
    if hashlib.sha256(model_bytes).hexdigest() != expected_sha256:
        raise RuntimeError("Model has been downloaded but the SHA256 checksum does not match. Please retry loading the model.")

    # all check passed, this means the model has been downloaded successfully
    # run after_func if it is not None
    logger.info("Download finished")
    if after_func:
        logger.info("Running after_func")
        threading.Thread(target=after_func, daemon=True).start()

    # tell setting window to check model again when it open 
    assert gc.sw is not None
    gc.sw.model_checked = False

    mbox("Model Downloaded Success", f"{model_name} model has been downloaded successfully", 0, master)
    return model_bytes if in_memory else download_target