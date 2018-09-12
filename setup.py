import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="labtools",
    version="0.0.1",
    author="MazinLab",
    author_email="mazinlab@ucsb.edu",
    description="Scripts and other software tools for lab testing purposes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MazinLab/labtools",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        "Development Status :: 1 - Planning",
        "Intended Audience :: Science/Research"
    ),
)
