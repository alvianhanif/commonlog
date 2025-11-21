from setuptools import setup, find_packages

setup(
    name="commonlog",
    version="0.1.1",
    description="Unified logging and alerting library for Python.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Alvian Rahman Hanif",
    author_email="alvian.hanif@pasarpolis.com",
    url="https://github.com/alvianhanif/commonlog",
    packages=find_packages(),
    install_requires=[],
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
)