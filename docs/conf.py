"""Sphinx configuration for cellgenerator docs."""

import sys
from pathlib import Path

# Make the package importable from the repo root
sys.path.insert(0, str(Path(__file__).parents[1]))

# ---------------------------------------------------------------------------
# Project metadata
# ---------------------------------------------------------------------------

project = "cellgenerator"
author = "Gregory Way, Hugh Warden"
copyright = "2024-2026, Gregory Way, Hugh Warden"
release = "0.2.0"
version = "0.2"

# ---------------------------------------------------------------------------
# Extensions
# ---------------------------------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",  # pull docstrings from source
    "sphinx.ext.napoleon",  # Google / NumPy docstring styles
    "sphinx.ext.viewcode",  # [source] links next to every object
    "sphinx.ext.intersphinx",  # cross-reference Python / NumPy / PIL docs
    "sphinx_autodoc_typehints",  # render type hints in the signature & params
    "sphinx_copybutton",  # copy button on every code block
    "sphinx_design",  # tabs, cards, grids
    "myst_nb",  # MyST Markdown + Jupyter notebook rendering (replaces myst_parser)
]

# ---------------------------------------------------------------------------
# MyST settings
# ---------------------------------------------------------------------------

myst_enable_extensions = [
    "colon_fence",  # ::: fences as an alternative to ```
    "deflist",  # definition lists
    "fieldlist",  # RST-style field lists inside Markdown
]

# ---------------------------------------------------------------------------
# autodoc settings
# ---------------------------------------------------------------------------

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
    "special-members": "__init__",
}
autodoc_typehints = "description"  # types in the Parameters section
autodoc_typehints_description_target = "documented"
napoleon_numpy_docstring = True
napoleon_google_docstring = False
napoleon_use_param = False  # napoleon handles Parameters itself
napoleon_use_rtype = False

# ---------------------------------------------------------------------------
# intersphinx mapping
# ---------------------------------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "scipy": ("https://docs.scipy.org/doc/scipy", None),
    "PIL": ("https://pillow.readthedocs.io/en/stable", None),
    "matplotlib": ("https://matplotlib.org/stable", None),
}

# ---------------------------------------------------------------------------
# HTML output
# ---------------------------------------------------------------------------

html_theme = "furo"
html_title = "cellgenerator"
html_static_path = ["_static"]

html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "source_repository": "https://github.com/gwaybio/cellgenerator/",
    "source_branch": "main",
    "source_directory": "docs/",
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/gwaybio/cellgenerator",
            "html": """
                <svg stroke="currentColor" fill="currentColor" stroke-width="0"
                    viewBox="0 0 16 16" height="1em" width="1em"
                    xmlns="http://www.w3.org/2000/svg">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29
                    6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37
                    -2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01
                    -.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28
                    -.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15
                    -.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27
                    2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16
                    1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95
                    .29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8
                    .013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path>
                </svg>
            """,
            "class": "",
        },
    ],
}

# copybutton: strip prompts from shell / Python REPL examples
copybutton_prompt_text = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp = True

# ---------------------------------------------------------------------------
# myst-nb settings
# ---------------------------------------------------------------------------

# Use stored outputs from the committed notebook — never re-execute during build.
# This means CI does not need CellProfiler or any kernel installed.
nb_execution_mode = "off"
