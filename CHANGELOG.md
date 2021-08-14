# Change log
This log follows the conventions of
[keepachangelog.com](http://keepachangelog.com/). It picks up from version 2.0.0.

## [Unreleased]
Nothing yet.

### Changed
- Implemented `dump`, previously a placeholder. It’s still basically
  `pyaml.dump` but now disables `sort_dicts` so that `map_fn` etc. can
  be meaningful with modern Python, without using `OrderedDict`.

### Added
- New keyword arguments to transform: `loader` and `dumper`.
  Behaviour can now be customized for e.g. multi-document files.

[Unreleased]: https://github.com/veikman/yamlwrap/compare/v2.0.0...HEAD
