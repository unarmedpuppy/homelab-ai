#!/usr/bin/env python3
"""
Script to enhance Grafana dashboard with new panels based on recommendations.
Adds temperature monitoring, ZFS metrics, disk I/O, network stats, and more.
"""

import json
import sys

def create_temperature_row():
    """Create Temperature & Health row section"""
    return {
        "collapsed": False,
        "datasource": {"type": "influxdb", "uid": "8zXyAXzRz"},
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": 70},
        "id": 70000,
        "panels": [],
        "title": "Temperature & Health",
        "type": "row"
    }

def create_cpu_temp_gauge():
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
        "gridPos": {"h": 6, "w": 4, "x": 0, "y": 71},
        "id": 70001,
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

def create_temp_trend_graph():
    """Temperature Trend Graph Panel"""
    return {
        "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": {"axisLabel": "", "axisPlacement": "auto", "barAlignment": 0, "drawStyle": "line", "fillOpacity": 10, "gradientMode": "none", "hideFrom": {"tooltip": False, "viz": False, "legend": False}, "lineInterpolation": "linear", "lineWidth": 1, "pointSize": 5, "scaleDistribution": {"type": "linear"}, "showPoints": "never", "spanNulls": False},
                "mappings": [],
                "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}]},
                "unit": "celsius"
            },
            "overrides": []
        },
        "gridPos": {"h": 6, "w": 20, "x": 4, "y": 71},
        "id": 70002,
        "options": {"legend": {"calcs": [], "displayMode": "list", "placement": "bottom"}, "tooltip": {"mode": "multi"}},
        "pluginVersion": "9.2.3",
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
        "title": "Temperature Trends",
        "type": "timeseries"
    }

def create_disk_io_row():
    """Create Storage I/O row section"""
    return {
        "collapsed": False,
        "datasource": {"type": "influxdb", "uid": "8zXyAXzRz"},
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": 77},
        "id": 70010,
        "panels": [],
        "title": "Storage I/O Performance",
        "type": "row"
    }

def create_disk_io_rates():
    """Disk I/O Read/Write Rates Panel"""
    return {
        "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": {"axisLabel": "", "axisPlacement": "auto", "barAlignment": 0, "drawStyle": "line", "fillOpacity": 10, "gradientMode": "none", "hideFrom": {"tooltip": False, "viz": False, "legend": False}, "lineInterpolation": "linear", "lineWidth": 1, "pointSize": 5, "scaleDistribution": {"type": "linear"}, "showPoints": "never", "spanNulls": False},
                "mappings": [],
                "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}]},
                "unit": "MBs"
            },
            "overrides": []
        },
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 78},
        "id": 70011,
        "options": {"legend": {"calcs": [], "displayMode": "list", "placement": "bottom"}, "tooltip": {"mode": "multi"}},
        "pluginVersion": "9.2.3",
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["name"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "diskio",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"read_bytes\") / 1024 / 1024 AS \"Read MB/s\", mean(\"write_bytes\") / 1024 / 1024 AS \"Write MB/s\" FROM \"diskio\" WHERE (\"name\" =~ /$disk/) AND $timeFilter GROUP BY time($interval), \"name\" fill(null)",
            "rawQuery": False,
            "refId": "A",
            "resultFormat": "time_series",
            "select": [[{"params": ["read_bytes"], "type": "field"}, {"params": [], "type": "mean"}, {"params": ["/ 1024 / 1024"], "type": "math"}], [{"params": ["write_bytes"], "type": "field"}, {"params": [], "type": "mean"}, {"params": ["/ 1024 / 1024"], "type": "math"}]],
            "tags": [{"key": "name", "operator": "=~", "value": "/$disk/"}]
        }],
        "title": "Disk I/O Read/Write Rates",
        "type": "timeseries"
    }

