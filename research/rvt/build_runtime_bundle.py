"""Build/validate/run an offline experimental RVT bundle; never enable production."""
import argparse,ast,ctypes,hashlib,json,os,platform,re,shutil,struct,subprocess,sys,tempfile
from pathlib import Path,PurePosixPath
REV='b6086d41b9758fd9b92f42f0a47b8345b9c58056'
SEED_SHA='674d9b621e599293faa07c1ca96ab3ba4ce8fc3c311e1f873ab0da6cea1ae3fe'
SEED_LICENSE_SHA='47479541ef4e0cef78174f121d2408cd9ea4a9c3182ff2699eb0c002943b23f8'
PROFILES=('seed_save_context.json','seed_level-profile.json','seed_categories.json','directshape-mesh-profile.json','directshape_legacy_audit.json','directshape_current.json')
PROBE_FILES=('element_properties_probe.rs','wall_candidate_probe.rs','seed_directshape_probe.rs')
MACHINES={62:'x86_64',183:'aarch64'}

def sha(data):return hashlib.sha256(data).hexdigest()
def closure(directory,roots):
    pending=list(roots);found=set()
    while pending:
        name=pending.pop()
        if name in found:continue
        path=directory/(name+'.py')
        if not path.is_file():raise ValueError('missing runtime entry module: '+name)
        found.add(name)
        for node in ast.walk(ast.parse(path.read_bytes())):
            mods=[a.name.split('.')[0]for a in node.names]if isinstance(node,ast.Import)else [node.module.split('.')[0]]if isinstance(node,ast.ImportFrom)and node.module else []
            pending.extend(m for m in mods if (directory/(m+'.py')).is_file())
    return sorted(found)
def elf_arch(data):
    if len(data)<20 or data[:6]!=b'\x7fELF\x02\x01':raise ValueError('requires little-endian64-bit ELF')
    machine=struct.unpack_from('<H',data,18)[0]
    if machine not in MACHINES:raise ValueError('unsupported ELF machine')
    return MACHINES[machine]
def version_tuple(value):
    if not isinstance(value,str)or not re.fullmatch(r'\d+(?:\.\d+)+',value):raise ValueError('invalid runtime version')
    return tuple(map(int,value.split('.')))
def binary_dependencies(path):
    dynamic=subprocess.check_output(['readelf','--dynamic',str(path)],text=True)
    versions=subprocess.check_output(['readelf','--version-info',str(path)],text=True)
    libraries=sorted(set(re.findall(r'Shared library: \[([^\]]+)\]',dynamic)))
    glibc=re.findall(r'Name: GLIBC_(\d+(?:\.\d+)+)',versions)
    if not libraries or not glibc:raise ValueError('unmeasured static/non-glibc executable')
    return {'needed_libraries':libraries,'minimum_glibc':max(glibc,key=version_tuple)}
def compatible_host(dependencies):
    libc,version=platform.libc_ver()
    if libc!='glibc':raise ValueError('measured runtime requires glibc')
    if version_tuple(version)<version_tuple(dependencies['minimum_glibc']):raise ValueError('host glibc is older than required symbols')
    libraries=dependencies['needed_libraries']
    if not libraries or libraries!=sorted(set(libraries)):raise ValueError('invalid dependency inventory')
    for name in libraries:
        if not isinstance(name,str)or not re.fullmatch(r'[A-Za-z0-9_+.-]+\.so(?:\.[0-9]+)*',name):raise ValueError('plain shared-library SONAME required')
        try:ctypes.CDLL(name)
        except OSError as error:raise ValueError('missing runtime dependency: '+name)from error

def safe_path(root,name):
    if not isinstance(name,str):raise ValueError('unsafe bundle path')
    p=PurePosixPath(name)
    if not name or p.is_absolute()or '..'in p.parts or str(p)!=name:raise ValueError('unsafe bundle path')
    target=root.joinpath(*p.parts)
    if target.is_symlink()or any(x.is_symlink()for x in target.parents if x!=root.parent):raise ValueError('bundle symlink forbidden')
    return target

