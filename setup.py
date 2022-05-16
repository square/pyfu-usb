"""Package configuration."""

import setuptools

setuptools.setup(
    name="pfu-util",
    author="Block, Inc.",
    version="0.1.0",
    description="Python device firmware update utility",
    packages=setuptools.find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "pyusb>=1.0.2",
    ],
    extras_require={
        "dev": [
            "black~=22.3.0",
            "pylint~=2.6.0",
            "pre-commit~=2.18.1",
            "wheel~=0.37.1",
        ]
    },
    entry_points={
        "console_scripts": ["pfu-util=pfu_util.__main__:main"],
    },
)
