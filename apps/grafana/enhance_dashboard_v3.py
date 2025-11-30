#!/usr/bin/env python3
"""
Script to add remaining dashboard enhancements:
- ZFS Pool metrics
- Enhanced per-container metrics
- Enhanced HTTP/DNS panels
"""

import json
import time

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

def create_zfs_row(panel_id, y_pos):
    """Create ZFS Storage row section"""
    return {
        "collapsed": False,
        "datasource": {"type": "influxdb", "uid": "8zXyAXzRz"},
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": y_pos},
        "id": panel_id,
        "panels": [],
        "title": "ZFS Storage",
        "type": "row"
    }

def create_zfs_pool_space(panel_id, y_pos):
    """ZFS Pool Space Usage Panel"""
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
                        {"color": "yellow", "value": 80},
                        {"color": "orange", "value": 90},
                        {"color": "red", "value": 95}
                    ]
                },
                "unit": "percent"
            },
            "overrides": []
        },
        "gridPos": {"h": 6, "w": 6, "x": 0, "y": y_pos},
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
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["pools"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "zfs",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT (mean(\"arcstats_size\") / mean(\"arcstats_c_max\")) * 100 FROM \"zfs\" WHERE $timeFilter GROUP BY time($interval), \"pools\" fill(null)",
            "rawQuery": False,
            "refId": "A",
            "resultFormat": "time_series",
            "select": [[{"params": ["arcstats_size"], "type": "field"}, {"params": [], "type": "mean"}], [{"params": ["arcstats_c_max"], "type": "field"}, {"params": [], "type": "mean"}]],
            "tags": []
        }],
        "title": "ZFS ARC Usage %",
        "type": "gauge"
    }

def create_zfs_io_graph(panel_id, y_pos):
    """ZFS I/O Statistics Graph Panel"""
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
        "gridPos": {"h": 6, "w": 9, "x": 6, "y": y_pos},
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
            "alias": "L2 Read MB/s - $tag_pools",
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["pools"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "zfs",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"arcstats_l2_read_bytes\") / 1024 / 1024 FROM \"zfs\" WHERE $timeFilter GROUP BY time($interval), \"pools\" fill(null)",
            "rawQuery": False,
            "refId": "A",
            "resultFormat": "time_series",
            "select": [[{"params": ["arcstats_l2_read_bytes"], "type": "field"}, {"params": [], "type": "mean"}, {"params": ["/ 1024 / 1024"], "type": "math"}]],
            "tags": []
        }, {
            "alias": "L2 Write MB/s - $tag_pools",
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["pools"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "zfs",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"arcstats_l2_write_bytes\") / 1024 / 1024 FROM \"zfs\" WHERE $timeFilter GROUP BY time($interval), \"pools\" fill(null)",
            "rawQuery": False,
            "refId": "B",
            "resultFormat": "time_series",
            "select": [[{"params": ["arcstats_l2_write_bytes"], "type": "field"}, {"params": [], "type": "mean"}, {"params": ["/ 1024 / 1024"], "type": "math"}]],
            "tags": []
        }],
        "thresholds": [],
        "timeRegions": [],
        "title": "ZFS L2 Cache I/O (MB/s)",
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

def create_zfs_arc_hits(panel_id, y_pos):
    """ZFS ARC Hit Rate Graph Panel"""
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
        "gridPos": {"h": 6, "w": 9, "x": 15, "y": y_pos},
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
            "alias": "ARC Hits - $tag_pools",
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["pools"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "zfs",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"arcstats_hits\") FROM \"zfs\" WHERE $timeFilter GROUP BY time($interval), \"pools\" fill(null)",
            "rawQuery": False,
            "refId": "A",
            "resultFormat": "time_series",
            "select": [[{"params": ["arcstats_hits"], "type": "field"}, {"params": [], "type": "mean"}]],
            "tags": []
        }, {
            "alias": "ARC Misses - $tag_pools",
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["pools"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "zfs",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"arcstats_misses\") FROM \"zfs\" WHERE $timeFilter GROUP BY time($interval), \"pools\" fill(null)",
            "rawQuery": False,
            "refId": "B",
            "resultFormat": "time_series",
            "select": [[{"params": ["arcstats_misses"], "type": "field"}, {"params": [], "type": "mean"}]],
            "tags": []
        }],
        "thresholds": [],
        "timeRegions": [],
        "title": "ZFS ARC Hits/Misses",
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
                "label": "Count",
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

