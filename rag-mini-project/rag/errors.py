"""Exception types with user-safe messages."""


class RAGError(Exception):
    """Base class; str(e) is safe to show to end users."""


class IngestionError(RAGError):
    """A source file could not be processed."""


class UnsupportedFormatError(IngestionError):
    pass


class EmptyDocumentError(IngestionError):
    pass


class IndexNotBuiltError(RAGError):
    pass


class RetrievalError(RAGError):
    pass


class GenerationError(RAGError):
    pass
