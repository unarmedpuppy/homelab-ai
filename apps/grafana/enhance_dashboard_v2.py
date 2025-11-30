#!/usr/bin/env python3
"""
Enhanced script to add new panels to Grafana dashboard.
Uses old "graph" panel format to match existing dashboard style.
"""

import json
import random

def get_next_panel_id(dashboard):
    """Get next available panel ID"""
    max_id = 0
    for panel in dashboard['panels']:
        if 'id' in panel and isinstance(panel['id'], int):
            max_id = max(max_id, panel['id'])
    return max_id + 1

def get_last_y_position(dashboard):
    """Get the last y position in the dashboard"""
    last_y = 0
    for panel in dashboard['panels']:
        if 'gridPos' in panel and 'y' in panel['gridPos']:
            last_y = max(last_y, panel['gridPos']['y'] + panel['gridPos'].get('h', 1))
    return last_y

def create_temperature_row(panel_id, y_pos):
    """Create Temperature & Health row section"""
    return {
        "collapsed": False,
        "datasource": {"type": "influxdb", "uid": "8zXyAXzRz"},
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": y_pos},
        "id": panel_id,
        "panels": [],
        "title": "Temperature & Health",
        "type": "row"
    }

def create_cpu_temp_gauge(panel_id, y_pos):
    """CPU Temperature Gauge Panel"""
    return {
        "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "thresholds"},
                "mappings": [],
                "max": 100,
                "min": 0,
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": None},
                        {"color": "yellow", "value": 60},
                        {"color": "orange", "value": 70},
                        {"color": "red", "value": 80}
                    ]
                },
                "unit": "celsius"
            },
            "overrides": []
        },
        "gridPos": {"h": 6, "w": 4, "x": 0, "y": y_pos},
        "id": panel_id,
        "options": {
            "orientation": "horizontal",
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "showThresholdLabels": False,
            "showThresholdMarkers": True,
            "text": {}
        },
        "pluginVersion": "9.2.3",
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["null"], "type": "fill"}],
            "measurement": "sensors",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"temp_input\") FROM \"sensors\" WHERE (\"chip\" = 'k10temp-pci-00c3') AND $timeFilter GROUP BY time($interval) fill(null)",
            "rawQuery": False,
            "refId": "A",
            "resultFormat": "time_series",
            "select": [[{"params": ["temp_input"], "type": "field"}, {"params": [], "type": "mean"}]],
            "tags": [{"key": "chip", "operator": "=", "value": "k10temp-pci-00c3"}]
        }],
        "title": "CPU Temperature",
        "type": "gauge"
    }

def create_temp_trend_graph(panel_id, y_pos):
    """Temperature Trend Graph Panel (old graph format)"""
    return {
        "aliasColors": {},
        "bars": False,
        "dashLength": 10,
        "dashes": False,
        "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
        "fieldConfig": {
            "defaults": {},
            "overrides": []
        },
        "fill": 1,
        "fillGradient": 0,
        "gridPos": {"h": 6, "w": 20, "x": 4, "y": y_pos},
        "hiddenSeries": False,
        "id": panel_id,
        "legend": {
            "avg": False,
            "current": False,
            "max": False,
            "min": False,
            "show": True,
            "total": False,
            "values": False
        },
        "lines": True,
        "linewidth": 1,
        "nullPointMode": "null",
        "options": {
            "alertThreshold": True
        },
        "pluginVersion": "9.2.3",
        "pointradius": 2,
        "points": False,
        "renderer": "flot",
        "seriesOverrides": [],
        "spaceLength": 10,
        "stack": False,
        "steppedLine": False,
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["chip"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "sensors",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"temp_input\") FROM \"sensors\" WHERE $timeFilter GROUP BY time($interval), \"chip\" fill(null)",
            "rawQuery": False,
            "refId": "A",
            "resultFormat": "time_series",
            "select": [[{"params": ["temp_input"], "type": "field"}, {"params": [], "type": "mean"}]],
            "tags": []
        }],
        "thresholds": [],
        "timeRegions": [],
        "title": "Temperature Trends by Sensor",
        "tooltip": {
            "shared": True,
            "sort": 0,
            "value_type": "individual"
        },
        "type": "graph",
        "xaxis": {
            "mode": "time",
            "show": True,
            "values": []
        },
        "yaxes": [
            {
                "format": "celsius",
                "label": "Temperature",
                "logBase": 1,
                "show": True
            },
            {
                "format": "short",
                "logBase": 1,
                "show": True
            }
        ],
        "yaxis": {
            "align": False
        }
    }

