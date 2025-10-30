import os
from setuptools import setup

lib_folder = os.path.dirname(os.path.realpath(__file__))

# get required packages from requirements.txt
requirement_path = os.path.join(lib_folder, 'requirements.txt')


setup(
    name="tactile_feature_extraction",
    version="0.1.0",
    author="Vincent",
    description="Tactile feature extraction and model learning package modified for ATI Mini45 sensor",
    packages=['tactile_feature_extraction'],
    install_requires=[
        "numpy",
        "opencv-python",
        "matplotlib",
        "scikit-image",
        "pandas",
        "tensorboard",
        "vit-pytorch",
        "pytorch-model-summary",
        'nidaqmx'
    ],
)
