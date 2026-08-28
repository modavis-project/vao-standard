# VAO fixtures

Fixture files in this repository are CC BY 4.0 unless a nested notice says otherwise. Their conformance values may be synthetic or may describe separately held development inputs; referenced external assets retain their own rights and are not relicensed here. Fixtures validate data-exchange and processing semantics only and are not scientific evidence, benchmark truth, or certification of a real instrument.

`VAO05` is the current 0.5 candidate fixture set. It mirrors the established 0.4 examples and adds the identified-carrier descriptor/release contract. `VAO04` remains the finalized 0.4 regression set.

- `VAO04/descriptors/kinoorgel-multimodal-scientific.example.json`: complex valid 0.4.0 manifest covering scientific, multimodal, physical, playable, and runtime semantics.
- `VAO04/descriptors/cuntz-positiv-acoustic.example.json`: complex positive spatial/acoustic integration fixture; its values demonstrate conformance structure, not independently certified acoustic results.
- `VAO04/companions`: positive release, pack, receipt, and explicitly legacy Zenodo projection contracts. The release, pack, and `materialization-receipt-minimal` examples cross-check against the exact minimal manifest/carrier; `materialization-receipt.example.json` independently exercises verified and blocked acquisition states with clearly synthetic identities.
- `VAO04/workspaces/minimal`: small valid unpacked carrier migrated from the private 0.3 fixture with one exact text realization.
- `VAO04/carriers/minimal.vao`: deterministic packed form of the minimal workspace.
- `VAO03/valid/embedded-private`: private-draft source retained only to test migration.

The packed carrier is regenerated from its workspace by the release checks and must remain byte-identical.
