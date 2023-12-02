import os
import urllib.request
from hashlib import sha256
from threading import Thread
from time import sleep, time
from tkinter import Tk, Toplevel, ttk, Text
from pathlib import Path
from typing import Union, Optional, Literal, List, Dict

import huggingface_hub
import requests
from tqdm.auto import tqdm as base_tqdm
from loguru import logger
from huggingface_hub.file_download import repo_folder_name

from speech_translate.utils.helper import kill_thread
from speech_translate._path import app_icon
from speech_translate.ui.custom.message import mbox
from speech_translate._logging import recent_stderr
from speech_translate.linker import bc


def whisper_download_with_progress_gui(
    master: Union[Tk, Toplevel],
    model_name: str,
    url: str,
    download_root: str,
    cancel_func,
    after_func,
    failed_func,
):
    """Download a model from whisper provided URL, the code is directly modified from whisper code with many modifications.

    Parameters
    ----------
    master : Union[Tk, Toplevel]
        Master window
    model_name : str
        The model name to download
    url : str
        The url to download
    download_root : str
        The download directory
    cancel_func: function
        function to run to cancel download. The function should raise flag to cancel download
    after_func : function
        Function to run after download is finished when download is successful
    failed_func: function
        function to run when it fails to download
    Returns
    -------
    bool
        True if download is successful, False otherwise
    """
    os.makedirs(download_root, exist_ok=True)

    expected_sha256 = url.split("/")[-2]
    download_target = os.path.join(download_root, os.path.basename(url))

    if os.path.exists(download_target) and not os.path.isfile(download_target):
        mbox("Download Failed", f"{download_target} exists and is not a regular file", 0, master)
        return False

    if os.path.isfile(download_target):
        with open(download_target, "rb") as f:
            model_bytes = f.read()
        if sha256(model_bytes).hexdigest() == expected_sha256:
            return download_target
        else:
            logger.warning(f"{download_target} exists, but the SHA256 checksum does not match; re-downloading the file")

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

    def toggle_pause():
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

    btn_pause = ttk.Button(btn_frame, text="Pause", command=toggle_pause)
    btn_pause.pack(side="left", fill="x", padx=5, pady=5, expand=True)

    btn_cancel = ttk.Button(btn_frame, text="Cancel", command=cancel_func, style="Accent.TButton")
    btn_cancel.pack(side="left", fill="x", padx=5, pady=5, expand=True)

    downloading = True
    try:
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

            update_progress_bar()
            while True:
                if bc.cancel_dl:
                    try:
                        logger.info("Download cancelled")
                        downloading = False
                        bc.cancel_dl = False
                        root.after(100, root.destroy)
                        mbox("Download Cancelled", f"Downloading of {model_name} model has been cancelled", 0, master)
                    except Exception:
                        pass

                    # download stopped, stop running this function
                    return False

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
    except Exception as e:
        try:
            if "getaddrinfo failed" in str(e):
                logger.info("Download Failed! No connection or host might be down!")
                root.after(100, root.destroy)
                mbox(
                    "Download Failed",
                    f"Downloading of {model_name} model has failed because of no connection or host might be down!", 0,
                    master
                )
            else:
                mbox("Download Failed", f"Downloading of {model_name} model has failed because of {str(e)}", 0, master)
        except Exception:
            pass

        Thread(target=failed_func, daemon=True).start()
        # download failed, stop running this function
        return False

    model_bytes = open(download_target, "rb").read()
    if sha256(model_bytes).hexdigest() != expected_sha256:
        mbox(
            "Download Failed",
            "Model has been downloaded but the SHA256 checksum does not match. Please retry loading the model.", 0, master
        )
        return False

    # all check passed, this means the model has been downloaded successfully
    # run after_func if it is not None
    logger.info("Download finished")

    # tell setting window to check model again when it open
    assert bc.sw is not None
    bc.sw.f_general.model_checked = False

    mbox("Model Downloaded Success", f"{model_name} whisper model has been downloaded successfully", 0, master)

    if after_func:
        logger.info("Running after_func")
        Thread(target=after_func, daemon=True).start()
    return True