def create_disk_iops():
    """Disk IOPS Panel"""
    return {
        "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": {"axisLabel": "", "axisPlacement": "auto", "barAlignment": 0, "drawStyle": "line", "fillOpacity": 10, "gradientMode": "none", "hideFrom": {"tooltip": False, "viz": False, "legend": False}, "lineInterpolation": "linear", "lineWidth": 1, "pointSize": 5, "scaleDistribution": {"type": "linear"}, "showPoints": "never", "spanNulls": False},
                "mappings": [],
                "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}]},
                "unit": "iops"
            },
            "overrides": []
        },
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 78},
        "id": 70012,
        "options": {"legend": {"calcs": [], "displayMode": "list", "placement": "bottom"}, "tooltip": {"mode": "multi"}},
        "pluginVersion": "9.2.3",
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["name"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "diskio",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"reads\") + mean(\"writes\") AS \"IOPS\" FROM \"diskio\" WHERE (\"name\" =~ /$disk/) AND $timeFilter GROUP BY time($interval), \"name\" fill(null)",
            "rawQuery": False,
            "refId": "A",
            "resultFormat": "time_series",
            "select": [[{"params": ["reads"], "type": "field"}, {"params": [], "type": "mean"}], [{"params": ["writes"], "type": "field"}, {"params": [], "type": "mean"}]],
            "tags": [{"key": "name", "operator": "=~", "value": "/$disk/"}]
        }],
        "title": "Disk IOPS",
        "type": "timeseries"
    }

def create_network_interfaces_row():
    """Create Network Interfaces row section"""
    return {
        "collapsed": False,
        "datasource": {"type": "influxdb", "uid": "8zXyAXzRz"},
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": 84},
        "id": 70020,
        "panels": [],
        "title": "Network Interfaces",
        "type": "row"
    }

def create_network_traffic():
    """Network Traffic per Interface Panel"""
    return {
        "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": {"axisLabel": "", "axisPlacement": "auto", "barAlignment": 0, "drawStyle": "line", "fillOpacity": 10, "gradientMode": "none", "hideFrom": {"tooltip": False, "viz": False, "legend": False}, "lineInterpolation": "linear", "lineWidth": 1, "pointSize": 5, "scaleDistribution": {"type": "linear"}, "showPoints": "never", "spanNulls": False},
                "mappings": [],
                "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}]},
                "unit": "Mbps"
            },
            "overrides": []
        },
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 85},
        "id": 70021,
        "options": {"legend": {"calcs": [], "displayMode": "list", "placement": "bottom"}, "tooltip": {"mode": "multi"}},
        "pluginVersion": "9.2.3",
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["interface"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "net",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"bytes_sent\") * 8 / 1000000 AS \"Upload Mbps\", mean(\"bytes_recv\") * 8 / 1000000 AS \"Download Mbps\" FROM \"net\" WHERE (\"interface\" =~ /$netif/ OR \"interface\" = 'docker0' OR \"interface\" = 'tun0') AND $timeFilter GROUP BY time($interval), \"interface\" fill(null)",
            "rawQuery": False,
            "refId": "A",
            "resultFormat": "time_series",
            "select": [[{"params": ["bytes_sent"], "type": "field"}, {"params": [], "type": "mean"}, {"params": ["* 8 / 1000000"], "type": "math"}], [{"params": ["bytes_recv"], "type": "field"}, {"params": [], "type": "mean"}, {"params": ["* 8 / 1000000"], "type": "math"}]],
            "tags": [{"key": "interface", "operator": "=~", "value": "/$netif/"}]
        }],
        "title": "Network Traffic per Interface",
        "type": "timeseries"
    }

def create_network_errors():
    """Network Error Rates Panel"""
    return {
        "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": {"axisLabel": "", "axisPlacement": "auto", "barAlignment": 0, "drawStyle": "line", "fillOpacity": 10, "gradientMode": "none", "hideFrom": {"tooltip": False, "viz": False, "legend": False}, "lineInterpolation": "linear", "lineWidth": 1, "pointSize": 5, "scaleDistribution": {"type": "linear"}, "showPoints": "never", "spanNulls": False},
                "mappings": [],
                "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}, {"color": "red", "value": 1}]},
                "unit": "short"
            },
            "overrides": []
        },
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 85},
        "id": 70022,
        "options": {"legend": {"calcs": [], "displayMode": "list", "placement": "bottom"}, "tooltip": {"mode": "multi"}},
        "pluginVersion": "9.2.3",
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["interface"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "net",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"err_in\") AS \"Errors In\", mean(\"err_out\") AS \"Errors Out\", mean(\"drop_in\") AS \"Drops In\", mean(\"drop_out\") AS \"Drops Out\" FROM \"net\" WHERE (\"interface\" =~ /$netif/) AND $timeFilter GROUP BY time($interval), \"interface\" fill(null)",
            "rawQuery": False,
            "refId": "A",
            "resultFormat": "time_series",
            "select": [[{"params": ["err_in"], "type": "field"}, {"params": [], "type": "mean"}], [{"params": ["err_out"], "type": "field"}, {"params": [], "type": "mean"}], [{"params": ["drop_in"], "type": "field"}, {"params": [], "type": "mean"}], [{"params": ["drop_out"], "type": "field"}, {"params": [], "type": "mean"}]],
            "tags": [{"key": "interface", "operator": "=~", "value": "/$netif/"}]
        }],
        "title": "Network Error & Drop Rates",
        "type": "timeseries"
    }

