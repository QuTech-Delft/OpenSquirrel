import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "opensquirrel",
    version = "0.0.3",
    author = "Pablo Le Henaff",
    author_email = "p.lehenaff@tudelft.nl",
    description = "A quantum circuit transformation and manipulation tool",
    license = "Apache",
    keywords = "quantum circuits compilation",
    url = "https://github.com/QuTech-Delft/OpenSquirrel",
    packages=['opensquirrel', 'test'],
    long_description=read('README.md'),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: Apache Software License",
    ],
)
