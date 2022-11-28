<p align="center">
    <img src="https://github.com/Dadangdut33/Speech-Translate/blob/master/assets/icon.png?raw=true" width="250px" alt="Speech Translate Logo">
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

# Preview

...

# Download

Latest release..

# User Requirements

Whisper uses vram to process the audio, so it is recommended to have a CUDA compatible GPU. If there is no compatible GPU, the application will use the CPU to process the audio (This might make it slower). For each model requirement you can check directly at the [whisper repository](https://github.com/openai/whisper) or you can hover over the model selection in the app (there will be a tooltip about the model info).

# Development

> **Warning** \
> As of right now (4th of November 2022) I guess pytorch is not compatible with python 3.11 so you can't use python 3.11. I tried with 3.11 but it doesn't work so i rollback to python 3.10.8.

## Setup

> **Note** \
> It is recommended to create a virtual environment, but it is not required.

1. Create your virtual environment by running `python -m venv venv`
2. Activate your virtual environment by running `source venv/bin/activate`
3. Install all the dependencies needed by running the [`devSetup.py`](./devSetup.py) located in **root directory** or install the packages yourself by installing from the requirements.txt yourself by running`pip install -r requirements.txt`
4. Run the script by typing `python Main.py`

**You must be at speech_translate directory when developing and compiling/building the project to avoid error**

## Using GPU for Whisper

> **Note** \
> This process could be handled automatically by running [devSetup.py](./devSetup.py)

To use GPU you first need to uninstall `torch` then you can go to [pytorch official website](https://pytorch.org/) to install the correct version of `pytorch` with GPU compatibily for your system.

## Building

You can use [pyinstaller](https://pyinstaller.org/) or [auto-py-to-exe](https://github.com/brentvollebregt/auto-py-to-exe) for a graphical interface.

- If you use **pyinstaller** you can load the [spec file](./build.spec) by running `pyinstaller ./build.spec` to build the project. Alternatively, you can type the build command directly like this:

  ```bash
  pyinstaller --noconfirm --onedir --console --icon "./speech_translate/assets/icon.ico" --name "Speech Translate" --clean --add-data "./assets;assets/" --copy-metadata "tqdm" --copy-metadata "regex" --copy-metadata "requests" --copy-metadata "packaging" --copy-metadata "filelock" --copy-metadata "numpy" --copy-metadata "tokenizers" --add-data "./venv/Lib/site-packages/whisper/assets;whisper/assets/"  "./Main.py"
  ```

  This will produce an exceutable file in the `dist` directory.

  **Note: Replace the venv with your venv name**

- If you use **auto-py-to-exe** you can load the [build.json file](./build.json) located in root directory. This will produce an exceutable file in the `output` directory.

You should be able to compile it on other platform (mac/linux) but I only tested it on Windows.

## Compatibility

This project should be compatible with Windows (preferrably windows 10 or later) and Linux but I haven't tested it on Mac.

# Contributing

Feel free to contribute to this project by forking the repository, making your changes, and submitting a pull request. You can also contribute by creating an issue if you find a bug or have a feature request.

# License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

# Other

Check out my other similar project called [Screen Translate](https://github.com/Dadangdut33/Speech-Translate/)
