from abc import ABC, abstractmethod
from typing import Dict, Type, Any

from ufc.core.models import DocumentModel


class InputReader(ABC):
    @classmethod
    @abstractmethod
    def get_supported_extensions(cls) -> list[str]:
        """e.g., ['.docx']"""
        pass

    @abstractmethod
    def read(self, file_path: str, options: Dict[str, Any]) -> DocumentModel:
        pass


class OutputWriter(ABC):
    @classmethod
    @abstractmethod
    def get_supported_extensions(cls) -> list[str]:
        """e.g., ['.txt']"""
        pass

    @abstractmethod
    def write(self, model: DocumentModel, output_path: str, options: Dict[str, Any]) -> None:
        pass


class PluginRegistry:
    _readers: Dict[str, Type[InputReader]] = {}
    _writers: Dict[str, Type[OutputWriter]] = {}

    @classmethod
    def register_reader(cls, reader_cls: Type[InputReader]) -> None:
        for ext in reader_cls.get_supported_extensions():
            cls._readers[ext.lower()] = reader_cls

    @classmethod
    def register_writer(cls, writer_cls: Type[OutputWriter]) -> None:
        for ext in writer_cls.get_supported_extensions():
            cls._writers[ext.lower()] = writer_cls

    @classmethod
    def get_reader(cls, ext: str) -> Type[InputReader]:
        return cls._readers.get(ext.lower())

    @classmethod
    def get_writer(cls, ext: str) -> Type[OutputWriter]:
        return cls._writers.get(ext.lower())

    @classmethod
    def available_inputs(cls) -> list[str]:
        return sorted(cls._readers.keys())

    @classmethod
    def available_outputs(cls) -> list[str]:
        return sorted(cls._writers.keys())
