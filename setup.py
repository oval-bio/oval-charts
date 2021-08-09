import os

from setuptools import setup


def get_version():
    """
    Get version info from version module dict.
    """
    vi = {}
    vf = os.path.join("oval", "version.py")
    with open(vf, 'r') as mod:
        code = compile(mod.read(), "version.py", "exec")
        exec(code, vi)
    return vi


version = get_version()["version"]

setup(
    name="oval",
    version=version,
    author="Joe Rivera",
    author_email="j@jriv.us",
    description="Oval.bio session data bundle utilities",
    url="https://github.com/transfix/oval-charts",
    zip_safe=True,
    entry_points={
        "console_scripts": [
            "oval = oval.__main__:root"
        ]
    },
)