@huggingface_hub.utils.validate_hf_hub_args
def snapshot_download(
    repo_id: str,
    *,
    repo_type: Optional[str] = None,
    revision: Optional[str] = None,
    endpoint: Optional[str] = None,
    cache_dir: Union[str, Path, None] = None,
    local_dir: Union[str, Path, None] = None,
    local_dir_use_symlinks: Union[bool, Literal["auto"]] = "auto",
    library_name: Optional[str] = None,
    library_version: Optional[str] = None,
    user_agent: Optional[Union[Dict, str]] = None,
    proxies: Optional[Dict] = None,
    etag_timeout: float = 10,
    resume_download: bool = False,
    force_download: bool = False,
    token: Optional[Union[bool, str]] = None,
    local_files_only: bool = False,
    allow_patterns: Optional[Union[List[str], str]] = None,
    ignore_patterns: Optional[Union[List[str], str]] = None,
    max_workers: int = 8,
    tqdm_class: Optional[base_tqdm] = None,
) -> str:
    """
    Taken from huggingface library, modified to be able to cancel download
    """
    if cache_dir is None:
        cache_dir = huggingface_hub.constants.HUGGINGFACE_HUB_CACHE

    if revision is None:
        revision = huggingface_hub.constants.DEFAULT_REVISION

    if isinstance(cache_dir, Path):
        cache_dir = str(cache_dir)

    if repo_type is None:
        repo_type = "model"
    if repo_type not in huggingface_hub.constants.REPO_TYPES:
        raise ValueError(
            f"Invalid repo type: {repo_type}. Accepted repo types are: {str(huggingface_hub.constants.REPO_TYPES)}"
        )

    storage_folder = os.path.join(cache_dir, repo_folder_name(repo_id=repo_id, repo_type=repo_type))

    # if we have no internet connection we will look for an
    # appropriate folder in the cache
    # If the specified revision is a commit hash, look inside "snapshots".
    # If the specified revision is a branch or tag, look inside "refs".
    if local_files_only:
        if huggingface_hub.file_download.REGEX_COMMIT_HASH.match(revision):
            commit_hash = revision
        else:
            # retrieve commit_hash from file
            ref_path = os.path.join(storage_folder, "refs", revision)
            with open(ref_path) as f:
                commit_hash = f.read()

        snapshot_folder = os.path.join(storage_folder, "snapshots", commit_hash)

        if os.path.exists(snapshot_folder):
            return snapshot_folder

        raise ValueError(
            "Cannot find an appropriate cached snapshot folder for the specified"
            " revision on the local disk and outgoing traffic has been disabled. To"
            " enable repo look-ups and downloads online, set 'local_files_only' to"
            " False."
        )

    # if we have internet connection we retrieve the correct folder name from the huggingface api
    api = huggingface_hub.hf_api.HfApi(
        library_name=library_name, library_version=library_version, user_agent=user_agent, endpoint=endpoint
    )
    repo_info = api.repo_info(repo_id=repo_id, repo_type=repo_type, revision=revision, token=token)
    assert repo_info.sha is not None, "Repo info returned from server must have a revision sha."

    filtered_repo_files = list(
        huggingface_hub.utils.filter_repo_objects(
            items=[f.rfilename for f in repo_info.siblings],  # type: ignore
            allow_patterns=allow_patterns,
            ignore_patterns=ignore_patterns,
        )
    )
    commit_hash = repo_info.sha
    snapshot_folder = os.path.join(storage_folder, "snapshots", commit_hash)
    # if passed revision is not identical to commit_hash
    # then revision has to be a branch name or tag name.
    # In that case store a ref.
    if revision != commit_hash:
        ref_path = os.path.join(storage_folder, "refs", revision)
        os.makedirs(os.path.dirname(ref_path), exist_ok=True)
        with open(ref_path, "w") as f:
            f.write(commit_hash)

    # we pass the commit_hash to hf_hub_download
    # so no network call happens if we already
    # have the file locally.
    def _inner_hf_hub_download(repo_file: str):
        return huggingface_hub.file_download.hf_hub_download(
            repo_id,
            filename=repo_file,
            repo_type=repo_type,
            revision=commit_hash,
            endpoint=endpoint,
            cache_dir=cache_dir,
            local_dir=local_dir,
            local_dir_use_symlinks=local_dir_use_symlinks,
            library_name=library_name,
            library_version=library_version,
            user_agent=user_agent,
            proxies=proxies,
            etag_timeout=etag_timeout,
            resume_download=resume_download,
            force_download=force_download,
            token=token,
        )

    # download files
    for file in filtered_repo_files:
        _inner_hf_hub_download(file)

    return snapshot_folder


