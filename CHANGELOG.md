# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]
### Added
- time4mind_test.py
- pkboxsoap.py errorlevel and handler now are in config
- webserver listen ipaddress now is in config
### Changed
### Fixed
- skip certificates with certificateStatus != ATTIVO
- removed customerinfo from signature params to fix errors
- improved logging 
- other minor fixes in README.md and RHEL.md
- create storage dir if not present
### Removed
### Security
### Deprecated


## [0.8.1] - 2017-03-13
### Added
- LGPL 3.0 license
### Fixed
- sign_test.py utility aligned with updated pkboxsoap.py
- module python-magic was not declared in README.md


## [0.8.0] - 2017-03-09
### First release
- telegram library
- time4mind simple library
- flask as RESTfull server to process time4mind callback
- pkbox SOAP library to sign using PkBox server


## [Unreleased]
### Added
### Changed
### Fixed
### Removed
### Security
### Deprecated


