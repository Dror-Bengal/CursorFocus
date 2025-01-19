from setuptools import setup, find_packages

setup(
    name="cursorfocus",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "PyYAML>=6.0.1",
        "watchdog>=3.0.0",
        "python-dotenv>=1.0.0",
        "colorama>=0.4.6",
        "rich>=13.7.0",
        "google-generativeai>=0.3.0"
    ],
    entry_points={
        "console_scripts": [
            "cursorfocus=cursorfocus.focus:main",
            "cursorfocus-review=cursorfocus.code_review:main"
        ]
    },
    author="Dror Bengal",
    author_email="your.email@example.com",
    description="AI-powered code review and project analysis tool",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Dror-Bengal/CursorFocus",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Documentation",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    include_package_data=True,
    package_data={
        "cursorfocus": ["templates/*"],
    }
) 