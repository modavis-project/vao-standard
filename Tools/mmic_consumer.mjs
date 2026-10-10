#!/usr/bin/env node
// SPDX-License-Identifier: Apache-2.0
// Independent MMIC reader/reference trace. No Python validator or generator imports.
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { createHash } from 'node:crypto';

const PROFILE = 'https://w3id.org/modavis/vao/profile/mmic/1.0.0';
const fail = message => { throw new Error(message); };
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const path = resolve(process.argv[2]);
const manifest = JSON.parse(readFileSync(resolve(path, 'vao-manifest.json')));
const carrier = JSON.parse(readFileSync(resolve(path, 'META-INF/vao-carrier.json')));
const declarations = new Map(manifest.realizations.map(x => [x.id, x]));
const members = new Map(carrier.embeddedRealizations.map(x => [x.realizationId, x.path]));
function asset(id) {
  if (!members.has(id)) return null;
  const member = members.get(id);
  if (!member.startsWith('payload/') || member.split('/').some(x => ['..', '.', ''].includes(x)) || member.includes('\\')) fail('Unsafe member');
  const bytes = readFileSync(resolve(path, member));
  const declared = declarations.get(id);
  if (!declared || bytes.length > 8 * 1024 * 1024 || bytes.length !== declared.byteSize || hash(bytes) !== declared.sha256) fail('Asset fixity failure');
  return bytes;
}
function mapping(anchors, position) {
  for (let i = 1; i < anchors.length; i++) {
    const a = anchors[i - 1], b = anchors[i];
    if (!(a.position < b.position)) fail('Unordered mapping');
    if (a.position <= position && position <= b.position)
      return a.seconds + (position - a.position) * (b.seconds - a.seconds) / (b.position - a.position);
  }
  fail('Uncovered position');
}
function native(feature, track, role, spec) {
  const loc = feature.location, geometry = spec.geometry;
  const a = loc.start + (loc.startTurn ?? 0) * (geometry.period ?? 0);
  const b = loc.end + (loc.endTurn ?? 0) * (geometry.period ?? 0);
  if (loc.kind === 'point' && (a !== b || loc.axialStart !== loc.axialEnd)) fail('Noncoincident point');
  const onset = mapping(spec.timing.anchors, a + role.readerOffset) + spec.reader.delaySeconds;
  const end = mapping(spec.timing.anchors, b + role.readerOffset) + spec.reader.delaySeconds;
  if (geometry.kind === 'cylindrical') {
    const trajectory = spec.reader.trajectory;
    for (const [position, axial] of [[a, loc.axialStart], [b, loc.axialEnd]]) {
      const measured = mapping(trajectory.map(t => ({ position: t.position, seconds: t.axial })), position);
      if (Math.abs(measured - axial) > 1e-9) fail('Helical reader path mismatch');
    }
  }
  const event = { kind: role.signalKind, onsetSeconds: onset };
  if (role.signalKind === 'gate') event.durationSeconds = end - onset;
  if (role.signalKind === 'latch') event.value = feature.value;
  if (role.signalKind === 'envelope') {
    event.unit = role.quantityUnit;
    event.samples = feature.samples.map(x => ({ seconds: mapping(spec.timing.anchors, x.position + role.readerOffset) + spec.reader.delaySeconds, value: x.value }));
  }
  return event;
}
function close(actual, expected, tolerance) {
  if (typeof expected === 'number') return typeof actual === 'number' && Math.abs(actual - expected) <= tolerance;
  if (Array.isArray(expected)) return Array.isArray(actual) && actual.length === expected.length && expected.every((x, i) => close(actual[i], x, tolerance));
  if (expected && typeof expected === 'object') return Object.entries(expected).every(([k, v]) => close(actual[k], v, tolerance));
  return actual === expected;
}
function midi(bytes) {
  let p = 0;
  const take = n => { if (p + n > bytes.length) fail('Truncated SMF'); const v = bytes.subarray(p, p + n); p += n; return v; };
  if (take(4).toString() !== 'MThd' || take(4).readUInt32BE() !== 6) fail('Bad SMF');
  const kind = take(2).readUInt16BE(), count = take(2).readUInt16BE(), division = take(2).readUInt16BE();
  if (kind > 1 || division === 0 || division & 0x8000) fail('Unsupported SMF clock');
  const messages = [], tempos = [];
  for (let track = 0; track < count; track++) {
    if (take(4).toString() !== 'MTrk') fail('Missing track');
    const body = take(take(4).readUInt32BE());
    let q = 0, tick = 0, running = null;
    function vlq() {
      let n = 0;
      for (let i = 0; i < 4; i++) { const b = body[q++]; if (b === undefined) fail('Truncated VLQ'); n = n * 128 + (b & 127); if (!(b & 128)) return n; }
      fail('Oversized VLQ');
    }
    while (q < body.length) {
      tick += vlq();
      let status = body[q++];
      if (status < 128) { q--; status = running; if (!status) fail('Bad running status'); }
      if (status === 255) {
        running = null; const meta = body[q++], length = vlq(), payload = body.subarray(q, q + length); q += length;
        if (meta === 0x51) tempos.push([tick, payload.readUIntBE(0, 3)]);
      } else {
        running = status; let command = status >> 4; const channel = status & 15, first = body[q++], second = body[q++];
        if (![8, 9, 11].includes(command)) fail('Unsupported SMF message');
        if (command === 9 && second === 0) command = 8;
        messages.push([tick, command, channel, first, second]);
      }
      if (messages.length > 100000) fail('MIDI budget exceeded');
    }
  }
  if (!tempos.length || tempos.some(x => x[0] !== 0 || x[1] !== tempos[0][1]) || p !== bytes.length) fail('Unsupported tempo/trailing bytes');
  return { division, tempo: tempos[0][1], messages: sortMessages(messages) };
}
const sortMessages = xs => xs.sort((a, b) => { for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return a[i] - b[i]; return 0; });
function nearestEven(n) { const lo = Math.floor(n), fraction = n - lo; return fraction < 0.5 ? lo : fraction > 0.5 ? lo + 1 : lo % 2 === 0 ? lo : lo + 1; }
function expectedExport(events, bindings, roleAssignments, roles, selection) {
  const chosen = bindings.filter(b => selection.includes(b.id));
  const division = chosen[0].ticksPerBeat, tempo = chosen[0].tempoMicroseconds;
  const messages = [], tick = seconds => nearestEven(seconds * 1e6 * division / tempo);
  for (const binding of chosen) {
    const role = roles.find(r => r.id === binding.roleId);
    if (!role || !role.bindingIds.includes(binding.id)) fail('Binding ownership mismatch');
    const knownControls = { 'https://w3id.org/modavis/vao/mmic#Sustain': 64, 'https://w3id.org/modavis/vao/mmic#SoftPedal': 67 };
    if (Object.hasOwn(knownControls, role.target) && binding.controller !== knownControls[role.target]) fail('Known control function mismatch');
    if (binding.message === 'control-change') messages.push([0, 11, binding.channel, binding.controller, binding.initialValue]);
    for (const event of events) {
      if (roleAssignments.find(a => a.id === event.roleAssignmentId).modelRoleId !== role.id) continue;
      if (binding.message === 'note') {
        if (role.role !== 'note') fail('Non-note fallback');
        const duration = binding.durationPolicy.kind === 'fixed' ? binding.durationPolicy.seconds : event.durationSeconds;
        messages.push([tick(event.onsetSeconds), 9, binding.channel, binding.pitch, binding.velocity]);
        messages.push([tick(event.onsetSeconds + duration), 8, binding.channel, binding.pitch, 0]);
      } else if (event.kind === 'gate') {
        messages.push([tick(event.onsetSeconds), 11, binding.channel, binding.controller, binding.onValue]);
        messages.push([tick(event.onsetSeconds + event.durationSeconds), 11, binding.channel, binding.controller, binding.offValue]);
      } else if (event.kind === 'latch') messages.push([tick(event.onsetSeconds), 11, binding.channel, binding.controller, event.value]);
      else if (event.kind === 'envelope') for (const sample of event.samples) messages.push([tick(sample.seconds), 11, binding.channel, binding.controller, sample.value]);
      else fail('Unresolved export');
    }
    if (binding.resetPolicy === 'explicit-final-reset') messages.push([Math.max(0, ...messages.map(x => x[0])) + 1, 11, binding.channel, binding.controller, binding.initialValue]);
  }
  return { division, tempo, messages: sortMessages(messages) };
}

