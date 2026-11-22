"""Contract tests for the tracker sql_exporter collectors."""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
COLLECTORS = ROOT / "collectors"
EXPECTED = {
    "vikunja": {
        "vikunja_open_tasks": ["project"],
        "vikunja_open_tasks_by_label": ["label"],
        "vikunja_open_tasks_by_epic": ["epic_id", "epic"],
        "vikunja_open_tasks_by_priority": ["priority"],
        "vikunja_open_tasks_by_age": ["age"],
        "vikunja_tasks_created_24h": [],
        "vikunja_tasks_done_24h": [],
    },
    "zammad": {
        "zammad_open_tickets": ["group"],
        "zammad_open_tickets_by_state": ["state"],
        "zammad_open_tickets_by_priority": ["priority"],
        "zammad_open_tickets_by_age": ["age"],
        "zammad_tickets_created_24h": [],
        "zammad_tickets_closed_24h": [],
    },
}
AGE_BUCKETS = {"lt_1d", "1d_7d", "7d_30d", "30d_90d", "gt_90d"}


def _collector(app):
    return yaml.safe_load((COLLECTORS / f"{app}.collector.yml").read_text(encoding="utf-8"))


def _tables(query):
    return set(re.findall(r"\b(?:FROM|JOIN)\s+([a-z_]+)", query, flags=re.IGNORECASE))


def test_each_collector_exports_the_expected_gauges_and_labels():
    for app, metrics in EXPECTED.items():
        collector = _collector(app)
        assert collector["collector_name"] == app
        found = {m["metric_name"]: m for m in collector["metrics"]}
        assert set(found) == set(metrics)
        for name, labels in metrics.items():
            metric = found[name]
            assert metric["type"] == "gauge"
            assert metric.get("key_labels", []) == labels
            assert metric["values"] == ["value"]
            for column in labels + ["value"]:
                assert re.search(rf'\bAS "?{column}"?', metric["query"]), (name, column)


# The tables each collector reads. The database login that runs it needs SELECT on exactly these.
TABLES = {
    "vikunja": {"tasks", "projects", "labels", "label_tasks", "task_relations"},
    "zammad": {"tickets", "groups", "ticket_states", "ticket_state_types", "ticket_priorities"},
}


def test_each_collector_reads_only_its_declared_tables():
    for app in EXPECTED:
        read = set().union(*(_tables(m["query"]) for m in _collector(app)["metrics"]))
        assert read == TABLES[app], app


def test_age_queries_emit_only_the_declared_buckets():
    for app in EXPECTED:
        (metric,) = [m for m in _collector(app)["metrics"] if m["metric_name"].endswith("_by_age")]
        assert set(re.findall(r"THEN '([a-z0-9_]+)'|ELSE '([a-z0-9_]+)'", metric["query"])) and {
            a or b for a, b in re.findall(r"THEN '([a-z0-9_]+)'|ELSE '([a-z0-9_]+)'", metric["query"])
        } == AGE_BUCKETS


def test_open_filters_exclude_closed_work():
    for metric in _collector("vikunja")["metrics"]:
        if "open" in metric["metric_name"]:
            assert "NOT t.done" in metric["query"]
    for metric in _collector("zammad")["metrics"]:
        if "open" in metric["metric_name"]:
            assert "NOT IN ('closed', 'merged', 'removed')" in metric["query"]
