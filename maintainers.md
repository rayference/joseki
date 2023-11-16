# Guide to maintainers

## Update the tutorials

### Make the modifications

* modify the file `docs/tutorials.ipynb` (not `docs/tutorials.md`)

### After the modifications

* run the notebook and check that it executes successfully
* strip the output: `nbstripout docs/tutorials`
* convert to markdown: `jupyter nbconvert --to markdown docs/tutorials.ipynb`

## Run the tests and verify test coverage

* run the test with `pytest tests`
* to verify the test coverage, run:
  ```shell
  coverage run -m pytest -v tests
  python -m coverage combine   
  python -m coverage html --skip-covered --skip-empty
  python -m coverage report --fail-under=100
  ```
  and inspect the coverage report.

## Make a PyPI/conda release

### Before the release

* run the tests with `pytest tests`
* build and inspect the docs with `mkdocs serve`

### Make the release

* Update `src/joseki/__version__.py`: change the `__version__` variable to the new version value
* Update `docs/changelog.md`: change the heading `"[Unreleased]"` to `"[major.minor.patch]  - YYYY-MM-DD"`
* Commit the changes on branch `main` with the message: `joseki version <major>.<minor>.<patch>`
* Tag the commit with `"v<major>.<minor>"`, e.g.: `git tag -a v2.3.0 -m "v2.3.0"` followed by `git push --tags`. This will trigger the `PyPI Release` workflow. It will also produce a pull request on the 
  [conda forge joseki feedstock](https://github.com/conda-forge/joseki-feedstock)
  within a delay (~1 hour).
* Review the pull request. When the pull request is merged, 
  `joseki` will be available on `conda` as well, within another delay (~ 15 minutes).

### After the release

* Deploy the documentation: `mike deploy --push --update-aliases major.minor latest`
* Describe the release on GitHub
* Update `CITATION.cff` file. The following field should be updated
  * `url`
  * `commit`
  * `version`
  * `date-released`
