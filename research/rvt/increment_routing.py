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


def select_record(episode,increments,present,holders):
    """Select only with an exact route, unique compaction holder, or sole holder.

    Partial compaction is an evidence-based extension: a chronological version
    names a later causing increment but does not redirect the entire residual
    population. When the initial route lacks the ID, follow those explicit
    causal links. Never choose between multiple reachable physical holders.
    The single-holder case establishes uniqueness, not its historical cause.
    """
    holders=set(holders)
    if not holders or not holders.issubset(present):raise ValueError('missing/invalid record holders')
    initial=route(episode,increments,present)
    if initial in holders:return initial,'exact_episode_route'
    reachable=set();queue=[initial]
    while queue:
        index=queue.pop()
        if index in reachable:continue
        reachable.add(index)
        row=increments[index]
        previous_cause=-2;previous_count=None
        for cause,count in row['redirects']:
            if (cause< -1 or cause<=previous_cause or (cause!=-1 and not index<cause<len(increments))
                    or count<0 or (previous_count is not None and count>previous_count)):
                raise ValueError('invalid partial-compaction history')
            previous_cause,previous_count=cause,count
            if cause>=0:queue.append(cause)
        if row['redirects'] and row['redirects'][-1][1]!=row['stored_elements']:
            raise ValueError('partial-compaction terminal count mismatch')
    candidates=holders & reachable
    if len(candidates)==1:return next(iter(candidates)),'unique_compaction_history_holder'
    if len(candidates)>1:raise ValueError('multiple compaction-history holders')
    if len(holders)==1:return next(iter(holders)),'sole_physical_holder_history_unresolved'
    raise ValueError('ambiguous holders outside explicit compaction history')
