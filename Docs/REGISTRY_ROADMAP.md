# Registry and persistent-identifier roadmap

Registry submission follows publication of the versioned specification, source archive, and DOI record. Working correspondence and submission forms are maintained separately from the standard's versioned source.

## IANA media types

Submit `application/vnd.modavis.vao+zip` through the IANA media-type form using the public immutable specification URL. Include binary encoding, no parameters/fragments, ZIP interoperability, comprehensive security considerations, `.vao`, first-member identification, applications, contact, and change controller.

Prerequisites: public specification, durable contact/change-control route, owner approval, final security review, and a repeated exact-subtype collision search against the current registry.

## W3ID

Propose `w3id.org/modavis/vao/` redirects through the `perma-id/w3id.org` repository. The submission directory includes `.htaccess` and README/contact information. Versioned routes must be immutable. VAO 0.4.0 defines no `/latest/` route for normative use; the unversioned project root is a moving discovery redirect only.

Prerequisites: public target repository/release pages and tested redirects.

## PRONOM

Submit a format proposal through The National Archives PRONOM Research GitHub submissions workflow. Provide format name/version, extension, MIME, vendor/project, description, ZIP container signature, internal `mimetype` signature, attribution, and openly licensed sample carriers. PRONOM samples have separate licensing expectations; use synthetic CC0 copies if requested rather than silently relicensing repository fixtures. Because the acronym/extension is not globally unique, request container-aware identification rather than an extension-only signature.

## Desktop MIME databases

A Shared MIME-info XML draft can identify `.vao`, ZIP magic, and first-member `mimetype`. Submit upstream only after IANA/identifier review to avoid conflicting identifiers.

## Wikidata and other registries

Prepare but do not execute Wikidata statements until stable public URLs, release date, license, and identifiers exist. Consider FAIRsharing, Research Data Alliance catalogues, Library of Congress registries, and preservation-community listings based on their scope and review criteria.

## DOI/repository deposit

The version DOI is `10.5281/zenodo.22122774`. Zenodo's automatic GitHub integration cannot use a separately reserved DOI, so this release uses the manual path: create the approved GitHub `v0.4.0` release, build and attach the deterministic source ZIP, upload that exact ZIP as the single compressed file in the prepared Zenodo record, compare SHA-256, link the GitHub release as an identical representation, and only then publish the record. The legacy GitHub metadata field cannot express the repository's file-specific licensing, so `.zenodo.json` uses the truthful generic `other-open` fallback; the deposited record must state both CC-BY-4.0 and Apache-2.0 rights consistently with `REUSE.toml`.

Every submission should use the same format name, version, media type, extension, editor/change controller, license, public specification URL, and security description.
