# Release

Commands for editing changelogs.

For all `release` commands:
    if `CHANGELOG.MD` does not exist, make it with the content of
```md
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
```

## `release bump <part>`

get latest version from `CHANGELOG.MD` and bump the version, moving changes from `Unreleased` to the new version.


## `release change`

open up `CHANGELOG.MD` w/ `$VISUAL_EDITOR`.

# `changes`

## `changes [version]`

if `version` parses as a version and `changelog.md` exists:
    open up the changelog for the current directory.

## `changes [package]`

if `changelog.md` doesn't exist or `package` cannot be a version:
    open up the changes since version `0.0.0` of `package`

## `changes <package> [version]`

open up the changes for `package` since `version`.