function generation(design, model) {
  if (model.spec.geometry.kind !== 'linear' || model.spec.reader.segmented) fail('Unsupported generation geometry');
  const source = asset(design.sourceRealizationId), parsed = midi(source);
  const layout = JSON.parse(asset(design.layoutRealizationId)), report = JSON.parse(asset(design.reportRealizationId));
  if (layout.modelSHA256 !== model.specSHA256 || report.modelSHA256 !== model.specSHA256 || layout.sourceSHA256 !== hash(source) || report.sourceSHA256 !== hash(source)) fail('Generation lineage mismatch');
  const constraints = model.spec.constraints, excluded = parsed.messages.filter(m => m[1] === 11 || (m[1] === 9 && (m[3] < constraints.minimumTarget || m[3] > constraints.maximumTarget)));
  if (JSON.stringify(report.excludedCommands) !== JSON.stringify(excluded) || (excluded.length && constraints.unsupportedPolicy !== 'explicit-exclusions') || report.adaptations.length || report.fabricated !== false) fail('Undeclared adaptation');
  const starts = new Map(), previous = new Map(), commands = [];
  const anchors = model.spec.timing.anchors.map(a => ({ position: a.seconds, seconds: a.position })).sort((a, b) => a.position - b.position);
  for (const m of parsed.messages) {
    const [tick, command, channel, pitch] = m;
    if (command === 11 || pitch < constraints.minimumTarget || pitch > constraints.maximumTarget) continue;
    const seconds = tick * parsed.tempo / parsed.division / 1e6, key = `${channel}/${pitch}`;
    if (command === 9) {
      if (starts.has(key) || seconds - (previous.get(key) ?? -1e12) < constraints.minimumRepeatSeconds) fail('Generation repetition/voice constraint');
      starts.set(key, seconds); previous.set(key, seconds);
    } else {
      if (!starts.has(key) || seconds <= starts.get(key)) fail('Orphan source note');
      const start = mapping(anchors, starts.get(key)), end = mapping(anchors, seconds);
      if (Math.abs(end - start) < constraints.minimumClearance) fail('Generation clearance constraint');
      commands.push({ channel, target: pitch, start, end }); starts.delete(key);
    }
  }
  if (starts.size || report.acceptedCount !== commands.length || !close(layout.commands, commands, 1e-9)) fail('Recomputed layout mismatch');
  return { designId: design.id, commands };
}

