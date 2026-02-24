class FileConverterError(Exception):
    """Base exception for all converter errors."""
    pass

class UnsupportedExtensionError(FileConverterError):
    pass

class ConversionFailedError(FileConverterError):
    pass
