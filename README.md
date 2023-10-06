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

Speech Translate is a practical application that combines OpenAI's Whisper ASR model with free translation APIs. It serves as a versatile tool for both real-time / live speech-to-text and speech translation, allowing the user to seamlessly convert spoken language into written text. Additionally, it has the option to import and transcribe audio / video files effortlessly.

<p align="center">
  <img src="https://raw.githubusercontent.com/Dadangdut33/Speech-Translate/master/speech_translate/assets/1.png" width="700" alt="Speech Translate Preview">
</p>

<details close>
  <summary>Preview - Usage</summary>
  <p align="center">
    <img src="https://raw.githubusercontent.com/Dadangdut33/Speech-Translate/master/speech_translate/assets/7.png" width="700" alt="Record">
    <img src="https://raw.githubusercontent.com/Dadangdut33/Speech-Translate/master/speech_translate/assets/8.png" width="700" alt="File import">
    <img src="https://raw.githubusercontent.com/Dadangdut33/Speech-Translate/master/speech_translate/assets/9.png" width="700" alt="Transcribe mode on subtitle window (English)">
    Transcribe mode on detached window (English)
    <img src="https://raw.githubusercontent.com/Dadangdut33/Speech-Translate/master/speech_translate/assets/10.png" width="700" alt="Translate mode on subtitle window (English to Indonesia)">
    Translate mode on detached window (English to Indonesia)
  </p>
</details>

<details close>
  <summary>Preview - Setting</summary>
  <p align="center">
    <img src="https://raw.githubusercontent.com/Dadangdut33/Speech-Translate/master/speech_translate/assets/2.png" width="700" alt="Setting">
    <img src="https://raw.githubusercontent.com/Dadangdut33/Speech-Translate/master/speech_translate/assets/3.png" width="700" alt="Setting">
    <img src="https://raw.githubusercontent.com/Dadangdut33/Speech-Translate/master/speech_translate/assets/4.png" width="700" alt="Setting">
    <img src="https://raw.githubusercontent.com/Dadangdut33/Speech-Translate/master/speech_translate/assets/4.png" width="700" alt="Setting">
    <img src="https://raw.githubusercontent.com/Dadangdut33/Speech-Translate/master/speech_translate/assets/5.png" width="700" alt="Setting">
    <img src="https://raw.githubusercontent.com/Dadangdut33/Speech-Translate/master/speech_translate/assets/6.png" width="700" alt="Setting">
    <img src="https://raw.githubusercontent.com/Dadangdut33/Speech-Translate/master/speech_translate/assets/7.png" width="700" alt="Record preview">
    <img src="https://raw.githubusercontent.com/Dadangdut33/Speech-Translate/master/speech_translate/assets/8.png" alt="Transcribe mode on subtitle window (English)">
    Transcribe mode on detached window (English)
    <img src="https://raw.githubusercontent.com/Dadangdut33/Speech-Translate/master/speech_translate/assets/9.png" alt="Translate mode on subtitle window (English to Indonesia)">
    Translate mode on detached window (English to Indonesia)
  </p>
</details>

<br />