function comparison(record, data) {
  const left = data.interpretations.find(i => i.id === record.leftInterpretationId), right = data.interpretations.find(i => i.id === record.rightInterpretationId);
  const bytes = JSON.parse(asset(record.alignmentRealizationId));
  if (!close(bytes, record.alignment, 0)) fail('Alignment bytes mismatch');
  const anchors = record.alignment.anchors.map(a => ({ position: a.left, seconds: a.right }));
  const usedLeft = new Set(), usedRight = new Set(), residuals = [];
  for (const pair of record.pairs) {
    if (usedLeft.has(pair.leftEventId) || usedRight.has(pair.rightEventId)) fail('Duplicate comparison pair');
    usedLeft.add(pair.leftEventId); usedRight.add(pair.rightEventId);
    const a = left.events.find(e => e.id === pair.leftEventId), b = right.events.find(e => e.id === pair.rightEventId);
    if (!a || !b) fail('Unknown paired event');
    residuals.push(Math.abs(mapping(anchors, a.onsetSeconds) - b.onsetSeconds));
  }
  const coverage = usedLeft.size / Math.max(1, left.events.length), residual = Math.max(0, ...residuals);
  if (Math.abs(record.metrics.matchedCoverage - coverage) > 1e-12 || Math.abs(record.metrics.maxResidualSeconds - residual) > 1e-9 || residual > record.alignment.toleranceSeconds) fail('Comparison metric mismatch');
  return { comparisonId: record.id, matchedCoverage: coverage, maxResidualSeconds: residual };
}

