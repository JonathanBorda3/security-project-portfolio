#!/usr/bin/env python3

# BGP Measurements - analyzing real-world BGP routing data using pybgpstream
# Parses MRT/RIB dumps from RIPE NCC route collectors to extract routing metrics

import pybgpstream


def unique_prefixes_by_snapshot(cache_files):
    """Count unique IP prefixes advertised in each BGP RIB snapshot."""
    results = []

    for fpath in cache_files:
        stream = pybgpstream.BGPStream(data_interface="singlefile")
        stream.set_data_interface_option("singlefile", "rib-file", fpath)

        prefixes = set()
        for elem in stream:
            prefix = elem.fields.get("prefix")
            if prefix:
                prefixes.add(prefix)

        results.append(len(prefixes))

    return results


def unique_ases_by_snapshot(cache_files):
    """Count unique autonomous systems seen in each BGP RIB snapshot."""
    results = []

    for fpath in cache_files:
        stream = pybgpstream.BGPStream(data_interface="singlefile")
        stream.set_data_interface_option("singlefile", "rib-file", fpath)

        ases = set()
        for elem in stream:
            as_path = elem.fields.get("as-path", "")
            if not as_path:
                continue
            for token in as_path.split():
                ases.add(token)

        results.append(len(ases))

    return results


def top_10_ases_by_prefix_growth(cache_files):
    """Find the top 10 origin ASes by percentage growth in advertised prefixes.
    Returns them sorted smallest to largest growth."""
    origin_to_snapshot_prefixes = {}
    num_snapshots = len(cache_files)

    for ndx, fpath in enumerate(cache_files):
        stream = pybgpstream.BGPStream(data_interface="singlefile")
        stream.set_data_interface_option("singlefile", "rib-file", fpath)

        for elem in stream:
            prefix = elem.fields.get("prefix")
            as_path = elem.fields.get("as-path", "")
            if not prefix or not as_path:
                continue

            tokens = as_path.split()
            if not tokens:
                continue
            origin = tokens[-1]

            if origin not in origin_to_snapshot_prefixes:
                origin_to_snapshot_prefixes[origin] = {}
            if ndx not in origin_to_snapshot_prefixes[origin]:
                origin_to_snapshot_prefixes[origin][ndx] = set()
            origin_to_snapshot_prefixes[origin][ndx].add(prefix)

    growth = {}
    for origin, snap_map in origin_to_snapshot_prefixes.items():
        first_snap = min(snap_map.keys())
        first_count = len(snap_map[first_snap])
        last_count = len(snap_map.get(num_snapshots - 1, set()))
        if first_count == 0:
            continue
        pct = (last_count - first_count) / first_count
        growth[origin] = pct

    sorted_origins = sorted(growth.items(), key=lambda kv: (kv[1], int(kv[0]) if kv[0].isdigit() else 0), reverse=True)
    top_10 = [origin for origin, _ in sorted_origins[:10]]
    return list(reversed(top_10))


def shortest_path_by_origin_by_snapshot(cache_files):
    """For every origin AS, find the shortest AS-path length in each snapshot.
    Uses global dedup (unique ASes in path) and skips single-hop paths."""
    num_snapshots = len(cache_files)
    per_snapshot = [dict() for _ in range(num_snapshots)]

    for ndx, fpath in enumerate(cache_files):
        stream = pybgpstream.BGPStream(data_interface="singlefile")
        stream.set_data_interface_option("singlefile", "rib-file", fpath)

        snap = per_snapshot[ndx]

        for elem in stream:
            as_path = elem.fields.get("as-path", "")
            if not as_path:
                continue

            tokens = as_path.split()
            if not tokens:
                continue

            seen = set()
            deduped = []
            for t in tokens:
                if t not in seen:
                    deduped.append(t)
                    seen.add(t)

            if len(deduped) < 2:
                continue

            path_len = len(deduped)
            origin = tokens[-1]

            cur = snap.get(origin)
            if cur is None or path_len < cur:
                snap[origin] = path_len

    all_origins = set()
    for snap in per_snapshot:
        all_origins.update(snap.keys())

    result = {}
    for origin in all_origins:
        result[origin] = [per_snapshot[i].get(origin, 0) for i in range(num_snapshots)]

    return result


def aw_event_durations(cache_files):
    """Track announcement-withdrawal pairs and compute event durations.
    Each new announcement refreshes the start timestamp."""
    results = {}
    last_announce = {}

    for ndx, fpath in enumerate(cache_files):
        stream = pybgpstream.BGPStream(data_interface="singlefile")
        stream.set_data_interface_option("singlefile", "upd-file", fpath)

        for elem in stream:
            if elem.type not in ("A", "W"):
                continue

            peer = elem.peer_address
            prefix = elem.fields.get("prefix")
            if not prefix:
                continue

            ts = float(elem.time)
            key = (peer, prefix)

            if elem.type == "A":
                last_announce[key] = ts
            else:
                if key in last_announce:
                    duration = ts - last_announce[key]
                    if duration > 0:
                        results.setdefault(peer, {}).setdefault(prefix, []).append(duration)
                    del last_announce[key]

    return results


def rtbh_event_durations(cache_files):
    """Track RTBH (Remote Triggered Blackholing) events.
    Opens on announcements with community value :666.
    Closes on withdrawal (emit duration) or non-RTBH announcement (silent close)."""
    results = {}
    bh_start = {}

    for fpath in cache_files:
        stream = pybgpstream.BGPStream(data_interface="singlefile")
        stream.set_data_interface_option("singlefile", "upd-file", fpath)

        for elem in stream:
            if elem.type not in ("A", "W"):
                continue

            peer = elem.peer_address
            prefix = elem.fields.get("prefix")
            if not prefix:
                continue

            ts = float(elem.time)
            key = (peer, prefix)

            if elem.type == "A":
                communities = elem.fields.get("communities", set()) or set()
                is_rtbh = False
                for c in communities:
                    if isinstance(c, str):
                        parts = c.split(":")
                    elif isinstance(c, (tuple, list)):
                        parts = [str(x) for x in c]
                    else:
                        continue
                    if len(parts) >= 2 and parts[-1] == "666":
                        is_rtbh = True
                        break

                if is_rtbh:
                    bh_start[key] = ts
                else:
                    if key in bh_start:
                        del bh_start[key]
            else:
                if key in bh_start:
                    duration = ts - bh_start[key]
                    if duration > 0:
                        results.setdefault(peer, {}).setdefault(prefix, []).append(duration)
                    del bh_start[key]

    return results