def create_disk_io_row(panel_id, y_pos):
    """Create Storage I/O row section"""
    return {
        "collapsed": False,
        "datasource": {"type": "influxdb", "uid": "8zXyAXzRz"},
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": y_pos},
        "id": panel_id,
        "panels": [],
        "title": "Storage I/O Performance",
        "type": "row"
    }

def create_disk_io_rates_graph(panel_id, y_pos):
    """Disk I/O Read/Write Rates Graph Panel"""
    return {
        "aliasColors": {},
        "bars": False,
        "dashLength": 10,
        "dashes": False,
        "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
        "fieldConfig": {
            "defaults": {},
            "overrides": []
        },
        "fill": 1,
        "fillGradient": 0,
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": y_pos},
        "hiddenSeries": False,
        "id": panel_id,
        "legend": {
            "avg": False,
            "current": False,
            "max": False,
            "min": False,
            "show": True,
            "total": False,
            "values": False
        },
        "lines": True,
        "linewidth": 1,
        "nullPointMode": "null",
        "options": {
            "alertThreshold": True
        },
        "pluginVersion": "9.2.3",
        "pointradius": 2,
        "points": False,
        "renderer": "flot",
        "seriesOverrides": [],
        "spaceLength": 10,
        "stack": False,
        "steppedLine": False,
        "targets": [{
            "alias": "Read MB/s - $tag_name",
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["name"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "diskio",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"read_bytes\") / 1024 / 1024 FROM \"diskio\" WHERE (\"name\" =~ /$disk/) AND $timeFilter GROUP BY time($interval), \"name\" fill(null)",
            "rawQuery": False,
            "refId": "A",
            "resultFormat": "time_series",
            "select": [[{"params": ["read_bytes"], "type": "field"}, {"params": [], "type": "mean"}, {"params": ["/ 1024 / 1024"], "type": "math"}]],
            "tags": [{"key": "name", "operator": "=~", "value": "/$disk/"}]
        }, {
            "alias": "Write MB/s - $tag_name",
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["name"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "diskio",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"write_bytes\") / 1024 / 1024 FROM \"diskio\" WHERE (\"name\" =~ /$disk/) AND $timeFilter GROUP BY time($interval), \"name\" fill(null)",
            "rawQuery": False,
            "refId": "B",
            "resultFormat": "time_series",
            "select": [[{"params": ["write_bytes"], "type": "field"}, {"params": [], "type": "mean"}, {"params": ["/ 1024 / 1024"], "type": "math"}]],
            "tags": [{"key": "name", "operator": "=~", "value": "/$disk/"}]
        }],
        "thresholds": [],
        "timeRegions": [],
        "title": "Disk I/O Read/Write Rates (MB/s)",
        "tooltip": {
            "shared": True,
            "sort": 0,
            "value_type": "individual"
        },
        "type": "graph",
        "xaxis": {
            "mode": "time",
            "show": True,
            "values": []
        },
        "yaxes": [
            {
                "format": "MBs",
                "label": "MB/s",
                "logBase": 1,
                "show": True
            },
            {
                "format": "short",
                "logBase": 1,
                "show": True
            }
        ],
        "yaxis": {
            "align": False
        }
    }

def create_disk_iops_graph(panel_id, y_pos):
    """Disk IOPS Graph Panel"""
    return {
        "aliasColors": {},
        "bars": False,
        "dashLength": 10,
        "dashes": False,
        "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
        "fieldConfig": {
            "defaults": {},
            "overrides": []
        },
        "fill": 1,
        "fillGradient": 0,
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": y_pos},
        "hiddenSeries": False,
        "id": panel_id,
        "legend": {
            "avg": False,
            "current": False,
            "max": False,
            "min": False,
            "show": True,
            "total": False,
            "values": False
        },
        "lines": True,
        "linewidth": 1,
        "nullPointMode": "null",
        "options": {
            "alertThreshold": True
        },
        "pluginVersion": "9.2.3",
        "pointradius": 2,
        "points": False,
        "renderer": "flot",
        "seriesOverrides": [],
        "spaceLength": 10,
        "stack": False,
        "steppedLine": False,
        "targets": [{
            "alias": "IOPS - $tag_name",
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["name"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "diskio",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"reads\") + mean(\"writes\") FROM \"diskio\" WHERE (\"name\" =~ /$disk/) AND $timeFilter GROUP BY time($interval), \"name\" fill(null)",
            "rawQuery": False,
            "refId": "A",
            "resultFormat": "time_series",
            "select": [[{"params": ["reads"], "type": "field"}, {"params": [], "type": "mean"}], [{"params": ["writes"], "type": "field"}, {"params": [], "type": "mean"}]],
            "tags": [{"key": "name", "operator": "=~", "value": "/$disk/"}]
        }],
        "thresholds": [],
        "timeRegions": [],
        "title": "Disk IOPS (Reads + Writes)",
        "tooltip": {
            "shared": True,
            "sort": 0,
            "value_type": "individual"
        },
        "type": "graph",
        "xaxis": {
            "mode": "time",
            "show": True,
            "values": []
        },
        "yaxes": [
            {
                "format": "iops",
                "label": "IOPS",
                "logBase": 1,
                "show": True
            },
            {
                "format": "short",
                "logBase": 1,
                "show": True
            }
        ],
        "yaxis": {
            "align": False
        }
    }

def create_network_interfaces_row(panel_id, y_pos):
    """Create Network Interfaces row section"""
    return {
        "collapsed": False,
        "datasource": {"type": "influxdb", "uid": "8zXyAXzRz"},
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": y_pos},
        "id": panel_id,
        "panels": [],
        "title": "Network Interfaces",
        "type": "row"
    }

def create_network_traffic_graph(panel_id, y_pos):
    """Network Traffic per Interface Graph Panel"""
    return {
        "aliasColors": {},
        "bars": False,
        "dashLength": 10,
        "dashes": False,
        "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
        "fieldConfig": {
            "defaults": {},
            "overrides": []
        },
        "fill": 1,
        "fillGradient": 0,
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": y_pos},
        "hiddenSeries": False,
        "id": panel_id,
        "legend": {
            "avg": False,
            "current": False,
            "max": False,
            "min": False,
            "show": True,
            "total": False,
            "values": False
        },
        "lines": True,
        "linewidth": 1,
        "nullPointMode": "null",
        "options": {
            "alertThreshold": True
        },
        "pluginVersion": "9.2.3",
        "pointradius": 2,
        "points": False,
        "renderer": "flot",
        "seriesOverrides": [],
        "spaceLength": 10,
        "stack": False,
        "steppedLine": False,
        "targets": [{
            "alias": "Upload - $tag_interface",
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["interface"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "net",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"bytes_sent\") * 8 / 1000000 FROM \"net\" WHERE (\"interface\" =~ /$netif/ OR \"interface\" = 'docker0' OR \"interface\" = 'tun0') AND $timeFilter GROUP BY time($interval), \"interface\" fill(null)",
            "rawQuery": False,
            "refId": "A",
            "resultFormat": "time_series",
            "select": [[{"params": ["bytes_sent"], "type": "field"}, {"params": [], "type": "mean"}, {"params": ["* 8 / 1000000"], "type": "math"}]],
            "tags": [{"key": "interface", "operator": "=~", "value": "/$netif/"}]
        }, {
            "alias": "Download - $tag_interface",
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["interface"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "net",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"bytes_recv\") * 8 / 1000000 FROM \"net\" WHERE (\"interface\" =~ /$netif/ OR \"interface\" = 'docker0' OR \"interface\" = 'tun0') AND $timeFilter GROUP BY time($interval), \"interface\" fill(null)",
            "rawQuery": False,
            "refId": "B",
            "resultFormat": "time_series",
            "select": [[{"params": ["bytes_recv"], "type": "field"}, {"params": [], "type": "mean"}, {"params": ["* 8 / 1000000"], "type": "math"}]],
            "tags": [{"key": "interface", "operator": "=~", "value": "/$netif/"}]
        }],
        "thresholds": [],
        "timeRegions": [],
        "title": "Network Traffic per Interface (Mbps)",
        "tooltip": {
            "shared": True,
            "sort": 0,
            "value_type": "individual"
        },
        "type": "graph",
        "xaxis": {
            "mode": "time",
            "show": True,
            "values": []
        },
        "yaxes": [
            {
                "format": "Mbps",
                "label": "Mbps",
                "logBase": 1,
                "show": True
            },
            {
                "format": "short",
                "logBase": 1,
                "show": True
            }
        ],
        "yaxis": {
            "align": False
        }
    }

def create_network_errors_graph(panel_id, y_pos):
    """Network Error Rates Graph Panel"""
    return {
        "aliasColors": {},
        "bars": False,
        "dashLength": 10,
        "dashes": False,
        "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
        "fieldConfig": {
            "defaults": {},
            "overrides": []
        },
        "fill": 1,
        "fillGradient": 0,
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": y_pos},
        "hiddenSeries": False,
        "id": panel_id,
        "legend": {
            "avg": False,
            "current": False,
            "max": False,
            "min": False,
            "show": True,
            "total": False,
            "values": False
        },
        "lines": True,
        "linewidth": 1,
        "nullPointMode": "null",
        "options": {
            "alertThreshold": True
        },
        "pluginVersion": "9.2.3",
        "pointradius": 2,
        "points": False,
        "renderer": "flot",
        "seriesOverrides": [],
        "spaceLength": 10,
        "stack": False,
        "steppedLine": False,
        "targets": [{
            "alias": "Errors In - $tag_interface",
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["interface"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "net",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"err_in\") FROM \"net\" WHERE (\"interface\" =~ /$netif/) AND $timeFilter GROUP BY time($interval), \"interface\" fill(null)",
            "rawQuery": False,
            "refId": "A",
            "resultFormat": "time_series",
            "select": [[{"params": ["err_in"], "type": "field"}, {"params": [], "type": "mean"}]],
            "tags": [{"key": "interface", "operator": "=~", "value": "/$netif/"}]
        }, {
            "alias": "Errors Out - $tag_interface",
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["interface"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "net",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"err_out\") FROM \"net\" WHERE (\"interface\" =~ /$netif/) AND $timeFilter GROUP BY time($interval), \"interface\" fill(null)",
            "rawQuery": False,
            "refId": "B",
            "resultFormat": "time_series",
            "select": [[{"params": ["err_out"], "type": "field"}, {"params": [], "type": "mean"}]],
            "tags": [{"key": "interface", "operator": "=~", "value": "/$netif/"}]
        }, {
            "alias": "Drops In - $tag_interface",
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["interface"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "net",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"drop_in\") FROM \"net\" WHERE (\"interface\" =~ /$netif/) AND $timeFilter GROUP BY time($interval), \"interface\" fill(null)",
            "rawQuery": False,
            "refId": "C",
            "resultFormat": "time_series",
            "select": [[{"params": ["drop_in"], "type": "field"}, {"params": [], "type": "mean"}]],
            "tags": [{"key": "interface", "operator": "=~", "value": "/$netif/"}]
        }, {
            "alias": "Drops Out - $tag_interface",
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["interface"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "net",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"drop_out\") FROM \"net\" WHERE (\"interface\" =~ /$netif/) AND $timeFilter GROUP BY time($interval), \"interface\" fill(null)",
            "rawQuery": False,
            "refId": "D",
            "resultFormat": "time_series",
            "select": [[{"params": ["drop_out"], "type": "field"}, {"params": [], "type": "mean"}]],
            "tags": [{"key": "interface", "operator": "=~", "value": "/$netif/"}]
        }],
        "thresholds": [],
        "timeRegions": [],
        "title": "Network Error & Drop Rates",
        "tooltip": {
            "shared": True,
            "sort": 0,
            "value_type": "individual"
        },
        "type": "graph",
        "xaxis": {
            "mode": "time",
            "show": True,
            "values": []
        },
        "yaxes": [
            {
                "format": "short",
                "label": "Errors/Drops",
                "logBase": 1,
                "show": True
            },
            {
                "format": "short",
                "logBase": 1,
                "show": True
            }
        ],
        "yaxis": {
            "align": False
        }
    }

def create_disk_mounts_row(panel_id, y_pos):
    """Create Disk Usage by Mount row section"""
    return {
        "collapsed": False,
        "datasource": {"type": "influxdb", "uid": "8zXyAXzRz"},
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": y_pos},
        "id": panel_id,
        "panels": [],
        "title": "Disk Usage by Mount Point",
        "type": "row"
    }

def create_disk_usage_mounts_graph(panel_id, y_pos):
    """Disk Usage per Mount Point Graph Panel"""
    return {
        "aliasColors": {},
        "bars": False,
        "dashLength": 10,
        "dashes": False,
        "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
        "fieldConfig": {
            "defaults": {},
            "overrides": []
        },
        "fill": 1,
        "fillGradient": 0,
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": y_pos},
        "hiddenSeries": False,
        "id": panel_id,
        "legend": {
            "avg": False,
            "current": False,
            "max": False,
            "min": False,
            "show": True,
            "total": False,
            "values": False
        },
        "lines": True,
        "linewidth": 1,
        "nullPointMode": "null",
        "options": {
            "alertThreshold": True
        },
        "pluginVersion": "9.2.3",
        "pointradius": 2,
        "points": False,
        "renderer": "flot",
        "seriesOverrides": [{
            "alias": "/.*/",
            "thresholds": [{"colorMode": "critical", "fill": True, "line": True, "op": "gt", "value": 90}, {"colorMode": "warning", "fill": True, "line": True, "op": "gt", "value": 80}]
        }],
        "spaceLength": 10,
        "stack": False,
        "steppedLine": False,
        "targets": [{
            "alias": "$tag_path",
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["path"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "disk",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"used_percent\") FROM \"disk\" WHERE (\"path\" =~ /$mountpoint/) AND $timeFilter GROUP BY time($interval), \"path\" fill(null)",
            "rawQuery": False,
            "refId": "A",
            "resultFormat": "time_series",
            "select": [[{"params": ["used_percent"], "type": "field"}, {"params": [], "type": "mean"}]],
            "tags": [{"key": "path", "operator": "=~", "value": "/$mountpoint/"}]
        }],
        "thresholds": [
            {"colorMode": "critical", "fill": True, "line": True, "op": "gt", "value": 90},
            {"colorMode": "warning", "fill": True, "line": True, "op": "gt", "value": 80}
        ],
        "timeRegions": [],
        "title": "Disk Usage % by Mount Point",
        "tooltip": {
            "shared": True,
            "sort": 0,
            "value_type": "individual"
        },
        "type": "graph",
        "xaxis": {
            "mode": "time",
            "show": True,
            "values": []
        },
        "yaxes": [
            {
                "format": "percent",
                "label": "Usage %",
                "logBase": 1,
                "max": 100,
                "min": 0,
                "show": True
            },
            {
                "format": "short",
                "logBase": 1,
                "show": True
            }
        ],
        "yaxis": {
            "align": False
        }
    }

def create_disk_space_mounts_graph(panel_id, y_pos):
    """Disk Space Used/Free per Mount Graph Panel"""
    return {
        "aliasColors": {},
        "bars": False,
        "dashLength": 10,
        "dashes": False,
        "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
        "fieldConfig": {
            "defaults": {},
            "overrides": []
        },
        "fill": 1,
        "fillGradient": 0,
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": y_pos},
        "hiddenSeries": False,
        "id": panel_id,
        "legend": {
            "avg": False,
            "current": False,
            "max": False,
            "min": False,
            "show": True,
            "total": False,
            "values": False
        },
        "lines": True,
        "linewidth": 1,
        "nullPointMode": "null",
        "options": {
            "alertThreshold": True
        },
        "pluginVersion": "9.2.3",
        "pointradius": 2,
        "points": False,
        "renderer": "flot",
        "seriesOverrides": [],
        "spaceLength": 10,
        "stack": False,
        "steppedLine": False,
        "targets": [{
            "alias": "Used GB - $tag_path",
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["path"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "disk",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"used\") / 1024 / 1024 / 1024 FROM \"disk\" WHERE (\"path\" =~ /$mountpoint/) AND $timeFilter GROUP BY time($interval), \"path\" fill(null)",
            "rawQuery": False,
            "refId": "A",
            "resultFormat": "time_series",
            "select": [[{"params": ["used"], "type": "field"}, {"params": [], "type": "mean"}, {"params": ["/ 1024 / 1024 / 1024"], "type": "math"}]],
            "tags": [{"key": "path", "operator": "=~", "value": "/$mountpoint/"}]
        }, {
            "alias": "Free GB - $tag_path",
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["path"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "disk",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"free\") / 1024 / 1024 / 1024 FROM \"disk\" WHERE (\"path\" =~ /$mountpoint/) AND $timeFilter GROUP BY time($interval), \"path\" fill(null)",
            "rawQuery": False,
            "refId": "B",
            "resultFormat": "time_series",
            "select": [[{"params": ["free"], "type": "field"}, {"params": [], "type": "mean"}, {"params": ["/ 1024 / 1024 / 1024"], "type": "math"}]],
            "tags": [{"key": "path", "operator": "=~", "value": "/$mountpoint/"}]
        }],
        "thresholds": [],
        "timeRegions": [],
        "title": "Disk Space Used/Free by Mount (GB)",
        "tooltip": {
            "shared": True,
            "sort": 0,
            "value_type": "individual"
        },
        "type": "graph",
        "xaxis": {
            "mode": "time",
            "show": True,
            "values": []
        },
        "yaxes": [
            {
                "format": "decgbytes",
                "label": "GB",
                "logBase": 1,
                "show": True
            },
            {
                "format": "short",
                "logBase": 1,
                "show": True
            }
        ],
        "yaxis": {
            "align": False
        }
    }

def create_memory_pressure_row(panel_id, y_pos):
    """Create Memory Health row section"""
    return {
        "collapsed": False,
        "datasource": {"type": "influxdb", "uid": "8zXyAXzRz"},
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": y_pos},
        "id": panel_id,
        "panels": [],
        "title": "Memory Health",
        "type": "row"
    }

def create_available_memory_graph(panel_id, y_pos):
    """Available Memory Trend Graph Panel"""
    return {
        "aliasColors": {},
        "bars": False,
        "dashLength": 10,
        "dashes": False,
        "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
        "fieldConfig": {
            "defaults": {},
            "overrides": []
        },
        "fill": 1,
        "fillGradient": 0,
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": y_pos},
        "hiddenSeries": False,
        "id": panel_id,
        "legend": {
            "avg": False,
            "current": False,
            "max": False,
            "min": False,
            "show": True,
            "total": False,
            "values": False
        },
        "lines": True,
        "linewidth": 1,
        "nullPointMode": "null",
        "options": {
            "alertThreshold": True
        },
        "pluginVersion": "9.2.3",
        "pointradius": 2,
        "points": False,
        "renderer": "flot",
        "seriesOverrides": [],
        "spaceLength": 10,
        "stack": False,
        "steppedLine": False,
        "targets": [{
            "alias": "Available Memory",
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["null"], "type": "fill"}],
            "measurement": "mem",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"available\") / 1024 / 1024 / 1024 FROM \"mem\" WHERE (\"host\" =~ /^$server$/) AND $timeFilter GROUP BY time($interval) fill(null)",
            "rawQuery": False,
            "refId": "A",
            "resultFormat": "time_series",
            "select": [[{"params": ["available"], "type": "field"}, {"params": [], "type": "mean"}, {"params": ["/ 1024 / 1024 / 1024"], "type": "math"}]],
            "tags": [{"key": "host", "operator": "=~", "value": "/^$server$/"}]
        }],
        "thresholds": [],
        "timeRegions": [],
        "title": "Available Memory Trend (GB)",
        "tooltip": {
            "shared": True,
            "sort": 0,
            "value_type": "individual"
        },
        "type": "graph",
        "xaxis": {
            "mode": "time",
            "show": True,
            "values": []
        },
        "yaxes": [
            {
                "format": "decgbytes",
                "label": "GB",
                "logBase": 1,
                "show": True
            },
            {
                "format": "short",
                "logBase": 1,
                "show": True
            }
        ],
        "yaxis": {
            "align": False
        }
    }

def create_memory_pressure_graph(panel_id, y_pos):
    """Memory Pressure Graph Panel"""
    return {
        "aliasColors": {},
        "bars": False,
        "dashLength": 10,
        "dashes": False,
        "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
        "fieldConfig": {
            "defaults": {},
            "overrides": []
        },
        "fill": 1,
        "fillGradient": 0,
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": y_pos},
        "hiddenSeries": False,
        "id": panel_id,
        "legend": {
            "avg": False,
            "current": False,
            "max": False,
            "min": False,
            "show": True,
            "total": False,
            "values": False
        },
        "lines": True,
        "linewidth": 1,
        "nullPointMode": "null",
        "options": {
            "alertThreshold": True
        },
        "pluginVersion": "9.2.3",
        "pointradius": 2,
        "points": False,
        "renderer": "flot",
        "seriesOverrides": [],
        "spaceLength": 10,
        "stack": False,
        "steppedLine": False,
        "targets": [{
            "alias": "Available %",
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["null"], "type": "fill"}],
            "measurement": "mem",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT (mean(\"available\") / mean(\"total\")) * 100 FROM \"mem\" WHERE (\"host\" =~ /^$server$/) AND $timeFilter GROUP BY time($interval) fill(null)",
            "rawQuery": False,
            "refId": "A",
            "resultFormat": "time_series",
            "select": [[{"params": ["available"], "type": "field"}, {"params": [], "type": "mean"}], [{"params": ["total"], "type": "field"}, {"params": [], "type": "mean"}]],
            "tags": [{"key": "host", "operator": "=~", "value": "/^$server$/"}]
        }],
        "thresholds": [
            {"colorMode": "critical", "fill": True, "line": True, "op": "lt", "value": 10},
            {"colorMode": "warning", "fill": True, "line": True, "op": "lt", "value": 20}
        ],
        "timeRegions": [],
        "title": "Memory Pressure (Available %)",
        "tooltip": {
            "shared": True,
            "sort": 0,
            "value_type": "individual"
        },
        "type": "graph",
        "xaxis": {
            "mode": "time",
            "show": True,
            "values": []
        },
        "yaxes": [
            {
                "format": "percent",
                "label": "Available %",
                "logBase": 1,
                "max": 100,
                "min": 0,
                "show": True
            },
            {
                "format": "short",
                "logBase": 1,
                "show": True
            }
        ],
        "yaxis": {
            "align": False
        }
    }

def main():
    # Read existing dashboard
    input_file = '/Users/joshuajenquist/repos/personal/home-server/apps/grafana/Grafana_Dashboard_Template.json'
    with open(input_file, 'r') as f:
        dashboard = json.load(f)
    
    # Get starting positions
    start_panel_id = get_next_panel_id(dashboard)
    start_y = get_last_y_position(dashboard) + 1
    
    print(f"Starting at panel ID: {start_panel_id}, y position: {start_y}")
    
    # Create new panels in order
    current_id = start_panel_id
    current_y = start_y
    
    new_panels = []
    
    # Temperature & Health section
    new_panels.append(create_temperature_row(current_id, current_y))
    current_id += 1
    current_y += 1
    
    new_panels.append(create_cpu_temp_gauge(current_id, current_y))
    current_id += 1
    
    new_panels.append(create_temp_trend_graph(current_id, current_y))
    current_id += 1
    current_y += 6
    
    # Storage I/O section
    new_panels.append(create_disk_io_row(current_id, current_y))
    current_id += 1
    current_y += 1
    
    new_panels.append(create_disk_io_rates_graph(current_id, current_y))
    current_id += 1
    
    new_panels.append(create_disk_iops_graph(current_id, current_y))
    current_id += 1
    current_y += 6
    
    # Network Interfaces section
    new_panels.append(create_network_interfaces_row(current_id, current_y))
    current_id += 1
    current_y += 1
    
    new_panels.append(create_network_traffic_graph(current_id, current_y))
    current_id += 1
    
    new_panels.append(create_network_errors_graph(current_id, current_y))
    current_id += 1
    current_y += 6
    
    # Disk Usage by Mount section
    new_panels.append(create_disk_mounts_row(current_id, current_y))
    current_id += 1
    current_y += 1
    
    new_panels.append(create_disk_usage_mounts_graph(current_id, current_y))
    current_id += 1
    
    new_panels.append(create_disk_space_mounts_graph(current_id, current_y))
    current_id += 1
    current_y += 6
    
    # Memory Health section
    new_panels.append(create_memory_pressure_row(current_id, current_y))
    current_id += 1
    current_y += 1
    
    new_panels.append(create_available_memory_graph(current_id, current_y))
    current_id += 1
    
    new_panels.append(create_memory_pressure_graph(current_id, current_y))
    current_id += 1
    
    # Add new panels to dashboard
    dashboard['panels'].extend(new_panels)
    
    # Write enhanced dashboard (backup original first)
    import shutil
    shutil.copy(input_file, input_file + '.backup.' + str(int(__import__('time').time())))
    
    with open(input_file, 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print(f"\n✅ Enhanced dashboard created!")
    print(f"   Added {len(new_panels)} new panels")
    print(f"   Total panels: {len(dashboard['panels'])}")
    print(f"   Original backed up to: {input_file}.backup.*")
    print(f"\n📋 New sections added:")
    print(f"   - Temperature & Health (CPU temp gauge + trends)")
    print(f"   - Storage I/O Performance (read/write rates + IOPS)")
    print(f"   - Network Interfaces (traffic + errors)")
    print(f"   - Disk Usage by Mount Point (usage % + space)")
    print(f"   - Memory Health (available memory + pressure)")

if __name__ == '__main__':
    main()