def create_disk_mounts_row():
    """Create Disk Usage by Mount row section"""
    return {
        "collapsed": False,
        "datasource": {"type": "influxdb", "uid": "8zXyAXzRz"},
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": 91},
        "id": 70030,
        "panels": [],
        "title": "Disk Usage by Mount Point",
        "type": "row"
    }

def create_disk_usage_mounts():
    """Disk Usage per Mount Point Panel"""
    return {
        "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": {"axisLabel": "", "axisPlacement": "auto", "barAlignment": 0, "drawStyle": "line", "fillOpacity": 10, "gradientMode": "none", "hideFrom": {"tooltip": False, "viz": False, "legend": False}, "lineInterpolation": "linear", "lineWidth": 1, "pointSize": 5, "scaleDistribution": {"type": "linear"}, "showPoints": "never", "spanNulls": False},
                "mappings": [],
                "max": 100,
                "min": 0,
                "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}, {"color": "yellow", "value": 80}, {"color": "red", "value": 90}]},
                "unit": "percent"
            },
            "overrides": []
        },
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 92},
        "id": 70031,
        "options": {"legend": {"calcs": [], "displayMode": "list", "placement": "bottom"}, "tooltip": {"mode": "multi"}},
        "pluginVersion": "9.2.3",
        "targets": [{
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
        "title": "Disk Usage % by Mount Point",
        "type": "timeseries"
    }

def create_disk_space_mounts():
    """Disk Space Used/Free per Mount Panel"""
    return {
        "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": {"axisLabel": "", "axisPlacement": "auto", "barAlignment": 0, "drawStyle": "line", "fillOpacity": 10, "gradientMode": "none", "hideFrom": {"tooltip": False, "viz": False, "legend": False}, "lineInterpolation": "linear", "lineWidth": 1, "pointSize": 5, "scaleDistribution": {"type": "linear"}, "showPoints": "never", "spanNulls": False},
                "mappings": [],
                "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}]},
                "unit": "decgbytes"
            },
            "overrides": []
        },
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 92},
        "id": 70032,
        "options": {"legend": {"calcs": [], "displayMode": "list", "placement": "bottom"}, "tooltip": {"mode": "multi"}},
        "pluginVersion": "9.2.3",
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["path"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "disk",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"used\") / 1024 / 1024 / 1024 AS \"Used GB\", mean(\"free\") / 1024 / 1024 / 1024 AS \"Free GB\" FROM \"disk\" WHERE (\"path\" =~ /$mountpoint/) AND $timeFilter GROUP BY time($interval), \"path\" fill(null)",
            "rawQuery": False,
            "refId": "A",
            "resultFormat": "time_series",
            "select": [[{"params": ["used"], "type": "field"}, {"params": [], "type": "mean"}, {"params": ["/ 1024 / 1024 / 1024"], "type": "math"}], [{"params": ["free"], "type": "field"}, {"params": [], "type": "mean"}, {"params": ["/ 1024 / 1024 / 1024"], "type": "math"}]],
            "tags": [{"key": "path", "operator": "=~", "value": "/$mountpoint/"}]
        }],
        "title": "Disk Space Used/Free by Mount",
        "type": "timeseries"
    }

def create_memory_pressure_row():
    """Create Memory Health row section"""
    return {
        "collapsed": False,
        "datasource": {"type": "influxdb", "uid": "8zXyAXzRz"},
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": 98},
        "id": 70040,
        "panels": [],
        "title": "Memory Health",
        "type": "row"
    }