def validate_bundle(root,*,check_host=True):
    root=Path(root).resolve();manifest=json.loads((root/'manifest.json').read_bytes())
    if manifest.get('schema')!='ma-experimental-rvt-runtime/1'or manifest.get('reader_revision')!=REV or manifest.get('production_enabled')is not False:raise ValueError('unsupported runtime manifest')
    if manifest.get('seed_sha256')!=SEED_SHA:raise ValueError('unexpected seed pin')
    payloads=manifest['payloads']
    if any(p.is_symlink()for p in root.rglob('*')):raise ValueError('bundle symlink forbidden')
    actual={p.relative_to(root).as_posix()for p in root.rglob('*')if p.is_file()and p.relative_to(root).as_posix()!='manifest.json'}
    if actual!=set(payloads):raise ValueError('bundle payload inventory differs')
    for name,entry in payloads.items():
        path=safe_path(root,name)
        if not path.is_file()or sha(path.read_bytes())!=entry['sha256']or path.stat().st_size!=entry['bytes']:raise ValueError('bundle payload hash differs: '+name)
        if name.startswith('bin/'):
            if elf_arch(path.read_bytes())!=manifest['architecture']or not os.access(path,os.X_OK):raise ValueError('binary architecture/mode differs')
    if sha((root/'assets/minimal-seed.rvt').read_bytes())!=SEED_SHA:raise ValueError('seed bytes differ')
    if check_host and (sys.platform!='linux'or platform.machine()!=manifest['architecture']):raise ValueError('bundle architecture does not match this host')
    if check_host and sys.version_info[:2]!=(3,12):raise ValueError('runtime requires measured Python3.12')
    if check_host:
        if set(manifest['binary_dependencies'])!={PurePosixPath(n).name for n in payloads if n.startswith('bin/')}:raise ValueError('missing binary dependency checks')
        for item in manifest['binary_dependencies'].values():compatible_host(item)
    return manifest

def run_bundle(root,request,output,*,acknowledge_hypotheses=False):
    if not acknowledge_hypotheses:raise ValueError('explicit experimental hypothesis acknowledgment required')
    root=Path(root).resolve();manifest=validate_bundle(root)
    sys.dont_write_bytecode=True
    sys.path.insert(0,str(root/'runtime'))
    # The bundle is validated before importing any authoring or verifier code.
    from seed_model_experiment import run
    props=manifest['probes']['properties'];probes=manifest['probes']
    runtime={'reader_revision':REV,'properties_probe':{'path':root/props['path'],'sha256':props['sha256'],'source_sha256':props['source_sha256'],'reader_revision':REV},
      'verifier_probes':{'index':root/probes['index']['path'],'scene':root/probes['scene']['path'],'reader_revision':REV,
        'source_sha256':{k:probes[k]['source_sha256']for k in ('index','scene')},'binary_sha256':{k:probes[k]['sha256']for k in ('index','scene')}}}
    result=run(root/'assets/minimal-seed.rvt',Path(output),Path(request),None,Path(output).parent/'.runtime-unused-target',root/'bin/ma-rvt-native',acknowledge_hypotheses=True,runtime=runtime)
    validate_bundle(root);return result

