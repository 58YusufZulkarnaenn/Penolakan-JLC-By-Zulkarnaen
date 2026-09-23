import streamlit.components.v1 as components
import os

# Arahin ke folder barcode_frontend (sejajar sama file ini)
_COMPONENT_PATH = os.path.join(os.path.dirname(__file__), "barcode_frontend")

_barcode_scanner = components.declare_component(
    "barcode_scanner",
    path=_COMPONENT_PATH
)

def barcode_scanner(key="barcode_scanner"):
    """Panggil komponen scanner barcode. Return: string hasil scan atau None."""
    return _barcode_scanner(key=key, default=None)