try {
  const ext = manifest.extensions[PROFILE];
  if (!ext) fail('Unsupported MMIC profile');
  const bytes = asset(ext.semanticRealizationId);
  if (!bytes) { console.log(JSON.stringify({ status: 'unmaterialized', preservesUnknown: true })); process.exit(0); }
  const data = JSON.parse(bytes);
  const refs = new Set();
  function dependencies(v) {
    if (Array.isArray(v)) for (const x of v) dependencies(x);
    else if (v && typeof v === 'object') for (const [key, x] of Object.entries(v)) {
      if (key === 'extensions') continue;
      if (key.endsWith('RealizationId') || key === 'realizationId') refs.add(x);
      else if (key.endsWith('RealizationIds') || key === 'realizationIds') for (const id of x) refs.add(id);
      else dependencies(x);
    }
  }
  dependencies(data);
  if ([...refs].some(id => !members.has(id))) { console.log(JSON.stringify({ status: 'unmaterialized', domainSHA256: hash(bytes), preservesUnknown: true })); process.exit(0); }
  const traces = [];
  const designs = data.levels.includes('generation') ? data.designs.map(d => generation(d, data.models.find(m => m.id === d.modelId))) : [];
  const comparisons = data.comparisons.map(c => comparison(c, data));
  for (const interpretation of data.interpretations) {
    const model = data.models.find(m => m.id === interpretation.modelId);
    if (model.spec.reader.segmented || model.spec.geometry.kind === 'undetermined') { console.log(JSON.stringify({ status: 'unsupported', domainSHA256: hash(bytes), preservesUnknown: true })); process.exit(0); }
    for (const event of interpretation.events) {
      if (interpretation.sourceKind !== 'carrier-derived') continue;
      const assignment = data.roleAssignments.find(a => a.id === event.roleAssignmentId);
      const role = model.spec.roles.find(r => r.id === assignment.modelRoleId);
      const feature = data.features.find(f => f.id === event.sourceFeatureIds[0]);
      const track = data.tracks.find(t => t.id === feature.trackId);
      const expected = native(feature, track, role, model.spec);
      if (!close(event, expected, model.spec.timing.toleranceSeconds)) fail('Recomputed native trace mismatch');
      traces.push({ eventId: event.id, ...expected });
    }
    for (const exported of interpretation.exports) {
      const expected = expectedExport(interpretation.events, model.spec.exportBindings, data.roleAssignments, model.spec.roles, exported.bindingIds);
      if (JSON.stringify(midi(asset(exported.realizationId))) !== JSON.stringify(expected)) fail('Selected role/export bytes mismatch');
    }
  }
  console.log(JSON.stringify({ status: 'valid', domainSHA256: hash(bytes), preservesUnknown: true, traces, designs, comparisons,
    physicalCarrierIds: data.carriers.map(c => c.id), partIds: data.parts.map(p => p.id),
    scope: 'Independent JavaScript consumer/reference trace; not the full Python conformance validator or an external maintainer review' }));
} catch (error) {
  console.log(JSON.stringify({ status: 'invalid', error: error.message }));
  process.exitCode = 1;
}
