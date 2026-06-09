# langchain-pymupdf4llm

An independent LangChain integration package connecting PyMuPDF4LLM to LangChain
as a document loader.

[![LangChain v1.0+](https://img.shields.io/badge/LangChain-v1.0+-blue)](https://pypi.org/project/langchain-core/)
[![PyMuPDF4LLM](https://img.shields.io/badge/PyMuPDF4LLM-dependency-blue)](https://pypi.org/project/pymupdf4llm/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: AGPL-3.0-only](https://img.shields.io/badge/License-AGPL--3.0--only-blue.svg)](LICENSE)

## Introduction

`langchain-pymupdf4llm` integrates PyMuPDF4LLM with LangChain as a document
loader. It extracts PDF content into Markdown for LLM and retrieval-augmented
generation workflows.

## Licensing

This package depends directly on `pymupdf4llm` / `pymupdf`, which are published
by Artifex under AGPL/commercial terms. Because this integration wraps that
stack directly, this repository is distributed under `AGPL-3.0-only`.

If you distribute software or provide a network service that uses this package,
you must evaluate your own AGPL compliance obligations. If you cannot comply
with the AGPL, obtain an appropriate commercial license for the PyMuPDF stack
from Artifex instead of relying on this package under the AGPL.

`langchain-core` remains MIT-licensed and is compatible with this package's
AGPL license. See `NOTICE` for third-party attribution details.

## Features

PyMuPDF4LLM provides Markdown extraction for standard text, tables, headers,
lists, code blocks, multi-column pages, images, and vector graphics.

This integration adds LangChain loader and parser APIs, including optional image
description replacement when an image parser is provided.

## Requirements

- Python 3.10 or higher
- LangChain Core v1.0.0 or higher
- PyMuPDF4LLM v1.27.2.1 up to, but not including, v1.28.0

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

## Licensing Correction For Existing Users

Earlier releases of this package were incorrectly labeled as MIT. The package
has always depended on the AGPL/commercial PyMuPDF stack, so existing users
should re-evaluate whether their usage and redistribution model is compatible
with that dependency chain.

Future corrective releases should:

1. Keep the AGPL package metadata and repository license files aligned.
2. Clearly disclose the licensing correction in release notes.
3. Deprecate or supersede the incorrectly labeled release on package indexes where possible.

## Usage

```python
from langchain_pymupdf4llm import PyMuPDF4LLMLoader

loader = PyMuPDF4LLMLoader(
    file_path="/path/to/input.pdf",
    mode="single",
    pages_delimiter="\n\f",
    use_layout=False,
    table_strategy="lines",
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

## Contribute

Issues and pull requests are welcome on the
[GitHub repository](https://github.com/pymupdf/langchain-pymupdf4llm).