def build_bundle(dest,reader,seed,cache,*,olefile_license):
    here=Path(__file__).resolve().parent;repo=here.parent.parent;dest=Path(dest).resolve();reader=Path(reader).resolve();cache=Path(cache).resolve()
    if dest.exists():raise FileExistsError(dest)
    if subprocess.check_output(['git','-C',str(reader),'rev-parse','HEAD'],text=True).strip()!=REV:raise ValueError('reader revision differs')
    subprocess.run(['git','-C',str(reader),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock','LICENSE','NOTICE'],check=True)
    if sha(Path(seed).read_bytes())!=SEED_SHA:raise ValueError('seed hash differs')
    modules=closure(here,['seed_model_experiment','seed_model','seed_model_verify','seed_metadata_audit','build_runtime_bundle'])
    sources={name: (here/(name+'.py')).read_bytes()for name in modules}
    inputs={f'runtime/{name}.py':raw for name,raw in sources.items()}
    inputs.update({f'runtime/results/{n}':(here/'results'/n).read_bytes()for n in PROFILES})
    inputs.update({f'runtime/{n}':(here/n).read_bytes()for n in PROBE_FILES})
    inputs['assets/minimal-seed.rvt']=Path(seed).read_bytes()
    probe_lock=(here/'runtime-probes.Cargo.lock').read_bytes()
    inputs['runtime/runtime-probes.Cargo.lock']=probe_lock
    license_bytes=(here/'results/minimal_seed-ricaun-io-LICENSE.txt').read_bytes()
    if sha(license_bytes)!=SEED_LICENSE_SHA:raise ValueError('seed license hash differs')
    inputs['notices/seed-MIT-LICENSE.txt']=license_bytes
    for name in ('LICENSE','NOTICE'):
        expected=subprocess.check_output(['git','-C',str(reader),'show',REV+':'+name])
        if (reader/name).read_bytes()!=expected:raise ValueError('reader notice differs from pinned git object')
        inputs['notices/reader-'+name+'.txt']=expected
    # Vendor the installed pure Python olefile; retain its own source notices and
    # require a supplied full license text, rather than guessing its location.
    import olefile
    ole_dir=Path(olefile.__file__).parent
    for name in ('__init__.py','olefile.py'):inputs['runtime/olefile/'+name]=(ole_dir/name).read_bytes()
    lic=Path(olefile_license).read_bytes()
    if b'Copyright'not in lic or b'Redistribution'not in lic:raise ValueError('olefile copyright/license text required')
    inputs['notices/olefile-LICENSE.txt']=lic
    inputs['notices/transport-Cargo.toml']=(repo/'processing/rvt-native/Cargo.toml').read_bytes()
    inputs['notices/README.txt']=b'Experimental internal runtime. Reader: Apache-2.0 LICENSE/NOTICE retained. Published seed: ricaun MIT license retained. olefile: bundled source and supplied license retained. Transport Cargo.toml declares MIT; this repository has no standalone transport LICENSE text. No Autodesk acceptance or production support is claimed.\n'
    from seed_model_verify import expected_probe_sources
    from runtime_licenses import collect_runtime_licenses
    probe_sources=expected_probe_sources();probe_sources['properties']=inputs['runtime/element_properties_probe.rs']
    dest.parent.mkdir(parents=True,exist_ok=True);cache.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='rvt-runtime-build-',dir=dest.parent)as temp:
        temp=Path(temp);project=temp/'probe';(project/'src').mkdir(parents=True)
        cargo='[package]\nname="ma-runtime-probes"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(reader))+'}\nserde_json="=1.0.154"\n'
        names={'properties':'rvt-element-properties-probe','index':'seed-model-index','scene':'seed-model-scene'}
        for key,raw in probe_sources.items():
            (project/'src'/f'{key}.rs').write_bytes(raw);cargo+=f'[[bin]]\nname="{names[key]}"\npath="src/{key}.rs"\n'
        (project/'Cargo.toml').write_text(cargo)
        (project/'Cargo.lock').write_bytes(probe_lock)
        subprocess.run(['cargo','build','--release','--locked','--offline','--manifest-path',str(project/'Cargo.toml'),'--target-dir',str(cache/'probes')],check=True)
        subprocess.run(['cargo','build','--release','--locked','--offline','--manifest-path',str(repo/'processing/rvt-native/Cargo.toml'),'--target-dir',str(cache/'transport')],check=True)
        inputs['provenance/probes-Cargo.lock']=(project/'Cargo.lock').read_bytes();inputs['provenance/transport-Cargo.lock']=(repo/'processing/rvt-native/Cargo.lock').read_bytes()
        license_payloads,license_report=collect_runtime_licenses([project/'Cargo.toml',repo/'processing/rvt-native/Cargo.toml'],excluded_roots=[project,repo/'processing/rvt-native'])
        if license_report['toolchain']['missing_evidence']:raise ValueError('Rust toolchain license evidence missing')
        if set(inputs)&set(license_payloads):raise ValueError('license payload path collision')
        inputs.update(license_payloads)
        inputs['notices/rust-dependencies.json']=(json.dumps(license_report,indent=2)+'\n').encode()
        inputs['bin/ma-rvt-native']=(cache/'transport/release/ma-rvt-native').read_bytes()
        probes={}
        for key,name in names.items():
            relative='bin/'+name;inputs[relative]=(cache/'probes/release'/name).read_bytes();probes[key]={'path':relative,'sha256':sha(inputs[relative]),'source_sha256':sha(probe_sources[key])}
        dependencies={'ma-rvt-native':binary_dependencies(cache/'transport/release/ma-rvt-native')}
        dependencies.update({name:binary_dependencies(cache/'probes/release'/name)for name in names.values()})
        arch=elf_arch(inputs['bin/ma-rvt-native'])
        if arch!=platform.machine()or any(elf_arch(v)!=arch for k,v in inputs.items()if k.startswith('bin/')):raise ValueError('mixed or cross architecture binaries unsupported')
        # Refuse a moving code snapshot after compilation.
        if (here/'runtime-probes.Cargo.lock').read_bytes()!=probe_lock or (project/'Cargo.lock').read_bytes()!=probe_lock:raise ValueError('pinned probe dependency lock changed')
        if any((here/(name+'.py')).read_bytes()!=raw for name,raw in sources.items())or expected_probe_sources()!= {k:v for k,v in probe_sources.items()if k!='properties'} or (here/'element_properties_probe.rs').read_bytes()!=probe_sources['properties']:raise ValueError('runtime sources changed during build')
        inputs['run.py']=b'import runpy,sys\nsys.dont_write_bytecode=True\nfrom pathlib import Path\nroot=Path(__file__).resolve().parent\nsys.argv=[str(root/"runtime/build_runtime_bundle.py"),"run",str(root),*sys.argv[1:]]\nrunpy.run_path(str(root/"runtime/build_runtime_bundle.py"),run_name="__main__")\n'
        stage=temp/'bundle';stage.mkdir()
        for name,raw in inputs.items():
            path=stage/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            if name.startswith('bin/'):path.chmod(0o755)
        manifest={'schema':'ma-experimental-rvt-runtime/1','reader_revision':REV,'seed_sha256':SEED_SHA,'architecture':arch,'python':'3.12','build_libc':platform.libc_ver(),'binary_dependencies':dependencies,
            'production_enabled':False,'autodesk_acceptance':'not_tested','rust_license_packages':len(license_report['packages']),'rust_license_manifest':'notices/rust-dependencies.json','olefile_version':olefile.__version__,'modules':modules,'profiles':list(PROFILES),'probes':probes,
            'payloads':{name:{'sha256':sha(raw),'bytes':len(raw)}for name,raw in sorted(inputs.items())}}
        (stage/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');validate_bundle(stage)
        if dest.exists():raise FileExistsError(dest)
        stage.rename(dest)
    return manifest

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    b=sub.add_parser('build');b.add_argument('dest',type=Path);b.add_argument('--reader',type=Path,required=True);b.add_argument('--seed',type=Path,required=True);b.add_argument('--cache',type=Path,required=True);b.add_argument('--olefile-license',type=Path,required=True)
    v=sub.add_parser('verify');v.add_argument('bundle',type=Path)
    r=sub.add_parser('run');r.add_argument('bundle',type=Path);r.add_argument('--request',type=Path,required=True);r.add_argument('--output',type=Path,required=True);r.add_argument('--acknowledge-hypotheses',action='store_true')
    a=p.parse_args()
    if a.command=='build':result=build_bundle(a.dest,a.reader,a.seed,a.cache,olefile_license=a.olefile_license);print(json.dumps({'architecture':result['architecture'],'payloads':len(result['payloads'])}))
    elif a.command=='verify':result=validate_bundle(a.bundle);print(json.dumps({'verified':True,'architecture':result['architecture']}))
    else:result=run_bundle(a.bundle,a.request,a.output,acknowledge_hypotheses=a.acknowledge_hypotheses);print(json.dumps({'status':result['status'],'candidate_sha256':result['candidate_sha256']}))
if __name__=='__main__':main()
