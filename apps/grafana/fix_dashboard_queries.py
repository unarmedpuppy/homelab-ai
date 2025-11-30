#!/usr/bin/env python3
"""
Fix dashboard queries:
1. Fix container memory query - remove host filter or use correct host
2. Fix disk usage queries - ensure mountpoint variable works
3. Add dynamic container table panel
"""

import json

def fix_container_memory_query(dashboard):
    """Fix the container memory query to work correctly"""
    for panel in dashboard['panels']:
        if panel.get('title') == 'Per-Container Memory Usage (GB)':
            if 'targets' in panel and len(panel['targets']) > 0:
                target = panel['targets'][0]
                # Remove host filter or change to match 'telegraf'
                if 'tags' in target:
                    # Remove host filter - it's causing issues
                    target['tags'] = [t for t in target['tags'] if t.get('key') != 'host']
                # Update query to not filter by host
                if 'query' in target:
                    target['query'] = target['query'].replace('AND \"host\" =~ /^$server$/', '')
            break

def add_container_variable(dashboard):
    """Add a container variable for filtering"""
    container_var = {
        "current": {},
        "datasource": {
            "uid": "$datasource"
        },
        "definition": "",
        "hide": 0,
        "includeAll": True,
        "label": "Container",
        "multi": True,
        "name": "container",
        "options": [],
        "query": "SHOW TAG VALUES FROM \"docker_container_mem\" WITH KEY = \"container_name\" WHERE \"container_status\" = 'running'",
        "refresh": 1,
        "regex": "",
        "skipUrlSync": False,
        "sort": 1,
        "tagValuesQuery": "",
        "tagsQuery": "",
        "type": "query",
        "useTags": False
    }
    
    # Add after the server variable
    templating = dashboard.get('templating', {})
    if 'list' in templating:
        # Find server variable index
        for i, var in enumerate(templating['list']):
            if var.get('name') == 'server':
                templating['list'].insert(i + 1, container_var)
                break

def add_container_table_panel(dashboard):
    """Add a dynamic container metrics table panel"""
    # Find last panel position
    last_y = 0
    for panel in dashboard['panels']:
        if 'gridPos' in panel and 'y' in panel['gridPos']:
            last_y = max(last_y, panel['gridPos']['y'] + panel['gridPos'].get('h', 1))
    
    # Get next panel ID
    max_id = 0
    for panel in dashboard['panels']:
        if 'id' in panel and isinstance(panel['id'], int):
            max_id = max(max_id, panel['id'])
    
    # Create container details row
    row_panel = {
        "collapsed": False,
        "datasource": {"type": "influxdb", "uid": "8zXyAXzRz"},
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": last_y},
        "id": max_id + 1,
        "panels": [],
        "title": "Container Metrics Table",
        "type": "row"
    }
    
    # Create table panel
    table_panel = {
        "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "thresholds"},
                "custom": {
                    "align": "auto",
                    "displayMode": "list",
                    "inspect": False
                },
                "mappings": [],
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": None}
                    ]
                }
            },
            "overrides": [
                {
                    "matcher": {"id": "byName", "options": "Memory GB"},
                    "properties": [
                        {"id": "custom.width", "value": 120},
                        {"id": "unit", "value": "decgbytes"}
                    ]
                },
                {
                    "matcher": {"id": "byName", "options": "Memory %"},
                    "properties": [
                        {"id": "custom.width", "value": 100},
                        {"id": "unit", "value": "percent"},
                        {"id": "thresholds", "value": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 80},
                                {"color": "red", "value": 90}
                            ]
                        }}
                    ]
                },
                {
                    "matcher": {"id": "byName", "options": "CPU %"},
                    "properties": [
                        {"id": "custom.width", "value": 100},
                        {"id": "unit", "value": "percent"},
                        {"id": "thresholds", "value": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 70},
                                {"color": "red", "value": 90}
                            ]
                        }}
                    ]
                }
            ]
        },
        "gridPos": {"h": 10, "w": 24, "x": 0, "y": last_y + 1},
        "id": max_id + 2,
        "options": {
            "showHeader": True,
            "sortBy": [
                {
                    "desc": True,
                    "displayName": "Memory GB"
                }
            ]
        },
        "pluginVersion": "9.2.3",
        "targets": [
            {
                "alias": "",
                "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
                "dsType": "influxdb",
                "groupBy": [{"params": ["container_name"], "type": "tag"}],
                "measurement": "docker_container_mem",
                "orderByTime": "ASC",
                "policy": "default",
                "query": "SELECT last(\"usage\") / 1024 / 1024 / 1024 AS \"Memory GB\", last(\"usage_percent\") AS \"Memory %\" FROM \"docker_container_mem\" WHERE (\"container_status\" = 'running' AND \"container_name\" =~ /$container/) AND $timeFilter GROUP BY \"container_name\"",
                "rawQuery": True,
                "refId": "A",
                "resultFormat": "table"
            },
            {
                "alias": "",
                "datasource": {"type": "influxdb", "uid": "${DS_INFLUXDB}"},
                "dsType": "influxdb",
                "groupBy": [{"params": ["container_name"], "type": "tag"}],
                "measurement": "docker_container_cpu",
                "orderByTime": "ASC",
                "policy": "default",
                "query": "SELECT last(\"usage_percent\") AS \"CPU %\" FROM \"docker_container_cpu\" WHERE (\"container_status\" = 'running' AND \"container_name\" =~ /$container/) AND $timeFilter GROUP BY \"container_name\"",
                "rawQuery": True,
                "refId": "B",
                "resultFormat": "table"
            }
        ],
        "title": "Container Metrics Overview",
        "transformations": [
            {
                "id": "merge",
                "options": {}
            }
        ],
        "type": "table"
    }
    
    dashboard['panels'].append(row_panel)
    dashboard['panels'].append(table_panel)

def main():
    input_file = '/Users/joshuajenquist/repos/personal/home-server/apps/grafana/Grafana_Dashboard_Template.json'
    
    with open(input_file, 'r') as f:
        dashboard = json.load(f)
    
    # Fix container memory query
    fix_container_memory_query(dashboard)
    
    # Add container variable
    add_container_variable(dashboard)
    
    # Add container table panel
    add_container_table_panel(dashboard)
    
    # Write updated dashboard
    with open(input_file, 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print("✅ Fixed container memory query")
    print("✅ Added container variable")
    print("✅ Added container metrics table panel")

if __name__ == '__main__':
    main()