def faster_whisper_download_with_progress_gui(
    master: Union[Tk, Toplevel], model_name: str, repo_id: str, cache_dir: str, cancel_func, after_func, failed_func
):
    """Download a model from the Hugging Face Hub with a progress bar that does not show the progress, 
    only there to show that the program is not frozen and is in fact downloading something.

    We instead read from the customized logger to get the download progress and show it in the text box

    Parameters
    ----------
    master : Union[Tk, Toplevel]
        Master window
    model_name : str
        The model name to download
    repo_id : str
        The model id to download
    cache_dir : str
        The download directory
    cancel_func: function
        function to run to cancel download. The function should raise flag to cancel download
    after_func : function
        Function to run after download is finished when download is successful
    failed_func: function
        function to run when it fails to download
    Returns
    -------
    bool
        True if download is successful, False otherwise
    """
    logger.debug("Downloading model from Hugging Face Hub")
    os.makedirs(cache_dir, exist_ok=True)  # make cache dir if not exist

    storage_folder = os.path.join(cache_dir, repo_folder_name(repo_id=repo_id, repo_type="model"))
    allow_patterns = ["config.json", "preprocessor_config.json", "model.bin", "tokenizer.json", "vocabulary.*"]
    kwargs = {"local_files_only": False, "allow_patterns": allow_patterns, "resume_download": True, "cache_dir": cache_dir}

    # Show toplevel window
    root = Toplevel(master)
    root.title("Checking Model")
    root.transient(master)
    root.geometry("600x180")
    root.protocol("WM_DELETE_WINDOW", lambda: master.state("iconic"))  # minimize window when click close button
    root.geometry("+{}+{}".format(master.winfo_rootx() + 50, master.winfo_rooty() + 50))
    root.minsize(200, 100)
    root.maxsize(1600, 200)
    try:
        root.iconbitmap(app_icon)
    except Exception:
        pass

    # clear recent_stderr
    recent_stderr.clear()

    f1 = ttk.Frame(root)
    f1.pack(side="top", fill="x", expand=True)

    f2 = ttk.Frame(root)
    f2.pack(side="top", fill="x", expand=True)

    f3 = ttk.Frame(root)
    f3.pack(side="top", fill="both", expand=True)

    lbl_status_title = ttk.Label(f1, text="Status:", font="TkDefaultFont 9 bold")
    lbl_status_title.pack(side="left", padx=(5, 0), pady=(5, 0))

    lbl_status_text = ttk.Label(f1, text="Checking please wait...")
    lbl_status_text.pack(side="left", padx=5, pady=(5, 0))

    btn_cancel = ttk.Button(f1, text="Cancel", command=cancel_func, style="Accent.TButton")
    btn_cancel.pack(side="right", padx=(5, 10), pady=(5, 0))

    btn_pause = ttk.Button(f1, text="Pause", command=lambda: toggle_pause())
    btn_pause.pack(side="right", padx=5, pady=(5, 0))

    # add progress bar that just goes back and forth
    progress = ttk.Progressbar(f2, orient="horizontal", length=200, mode="indeterminate")
    progress.pack(expand=True, fill="x", padx=10, pady=(2, 2))
    progress.start(15)

    text_log = Text(f3, height=5, width=50, font=("Consolas", 10))
    text_log.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 10))
    text_log.bind("<Key>", lambda event: "break")  # disable text box
    text_log.insert(1.0, "Checking model please wait...")

    def get_file_amount(path):
        try:
            # filter out .incomplete or .lock files
            return len([name for name in os.listdir(path) if not name.endswith((".incomplete", ".lock"))])
        except Exception:
            return "Unknown"

    def update_log():
        # get only last 7 lines
        content = "\n".join(recent_stderr[-7:])
        text_log.delete(1.0, "end")
        text_log.insert(1.0, content)
        text_log.see("end")  # scroll to the bottom

    failed = False
    msg = ""
    finished = False
    paused = False
    killed = False

    def run_threaded():
        nonlocal failed, msg, finished, paused

        root.title("Verifying Model")
        lbl_status_text.configure(text=f"Verifying {model_name} model please wait...")
        text_log.insert("end", f"\nVerifying {model_name} model please wait...")
        try:
            snapshot_download(repo_id, **kwargs)
        except (
            huggingface_hub.utils.HfHubHTTPError,
            requests.exceptions.ConnectionError,
        ) as exception:
            logger.warning(
                f"An error occured while synchronizing the model {repo_id} from the Hugging Face Hub:\n{exception}"
            )
            logger.warning("Trying to load the model directly from the local cache, if it exists.")

            try:
                kwargs["local_files_only"] = True
                snapshot_download(repo_id, **kwargs)
            except Exception as e:
                failed = True
                msg = f"Failed to download faster whisper model. Have tried to download the model from the Hugging Face Hub and from the local cache. Please check your internet connection and try again.\n\nError: {str(e)}"

        except Exception as e:
            logger.exception(e)
            failed = True
            msg = str(e)

        finally:
            if not paused:
                finished = True

    threaded = Thread(target=run_threaded, daemon=True)
    threaded.start()
    start_time = time()

    def toggle_pause():
        nonlocal paused, killed, threaded
        paused = not paused
        if paused:
            logger.info("Download paused")
            btn_pause["text"] = "Resume"
            progress.stop()
        else:
            logger.info("Download resumed")
            btn_pause["text"] = "Pause"
            progress.start(15)
            killed = False
            threaded = Thread(target=run_threaded, daemon=True)
            threaded.start()

    while not finished:
        if paused and not killed:
            kill_thread(threaded)
            killed = True
            recent_stderr.append("Download paused")
            update_log()

        if bc.cancel_dl:
            kill_thread(threaded)
            finished = True  # mark as finished
            root.destroy()
            mbox("Download Cancelled", f"Downloading of {model_name} faster whisper model has been cancelled", 0, master)
            break

        # check if 2 second have passed. Means probably downloading from the hub
        if time() - start_time > 2:
            root.title(f"{'Downloading' if not paused else 'Paused downloading of'} Faster Whisper Model")
            lbl_status_text.configure(
                text=
                f"{'Downloading' if not paused else 'Paused downloading'} {model_name} model, {get_file_amount(storage_folder + '/' + 'blobs')} files downloaded..."
            )
            if not paused:
                update_log()
        sleep(1)

    # if cancel button is pressed, return
    if bc.cancel_dl:
        bc.cancel_dl = False
        return

    # everything is done
    root.destroy()

    # tell setting window to check model again when it is opened
    assert bc.sw is not None
    bc.sw.f_general.model_checked = False

    if success := not failed:
        logger.info("Download finished")
        mbox("Model Downloaded Success", f"{model_name} faster whisper model has been downloaded successfully", 0, master)
        # run after_func
        if after_func:
            logger.info("Running after_func")
            Thread(target=after_func, daemon=True).start()
    else:
        logger.info("Download failed")
        mbox("Model Download Failed", msg, 0, master)
        Thread(target=failed_func, daemon=True).start()

    return success
