import copy
import tempfile
import unittest
from pathlib import Path
from runtime_licenses import collect_metadata_licenses, collect_toolchain_licenses

class LicenseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.pkg = self.root / 'dependency'
        self.pkg.mkdir()
        (self.pkg / 'Cargo.toml').write_text('[package]\n')
        self.package = {'id': 'registry+test#dependency@1.0', 'name': 'dependency',
                        'version': '1.0', 'source': 'registry+test',
                        'license': '(MIT OR Apache-2.0) AND Unicode-3.0',
                        'license_file': None, 'manifest_path': str(self.pkg / 'Cargo.toml')}
    def metadata(self, packages=None):
        packages = packages or [self.package]
        return {'packages': packages, 'resolve': {'root': packages[0]['id'],
                'nodes': [{'id': p['id'], 'dependencies': [q['id'] for q in packages[1:]] if i == 0 else []}
                          for i,p in enumerate(packages)]}}
    def collect(self):
        return collect_metadata_licenses([self.metadata()])
    def test_all_alternatives_unicode_and_notice_bytes_preserved(self):
        files = {'LICENSE-MIT': b'MIT evidence', 'LICENSE-APACHE': b'Apache evidence',
                 'LICENSE-UNICODE': 'Unicode Δ'.encode(), 'NOTICE': b'notices exact\n'}
        for name, data in files.items(): (self.pkg / name).write_bytes(data)
        payloads, report = self.collect()
        self.assertEqual(set(payloads.values()), set(files.values()))
        self.assertEqual(report['packages'][0]['declared_license'], self.package['license'])
        self.assertEqual(len(report['packages'][0]['files']), 4)
    def test_missing_evidence_and_notice_only_rejected(self):
        with self.assertRaisesRegex(ValueError, 'missing third-party'): self.collect()
        (self.pkg / 'NOTICE').write_text('Attribution only')
        with self.assertRaisesRegex(ValueError, 'missing third-party license text'): self.collect()
    def test_explicit_license_file(self):
        self.package['license_file'] = 'legal/terms.txt'
        (self.pkg / 'legal').mkdir()
        (self.pkg / 'legal/terms.txt').write_text('actual terms')
        self.assertEqual(len(self.collect()[0]), 1)
    def test_explicit_escape_rejected(self):
        (self.root / 'terms').write_text('outside')
        self.package['license_file'] = '../terms'
        with self.assertRaisesRegex(ValueError, 'escapes'): self.collect()
    def test_symlink_file_and_directory_rejected(self):
        (self.root / 'text').write_text('actual text')
        (self.pkg / 'LICENSE').symlink_to(self.root / 'text')
        with self.assertRaisesRegex(ValueError, 'symlink'): self.collect()
        (self.pkg / 'LICENSE').unlink()
        (self.pkg / 'legal').symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'): self.collect()
    def test_package_collision_rejected(self):
        (self.pkg / 'LICENSE').write_text('license')
        other = copy.deepcopy(self.package)
        other.update(id='registry+other#dependency@1.0', source='registry+other')
        with self.assertRaisesRegex(ValueError, 'collision'):
            collect_metadata_licenses([self.metadata([self.package, other])])
    def test_same_package_deduplicated(self):
        (self.pkg / 'LICENSE').write_text('license')
        payloads, report = collect_metadata_licenses([self.metadata(), self.metadata()])
        self.assertEqual(len(payloads), 1)
        self.assertEqual(len(report['packages']), 1)
    def test_exclusion_is_explicit_root_not_name(self):
        _, report = collect_metadata_licenses([self.metadata()], excluded_roots=[self.pkg])
        self.assertEqual(len(report['excluded_packages']), 1)
        with self.assertRaises(ValueError):
            collect_metadata_licenses([self.metadata()], excluded_roots=[self.root])
    def test_toolchain_gap_explicit(self):
        payloads, report = collect_toolchain_licenses(self.root, 'test rustc')
        self.assertFalse(payloads)
        self.assertEqual(len(report['missing_evidence']), 3)

if __name__ == '__main__': unittest.main()
