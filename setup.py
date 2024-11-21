from setuptools import setup, find_packages

setup(
    name="diagify",  # Name of your package
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "openai",
        "diagrams",
    ],
    entry_points={
        "console_scripts": [
            "diagify=diagify.main:main",  # Command = module:function
        ],
    },
    author="Alex Minnaar",
    author_email="minnaaralex@gmail.com",
    description="A tool to generate diagrams from natural language using Mingrammer.",
    url="https://github.com/alexminnaar/diagify",  # Optional
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",  # Adjust based on your compatibility
)
