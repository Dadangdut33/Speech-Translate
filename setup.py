import os
from setuptools import setup


def version():
    with open(os.path.join(os.path.dirname(__file__), "speech_translate/_version.py")) as f:
        return f.readline().split("=")[1].strip().strip('"').strip("'")


def read_me():
    with open("README.md", "r", encoding="utf-8") as f:
        return f.read()


def install_requires():
    with open("requirements.txt", "r", encoding="utf-8") as f:
        req = f.read().splitlines()
        return req
    
print(install_requires())

setup(
    name="SpeechTranslate",
    version=version(),
    description="A realtime speech transcription and translation application using Whisper OpenAI and free translation API. Interface made using Tkinter. Code written fully in Python.",
    long_description=read_me(),
    long_description_content_type="text/markdown",
    python_requires=">=3.8",
    author="Dadangdut33",
    url="https://github.com/Dadangdut33/Speech-Translate",
    license="MIT",
    packages=[
        "speech_translate",
        "speech_translate.utils",
        "speech_translate.components",
        "speech_translate.components.abstract",
        "speech_translate.components.custom",
        "speech_translate.components.window",
        "speech_translate.assets",
        "speech_translate.theme",
        "speech_translate.theme.skip",
        "speech_translate.theme.sv",
        "speech_translate.theme.sv.resource",
    ],
    package_data={
        "speech_translate.assets": ["*"],
        "speech_translate.theme": ["*"],
        "speech_translate.theme.skip": ["*"],
        "speech_translate.theme.sv": ["*"],
        "speech_translate.theme.sv.resource": ["*"],
    },
    install_requires=install_requires(),
    entry_points={
        "console_scripts": [
            "speech-translate=speech_translate.__main__:main",
        ]
    },
    include_package_data=True,
)
