#!/bin/bash
# Add providers directly to LazyLibrarian database

# NZBHydra2 configuration
docker exec media-download-lazylibrarian sqlite3 /config/lazylibrarian.db <<EOF
INSERT OR REPLACE INTO newznab (Name, Host, Apipath, Apikey, Enabled, Priority, Types)
VALUES (
    'NZBHydra2',
    'http://media-download-nzbhydra2:5076',
    '/api',
    '2SQ42T9209NUIQCAJTPBMTLBJF',
    1,
    0,
    'E,A'
);
EOF

# Jackett configuration
docker exec media-download-lazylibrarian sqlite3 /config/lazylibrarian.db <<EOF
INSERT OR REPLACE INTO torznab (Name, Host, Apipath, Apikey, Enabled, Priority, Seeders, Types)
VALUES (
    'Jackett',
    'http://media-download-jackett:9117',
    '/api/v2.0/indexers/all/results/torznab',
    'orjbnk0p7ar5s2u521emxrwb8cjvrz8c',
    1,
    0,
    0,
    'E,A'
);
EOF

echo "✓ Providers added to LazyLibrarian database"
echo "Refresh the LazyLibrarian web UI to see them"