<h1>Table Of Contents</h1>

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
  - [From Prebuilt binary:](#from-prebuilt-binary)
  - [As module:](#as-module)
- [More Information](#more-information)
- [Building / Developing / Compiling Yourself](#building--developing--compiling-yourself)
  - [Setup](#setup)
  - [Running the app](#running-the-app)
  - [Building](#building)
  - [Compatibility](#compatibility)
- [Contributing](#contributing)
- [License](#license)
- [Attribution](#attribution)
- [Other](#other)

# Features

- Speech to text
- Speech translation (transcribed text can be translated to other languages)
- Live input from mic and speaker
- Batch file processing of audio / video files for transcription and translation with output of (.txt .srt .tsv .vtt .json)

# Requirements

- Compatible OS: 

|    OS       | Prebuilt binary | As a module |
|:-----------:|:---------------:|:-----------:|
|    Windows  |        ✔️       |     ✔️     |
|    MacOS    |        ❌       |     ✔️     |
|    Linux    |        ❌       |     ✔️     |

\* Python 3.8 or later (3.10 is recommended) for installation as module.

- Speaker input only work on windows 8 and above.
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

- Recommended to have capable GPU with CUDA compatibility to run each model. Each model has different requirements, for more information you can check it directly at the [whisper repository](https://github.com/openai/whisper).

|  Size  | Parameters | English-only model | Multilingual model | Required VRAM | Relative speed |
|:------:|:----------:|:------------------:|:------------------:|:-------------:|:--------------:|
|  tiny  |    39 M    |     `tiny.en`      |       `tiny`       |     ~1 GB     |      ~32x      |
|  base  |    74 M    |     `base.en`      |       `base`       |     ~1 GB     |      ~16x      |
| small  |   244 M    |     `small.en`     |      `small`       |     ~2 GB     |      ~6x       |
| medium |   769 M    |    `medium.en`     |      `medium`      |     ~5 GB     |      ~2x       |
| large  |   1550 M   |        N/A         |      `large`       |    ~10 GB     |       1x       |

\* This information is also available in the app (hover over the model selection in the app and there will be a tooltip about the model info). 


# Installation

> [!IMPORTANT]  
> Make sure that you have installed [FFmpeg](https://ffmpeg.org/) and added it to the PATH environment variable. [See here](#requirements) for more info

## From Prebuilt binary:

1. Download the [latest release](https://github.com/Dadangdut33/Speech-Translate/releases/latest) (There are 2 versions, CPU and GPU)
2. Install/extract the downloaded file
3. Run the program
4. Enjoy!

## As module:

To install as module, we can use pip, with the following command.

- Install with **GPU (Cuda compatible)** support:
  
  `pip install -U git+https://github.com/Dadangdut33/Speech-Translate.git --extra-index-url https://download.pytorch.org/whl/cu118`

- **CPU** only:
  
  `pip install -U git+https://github.com/Dadangdut33/Speech-Translate.git`

You can then run the program by typing `speech-translate` in your terminal/console. Alternatively, when installing as a module, you can also clone the repo and install it locally by running `pip install -e .` in the project directory. (Don't forget to add `--extra-index-url` if you want to install with GPU support)

**Notes:**

- If you are updating from an older version, you need to add `--upgrade --no-deps --force-reinstall` at the end of the command.
- If you want to install from a specific branch or commit, you can do it by adding `@branch_name` or `@commit_hash` at the end of the url. Example: `pip install -U git+https://github.com/Dadangdut33/Speech-Translate.git@dev --extra-index-url https://download.pytorch.org/whl/cu118`
- The --extra-index-url here might not always be up to date, so you can check the latest version of pytorch [here](https://pytorch.org/get-started/locally/). You can also check the available version of pytorch [here](https://download.pytorch.org/whl/torch_stable.html).

# More Information

Check out the [wiki](https://github.com/Dadangdut33/Speech-Translate/wiki) for more information about the app, the user settings, and how to use it.

# Building / Developing / Compiling Yourself

## Setup

> [!NOTE]  
> It is recommended to create a virtual environment, but it is not required.

1. Create your virtual environment by running `python -m venv venv`
2. Activate your virtual environment by running `source venv/bin/activate`
3. Install all the dependencies needed by running `pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu118` if you are using GPU or `pip install -r requirements.txt` if you are using CPU.
4. Make sure to have ffmpeg installed and added to your PATH
5. Get to root directory and Run the script by typing `python Main.py`

## Running the app

You can run the app by running the [`Run.py`](./Run.py) located in **root directory**. Alternatively you can also run it using `python -m speech_translate` in the **root directory**.

## Building

Before compiling the project, make sure you have installed all the dependencies and setup your pytorch correctly. Your pytorch version will control wether the app will use GPU or CPU (that's why it's recommended to make virtual environment for the project). The pre compiled version in this project is built using cx_freeze, i have provided the script in [build.py](./build.py). To compile it into an exe run `python build.py build` in the **root directory**. This will produce an executable file in the `build` directory. After that, use innosetup script to create an installer. You can use the provided [installer.iss](./installer.iss) to create an installer. 

## Compatibility

This project should be compatible with Windows (preferrably windows 10 or later) and other platforms. But I haven't tested it extensively on other platforms. If you find any bugs or issues, feel free to create an issue.

---

# Contributing

Feel free to contribute to this project by forking the repository, making your changes, and submitting a pull request. You can also contribute by creating an issue if you find a bug or have a feature request. Also, feel free to give this project a star if you like it.

# License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

# Attribution

- [Sunvalley TTK Theme](https://github.com/rdbende/Sun-Valley-ttk-theme/) (used for app theme although i modified it a bit)

# Other

Check out my other similar project called [Screen Translate](https://github.com/Dadangdut33/Screen-Translate/) a screen translator / OCR tools made possible using tesseract.
