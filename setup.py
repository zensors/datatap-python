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
    name = "datatap",
    version = "0.1.2",
    author = "Zensors' Dev Team",
    author_email = "dev-team@zensors.com",
    description = "Client library for dataTap",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://datatap.dev",
    packages = setuptools.find_packages(),
    package_data = { "": ["image/assets/*"], "datatap": ["py.typed"] },
    classifiers = [
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires = ">=3.7",
    install_requires = requirements,
    extras_require = extras_require,
    dependency_links = [
        "https://download.pytorch.org/whl/nightly/cpu/torch_nightly.html"
    ]
)
