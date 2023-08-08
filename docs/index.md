# Welcome to `joseki` documentation

## Table of contents

The documentation consists of four separate parts:

* [How-To Guides](how-to-guides.md)
* [Explanation](explanation.md)
* [Tutorials](tutorials.md)
* [Reference](reference.md)

## Project layout

??? abstract "Project layout"
    
    ```
        docs/
            bibliography.bib            # BibTeX file
            bibliography.md             # Bibliography 
            changelog.md                # Changelog
            explanation.md              # Understanding-oriented documentation
            how-to-guides.md            # Task-oriented documentation
            index.md                    # The documentation homepage.
            reference.md                # Information-oriented
            tutorials.md                # Learning-oriented documentation
        CITATION.cff                    # Citation file
        codecov.yml                     # Code coverage configuration file
        LICENSE                         # License file
        maintainers.md                  # Maintainers guide
        mkdocs.yml                      # The configuration file.
        pdm.lock                        # PDM lock file
        noxfile.py                      # Nox sessions
        pyproject.toml                  # Build system requirements
        README.md                       # README file
        src/
            joseki/                     # Source code
        tests/
            data/                       # Test data
            profiles/
                test_afgl_1986.py       # AFGL (1986) profiles tests
                test_core.py            # Profile core module tests
                test_factory.py         # Profile factory tests
                test_mipas_2007.py      # MIPAS (2007) profiles tests
                test_ussa_1976.py       # U.S.S.A. 1976 profile tests
                test_util.py            # Profile utilities tests
            test_accessor.py            # Accessor module tests
            test_core.py                # Core module tests
            test_main.py                # CLI test module
            test_units.py               # Units module tests
    ```
