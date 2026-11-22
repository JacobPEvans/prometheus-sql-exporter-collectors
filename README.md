# prometheus-sql-exporter-collectors

Collector definitions for [sql_exporter](https://github.com/burningalchemist/sql_exporter), the exporter
that turns SQL query results into Prometheus metrics, for the homelab estate.

## Installation

Point an sql_exporter deployment's `collector_files` at the files under `collectors/`. Which deployment
loads this repository is tracked separately: this repo holds only collector definitions, not deployment
wiring or database grants.

## Usage

Each file under `collectors/` is one standard sql_exporter collector (`collector_name`, `metrics`). Add a
file per monitored application. Every query reads only; the database login that runs it needs `SELECT` on
the tables the file names.

## License

Apache License 2.0 — see [LICENSE](./LICENSE).
