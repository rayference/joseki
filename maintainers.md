# Guide to maintainers

## Development setup

This project is managed using [Rye](https://rye-up.com). Development setup
requires installing it. Once this is done, simply navigate to the root of the
source repository and run:
```
rye sync
```

## Run the tests and verify test coverage

* Run tests with `rye run pytest tests`
* To verify test coverage, run:
  ```shell
  rye run coverage-report
  ```
  and inspect the coverage report

## Make a PyPI/conda release

### Before the release

* Run the tests with `rye run pytest tests`
* Build and inspect the docs with `mkdocs serve`

### Make the release

* Bump the version number to the target value using the
  `rye version <major>.<minor>.<patch>` command
* Update `docs/changelog.md`: change the heading
  `"[Unreleased]"` to `"[major.minor.patch]  - YYYY-MM-DD"`
* Commit the changes on branch `main` with the message:
  `joseki version <major>.<minor>.<patch>`
* Tag the commit with `"v<major>.<minor>.<patch>"`, *e.g.*:
  `git tag -a v2.3.0 -m "v2.3.0"` followed by `git push --tags`. This will
  trigger the `PyPI Release` workflow. It will also produce a pull request on
  the [conda forge joseki feedstock](https://github.com/conda-forge/joseki-feedstock) within a delay (~1 hour)
* Review the pull request. When the pull request is merged,
  `joseki` will be available on `conda` as well, within another delay
  (~ 15 minutes).

### After the release

* Deploy the documentation:
  `mike deploy --push --update-aliases major.minor.patch latest`
* Describe the release on GitHub
* Update `CITATION.cff` file. The following fields should be updated
  * `url`
  * `commit`
  * `version`
  * `date-released`
