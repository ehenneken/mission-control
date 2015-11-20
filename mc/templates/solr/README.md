# Solr provisioner.

All data are scrubbed. Using the following pattern to create the solr data:

    curl localhost:8983/solr/query?bibcode="MYBIBCODE"
    [{"id": ["1"], "bibcode": "MYBIBCODE", ....}]

(On new instance)

    curl "http://localhost:8983/solr/update/json?commit=true" -H 'Content-type: application/json' -d '[{"id": ["1"], "bibcode": "MYBIBCODE", ....}]'
    curl "http://localhost:8983/solr/query?q=warm_cache(foo)"

The last command is to warm the cache so that citations/references can be search properly. This is relevant for services such as metrics/vis, etc.