# About

A speech transcription and translation application using whisper AI model.

## Preview

...

## Download

Latest release..

## Development

> **Warning** \
> As of right now (4th of November 2022) I guess pytorch is not compatible with python 3.11 so you cann't use python 3.11. I tried with 3.11 but it doesn't work so i rollback to python 3.10.8.

### Setup

> **Note** \
> It is recommended to create a virtual environment, but it is not required.

1. Create your virtual environment by running `python -m venv venv`
2. Activate your virtual environment by running `source venv/bin/activate`
3. Install all the dependencies needed by running the [`devSetup.py`](./devSetup.py) located in **root directory** or install the packages yourself by installing from the requirements.txt yourself by running`pip install -r requirements.txt`
4. Run the script by typing `python Main.py`

**You must be at speech_translate directory when developing and compiling/building the project to avoid error**

### Using GPU for Whisper

> **Note** \
> This process could be handled automatically by running [devSetup.py](./devSetup.py)

To use GPU you first need to uninstall `torch` then you can go to [pytorch official website](https://pytorch.org/) to install the correct version of `pytorch` with GPU compatibily for your system.

### Building

You can use [pyinstaller](https://pyinstaller.org/) or [auto-py-to-exe](https://github.com/brentvollebregt/auto-py-to-exe) for a graphical interface.

- If you use **pyinstaller** you can load the [spec file](./build.spec) by running `pyinstaller ./build.spec` to build the project. Alternatively, you can type the build command directly like this:

  ```bash
  pyinstaller --noconfirm --onedir --console --icon "./speech_translate/assets/icon.ico" --name "Speech Translate" --clean --add-data "./assets;assets/" --copy-metadata "tqdm" --copy-metadata "regex" --copy-metadata "requests" --copy-metadata "packaging" --copy-metadata "filelock" --copy-metadata "numpy" --copy-metadata "tokenizers" --add-data "./venv/Lib/site-packages/whisper/assets;whisper/assets/"  "./Main.py"
  ```

  This will produce an exceutable file in the `dist` directory.

  **Note: Replace the venv with your venv name**

- If you use **auto-py-to-exe** you can load the [build.json file](./build.json) located in root directory. This will produce an exceutable file in the `output` directory.

You should be able to compile it on other platform (mac/linux) but I only tested it on Windows.

### Compatibility

This project should be compatible with Windows (preferrably windows 10 or later) and Linux but I haven't tested it on Mac.

## Contributing

Feel free to contribute to this project by forking the repository, making your changes, and submitting a pull request. You can also contribute by creating an issue if you find a bug or have a feature request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## Other

Check out my other similar project [screen translate](https://github.com/Dadangdut33/Screen-Translate/)
