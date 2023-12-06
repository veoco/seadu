from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="seadu",
    version="0.1.1",
    author="Veoco",
    author_email="one@nomox.cn",
    description="Seafile Downloader and Uploader",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/veoco/seadu",
    packages=find_packages(),
    entry_points={"console_scripts": ["seadu = seadu.__main__:main"]},
    install_requires=["aiohttp", "tqdm"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
)
