import glob
import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

with open("requirements.txt", "r") as f:
    requirements = f.read().strip().split("\n")

extras_require = {}
for path in glob.glob("requirements_*.txt"):
    extra = path.split("_")[-1].split(".")[0]
    with open(path, "r") as f:
        extras_require[extra] = [
            dep
            for dep in map(str.strip, f.readlines())
            if dep != "" and not dep.startswith("-")
        ]


setuptools.setup(
    name="neo-mldl",
    version="1.1.4",
    author="Matthew Savage",
    author_email="mdsavage@zensors.com",
    description="Machine Learning Data Lake Utilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://zensors.com",
    packages=setuptools.find_packages(),
    package_data={"": ["image/assets/*"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    extras_require=extras_require,
    dependency_links=[
        "https://download.pytorch.org/whl/nightly/cpu/torch_nightly.html"
    ]
)
