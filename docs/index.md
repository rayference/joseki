# Welcome to `joseki` documentation

## Table of contents

The documentation follows the best practice for
project documentation as described by Daniele Procida
in the [Diátaxis documentation framework](https://diataxis.fr/)
and consists of four separate parts:

1. [Tutorials](tutorials.md)
2. [How-To Guides](how-to-guides.md)
3. [Reference](reference.md)
4. [Explanation](explanation.md)

Quickly find what you're looking for depending on
your use case by looking at the different pages.

## Project layout

??? abstract "Project layout"
    
    ```
        docs/
            changelog.md                # Changelog
            explanation.md              # Understanding-oriented documentation
            how-to-guides.md            # Task-oriented documentation
            index.md                    # The documentation homepage.
            reference.md                # Information-oriented
            tutorials.md                # Learning-oriented documentation
        mkdocs.yml                      # The configuration file.
        pdm.lock                        # PDM lock file
        pyproject.toml                  # Build system requirements
        README.md                       # README file
        src/
            joseki/                     # Source code
        tests/
            profiles/
                test_afgl_1986.py       # AFGL (1986) profiles tests
                test_core.py            # Profile core module tests
                test_factory.py         # Profile factory tests
                test_mipas_2007.py      # MIPAS (2007) profiles tests
            test_accessor.py            # Accessor module tests
            test_core.py                # Core module tests
            test_main.py                # CLI test module
            test_units.py               # Units module tests
    ```
