# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.3] - 2023-07-18

### Fixed
- `package.binfile` not actually being used when making the symlink.

## [0.3.2] - 2023-02-02

### Fixed
- `changes all` now displays changes for all packages since version `0.0.0`

## [0.3.1] - 2023-02-01

### Fixed
- Remove tabs on newlines in help output - adapt to CLIParse 0.0.1 fixes

## [0.3.0] - 2023-02-01

### Added
- `release bump`: move changes from `Unreleased` to a new version in `CHANGELOG.MD`
- `release change`: edit `CHANGELOG.MD`
- for `release` commands: make `CHANGELOG.MD` if it doesn't exist.
- `changes <package> [version]`: List changes made since `version` in `package`
- `changes [version]`
- `changes [package]`

## [0.2.1] - 2023-02-01

### Fixed
- `apm pack` uses `package` as the template instead of `apm`

## [0.2.0] - 2023-01-31

### Added
- Semantic version parsing with `semver`
- Changelog parsing with `keepachangelog`
- `-m`, `--machine` flag: disable user features like changelogs.
- Changelogs are displayed in less when a package is updated