def create_container_details_row(panel_id, y_pos):
    """Create Docker Container Details row section"""
    return {
        "collapsed": False,
        "datasource": {"type": "influxdb", "uid": "8zXyAXzRz"},
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": y_pos},
        "id": panel_id,
        "panels": [],
        "title": "Docker Container Details",
        "type": "row"
    }

def create_container_memory_graph(panel_id, y_pos):
    """Per-Container Memory Usage Graph Panel"""
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
        "stack": True,
        "steppedLine": False,
        "targets": [{
            "alias": "$tag_container_name",
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["container_name"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "docker_container_mem",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"limit\") / 1024 / 1024 / 1024 FROM \"docker_container_mem\" WHERE (\"container_status\" = 'running' AND \"host\" =~ /^$server$/) AND $timeFilter GROUP BY time($interval), \"container_name\" fill(null)",
            "rawQuery": False,
            "refId": "A",
            "resultFormat": "time_series",
            "select": [[{"params": ["limit"], "type": "field"}, {"params": [], "type": "mean"}, {"params": ["/ 1024 / 1024 / 1024"], "type": "math"}]],
            "tags": [{"key": "container_status", "operator": "=", "value": "running"}]
        }],
        "thresholds": [],
        "timeRegions": [],
        "title": "Per-Container Memory Usage (GB)",
        "tooltip": {
            "shared": True,
            "sort": 2,
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
                "label": "Memory (GB)",
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

def create_container_network_graph(panel_id, y_pos):
    """Per-Container Network I/O Graph Panel"""
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
            "alias": "RX - $tag_container_name",
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["container_name"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "docker_container_net",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"rx_bytes\") / 1024 / 1024 FROM \"docker_container_net\" WHERE (\"container_status\" = 'running' AND \"host\" =~ /^$server$/) AND $timeFilter GROUP BY time($interval), \"container_name\" fill(null)",
            "rawQuery": False,
            "refId": "A",
            "resultFormat": "time_series",
            "select": [[{"params": ["rx_bytes"], "type": "field"}, {"params": [], "type": "mean"}, {"params": ["/ 1024 / 1024"], "type": "math"}]],
            "tags": [{"key": "container_status", "operator": "=", "value": "running"}]
        }, {
            "alias": "TX - $tag_container_name",
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["container_name"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "docker_container_net",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"tx_bytes\") / 1024 / 1024 FROM \"docker_container_net\" WHERE (\"container_status\" = 'running' AND \"host\" =~ /^$server$/) AND $timeFilter GROUP BY time($interval), \"container_name\" fill(null)",
            "rawQuery": False,
            "refId": "B",
            "resultFormat": "time_series",
            "select": [[{"params": ["tx_bytes"], "type": "field"}, {"params": [], "type": "mean"}, {"params": ["/ 1024 / 1024"], "type": "math"}]],
            "tags": [{"key": "container_status", "operator": "=", "value": "running"}]
        }],
        "thresholds": [],
        "timeRegions": [],
        "title": "Per-Container Network I/O (MB/s)",
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

def create_http_response_enhanced(panel_id, y_pos):
    """Enhanced HTTP Response Time with Percentiles Graph Panel"""
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
            "alias": "Mean - $tag_url",
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["url"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "http_response",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT mean(\"response_time\") FROM \"http_response\" WHERE $timeFilter GROUP BY time($interval), \"url\" fill(null)",
            "rawQuery": False,
            "refId": "A",
            "resultFormat": "time_series",
            "select": [[{"params": ["response_time"], "type": "field"}, {"params": [], "type": "mean"}]],
            "tags": []
        }, {
            "alias": "Max - $tag_url",
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["url"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "http_response",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT max(\"response_time\") FROM \"http_response\" WHERE $timeFilter GROUP BY time($interval), \"url\" fill(null)",
            "rawQuery": False,
            "refId": "B",
            "resultFormat": "time_series",
            "select": [[{"params": ["response_time"], "type": "field"}, {"params": [], "type": "max"}]],
            "tags": []
        }],
        "thresholds": [
            {"colorMode": "critical", "fill": True, "line": True, "op": "gt", "value": 1000}
        ],
        "timeRegions": [],
        "title": "HTTP Response Times (Enhanced)",
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
                "format": "ms",
                "label": "Response Time (ms)",
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

def create_http_status_codes(panel_id, y_pos):
    """HTTP Status Codes Panel"""
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
        "seriesOverrides": [
            {"alias": "/2.*/", "color": "green"},
            {"alias": "/4.*/", "color": "yellow"},
            {"alias": "/5.*/", "color": "red"}
        ],
        "spaceLength": 10,
        "stack": False,
        "steppedLine": False,
        "targets": [{
            "alias": "$tag_http_response_code - $tag_url",
            "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
            "dsType": "influxdb",
            "groupBy": [{"params": ["$interval"], "type": "time"}, {"params": ["http_response_code"], "type": "tag"}, {"params": ["url"], "type": "tag"}, {"params": ["null"], "type": "fill"}],
            "measurement": "http_response",
            "orderByTime": "ASC",
            "policy": "default",
            "query": "SELECT count(\"http_response_code\") FROM \"http_response\" WHERE $timeFilter GROUP BY time($interval), \"http_response_code\", \"url\" fill(null)",
            "rawQuery": False,
            "refId": "A",
            "resultFormat": "time_series",
            "select": [[{"params": ["http_response_code"], "type": "field"}, {"params": [], "type": "count"}]],
            "tags": []
        }],
        "thresholds": [],
        "timeRegions": [],
        "title": "HTTP Status Codes",
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
                "label": "Count",
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
    
    # ZFS Storage section
    new_panels.append(create_zfs_row(current_id, current_y))
    current_id += 1
    current_y += 1
    
    new_panels.append(create_zfs_pool_space(current_id, current_y))
    current_id += 1
    
    new_panels.append(create_zfs_io_graph(current_id, current_y))
    current_id += 1
    
    new_panels.append(create_zfs_arc_hits(current_id, current_y))
    current_id += 1
    current_y += 6
    
    # Docker Container Details section
    new_panels.append(create_container_details_row(current_id, current_y))
    current_id += 1
    current_y += 1
    
    new_panels.append(create_container_memory_graph(current_id, current_y))
    current_id += 1
    
    new_panels.append(create_container_network_graph(current_id, current_y))
    current_id += 1
    current_y += 6
    
    # Enhanced HTTP/DNS section
    new_panels.append(create_http_response_enhanced(current_id, current_y))
    current_id += 1
    
    new_panels.append(create_http_status_codes(current_id, current_y))
    current_id += 1
    
    # Add new panels to dashboard
    dashboard['panels'].extend(new_panels)
    
    # Write enhanced dashboard (backup original first)
    import shutil
    backup_file = input_file + '.backup.' + str(int(time.time()))
    shutil.copy(input_file, backup_file)
    
    with open(input_file, 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print(f"\n✅ Enhanced dashboard updated!")
    print(f"   Added {len(new_panels)} new panels")
    print(f"   Total panels: {len(dashboard['panels'])}")
    print(f"   Original backed up to: {backup_file}")
    print(f"\n📋 New sections added:")
    print(f"   - ZFS Storage (ARC usage, I/O, hits/misses)")
    print(f"   - Docker Container Details (memory + network)")
    print(f"   - Enhanced HTTP/DNS (response times + status codes)")

if __name__ == '__main__':
    main()

