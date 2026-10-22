import unittest
from signature_history import differences


class EnvelopeDifferenceTests(unittest.TestCase):
    def baseline(self):
        return {key:0 for key in ('root_tag','count','content_key','public_field',
            'member_layout','gzip_headers','inflated_sha256','gzip_sha256',
            'deflate_sha256','member_blocks_sha256','group_index','is_last_group',
            'partition_payload_sha256','stream')}

    def test_equal_inflation_does_not_hide_gzip_header_difference(self):
        left=self.baseline();right=dict(left)
        right.update(gzip_headers=1,gzip_sha256=1,member_blocks_sha256=1,partition_payload_sha256=1)
        self.assertEqual(differences(left,right),['gzip_headers','gzip_sha256','member_blocks_sha256','partition_payload_sha256'])

    def test_context_difference_is_reported(self):
        left=self.baseline();right=dict(left)
        right.update(content_key=1,is_last_group=1,stream=1)
        self.assertEqual(differences(left,right),['content_key','is_last_group','stream'])


if __name__=='__main__':unittest.main()
