# Changelog

## Unreleased
- Make it work
- Added documentation
- Added FastAPI endpoint
- Added software tests and CI configuration
- Used CrateDB as job store
- Added software tests for JobStore
- Refactored modules, and separate concerns
- Improved UX and configurability
- Established command-line entrypoints `supertask` and `st`
- Settings: Obtain HTTP listen address and path/URL to seed file
  from user space
- Got rid of global `CRONJOBS_JSON` variable
- Improved software tests and documentation
- Settings: Obtain environment variables from `.env` file
- Settings: Obtain job store schema- and table names alongside database address
- Packaging / Refactoring
- Dropped support for Python 3.8
- Refactored scheduling and rescheduling, improved data model
- Documentation: Added Sphinx and Read the Docs, publishing to
  https://supertask.readthedocs.io/
