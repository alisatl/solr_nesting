These files accompany my blog post on nested document handling capabilities of Solr 5.3.1 and 5.5.0:
https://medium.com/@alisazhila/solr-s-nesting-on-solr-s-capabilities-to-handle-deeply-nested-document-structures-50eeaaa4347a#.90xb5dqo8

### Script usage:

$python ./scripts/convert_data2solrjson.py -i ./data/example-data.json -o ./data/example-data-solr.json

$python ./scripts/convert_data2solrjson_for_faceting.py -i ./data/example-data.json -o ./data/example-data-solr-for-faceting.json
