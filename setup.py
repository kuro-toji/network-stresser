from setuptools import setup, find_packages

setup(
    name="network-stresser",
    version="1.0.0",
    description="Professional-grade network load testing and stress testing tool",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Network Stresser",
    author_email="dev@example.com",
    url="https://github.com/example/network-stresser",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests>=2.28.0",
        "httpx>=0.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "ruff>=0.1.0",
        ],
        "reports": [
            "matplotlib>=3.7.0",
            "jinja2>=3.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "network-stresser=loadtest:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Networking",
        "Topic :: System :: Benchmark",
        "Topic :: Security",
    ],
    python_requires=">=3.8",
)
