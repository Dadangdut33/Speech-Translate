<p align="center">
    <img src="https://github.com/Dadangdut33/Speech-Translate/blob/master/speech_translate/assets/icon.png?raw=true" width="250px" alt="Speech Translate Logo">
</p>

<h1 align="center">Speech Translate</h1>

<p align="center">
    <a href="https://github.com/Dadangdut33/Speech-Translate/issues"><img alt="GitHub issues" src="https://img.shields.io/github/issues/Dadangdut33/Speech-Translate"></a>
    <a href="https://github.com/Dadangdut33/Speech-Translate/pulls"><img alt="GitHub pull requests" src="https://img.shields.io/github/issues-pr/Dadangdut33/Speech-Translate"></a>
    <a href="https://github.com/Dadangdut33/Speech-Translate/releases/latest"><img alt="github downloads"  src="https://img.shields.io/github/downloads/Dadangdut33/Speech-Translate/total?label=downloads (github)"></a> 
    <a href="https://github.com/Dadangdut33/Speech-Translate/releases/latest"><img alt="GitHub release (latest SemVer)" src="https://img.shields.io/github/v/release/Dadangdut33/Speech-Translate"></a>
    <a href="https://github.com/Dadangdut33/Speech-Translate/commits/main"><img alt="GitHub commits since latest release (by date)" src="https://img.shields.io/github/commits-since/Dadangdut33/Speech-Translate/latest"></a><Br>
    <a href="https://github.com/Dadangdut33/Speech-Translate/stargazers"><img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/Dadangdut33/Speech-Translate?style=social"></a>
    <a href="https://github.com/Dadangdut33/Speech-Translate/network/members"><img alt="GitHub forks" src="https://img.shields.io/github/forks/Dadangdut33/Speech-Translate?style=social"></a>
</p>

A speech transcription and translation application using whisper AI model.

<h1>Jump to</h1>

