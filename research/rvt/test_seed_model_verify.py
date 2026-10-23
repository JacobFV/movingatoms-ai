"""Independent geometry and prebuilt-probe provenance controls."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from seed_model_verify import sha,triangle_multiset,validated_prebuilt_probes


class SeedModelVerifierTests(unittest.TestCase):
    def test_oriented_geometry_accepts_reindexing_but_rejects_winding_or_loss(self):
        original=[{'vertices':[[0,0,0],[1,0,0],[0,1,0]],'triangles':[[0,1,2]]}]
        reindexed=[{'vertices':[[0,1,0],[0,0,0],[1,0,0]],'triangles':[[1,2,0]]}]
        self.assertEqual(triangle_multiset(original),triangle_multiset(reindexed))
        reversed_face=deepcopy(original);reversed_face[0]['triangles']=[[0,2,1]]
        self.assertNotEqual(triangle_multiset(original),triangle_multiset(reversed_face))
        self.assertNotEqual(triangle_multiset(original),triangle_multiset([]))
        self.assertNotEqual(triangle_multiset(original),triangle_multiset(original*2))

    def test_prebuilt_probes_bind_revision_source_and_executable_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            sources={'index':b'index source','scene':b'scene source'}
            paths={name:Path(directory)/name for name in sources}
            for name,path in paths.items():path.write_bytes(name.encode())
            config={**paths,'reader_revision':'pinned','source_sha256':{n:sha(v)for n,v in sources.items()},'binary_sha256':{n:sha(p.read_bytes())for n,p in paths.items()}}
            self.assertEqual(validated_prebuilt_probes(config,sources,'pinned'),paths)
            for field in ('reader_revision','source_sha256','binary_sha256'):
                bad=deepcopy(config)
                if field=='reader_revision':bad[field]='other'
                else:bad[field]['scene']='0'*64
                with self.subTest(field=field),self.assertRaisesRegex(ValueError,'provenance|hash'):
                    validated_prebuilt_probes(bad,sources,'pinned')
            paths['index'].write_bytes(b'changed executable')
            with self.assertRaisesRegex(ValueError,'hash'):
                validated_prebuilt_probes(config,sources,'pinned')


if __name__=='__main__':unittest.main()
