import os

import setuptools

CUR_DIR = os.path.abspath(os.path.dirname(__file__))

about = {}
with open(os.path.join(CUR_DIR, "rest_framework_idempotency_key", "__version__.py"), "r") as f:
    exec(f.read(), about)

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="djangorestframework-idempotency-key",
    version=about['__version__'],
    author="xeonchen, kilikkuo",
    author_email="pypi@hardcoretech.co",
    description="Idempotency key app & middleware for Django Rest Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hardcoretech/djangorestframework-idempotency-key",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=[
        'rest_framework_idempotency_key',
        'rest_framework_idempotency_key.migrations',
    ],
    install_requires=[
        'django',
        'djangorestframework',
        'data-spec-validator>=1.2.0',
    ],
    python_requires='>=3.6',
    project_urls={
        "Changelog": "https://github.com/hardcoretech/djangorestframework-idempotency-key/blob/main/CHANGELOG.md"
    },
)