- [Features](#features)
- [User Requirements](#user-requirements)
- [Download \& Installation](#download--installation)
- [General Usage](#general-usage)
- [User Settings](#user-settings-and-thing-to-note)
- [Development](#--development--)
  - [Setup](#setup)
  - [Using GPU](#using-gpu)
  - [Building](#building)
  - [Compatibility](#compatibility)
- [Contributing](#contributing)
- [License](#license)
- [Attribution](#attribution)
- [Other](#other)

# Features

- Speech to text
- Translation of transcribed text (Speech to translated text)
- Realtime input from mic and speaker
- Batch file processing with timestamp
- <details open>
    <summary>Preview</summary>
    <p align="center">
      <img src="https://raw.githubusercontent.com/Dadangdut33/Speech-Translate/master/speech_translate/assets/1.png" width="700" alt="Speech Translate Looks">
      <img src="https://raw.githubusercontent.com/Dadangdut33/Speech-Translate/master/speech_translate/assets/2.png" width="700" alt="Setting transcription">
      <img src="https://raw.githubusercontent.com/Dadangdut33/Speech-Translate/master/speech_translate/assets/3.png" width="700" alt="Setting textbox">
      <img src="https://raw.githubusercontent.com/Dadangdut33/Speech-Translate/master/speech_translate/assets/4.png" width="700" alt="About window">
      <img src="https://raw.githubusercontent.com/Dadangdut33/Speech-Translate/master/speech_translate/assets/5.png" alt="Detached window preview">
      Detached window preview
      <img src="https://raw.githubusercontent.com/Dadangdut33/Speech-Translate/master/speech_translate/assets/6.png" alt="Transcribe mode on detached window (English)">
      Transcribe mode on detached window (English)
      <img src="https://raw.githubusercontent.com/Dadangdut33/Speech-Translate/master/speech_translate/assets/7.png" alt="Translate mode on detached window (English to Indonesia)">
      Translate mode on detached window (English to Indonesia)
    </p>
  </details>

# User Requirements

- [FFmpeg](https://ffmpeg.org/) is required to be installed and added to the PATH environment variable. You can download it [here](https://ffmpeg.org/download.html) and add it to your path manually OR you can do it automatically using the following commands:

```
# on Windows using Chocolatey (https://chocolatey.org/)
choco install ffmpeg

# on Windows using Scoop (https://scoop.sh/)
scoop install ffmpeg

# on Ubuntu or Debian
sudo apt update && sudo apt install ffmpeg

# on Arch Linux
sudo pacman -S ffmpeg

# on MacOS using Homebrew (https://brew.sh/)
brew install ffmpeg
```
- Whisper uses vram/gpu to process the audio, so it is recommended to have a CUDA compatible GPU. If there is no compatible GPU, the application will use the CPU to process the audio (This might make it slower). For each model requirement you can check directly at the [whisper repository](https://github.com/openai/whisper) or you can hover over the model selection in the app (there will be a tooltip about the model info).
- Speaker input only work on windows 8 and above.


# Download & Installation

> [!Important] \ 
> Make sure that you have installed [FFmpeg](https://ffmpeg.org/) and added it to the PATH environment variable. [See here](#user-requirements) for more info

## From Prebuilt binary:
  1. Download the [latest release](https://github.com/Dadangdut33/Speech-Translate/releases/latest) (There are 2 versions, CPU and GPU)
  2. Install/extract the downloaded file
  3. Run the program
  
## As module:
  - From the latest commit: 
  
    with **GPU (Cuda compatible)** support: 

    `pip install -U git+https://github.com/Dadangdut33/Speech-Translate.git --extra-index-url https://download.pytorch.org/whl/cu118`

    **CPU** only:

    `pip install -U git+https://github.com/Dadangdut33/Speech-Translate.git`

    If you are updating from an older version, you can add `--upgrade --no-deps --force-reinstall` at the end of the command.

    **Notes:**

    -  This will install the latest commit from the main branch. You can also install from a specific branch or commit by adding `@branch_name` or `@commit_hash` at the end of the url. Example:
```pip install -U git+https://github.com/Dadangdut33/Speech-Translate.git@dev --extra-index-url https://download.pytorch.org/whl/cu118```

    - The --extra-index-url shown here might not always be up to date, so you can check the latest version of pytorch [here](https://pytorch.org/get-started/locally/). You can also check the available version of pytorch [here](https://download.pytorch.org/whl/torch_stable.html).
    -  You can also clone the repo and install it locally by running `pip install -e .` in the project directory. (Don't forget to add `--extra-index-url` if you want to install with GPU support)

    You can then run the program by typing `speech-translate` in your terminal/console.

# General Usage

- Realtime Record:

  1. Set user setting
  2. Select model, mode, and language
  3. Click the record from mic / system button
  4. Open the subtitle window
  5. Stop record

- File import:

  1. Set user setting
  2. Select model, mode, and language
  3. Click the import file button
  4. Wait for the process to finish or cancel it


# User Settings and Thing to Note

- You can change the settings by clicking the settings button on the menubar of the app. Alternatively, you can press F2 to open the menu window when in focus or you could also edit the settings file manually located at `$project_dir/user/setting.json`.
- If the terminal/console is still showing, you will need to set your `default terminal application` to `windows console host` in your `windows terminal` setting. 
![image](https://user-images.githubusercontent.com/57717531/226117592-e10ebdf3-fb09-44b2-b6be-1a445dc8c265.png)

---

<h1 align="center">- Development -</h1>

> [!Warning] \
> As of right now (4th of November 2022) I guess pytorch is not compatible with python 3.11 so you can't use python 3.11. I tried with 3.11 but it doesn't work so i rollback to python 3.10.9.

> [!Note] \
> Ignore all this if you are using the prebuilt/compiled version.

## Setup

> [!Note] \
> It is recommended to create a virtual environment, but it is not required.

1. Create your virtual environment by running `python -m venv venv`
2. Activate your virtual environment by running `source venv/bin/activate`
3. Install all the dependencies needed by running the [`devSetup.py`](./devSetup.py) located in **root directory** or install the packages yourself by running `pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu118` if you are using GPU or `pip install -r requirements.txt` if you are using CPU.
4. Make sure to have ffmpeg installed and added to your PATH
5. Get to root directory and Run the script by typing `python Main.py`

## Using GPU

> [!Note] \
> The `--extra-index-url` here might not always be up to date, so you can check the latest version of pytorch [here](https://pytorch.org/get-started/locally/). You can also check the available version of pytorch [here](https://download.pytorch.org/whl/torch_stable.html).

Make sure that you add `--extra-index-url https://download.pytorch.org/whl/cu118` when installing the dependencies if you want to use GPU for pytorch.

## Running the app

You can run the app by running the [`Run.py`](./Run.py) located in **root directory**. Alternatively you can also run it using `python -m speech_translate` in the **root directory**. 

## Building

Before compiling the project, make sure you have installed all the dependencies and setup your pytorch correctly. Your pytorch version will control wether the app will use GPU or CPU (that's why it's recommended to make virtual environment for the project).

I have provided a `[build script](./build.py)` that will build the project for you. You can run it by typing `python build.py` in the **root directory**. This will produce an executable file in the `dist` directory. An active python virtual environment is required to run the script. Alternatively you can use the following commands to build the project:

```bash
pyinstaller --noconfirm --onedir --console --icon "./assets/icon.ico" --name "Speech Translate" --clean --add-data "./assets;assets/" --copy-metadata "tqdm" --copy-metadata "regex" --copy-metadata "requests" --copy-metadata "packaging" --copy-metadata "filelock" --copy-metadata "numpy" --copy-metadata "tokenizers" --add-data "./venv/Lib/site-packages/whisper/assets;whisper/assets/"  "./Run.py"
```

**Note: Replace the __venv__ with your actual venv / python path**

## Compatibility

This project should be compatible with Windows (preferrably windows 10 or later) and other platforms. But I haven't tested it on platform other than windows.

---


# Contributing

Feel free to contribute to this project by forking the repository, making your changes, and submitting a pull request. You can also contribute by creating an issue if you find a bug or have a feature request. Also, feel free to give this project a star if you like it.

# License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

# Attribution

- [Sunvalley TTK Theme](https://github.com/rdbende/Sun-Valley-ttk-theme/) (used for app theme although i modified it a bit)

# Other

Check out my other similar project called [Screen Translate](https://github.com/Dadangdut33/Screen-Translate/) a screen translator / OCR tools made possible using tesseract.
