# SPDX-License-Identifier: Apache-2.0
# Adapted from rvt-rs native_index.rs, Copyright 2026 Griffin Long.
# Changes: Python implementation; rejects permutations; no fallback routing.
# See licenses/rvt-rs-Apache-2.0.txt and licenses/rvt-rs-NOTICE.txt.
"""Resolve modification episodes through observed chronological increment routes.

Ordinal routing follows the pinned public reader's native_index contract.
No highest-stream fallback is used: missing routed records stay unresolved.
"""

def route(episode,increments,present):
    if not isinstance(episode,int) or episode<0:raise ValueError('invalid episode')
    if any(r.get('episode_permutation') for r in increments):
        raise ValueError('episode permutations require a separate routing contract')
    if any(r['stored_elements']<0 for r in increments):raise ValueError('negative stored count')
    initial=next((i for i,r in enumerate(increments) if r['greatest_episode']>=episode),None)
    if initial is None:raise ValueError('episode outside increment ranges')
    index=initial;seen=set()
    while index not in seen:
        seen.add(index)
        if not 0<=index<len(increments):raise ValueError('redirect outside increment table')
        row=increments[index];previous_cause=-2;previous_count=None
        for cause,count in row['redirects']:
            if (cause< -1 or cause<=previous_cause or (cause!=-1 and not index<cause<len(increments))
                    or count<0 or (previous_count is not None and count>previous_count)):
                raise ValueError('invalid chronological redirect history')
            previous_cause,previous_count=cause,count
        if row['redirects'] and row['redirects'][-1][1]!=row['stored_elements']:
            raise ValueError('terminal redirect count differs from stored count')
        if row['stored_elements']>0:
            if index not in present:raise ValueError('active increment stream absent')
            return index
        if not row['redirects']:raise ValueError('empty increment lacks redirect')
        target,count=row['redirects'][-1]
        if count!=0 or target<=index:raise ValueError('invalid terminal redirect')
        index=target
    raise ValueError('increment redirect cycle')
