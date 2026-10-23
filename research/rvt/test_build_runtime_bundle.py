import json,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import build_runtime_bundle as b

class RuntimeBundleTests(unittest.TestCase):
    def fixture(self,root):
        seed=b'test seed';binary=bytearray(32);binary[:6]=b'\x7fELF\x02\x01';struct.pack_into('<H',binary,18,183)
        files={'assets/minimal-seed.rvt':seed,'bin/probe':bytes(binary),'runtime/main.py':b'pass\n'}
        for name,raw in files.items():
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
            if name.startswith('bin/'):p.chmod(0o755)
        manifest={'schema':'ma-experimental-rvt-runtime/1','reader_revision':b.REV,'seed_sha256':b.sha(seed),'architecture':'aarch64','production_enabled':False,'payloads':{n:{'sha256':b.sha(v),'bytes':len(v)}for n,v in files.items()}}
        (root/'manifest.json').write_text(json.dumps(manifest));return b.sha(seed)
    def test_inventory_and_payload_integrity(self):
        for variant in ('valid','nested_manifest','cache','missing','altered_binary','symlink','symlink_directory'):
            with self.subTest(variant=variant),tempfile.TemporaryDirectory()as d:
                root=Path(d);seedsha=self.fixture(root)
                if variant=='nested_manifest':(root/'runtime/manifest.json').write_text('{}')
                if variant=='cache':(root/'runtime/cache.pyc').write_bytes(b'bad')
                if variant=='missing':(root/'bin/probe').unlink()
                if variant=='altered_binary':(root/'bin/probe').write_bytes(b'broken')
                if variant=='symlink':
                    (root/'runtime/main.py').unlink();(root/'runtime/main.py').symlink_to(root/'assets/minimal-seed.rvt')
                if variant=='symlink_directory':(root/'unlisted').symlink_to(root/'assets',target_is_directory=True)
                with patch.object(b,'SEED_SHA',seedsha):
                    if variant=='valid':self.assertEqual(b.validate_bundle(root,check_host=False)['architecture'],'aarch64')
                    else:
                        with self.assertRaises(ValueError):b.validate_bundle(root,check_host=False)
    def test_unsafe_paths(self):
        with tempfile.TemporaryDirectory()as d:
            for name in ('../escape','/etc/passwd','a/../b','a//b'):
                with self.subTest(name=name),self.assertRaises(ValueError):b.safe_path(Path(d),name)
    def test_elf_and_compatibility(self):
        with self.assertRaises(ValueError):b.elf_arch(b'not ELF')
        good={'minimum_glibc':'2.34','needed_libraries':['libc.so.6','libgcc_s.so.1']}
        with patch.object(b.platform,'libc_ver',return_value=('glibc','2.39')),patch.object(b.ctypes,'CDLL')as loader:
            b.compatible_host(good);self.assertEqual(loader.call_count,2)
            with self.assertRaises(ValueError):b.compatible_host({**good,'needed_libraries':['../../evil.so']})
        with patch.object(b.platform,'libc_ver',return_value=('glibc','2.33')):
            with self.assertRaises(ValueError):b.compatible_host(good)
        with patch.object(b.platform,'libc_ver',return_value=('musl','1.2')):
            with self.assertRaises(ValueError):b.compatible_host(good)
    def test_build_refuses_existing_destination_before_compiling(self):
        with tempfile.TemporaryDirectory()as d,patch.object(b.subprocess,'run')as call:
            with self.assertRaises(FileExistsError):b.build_bundle(Path(d),Path('/absent'),Path('/absent'),Path('/absent'),olefile_license=Path('/absent'))
            call.assert_not_called()
    def test_closure_excludes_unreachable_files(self):
        with tempfile.TemporaryDirectory()as d:
            root=Path(d);(root/'entry.py').write_text('from useful import run\n');(root/'useful.py').write_text('def run(): pass\n');(root/'unrelated.py').write_text('import missing\n')
            self.assertEqual(b.closure(root,['entry']),['entry','useful'])

if __name__=='__main__':unittest.main()
