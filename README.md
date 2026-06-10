# langchain-pymupdf4llm

An independent LangChain integration package connecting PyMuPDF4LLM to LangChain
as a document loader.

[![LangChain v1.0+](https://img.shields.io/badge/LangChain-v1.0+-blue)](https://pypi.org/project/langchain-core/)
[![PyMuPDF4LLM](https://img.shields.io/badge/PyMuPDF4LLM-dependency-blue)](https://pypi.org/project/pymupdf4llm/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: AGPL-3.0-only](https://img.shields.io/badge/License-AGPL--3.0--only-blue.svg)](LICENSE)
[![PyPI Downloads](https://static.pepy.tech/badge/langchain-pymupdf4llm/month)](https://pepy.tech/projects/langchain-pymupdf4llm)
[![Discord](https://img.shields.io/discord/770681584617652264?color=6A7EC2&logo=discord&logoColor=ffffff)](https://artifex.com/discord/artifex?utm_source=github&utm_medium=referral&utm_campaign=pymupdf_github&utm_content=badges&utm_term=discord)
[![Forum](https://img.shields.io/badge/Forum-ff6600?logo=python&logoColor=ffffff)](https://forum.mupdf.com/c/general/4?utm_source=github&utm_medium=referral&utm_campaign=pymupdf_github&utm_content=badges&utm_term=forum)
[![Twitter](https://img.shields.io/twitter/follow/pymupdf4llm)](https://x.com/pymupdf4llm)
[![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97_Hugging_Face-007ec6)](https://huggingface.co/artifex-software)
[![Demo](https://img.shields.io/badge/PyMuPDF4LLM-live?badge&label=DEMO&logo=python&logoColor=ffffff)](https://demo.pymupdf.io?utm_source=github&utm_medium=referral&utm_campaign=pymupdf_github&utm_content=badges&utm_term=demo)

## Introduction

`langchain-pymupdf4llm` integrates PyMuPDF4LLM with LangChain as a document
loader. It extracts PDF content into Markdown for LLM and retrieval-augmented
generation workflows.

## Features

PyMuPDF4LLM provides Markdown extraction for standard text, tables, headers,
lists, code blocks, multi-column pages, images, and vector graphics.

This integration adds LangChain loader and parser APIs, including optional image
description replacement when an image parser is provided.

## Requirements

- Python 3.10 or higher
- LangChain Core v1.0.0 or higher
- PyMuPDF4LLM v1.27.2.1 or higher

## Installation

Install the package using pip:

```bash
pip install -U langchain-pymupdf4llm
```

Before installing, make sure the AGPL/commercial licensing model of the
PyMuPDF stack works for your use case.

For optional image parsing capabilities, you may also want to install:

```bash
pip install langchain-community
```

## Usage

```python
from langchain_pymupdf4llm import PyMuPDF4LLMLoader

loader = PyMuPDF4LLMLoader(
    file_path="/path/to/input.pdf",
    mode="single",
    pages_delimiter="\n\f"
)

docs = loader.load()
print(docs[0].page_content[:100])
print(docs[0].metadata)
```

Use `lazy_load()` to stream documents:

```python
for doc in loader.lazy_load():
    print(doc.metadata)
```

Use the parser with LangChain blob loaders:

```python
from langchain_community.document_loaders import FileSystemBlobLoader
from langchain_community.document_loaders.generic import GenericLoader
from langchain_pymupdf4llm import PyMuPDF4LLMParser

loader = GenericLoader(
    blob_loader=FileSystemBlobLoader(path="path/to/docs/", glob="*.pdf"),
    blob_parser=PyMuPDF4LLMParser(),
)
```

### Image options

You can utilize the Langchain Community `LLMImageBlobParser` along with a model to describe sourced images instead of reference them by filename.

For example:

```python
from langchain_pymupdf4llm import PyMuPDF4LLMLoader
from langchain_community.document_loaders.parsers import LLMImageBlobParser
from langchain_openai import ChatOpenAI

loader = PyMuPDF4LLMLoader(
    "test.pdf",
    mode="page",
    extract_images=True,
    images_parser=LLMImageBlobParser(
        model=ChatOpenAI(model="gpt-5.5", max_tokens=1024),
        prompt="Describe the content of each image in a few sentences."
    ),
)
docs = loader.load()

print(docs[0].page_content[0:])
```

## Development

Open the workspace in the devcontainer, then install dependencies manually:

```bash
uv sync --group dev --group test --group lint --group typing
```

Install lightweight pre-commit hooks for formatting and hygiene checks:

```bash
uv run pre-commit install
```

Common commands are available as Cursor/VS Code tasks:

- `uv sync`
- `test`
- `coverage`
- `lint`
- `format`
- `typecheck`
- `jupyter`

JupyterLab is configured as a foreground task on port `8888`. It does not start automatically when the container starts.

Run checks locally:

```bash
uv run --group test python -m pytest
uv run pytest --cov=src/langchain_pymupdf4llm --cov-report=term-missing --cov-fail-under=90
uv run black --check .
uv run ruff check .
uv run mypy .
uv run pre-commit run --all-files
```

The default pytest run disables sockets and skips tests marked `network`. To run
network tests explicitly:

```bash
uv run --group test python -m pytest --force-enable-socket -m network
```

## Creating Test Documents

To recreate the example PDF documents from LaTeX with deterministic PDF metadata:

```bash
cd ./tests/examples
SOURCE_DATE_EPOCH=1704067200 FORCE_SOURCE_DATE=1 pdflatex -interaction=nonstopmode sample_1.tex
```

## Jupyter Notebooks

Start JupyterLab from the devcontainer:

```bash
uv run jupyter lab --ip 0.0.0.0 --port 8888 --no-browser
```

## Licensing

This package depends directly on `pymupdf4llm` / `pymupdf`, which are published
by Artifex under AGPL/commercial terms. Because this integration wraps that
stack directly, this repository is distributed under `AGPL-3.0-only`.

PyMuPDF4LLM and PyMuPDF are maintained by [Artifex Software, Inc.](https://artifex.com?utm_source=github&utm_medium=referral&utm_campaign=pymupdf_github&utm_content=footer&utm_term=website)

- **Open source** — [GNU AGPL v3](https://www.gnu.org/licenses/agpl-3.0.html). Free for open-source projects.
- **Commercial** — separate commercial licences available from [Artifex](https://artifex.com/licensing?utm_source=github&utm_medium=referral&utm_campaign=pymupdf_github&utm_content=footer&utm_term=licensing) for proprietary applications.

---

## Contributing

Contributions are welcome. Please open an issue before submitting large pull requests.

- [Issue tracker](https://github.com/pymupdf/langchain-pymupdf4llm/issues)
- [Discord community](https://artifex.com/discord/artifex?utm_source=github&utm_medium=referral&utm_campaign=pymupdf_github&utm_content=footer&utm_term=discord)

## ⭐ Support this project

If you find this useful, please consider giving it a star — it helps others discover it!

[![Star on GitHub](https://img.shields.io/github/stars/pymupdf/langchain-pymupdf4llm.svg?style=for-the-badge&label=Star&logo=github)](https://github.com/pymupdf/langchain-pymupdf4llm/)

