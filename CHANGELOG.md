# Change log
This log follows the conventions of
[keepachangelog.com](http://keepachangelog.com/). It picks up from version 2.0.0.

## [Unreleased]
Nothing yet.

### Changed
- Implemented `dump`, previously a placeholder. It’s still basically
  `pyaml.dump` but now disables `sort_dicts` so that `map_fn` etc. can more
  easily be meaningful with modern Python that doesn’t use `OrderedDict`.

### Added
- New keyword arguments to transform: `loader` and `dumper`.
  This was done so that behaviour can be customized for multi-document files.

[Unreleased]: https://github.com/veikman/yamlwrap/compare/v2.0.0...HEAD
