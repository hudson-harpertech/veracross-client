from setuptools import setup, find_packages

setup(
    name="veracross-client",
    version="0.0.4",
    author="Hudson Harper",
    author_email="hudson@harpertech.io",
    description="Python wrapper for communicating with the Veracross API",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    test_suite="nose.collector",
)
