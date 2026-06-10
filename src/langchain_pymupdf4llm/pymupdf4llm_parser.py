"""Parse PDF blobs to Markdown documents with PyMuPDF4LLM."""

from __future__ import annotations

import importlib
import logging
import re
import threading
from collections.abc import Callable, Iterator, Mapping
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Literal, TypeAlias, cast

import pymupdf
from langchain_core.document_loaders import BaseBlobParser, Blob
from langchain_core.documents import Document

_DEFAULT_PAGES_DELIMITER = "\n-----\n\n"
_STD_METADATA_KEYS = {"source", "total_pages", "creationdate", "creator", "producer"}
_TRAILING_PAGE_DELIMITER = "\n-----\n\n"
_CONFLICTING_IMAGE_KWARGS = {"ignore_images", "ignore_graphics"}
_UNSUPPORTED_KWARGS = {
    "write_images",
    "embed_images",
    "image_path",
    "filename",
    "page_chunks",
    "extract_words",
    "show_progress",
}
_DEFAULT_GRAPHICS_LIMIT = 5000

logger = logging.getLogger(__name__)

MetadataValue: TypeAlias = str | int
Metadata: TypeAlias = dict[str, MetadataValue]


def _validate_metadata(metadata: Metadata) -> Metadata:
    """Validate standard metadata keys and page type."""
    if not _STD_METADATA_KEYS.issubset(metadata):
        message = "The PDF parser must valorize the standard metadata."
        raise ValueError(message)
    if not isinstance(metadata.get("page", 0), int):
        message = "The PDF metadata page must be an integer."
        raise ValueError(message)
    return metadata


def _format_pdf_date(value: str) -> str:
    """Convert PDF date strings to ISO format when possible."""
    try:
        return datetime.strptime(value.replace("'", ""), "D:%Y%m%d%H%M%S%z").isoformat(
            "T",
        )
    except ValueError:
        return value


def _purge_metadata(metadata: Mapping[str, object]) -> Metadata:
    """Purge unwanted metadata keys and normalize key names."""
    new_metadata: Metadata = {}
    map_key = {
        "page_count": "total_pages",
        "file_path": "source",
    }
    for key, raw_value in metadata.items():
        value = raw_value if isinstance(raw_value, (str, int)) else str(raw_value)
        normalized_key = key.removeprefix("/")
        normalized_key = normalized_key.lower()

        if normalized_key in {"creationdate", "moddate"}:
            new_metadata[normalized_key] = _format_pdf_date(str(value))
        elif normalized_key in map_key:
            mapped_key = map_key[normalized_key]
            new_metadata[mapped_key] = value
            new_metadata[normalized_key] = value
        elif isinstance(value, str):
            new_metadata[normalized_key] = value.strip()
        else:
            new_metadata[normalized_key] = value
    return new_metadata


def _find_img_paths_in_md(md_text: str) -> list[str]:
    """Find image paths generated in Markdown image references."""
    return re.findall(r"!\[\]\((.*?)\)", md_text)


def _load_pymupdf4llm() -> ModuleType:
    """Import PyMuPDF4LLM with a helpful package-specific error."""
    try:
        return importlib.import_module("pymupdf4llm")
    except ImportError as exc:
        message = (
            "pymupdf4llm package not found, please install it with "
            "`pip install pymupdf4llm`"
        )
        raise ImportError(message) from exc


def _to_markdown(module: ModuleType) -> Callable[..., str]:
    """Return the PyMuPDF4LLM to_markdown callable."""
    return cast("Callable[..., str]", vars(module)["to_markdown"])


