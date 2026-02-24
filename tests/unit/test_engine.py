import pytest
from ufc.plugins.registry import PluginRegistry, InputReader, OutputWriter
from ufc.core.engine import CoreEngine
from ufc.core.errors import UnsupportedExtensionError

def test_plugin_registry():
    assert ".docx" in PluginRegistry.available_inputs()
    assert ".txt" in PluginRegistry.available_outputs()

    # Get readers
    assert PluginRegistry.get_reader(".docx") is not None
    assert PluginRegistry.get_reader(".invalid") is None

def test_engine_unsupported_extensions():
    with pytest.raises(UnsupportedExtensionError):
        CoreEngine.convert("in.invalid", "out.txt", {}, {})
        
    with pytest.raises(UnsupportedExtensionError):
        CoreEngine.convert("in.docx", "out.invalid", {}, {})
