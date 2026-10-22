"""Capture actual browser screenshots of local research reports, with provenance.

These are screenshots of generated evidence pages, never Autodesk/Revit UI.
No network requests, fixture binaries or account credentials are needed.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import html
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
SOURCES=('object-repacking','resized-graph','resized-reader','record-selection',
         'save-increments','signature-analysis','save-history','transport-create',
         'contents-codec','save-candidate-identity','save-candidate-v5-verification',
         'ifc-identity-audit-v5','historical-codec','new-element-registration',
         'create-candidate-registered-verification')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def esc(value):return html.escape(str(value))


def code_hashes():
    paths=list((ROOT/'research/rvt').glob('*.py'))
    paths+=list((ROOT/'research/rvt').glob('*.rs'))
    paths+=list((ROOT/'processing/rvt-native/src').rglob('*.rs'))
    paths+=list((ROOT/'processing/rvt-native/tests').rglob('*.rs'))
    paths += [ROOT/'processing/rvt-native/Cargo.toml', ROOT/'processing/rvt-native/Cargo.lock']
    return {str(p.relative_to(ROOT)):sha(p) for p in sorted(paths) if p.is_file()}


def capture(dest,chrome):
    dest=dest.resolve();dest.mkdir(parents=True,exist_ok=False)
    timestamp=datetime.now(timezone.utc).isoformat()
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    status=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True)
    sources={};values={}
    for name in SOURCES:
        path=ROOT/'research/rvt/results'/f'{name}.json'
        snapshot=path.read_bytes()
        sources[str(path.relative_to(ROOT))]=hashlib.sha256(snapshot).hexdigest()
        values[name]=json.loads(snapshot)
        (dest/path.name).write_bytes(snapshot)
    test_command=['python3','-m','unittest','discover','-s','research/rvt','-p','test_*.py']
    tested_code=code_hashes()
    test=subprocess.run(test_command,cwd=ROOT,capture_output=True,text=True)
    log=test.stdout+test.stderr;(dest/'tests.txt').write_text(log)
    if tested_code!=code_hashes():
        raise RuntimeError('source changed during test run; retry in a fresh capture directory')
    corpus=values['object-repacking'];graph=values['resized-graph'];edit=values['resized-reader']
    routing=values['record-selection']
    style='''body{margin:0;background:#edf1f5;color:#172338;font:19px Arial,sans-serif}main{max-width:1100px;margin:35px auto;padding:35px;background:white;border-top:7px solid #166c61}h1{font-size:34px;margin:12px 0 22px}h2{font-size:23px}small,.label{font-size:14px;color:#536274}table{border-collapse:collapse;width:100%;font-size:17px}td,th{padding:11px;border-bottom:1px solid #dce3e9;text-align:left}.cards{display:flex;gap:20px;margin:20px 0}.card{flex:1;min-width:0;font-size:17px;line-height:1.4;background:#eef7f5;padding:20px}.number{font-size:34px;font-weight:bold}.warning{background:#fff3dc;padding:17px;margin-top:25px}pre{font:15px monospace;white-space:pre-wrap;overflow-wrap:anywhere;background:#eef1f5;padding:16px}footer{font-size:13px;color:#536274;margin-top:24px;overflow-wrap:anywhere}'''
    common=f'<div class="label">RVT CLEAN-ROOM RESEARCH · LOCAL EVIDENCE REPORT</div><small>Captured {esc(timestamp)} · source commit {revision[:12]}</small>'
    warning='<div class="warning"><strong>Acceptance boundary:</strong> no Autodesk open/save test. Signature generation, complete save transactions and new-element creation remain unresolved. This is not a Revit screenshot.</div>'
    rows=''.join(f'<tr><td>{esc(r["file"])}</td><td>{r["object_records"]:,}</td><td>{r["content_groups"]}</td><td>Exact record bodies</td></tr>' for r in corpus)
    summary=common+'<h1>Object reconstruction across six licensed files</h1>'+f'<div class="cards"><div class="card"><div class="number">{sum(x["object_records"] for x in corpus):,}</div>records repacked</div><div class="card"><div class="number">{sum(x["content_groups"] for x in corpus):,}</div>content groups</div><div class="card"><div class="number">{sum(x["exact_episode_routes"] for x in routing):,}</div>exact revision routes</div></div>'+'<table><tr><th>Fixture</th><th>Records</th><th>Groups</th><th>Recorded result</th></tr>'+rows+'</table>'+f'<p>Additional selection evidence: {sum(x["unique_compaction_history_holders"] for x in routing)} unique compaction-history holders; {sum(x["sole_holders_with_unresolved_history"] for x in routing)} sole holders with unexplained history.</p>'+warning
    changed=common+f'<h1>Real room edit: {esc(edit["old"])} → {esc(edit["new"])}</h1><p>RE1 Architecture · room {edit["changed_element"]} · {esc(edit["changed_field"])}</p>'+f'<div class="cards"><div class="card"><div class="number">+{graph["body_growth_bytes"]}</div>serialized bytes</div><div class="card"><div class="number">{graph["complete_objects"]}</div>complete graph objects</div><div class="card"><div class="number">{graph["resolved_pointer_edges"]}</div>resolved pointer edges</div></div>'+f'<p>Independent reader: one changed property among {edit["element_count"]} exported elements. All other graph values and pointer targets preserved.</p><h2>Independent IFC before / after</h2><pre>{esc(edit["ifc_before_line"])}\n{esc(edit["ifc_after_line"])}</pre><h2>Fresh Python regression run · exit {test.returncode}</h2><pre>{esc(log[-1400:])}</pre>'+warning
    save=values['save-increments'];signature=values['signature-analysis']
    rejected=signature['nonempty_private_signature_groups']-signature['structure_true_counts']['ed25519_canonical_s']
    investigations=common+'<h1>Parallel investigations: save tables and signatures</h1>'+f'<div class="cards"><div class="card"><div class="number">{sum(r["increments"]+r["local_increments"] for r in save):,}</div>save records reproduced</div><div class="card"><div class="number">{sum(r["inflated_bytes"] for r in save):,}</div>bytes reproduced exactly</div><div class="card"><div class="number">{signature["nonempty_private_signature_groups"]}</div>nonempty signature fields</div></div>'
    investigations+='<h2>Save-table codec</h2><p>Six licensed files: byte-for-byte reconstruction and field-for-field comparison against the independent schema decoder. Revision advancement and save semantics remain unproven.</p>'
    investigations+=f'<h2>Signature hypotheses tested</h2><p>{rejected} fields fail the necessary scalar bound for standard canonical raw Ed25519 in R || S layout. This excludes that exact interpretation, not transformed encodings.</p><p>{signature["digest_comparisons"]:,} enumerated SHA-512, SHA3-512 and BLAKE2b comparisons; {len(signature["digest_matches"])} matches. Negative tests do not establish keying or identify an algorithm.</p><p>Both observed unsigned groups contain zero elements. No unsigned nonempty source group establishes that removing the signature is accepted.</p>'+warning
    history=values['save-history'];transport=values['transport-create']
    pipeline=common+'<h1>History codec and atomic partition creation</h1>'+f'<div class="cards"><div class="card"><div class="number">{sum(r["episodes"] for r in history):,}</div>History episodes verified</div><div class="card"><div class="number">{sum(r["inflated_bytes"] for r in history):,}</div>History bytes reproduced</div><div class="card"><div class="number">{transport["rust_unit_tests_passed"]+transport["rust_transaction_tests_passed"]}</div>Rust tests passed</div></div>'
    pipeline+='<h2>Complete observed History serialization</h2><p>Six files: all root fields and episode GUID/strength fields independently decoded before and after a guarded prepend. Existing episode identities remain mapped to their original GUIDs.</p>'
    pipeline+=f'<h2>Explicit new-partition transaction</h2><p>Real-file transport control: {transport["independent_olefile_comparison"]["unchanged_original_streams"]} original streams unchanged; one new stream copied byte-for-byte from Partitions/80. Input and output hashes are recorded in transport-create.json.</p><p>Creation requires an absent numeric partition name and an existing parent storage. Output is published only after stream hashes, page framing and original directory metadata pass verification. Existing output files are never overwritten.</p><p>This control does not link the new partition into History, increment tables or element tables. It is not a complete save or a new-element creation test.</p>'+warning
    candidate=values['save-candidate-v5-verification'];identities=values['save-candidate-identity']
    contents=values['contents-codec']
    candidate_rows=''.join('<tr><td>'+esc(row['file'])+'</td><td>'+str(sum(row['relationships'].values()))+' / '+str(len(row['relationships']))+'</td><td>'+('yes' if row['binary_and_text_match_new_increment_and_episode'] else 'no')+'</td></tr>' for row in identities)
    candidate_page=common+'<h1>Append-save candidate: independent checks</h1>'
    candidate_page+=f'<div class="cards"><div class="card"><div class="number">{candidate["reader_element_count"]}</div>elements retained</div><div class="card"><div class="number">{candidate["full_graph"]["complete_objects"]}</div>room graph objects</div><div class="card"><div class="number">{sum(r["rust_inventory"]["parity_pages_verified"]+r["rust_inventory"]["final_pages_verified"] for r in contents)}</div>original pages verified, including Contents</div></div>'
    candidate_page+='<table><tr><th>Preserved candidate</th><th>Text / Contents checks</th><th>Binary identity updated</th></tr>'+candidate_rows+'</table>'
    candidate_page+=f'<p>Current room route: {esc(candidate["current_record_before"])} → {esc(candidate["current_record_after"])}. Native UniqueId and derived element IFC GUID are unchanged. The requested finish edit is the only graph value change.</p>'
    candidate_page+=f'<h2>IFC projection: cause isolated and adapter tested</h2><p>Default exporter: {sum(candidate["ifc_identifier_only_changes"].values())} generated ID changes. Explicit persistent namespace: {values["ifc-identity-audit-v5"]["explicit_stable_namespace_projection"]["identifier_change_count"]} ID changes; only the intended finish and source-stream lines differ. Native IDs are preserved.</p>'
    candidate_page+='<p><strong>v5 synchronizes all four counter copies and four GUID copies.</strong> Reversing the BasicFileInfo edit restores original bytes exactly. Unsigned partition acceptance and ancillary save revisions remain unproven. All five controls retain hashes and independent results.</p><pre>Latest candidate SHA-256: '+esc(candidate['candidate_sha256'])+'</pre>'+warning
    historical=values['historical-codec']['files']
    noncanonical=sum(not s['canonical_encoding_equals_source'] for f in historical for s in f['streams'])
    historical_page=common+'<h1>Historical corpus: verified layout extension</h1>'
    historical_page+=f'<div class="cards"><div class="card"><div class="number">{len(historical)}</div>licensed files</div><div class="card"><div class="number">{sum(f["rust_inventory"]["parity_pages_verified"]+f["rust_inventory"]["final_pages_verified"] for f in historical):,}</div>pages verified</div><div class="card"><div class="number">{noncanonical}</div>streams outside default encoder policy</div></div>'
    historical_page+='<table><tr><th>File</th><th>Full pages</th><th>Final pages</th></tr>'+''.join(f'<tr><td>{esc(f["file"])}</td><td>{f["rust_inventory"]["parity_pages_verified"]}</td><td>{f["rust_inventory"]["final_pages_verified"]}</td></tr>' for f in historical)+'</table>'
    historical_page+='<p>Both decoders agree on every logical byte. Every source layout reproduces exactly with its detected dimensions. Default encoder output agrees across languages and roundtrips, but does not reproduce nine historical layouts.</p><p>Unchanged streams and no-op logical patches preserve original bytes. Alternative output layout acceptance is untested.</p>'+warning
    created=values['create-candidate-registered-verification'];registration=values['new-element-registration']
    creation_page=common+'<h1>Fresh native DataStorage: registered candidate</h1>'
    creation_page+=f'<div class="cards"><div class="card"><div class="number">{created["new_native_identity"]["element_id"]}</div>new element ID</div><div class="card"><div class="number">{created["prior_native_identities_preserved"]:,}</div>existing identities preserved</div><div class="card"><div class="number">{len(registration["changes"])}</div>known registration lists updated</div></div>'
    creation_page+='<table><tr><th>Record channel</th><th>Bytes</th><th>Complete objects / edges</th></tr>'+''.join(f'<tr><td>{esc(k)}</td><td>{v["bytes"]}</td><td>{v["objects"]} / {v["edges"]}</td></tr>' for k,v in sorted(created['new_channels'].items()))+'</table>'
    creation_page+=f'<p>Fresh bodies are encoded from named values and file-local schema declarations. Positive element references are self-only; the new storage GUID is absent from the source DataStorage inventory.</p><p>Global/Latest: {registration["objects_after"]} objects and {registration["edges_after"]} edges independently decoded. Exactly three ID-list insertions; +{registration["byte_growth"]} bytes. All other semantic graph values match.</p>'
    creation_page+='<p>BasicFileInfo identity copies agree. The candidate preserves original partitions and all existing native identities. A retained unregistered control demonstrates why element extraction alone misses document registrations.</p><pre>Candidate SHA-256: '+esc(created['candidate_sha256'])+'</pre>'
    creation_page+='<div class="warning"><strong>Scope:</strong> a non-geometric DataStorage element in one measured 2024 profile, using existing ES schemas. All registration rules, signatures, complete native save semantics and Autodesk acceptance remain unproven. This is not a Revit screenshot.</div>'
    browser_version=subprocess.check_output([chrome,'--version'],text=True).strip()
    with tempfile.TemporaryDirectory(prefix='rvt-evidence-browser-') as profile:
        for name,body in [('corpus',summary),('room-edit',changed),('investigations',investigations),('save-pipeline',pipeline),('save-candidate',candidate_page),('historical-layouts',historical_page),('element-creation',creation_page)]:
            page=dest/f'{name}.html';page.write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>RVT research evidence</title><style>'+style+'</style><main>'+body+f'<footer>Source JSON copies and SHA-256 provenance are stored beside this capture. Browser: {esc(browser_version)}.</footer></main></html>')
            args=[chrome,'--headless','--no-sandbox','--disable-gpu','--disable-background-networking','--no-first-run',f'--user-data-dir={profile}','--hide-scrollbars','--window-size=1280,1100',f'--screenshot={dest/name}.png',page.as_uri()]
            subprocess.run(args,check=True,capture_output=True,text=True,timeout=45)
    artifacts={p.name:sha(p) for p in sorted(dest.iterdir()) if p.is_file()}
    manifest={'captured_at_utc':timestamp,'source_commit':revision,'working_tree_status':status,
              'browser':browser_version,'capture_type':'actual headless-browser screenshot of local generated research report',
              'not_autodesk_ui':True,'sources':sources,'test_command':test_command,'test_exit_code':test.returncode,
              'tested_code_sha256':tested_code,
              'generator_sha256':sha(Path(__file__)),'artifacts':artifacts}
    (dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    if test.returncode:raise RuntimeError('regression tests failed; evidence retained')
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path)
    p.add_argument('--chrome',default=shutil.which('google-chrome') or shutil.which('chromium'))
    a=p.parse_args()
    if not a.chrome:p.error('Chrome/Chromium executable required')
    result=capture(a.destination,a.chrome)
    print(json.dumps({'captured_at_utc':result['captured_at_utc'],'test_exit_code':result['test_exit_code'],'artifacts':list(result['artifacts'])}))