def create_available_memory():
    """Available Memory Trend Panel"""
    return {
        "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": {"axisLabel": "", "axisPlacement": "auto", "barAlignment": 0, "drawStyle": "line", "fillOpacity": 10, "gradientMode": "none", "hideFrom": {"tooltip": False, "viz": False, "legend": False}, "lineInterpolation": "linear", "lineWidth": 1, "pointSize": 5, "scaleDistribution": {"type": "linear"}, "showPoints": "never", "spanNulls": False},
                "mappings": [],
                "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}]},
                "unit": "decgbytes"
            },
            "overrides": []
        },
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 99},
        "id": 70041,
        "options": {"legend": {"calcs": [], "displayMode": "list", "placement": "bottom"}, "tooltip": {"mode": "multi"}},
        "pluginVersion": "9.2.3",
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["null"], "type": "fill"}],
            "measurement": "mem",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"available\") / 1024 / 1024 / 1024 AS \"Available GB\" FROM \"mem\" WHERE (\"host\" =~ /^$server$/) AND $timeFilter GROUP BY time($interval) fill(null)",
            "rawQuery": False,
            "refId": "A",
            "resultFormat": "time_series",
            "select": [[{"params": ["available"], "type": "field"}, {"params": [], "type": "mean"}, {"params": ["/ 1024 / 1024 / 1024"], "type": "math"}]],
            "tags": [{"key": "host", "operator": "=~", "value": "/^$server$/"}]
        }],
        "title": "Available Memory Trend",
        "type": "timeseries"
    }

def create_memory_pressure():
    """Memory Pressure Panel"""
    return {
        "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "thresholds"},
                "custom": {"axisLabel": "", "axisPlacement": "auto", "barAlignment": 0, "drawStyle": "line", "fillOpacity": 10, "gradientMode": "none", "hideFrom": {"tooltip": False, "viz": False, "legend": False}, "lineInterpolation": "linear", "lineWidth": 1, "pointSize": 5, "scaleDistribution": {"type": "linear"}, "showPoints": "never", "spanNulls": False},
                "mappings": [],
                "max": 100,
                "min": 0,
                "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}, {"color": "yellow", "value": 20}, {"color": "red", "value": 10}]},
                "unit": "percent"
            },
            "overrides": []
        },
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 99},
        "id": 70042,
        "options": {"legend": {"calcs": [], "displayMode": "list", "placement": "bottom"}, "tooltip": {"mode": "multi"}},
        "pluginVersion": "9.2.3",
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["null"], "type": "fill"}],
            "measurement": "mem",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT (mean(\"available\") / mean(\"total\")) * 100 AS \"Available %\" FROM \"mem\" WHERE (\"host\" =~ /^$server$/) AND $timeFilter GROUP BY time($interval) fill(null)",
            "rawQuery": False,
            "refId": "A",
            "resultFormat": "time_series",
            "select": [[{"params": ["available"], "type": "field"}, {"params": [], "type": "mean"}], [{"params": ["total"], "type": "field"}, {"params": [], "type": "mean"}]],
            "tags": [{"key": "host", "operator": "=~", "value": "/^$server$/"}]
        }],
        "title": "Memory Pressure (Available %)",
        "type": "timeseries"
    }

def main():
    # Read existing dashboard
    with open('/Users/joshuajenquist/repos/personal/home-server/apps/grafana/Grafana_Dashboard_Template.json', 'r') as f:
        dashboard = json.load(f)
    
    # Create new panels
    new_panels = [
        create_temperature_row(),
        create_cpu_temp_gauge(),
        create_temp_trend_graph(),
        create_disk_io_row(),
        create_disk_io_rates(),
        create_disk_iops(),
        create_network_interfaces_row(),
        create_network_traffic(),
        create_network_errors(),
        create_disk_mounts_row(),
        create_disk_usage_mounts(),
        create_disk_space_mounts(),
        create_memory_pressure_row(),
        create_available_memory(),
        create_memory_pressure()
    ]
    
    # Add new panels to dashboard
    dashboard['panels'].extend(new_panels)
    
    # Write enhanced dashboard
    output_file = '/Users/joshuajenquist/repos/personal/home-server/apps/grafana/Grafana_Dashboard_Template_Enhanced.json'
    with open(output_file, 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print(f"✅ Enhanced dashboard created: {output_file}")
    print(f"   Added {len(new_panels)} new panels")
    print(f"   Total panels: {len(dashboard['panels'])}")

if __name__ == '__main__':
    main()

