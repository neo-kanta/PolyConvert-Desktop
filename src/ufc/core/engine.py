from typing import Any, Dict
from pathlib import Path

from ufc.core.errors import UnsupportedExtensionError, ConversionFailedError
from ufc.plugins.registry import PluginRegistry


class CoreEngine:
    """
    Orchestrates the conversion from an input file to an output file.
    Does not know about parsing logic or writing logic, only routing.
    """

    @staticmethod
    def convert(input_path: str, output_path: str, read_options: Dict[str, Any], write_options: Dict[str, Any]) -> None:
        """
        Convert file at `input_path` to `output_path`.
        read_options and write_options allow passing format-specific toggles (e.g. utf8_bom, include_tables).
        """
        in_ext = Path(input_path).suffix.lower()
        out_ext = Path(output_path).suffix.lower()

        ReaderCls = PluginRegistry.get_reader(in_ext)
        if not ReaderCls:
            raise UnsupportedExtensionError(f"No reader found for extension '{in_ext}'")

        WriterCls = PluginRegistry.get_writer(out_ext)
        if not WriterCls:
            raise UnsupportedExtensionError(f"No writer found for extension '{out_ext}'")

        try:
            reader = ReaderCls()
            model = reader.read(input_path, read_options)
            
            writer = WriterCls()
            writer.write(model, output_path, write_options)
        except Exception as e:
            raise ConversionFailedError(f"Conversion failed: {e}") from e
