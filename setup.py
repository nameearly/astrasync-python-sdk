from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="astrasyncai",
    version="1.0.0",
    # NOTE(发布一致性): astrasync/__init__.py 里的 __version__ 当前为 0.2.1，且 utils/api.py 的
    # User-Agent 也写死为 1.0.0。建议统一版本来源，避免 CLI/包版本/UA 不一致。
    author="AstraSync AI",
    author_email="developers@astrasync.ai",
    description="Universal AI agent registration for blockchain compliance",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AstraSyncAI/astrasync-python-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "click>=8.0.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "astrasync=astrasync.cli:cli",
        ],
    },
)
