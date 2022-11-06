# About

A speech transcription and translation application using whisper AI

# Development

## Incompatibility

As of right now (4th of November 2022) pytorch is not compatible with python 3.11 so you cann't use python 3.11. I use python 3.10.8.

## Setup

1. Create your virtual environment by running `python -m venv venv`
2. Activate your virtual environment by running `source venv/bin/activate`
3. Install the dependencies by running the `setup.py` located in root directory or install the packages yourself by running `pip install -r requirements.txt`
4. Navigate to the `speech_translate` directory, and run `python Main.py`

## Using GPU for Whisper

To use GPU you first need to uninstall `torch` then you can go to [pytorch official website](https://pytorch.org/) to install the correct version of `pytorch` with GPU compatibily for your system.

## Building

To be addded.

## Contributing

Feel free to contribute to this project by forking the repository, making your changes, and submitting a pull request. You can also contribute by creating an issue if you find a bug or have a feature request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
