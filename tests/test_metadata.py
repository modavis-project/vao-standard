# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import re
import unittest
from urllib.parse import unquote

import yaml


ROOT = Path(__file__).resolve().parent.parent


def frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise AssertionError(f"Missing YAML front matter: {path}")
    return yaml.safe_load(text.split("---\n", 2)[1]) or {}


class MetadataTests(unittest.TestCase):
    def test_json_and_citation_metadata(self) -> None:
        codemeta = json.loads((ROOT / "codemeta.json").read_text(encoding="utf-8"))
        zenodo = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
        self.assertEqual(
            {
                "https://spdx.org/licenses/Apache-2.0",
                "https://spdx.org/licenses/CC-BY-4.0",
            },
            set(codemeta["license"]),
        )
        self.assertEqual("other-open", zenodo["license"])
        self.assertEqual("0.5.0", zenodo["version"])
        self.assertEqual("2026-08-31", zenodo["publication_date"])
        self.assertIn("CC BY 4.0", zenodo["description"])
        self.assertIn("Apache-2.0", zenodo["description"])
        citation = yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))
        self.assertEqual("1.2.0", citation["cff-version"])
        self.assertEqual("0.5.0", citation["version"])
        self.assertEqual("2026-08-31", str(citation["date-released"]))
        self.assertEqual("10.5281/zenodo.22214248", citation["doi"])
        self.assertEqual("CC-BY-4.0", citation["license"])
        self.assertEqual(
            "https://orcid.org/0000-0002-7904-3892", citation["authors"][0]["orcid"]
        )
        for path in (ROOT / ".github").rglob("*.yml"):
            self.assertIsNotNone(yaml.safe_load(path.read_text(encoding="utf-8")), path)

    def test_workflow_actions_are_immutably_pinned(self) -> None:
        action = re.compile(r"(?m)^\s*-\s+uses:\s+([^\s#]+)")
        pinned = re.compile(r"^[^@\s]+@[0-9a-f]{40}$")
        mutable: list[str] = []
        for path in (ROOT / ".github" / "workflows").glob("*.yml"):
            for dependency in action.findall(path.read_text(encoding="utf-8")):
                if not pinned.fullmatch(dependency):
                    mutable.append(f"{path.relative_to(ROOT)}: {dependency}")
        self.assertEqual([], mutable)

    def test_release_dependency_lock_is_exact_and_hashed(self) -> None:
        lock = (ROOT / "requirements-lock.txt").read_text(encoding="utf-8")
        requirement = re.compile(r"(?m)^[a-z0-9][a-z0-9._-]*==[^\s;]+(?:\s*;.*)?\s*\\$")
        matches = list(requirement.finditer(lock))
        self.assertTrue(matches)
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(lock)
            stanza = lock[match.start() : end]
            self.assertIn("--hash=sha256:", stanza)
        for workflow in (ROOT / ".github" / "workflows").glob("*.yml"):
            text = workflow.read_text(encoding="utf-8")
            self.assertIn("--require-hashes -r requirements-lock.txt", text)

    def test_semantic_artifact_syntax(self) -> None:
        from rdflib import Graph, URIRef
        from rdflib.namespace import OWL, RDF

        context = json.loads(
            (ROOT / "Schemas/vao-context-0.5.0.jsonld").read_text(encoding="utf-8")
        )["@context"]
        self.assertIs(context["@protected"], True)
        self.assertEqual("https://w3id.org/modavis/vao/ontology#", context["@vocab"])
        for path in (ROOT / "Schemas").glob("*.ttl"):
            self.assertGreater(len(Graph().parse(path, format="turtle")), 0, path)

        vocabulary = Graph().parse(ROOT / "Schemas/vao-vocabulary-0.5.0.ttl")
        object_properties = set(vocabulary.subjects(RDF.type, OWL.ObjectProperty))
        datatype_properties = set(vocabulary.subjects(RDF.type, OWL.DatatypeProperty))
        self.assertEqual(set(), object_properties & datatype_properties)
        vao_terms: set[str] = set()

        def collect(value: object) -> None:
            if isinstance(value, str) and value.startswith("vao:"):
                vao_terms.add(context["@vocab"] + value[4:])
            elif isinstance(value, dict):
                for child in value.values():
                    collect(child)
            elif isinstance(value, list):
                for child in value:
                    collect(child)

        collect(context)
        self.assertEqual(
            [],
            sorted(
                term
                for term in vao_terms
                if not any(vocabulary.triples((URIRef(term), None, None)))
            ),
        )

        schema = json.loads(
            (ROOT / "Schemas/vao-manifest-0.5.0.schema.json").read_text(
                encoding="utf-8"
            )
        )
        schema_properties: set[str] = set()
        iri_fields: set[str] = set()

        def find_iri_fields(value: object) -> None:
            if isinstance(value, dict):
                properties = value.get("properties")
                if isinstance(properties, dict):
                    schema_properties.update(properties)
                    for name, contract in properties.items():
                        items = (
                            contract.get("items")
                            if isinstance(contract, dict)
                            else None
                        )
                        if isinstance(contract, dict) and (
                            str(contract.get("$ref", "")).endswith("/$defs/iri")
                            or (
                                isinstance(items, dict)
                                and str(items.get("$ref", "")).endswith("/$defs/iri")
                            )
                        ):
                            iri_fields.add(name)
                for child in value.values():
                    find_iri_fields(child)
            elif isinstance(value, list):
                for child in value:
                    find_iri_fields(child)

        find_iri_fields(schema)
        for name in iri_fields - {"id", "scheme"}:
            mapping = context.get(name)
            self.assertIsInstance(mapping, dict, name)
            self.assertIn(mapping.get("@type"), {"@id", "@vocab"}, name)

        base = context["@vocab"]
        prefixes = {
            name: value
            for name, value in context.items()
            if isinstance(value, str) and value.endswith(("/", "#"))
        }

        def expand(term: object) -> str | None:
            if not isinstance(term, str) or term.startswith(("@", "#")):
                return None
            if ":" in term:
                prefix, suffix = term.split(":", 1)
                return prefixes.get(prefix, f"{prefix}:") + suffix
            return base + term

        undeclared: list[str] = []
        for name in schema_properties - {"$ref", "@context"}:
            mapping = context.get(name)
            if isinstance(mapping, str):
                predicate = expand(mapping)
            elif isinstance(mapping, dict):
                predicate = expand(mapping.get("@id", name))
            else:
                predicate = base + name
            if (
                predicate is not None
                and predicate.startswith(base)
                and not any(vocabulary.triples((URIRef(predicate), None, None)))
            ):
                undeclared.append(predicate)
        self.assertEqual([], sorted(set(undeclared)))

    def test_modavis_010_binding_is_exact_and_uses_released_terms(self) -> None:
        from rdflib import Graph, URIRef
        from rdflib.namespace import OWL, RDFS

        mapping = Graph().parse(ROOT / "Schemas/vao-modavis-mapping-0.5.0.ttl")
        mapping_iri = URIRef("https://w3id.org/modavis/vao/0.5.0/modavis-mapping")
        self.assertEqual(
            {
                URIRef("https://w3id.org/modavis/vao/0.5.0/vocabulary"),
                URIRef("https://w3id.org/modavis/ontology/0.1.0"),
            },
            set(mapping.objects(mapping_iri, OWL.imports)),
        )
        self.assertIn(
            (
                URIRef("https://w3id.org/modavis/vao/ontology#Realization"),
                RDFS.subClassOf,
                URIRef("https://w3id.org/modavis/ontology/media#Bitstream"),
            ),
            mapping,
        )

        manifests = [
            ROOT / "Fixtures/VAO05/workspaces/minimal/vao-manifest.json",
            ROOT
            / "Fixtures/VAO05/descriptors/kinoorgel-multimodal-scientific.example.json",
            ROOT / "Fixtures/VAO05/descriptors/cuntz-positiv-acoustic.example.json",
        ]
        serialized = ""
        for path in manifests:
            document = json.loads(path.read_text(encoding="utf-8"))
            binding = document["modavisBinding"]
            self.assertEqual("released", binding["ontologyStatus"])
            self.assertEqual("0.1.0", binding["ontologyVersion"])
            self.assertEqual(
                "https://w3id.org/modavis/ontology/0.1.0",
                binding["ontologyVersionIRI"],
            )
            self.assertEqual(str(mapping_iri), binding["mappingIRI"])
            self.assertEqual("0.5.0", binding["mappingVersion"])
            serialized += json.dumps(document)

        for obsolete in (
            "https://w3id.org/modavis/ontology/instrument#PipeOrgan",
            "https://w3id.org/modavis/ontology/instrument#Manual",
            "https://w3id.org/modavis/ontology/instrument#Stop",
        ):
            self.assertNotIn(obsolete, serialized)
        for current in (
            "https://w3id.org/modavis/ontology/organ#PipeOrgan",
            "https://w3id.org/modavis/ontology/organ#OrganKeyboard",
            "https://w3id.org/modavis/ontology/organ#OrganStop",
        ):
            self.assertIn(current, serialized)

    def test_okf_bundle(self) -> None:
        index = frontmatter(ROOT / "knowledge/index.md")
        self.assertEqual({"okf_version": "0.2"}, index)
        log = (ROOT / "knowledge/log.md").read_text(encoding="utf-8")
        self.assertFalse(log.startswith("---\n"))
        self.assertRegex(log, r"(?m)^## \d{4}-\d{2}-\d{2}$")
        for path in (ROOT / "knowledge").rglob("*.md"):
            if path.name in {"index.md", "log.md"}:
                continue
            metadata = frontmatter(path)
            self.assertIsInstance(metadata.get("type"), str, path)
            self.assertIn(
                metadata.get("status", "stable"), {"draft", "stable", "deprecated"}
            )
            sources = metadata.get("sources")
            self.assertIsInstance(sources, list, path)
            self.assertTrue(sources, path)
            for source in sources:
                self.assertIsInstance(source, dict, path)
                self.assertIsInstance(source.get("resource"), str, path)
            generated = metadata.get("generated")
            if generated is not None:
                self.assertIsInstance(generated, dict, path)
                self.assertIsInstance(generated.get("by"), str, path)
                if generated.get("at") is not None:
                    timestamp = datetime.fromisoformat(
                        str(generated["at"]).replace("Z", "+00:00")
                    )
                    self.assertIsNotNone(timestamp.utcoffset(), path)
            verified = metadata.get("verified", [])
            events = verified if isinstance(verified, list) else [verified]
            for event in events:
                self.assertIsInstance(event, dict, path)
                self.assertIsInstance(event.get("by"), str, path)
                timestamp = datetime.fromisoformat(
                    str(event["at"]).replace("Z", "+00:00")
                )
                self.assertIsNotNone(timestamp.utcoffset(), path)

    def test_local_markdown_links_resolve(self) -> None:
        pattern = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
        fenced_code = re.compile(r"(```|~~~).*?\1", re.DOTALL)
        inline_code = re.compile(r"`[^`\n]*`")
        missing: list[str] = []
        for path in ROOT.rglob("*.md"):
            if ".git" in path.parts or ".venv" in path.parts:
                continue
            markdown = path.read_text(encoding="utf-8")
            prose = inline_code.sub("", fenced_code.sub("", markdown))
            for target in pattern.findall(prose):
                target = target.strip().strip("<>")
                if not target or target.startswith(
                    ("http://", "https://", "mailto:", "#")
                ):
                    continue
                local = unquote(target.split("#", 1)[0])
                if local and not (path.parent / local).exists():
                    missing.append(f"{path.relative_to(ROOT)} -> {target}")
        self.assertEqual([], missing)

    def test_no_machine_local_paths_or_release_placeholders(self) -> None:
        forbidden = (
            "/Users/" + "dominik/",
            "TO" + "DO",
            "T" + "BD",
            "<" + "INSERT",
            "example.com/" + "contact",
            "Chat" + "GPT",
            "Open" + "AI",
            "Cod" + "ex",
            "large language " + "model",
            "AI-" + "generated",
            "engineer-" + "weeks",
            "engineer " + "weeks",
        )
        findings: list[str] = []
        for path in ROOT.rglob("*"):
            if (
                not path.is_file()
                or ".git" in path.parts
                or ".venv" in path.parts
                or ".pytest_cache" in path.parts
                or ".ruff_cache" in path.parts
                or "build" in path.parts
                or "dist" in path.parts
                or path.suffix == ".vao"
            ):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for token in forbidden:
                if token in text:
                    findings.append(f"{path.relative_to(ROOT)}: {token}")
        self.assertEqual([], findings)

    def test_required_project_files(self) -> None:
        required = [
            "README.md",
            "LICENSE",
            "LICENSES/CC-BY-4.0.txt",
            "LICENSES/Apache-2.0.txt",
            "CHANGELOG.md",
            "CONTRIBUTING.md",
            "GOVERNANCE.md",
            "CODE_OF_CONDUCT.md",
            "SECURITY.md",
            "SUPPORT.md",
            "CITATION.cff",
            "codemeta.json",
            ".zenodo.json",
            "REUSE.toml",
            "RELEASE_STATUS.md",
            "VERSION",
        ]
        self.assertEqual([], [name for name in required if not (ROOT / name).is_file()])


if __name__ == "__main__":
    unittest.main()
