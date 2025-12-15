"""
Setup script for gee_acolite package
"""
from setuptools import setup, find_packages
import pathlib

# Read the contents of README file
here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8") if (here / "README.md").exists() else ""

setup(
    name="gee_acolite",
    version="1.0.0",
    author="Sergio",
    author_email="sergiohercar1@gmail.com",  # Cambiar por tu email
    description="ACOLITE atmospheric correction for Google Earth Engine",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Aouei/gee_acolite",  # URL de tu repositorio
    project_urls={
        "Bug Tracker": "https://github.com/Aouei/gee_acolite/issues",
        "Documentation": "https://github.com/Aouei/gee_acolite",
        "Source Code": "https://github.com/Aouei/gee_acolite",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    keywords="earth-engine, atmospheric-correction, acolite, sentinel-2, remote-sensing, water-quality",
    packages=find_packages(exclude=["tests", "jupyters", "examples"]),
    python_requires=">=3.8",
    install_requires=[
        "earthengine-api>=0.1.350",
        "numpy>=1.20.0",
        "scipy>=1.7.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=3.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.950",
        ],
        "notebooks": [
            "jupyter>=1.0.0",
            "matplotlib>=3.5.0",
            "geemap>=0.20.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "gee-acolite=gee_acolite.cli:main",  # Si creas una CLI en el futuro
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
