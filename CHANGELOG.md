# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed

- Corrected invalid GitHub Actions workflow definitions so CI and publish
  workflows parse before execution.
- Added workflow linting and removed unused OIDC publish permission from
  the publish workflow.

### Added

- Community health files, issue/PR templates, release workflow, and
  examples to make the repository more complete for contributors and users.

## [0.1.0] - 2026-03-24

### Added (0.1.0)

- Standalone embedding-based topic modeling package for reusable vector
  workflows.
- Dependency-light clustering, session-aware representative selection,
  provider-driven orchestration, and CLI entrypoint.
- Initial CI workflow, package build validation, smoke install checks,
  and canonical engineering docs.

[Unreleased]: https://github.com/seonghobae/vector-topic-modeling/compare/0.1.0...HEAD
[0.1.0]: https://github.com/seonghobae/vector-topic-modeling/releases/tag/0.1.0