class PyMuPDF4LLMParser(BaseBlobParser):
    """Parse a PDF blob into LangChain documents using PyMuPDF4LLM."""

    # PyMuPDF is not thread safe.
    # See https://pymupdf.readthedocs.io/en/latest/recipes-multiprocessing.html
    _lock = threading.Lock()

    def __init__(
        self,
        extract_images: bool = False,
        *,
        password: str | None = None,
        mode: Literal["single", "page"] = "page",
        pages_delimiter: str = _DEFAULT_PAGES_DELIMITER,
        images_parser: BaseBlobParser | None = None,
        use_layout: bool = False,
        **pymupdf4llm_kwargs: object,
    ) -> None:
        """Initialize a parser that extracts PDF content as Markdown.

        Args:
            extract_images: Whether to replace images with parsed image text.
            password: Optional password for encrypted PDFs.
            mode: Extraction mode, either ``single`` or ``page``.
            pages_delimiter: Delimiter for page content in ``single`` mode.
            images_parser: Image parser required when ``extract_images`` is true.
            use_layout: Whether to enable PyMuPDF4LLM layout mode when available.
            **pymupdf4llm_kwargs: Extra arguments passed to ``to_markdown``.
        """
        self._validate_init_args(
            extract_images=extract_images,
            images_parser=images_parser,
            mode=mode,
            pymupdf4llm_kwargs=pymupdf4llm_kwargs,
        )

        super().__init__()
        self.mode = mode
        self.pages_delimiter = pages_delimiter
        self.password = password
        self.extract_images = extract_images
        self.images_parser = images_parser
        self.use_layout = use_layout
        self.pymupdf4llm_kwargs = pymupdf4llm_kwargs

    @staticmethod
    def _validate_init_args(
        *,
        extract_images: bool,
        images_parser: BaseBlobParser | None,
        mode: str,
        pymupdf4llm_kwargs: Mapping[str, object],
    ) -> None:
        """Validate parser initialization arguments."""
        if mode not in {"single", "page"}:
            message = "mode must be single or page"
            raise ValueError(message)
        if extract_images and images_parser is None:
            message = "images_parser must be provided if extract_images is True"
            raise ValueError(message)
        conflicting_image_kwargs = (
            _CONFLICTING_IMAGE_KWARGS & pymupdf4llm_kwargs.keys()
            if extract_images
            else set()
        )
        for key in conflicting_image_kwargs:
            message = (
                f"PyMuPDF4LLM argument: {key} cannot be set to True when "
                "extract_images is True."
            )
            raise ValueError(message)
        for key in _UNSUPPORTED_KWARGS & pymupdf4llm_kwargs.keys():
            message = f"PyMuPDF4LLM argument: {key} cannot be set to True."
            raise ValueError(message)

    def lazy_parse(self, blob: Blob) -> Iterator[Document]:
        """Lazily parse a PDF blob."""
        _load_pymupdf4llm()

        with PyMuPDF4LLMParser._lock, blob.as_bytes_io() as file_path:
            if blob.data is None:
                doc = pymupdf.open(file_path)  # type: ignore[no-untyped-call]
            else:
                doc = pymupdf.open(stream=file_path, filetype="pdf")  # type: ignore[no-untyped-call]
            if doc.is_encrypted:
                doc.authenticate(self.password)  # type: ignore[no-untyped-call]
            doc_metadata = self._extract_metadata(doc, blob)
            full_content_md: list[str] = []
            for page_number in range(len(doc)):
                all_text_md = self._get_page_content_in_md(doc, page_number)
                all_text_md = all_text_md.removesuffix(_TRAILING_PAGE_DELIMITER)
                if self.mode == "page":
                    yield Document(
                        page_content=all_text_md,
                        metadata=_validate_metadata(
                            doc_metadata | {"page": page_number},
                        ),
                    )
                else:
                    full_content_md.append(all_text_md)

            if self.mode == "single":
                yield Document(
                    page_content=self.pages_delimiter.join(full_content_md),
                    metadata=_validate_metadata(doc_metadata),
                )

    def _get_page_content_in_md(
        self,
        doc: pymupdf.Document,
        page: int,
    ) -> str:
        """Get one page's content as Markdown."""
        pymupdf4llm = _load_pymupdf4llm()

        use_layout = getattr(pymupdf4llm, "use_layout", None)
        if callable(use_layout):
            use_layout(self.use_layout)

        pymupdf4llm_params: dict[str, object] = {
            **self.pymupdf4llm_kwargs,
        }
        pymupdf4llm_params.setdefault("graphics_limit", _DEFAULT_GRAPHICS_LIMIT)

        if self.extract_images and self.images_parser:
            return self._get_page_content_with_images(
                doc=doc,
                page=page,
                pymupdf4llm_params=pymupdf4llm_params,
            )

        return _to_markdown(pymupdf4llm)(
            doc,
            pages=[page],
            show_progress=False,
            **pymupdf4llm_params,
        )

    def _get_page_content_with_images(
        self,
        *,
        doc: pymupdf.Document,
        page: int,
        pymupdf4llm_params: dict[str, object],
    ) -> str:
        """Get one page's Markdown and replace image links with parsed image text."""
        pymupdf4llm = _load_pymupdf4llm()

        if self.images_parser is None:
            message = "images_parser must be provided if extract_images is True"
            raise ValueError(message)

        with TemporaryDirectory() as temp_dir:

            print(f"Using temporary directory for images: {temp_dir}")
            pymupdf4llm_params["write_images"] = True
            pymupdf4llm_params["image_path"] = temp_dir
            page_content_md = _to_markdown(pymupdf4llm)(
                doc,
                pages=[page],
                show_progress=False,
                **pymupdf4llm_params,
            )

            for img_path in _find_img_paths_in_md(page_content_md):
                image_path = Path(img_path)
                if image_path.exists():
                    image_blob = Blob.from_path(image_path)
                    image_text = next(
                        self.images_parser.lazy_parse(image_blob),
                    ).page_content.replace("]", r"\\]")
                    img_md = f"![{image_text}](#)"
                    page_content_md = page_content_md.replace(
                        f"![]({img_path})",
                        img_md,
                    )
                else:
                    logger.warning(
                        "Image path referenced in markdown but not found: %s",
                        img_path,
                    )

        return page_content_md

    def _extract_metadata(self, doc: pymupdf.Document, blob: Blob) -> Metadata:
        """Extract metadata from the PDF document."""
        raw_metadata: dict[str, object] = {
            "producer": "PyMuPDF4LLM",
            "creator": "PyMuPDF4LLM",
            "creationdate": "",
            "source": blob.source,
            "file_path": blob.source,
            "total_pages": len(doc),
        }
        doc_metadata = doc.metadata or {}
        raw_metadata.update(
            {
                key: value
                for key, value in doc_metadata.items()
                if isinstance(value, (str, int))
            },
        )
        metadata = _purge_metadata(raw_metadata)
        for key in ("modDate", "creationDate"):
            if key in doc_metadata:
                metadata[key] = str(doc_metadata[key])
        return metadata
