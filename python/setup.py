from setuptools import setup, find_packages
import subprocess

def get_latest_git_tag():
    try:
        tag = subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"]).decode().strip()
        # Clean up invalid version formats
        if '-v' in tag:
            # Extract base version from tags like 0.1.7-v24
            base_version = tag.split('-v')[0]
            return base_version
        return tag
    except Exception:
        return "0.0.0"

setup(
    name="commonlog",
    version=get_latest_git_tag(),
    description="Unified logging and alerting library for Python.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Alvian Rahman Hanif",
    author_email="alvian.hanif@pasarpolis.com",
    url="https://github.com/alvianhanif/commonlog",
    packages=find_packages(),
    install_requires=[],
    license="MIT",
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
)