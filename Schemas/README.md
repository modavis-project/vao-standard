# Versioned VAO schemas and semantic artifacts

## Current 0.6.0 artifacts

- `vao-manifest-0.6.0.schema.json`
- `vao-carrier-0.6.0.schema.json`
- `vao-release-0.6.0.schema.json`
- `vao-pack-manifest-0.6.0.schema.json`
- `vao-materialization-receipt-0.6.0.schema.json`
- `vao-zenodo-metadata-0.6.0.schema.json`
- `vao-context-0.6.0.jsonld`
- `vao-vocabulary-0.6.0.ttl`
- `vao-modavis-mapping-0.6.0.ttl`
- `vao-shapes-0.6.0.ttl`
- `vao-release-bundle-0.6.0.json`

The independently versioned MMIC 1.0.0 schema, context, vocabulary, shapes, mappings, catalog and registry are in [Profiles/MMIC/1.0.0](../Profiles/MMIC/1.0.0/contract.md). Both current core and MMIC resources are available locally; 0.6.0 resolver routing is pending.

Regenerate the 0.6 bundle with `python Tools/update_release_bundle06.py`; CI uses `--check` to reject stale fixity. Versioned 0.5/0.4 artifacts remain unchanged. `python Tools/update_release_bundle.py` continues to verify the original 0.5 bundle.
