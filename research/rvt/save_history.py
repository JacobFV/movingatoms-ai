"""Strict observed History wire codec; episode mutation is not a complete save."""
from dataclasses import dataclass, replace
import struct
from save_increments import Cursor

PROFILES = {1244, 1279, 1309}
GUID_NAMES = ('m_creationGUID', 'm_detachGUID', 'm_upgradeGUID',
              'm_previousUpgradeGUID', 'm_saveAsGUID')


@dataclass(frozen=True)
class History:
    tag: int
    document_pointer: int
    increment_pointer: int
    next_sequence: int
    subsequence_deficit: int
    guids: tuple
    upgrade_versions: tuple
    episodes: tuple


def decode(data):
    c = Cursor(data); tag = c.number('H')
    if tag not in PROFILES: raise ValueError('unsupported History profile')
    document, increment = c.number('I'), c.number('I')
    # Only null and already-referenced pointer tokens have observed fixed widths.
    if document not in (0, 1) or increment not in (0, 1):
        raise ValueError('unsupported History pointer token')
    if c.number('I') != 0: raise ValueError('inline History episodes unsupported')
    next_sequence, deficit = c.number(), c.number()
    guids = tuple(c.take(16) for _ in GUID_NAMES)
    upgrades = tuple(c.number() for _ in range(c.count(4)))
    episodes = tuple(c.take(17) for _ in range(c.count(17)))
    if any(e[16] != 0x28 for e in episodes): raise ValueError('unsupported episode strength')
    if c.take(4) != b'\0'*4 or c.pos != len(data): raise ValueError('invalid History closing marker')
    return History(tag, document, increment, next_sequence, deficit, guids, upgrades, episodes)


def encode(history):
    if len(history.guids) != 5 or any(len(g) != 16 for g in history.guids):
        raise ValueError('invalid History GUID fields')
    if any(len(e) != 17 for e in history.episodes): raise ValueError('invalid episode width')
    try:
        data = (struct.pack('<HIIIii', history.tag, history.document_pointer, history.increment_pointer,
                            0, history.next_sequence, history.subsequence_deficit)
                + b''.join(history.guids) + struct.pack('<I', len(history.upgrade_versions))
                + b''.join(struct.pack('<i', v) for v in history.upgrade_versions)
                + struct.pack('<I', len(history.episodes)) + b''.join(history.episodes) + b'\0'*4)
    except (struct.error, TypeError) as error: raise ValueError('invalid History integer') from error
    if decode(data) != history: raise ValueError('History encode contract failed')
    return data


def prepend_episode(history, guid):
    """Append one chronological ID by prepending its newest-first GUID record.

    Existing IDs retain their reverse-indexed GUID mapping. This operation
    updates only History, not increment records, element revisions or signatures.
    """
    encode(history)
    if len(guid) != 16 or guid == b'\0'*16: raise ValueError('new episode requires nonzero 16-byte GUID')
    if history.next_sequence != len(history.episodes) or history.subsequence_deficit != 0:
        raise ValueError('unsupported History sequence allocation state')
    if guid in (e[:16] for e in history.episodes): raise ValueError('duplicate episode GUID')
    if history.next_sequence == 0x7fffffff: raise ValueError('episode sequence exhausted')
    changed = replace(history, next_sequence=history.next_sequence+1,
                      episodes=(guid+b'\x28',)+history.episodes)
    encode(changed)
    return changed


def root_fields(history):
    def pointer(value, offset): return {'class_tag': None, 'offset': offset, 'pointer_token': value}
    fields = {'m_pADoc': pointer(history.document_pointer, 2),
              'm_pIncrementTable': pointer(history.increment_pointer, 6),
              'm_episodeList': {'m_oEpisodes': []},
              'm_nextLocalSequenceNumber': history.next_sequence,
              'm_subsequenceNumberDeficit': history.subsequence_deficit,
              'm_upgradeVersions': list(history.upgrade_versions)}
    fields.update((name, {'m_guid': {'m_guid': {'guid_bytes': list(g)}}})
                  for name, g in zip(GUID_NAMES, history.guids))
    return fields
