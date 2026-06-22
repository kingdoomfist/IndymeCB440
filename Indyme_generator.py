#!/usr/bin/env python3
"""
Indyme Call Button .sub File Generator
Reverse-engineered from captured signals.

Encoding: frame(N) = BASE + c_d1[hundreds] + c_d23[tens*10+units]  (mod 3)
Symbols: 0=long gap (~4680us), 1=short gap (~1800us), S=sync gap (~7600us)
Frame: 19 symbols + trailing sync, repeated ~18x, separated by frame gaps (~10500us)

Usage:
    python3 indyme_generator.py 42          # generate call 042
    python3 indyme_generator.py 1 5 10 42   # generate multiple calls
    python3 indyme_generator.py --all       # generate all known calls
    python3 indyme_generator.py --list      # list all generatable call numbers
"""

import sys
import os

# ── Encoding tables ──────────────────────────────────────────────────────────

BASE = [1,0,1,2,1,0,2,1,0,0,0,0,2,1,0,0,0,0,0]  # '010S10S10000S100000'

# Hundreds digit contributions (c_d1)
D1_CONTRIB = {
    0: [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    1: [0,2,1,2,0,2,2,0,2,1,0,0,2,0,2,2,2,0,0],
    2: [0,2,2,2,1,2,0,0,2,2,2,2,0,2,1,0,0,0,0],
    3: [0,0,2,0,0,2,2,0,2,1,0,2,0,0,2,1,0,0,0],
    4: [0,0,0,2,0,2,2,0,2,1,0,0,2,0,2,1,0,0,0],
    5: [0,0,0,2,0,2,0,0,2,1,0,0,2,0,2,2,2,0,0],
    6: [0,2,2,2,1,0,2,0,2,1,0,0,2,0,0,2,0,0,0],
    7: [0,0,1,2,1,0,0,0,2,1,0,0,2,0,0,0,2,0,0],
    8: [0,0,1,0,0,2,0,0,1,2,2,1,2,1,0,2,1,0,0],
    9: [0,2,1,2,0,0,0,0,0,0,1,2,0,0,2,1,0,0,0],
}

# Tens+units (d23 = d2*10+d3) contributions (c_d23)
D23_CONTRIB = {
    0:  [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    1:  [0,0,0,0,0,0,0,0,2,1,0,0,0,0,0,0,0,0,0],
    2:  [0,0,0,0,0,0,0,0,0,2,1,0,0,0,0,0,0,0,0],
    3:  [0,0,0,0,0,0,0,0,2,0,1,0,0,0,0,0,0,0,0],
    4:  [0,0,0,0,0,0,0,0,0,0,2,1,0,0,0,0,0,0,0],
    5:  [0,0,0,0,0,0,0,0,2,1,2,1,0,0,0,0,0,0,0],
    6:  [0,0,0,0,0,0,0,0,0,2,0,1,0,0,0,0,0,0,0],
    7:  [0,0,0,0,0,0,0,0,2,0,0,1,0,0,0,0,0,0,0],
    8:  [0,0,0,0,0,0,0,0,0,0,0,2,1,2,0,0,0,0,0],
    9:  [0,0,0,0,0,0,0,0,2,1,0,0,1,2,1,0,0,0,0],
    10: [0,0,0,0,0,0,0,0,0,2,1,0,1,2,1,0,0,0,0],
    11: [0,0,0,0,0,0,0,0,2,0,1,0,1,2,1,0,0,0,0],
    12: [0,0,0,0,0,0,0,0,0,0,2,1,1,2,1,0,0,0,0],
    20: [0,0,0,0,0,0,0,0,0,0,2,1,0,2,1,0,0,0,0],
    21: [0,0,0,0,0,0,0,2,2,1,0,2,1,2,0,2,2,0,0],
    22: [0,0,0,0,0,0,0,0,0,2,2,0,2,0,2,1,0,0,0],
    23: [0,0,0,0,0,0,0,0,2,0,2,0,2,0,0,1,1,1,0],
    24: [0,0,0,0,0,0,0,0,0,0,0,2,0,2,1,0,0,0,0],
    30: [0,0,0,0,0,0,0,0,0,2,0,1,0,0,2,1,0,0,0],
    33: [0,0,0,0,0,0,0,0,2,0,1,0,1,0,2,1,0,0,0],
    35: [0,0,0,1,2,0,0,0,2,0,2,0,1,0,2,1,0,0,0],
    40: [0,0,0,0,0,0,0,0,0,0,0,2,1,2,1,0,0,0,0],
    50: [0,0,0,0,0,0,0,0,0,2,1,0,0,2,2,1,0,0,0],
    60: [0,0,0,0,0,0,0,0,0,0,2,1,0,0,0,2,2,0,0],
    66: [0,0,0,0,0,0,0,0,0,0,2,1,1,0,2,2,0,0,0],
    70: [0,0,0,0,0,0,0,2,0,2,0,1,0,0,2,1,0,0,0],
    80: [0,0,0,0,0,0,0,2,0,2,2,0,0,2,0,1,0,0,0],
    90: [0,0,0,0,0,0,0,2,0,2,0,1,0,0,0,2,0,0,0],
    99: [0,0,0,0,0,0,0,2,0,2,0,1,1,0,0,2,0,0,0],
}

KNOWN_D23 = set(D23_CONTRIB.keys())

# ── Timing constants (microseconds) ─────────────────────────────────────────

PULSE    =  1250   # pulse on-time (all pulses same width)
GAP_1    =  1800   # short gap  -> symbol '1'
GAP_0    =  4680   # long gap   -> symbol '0'
GAP_S    =  7600   # sync gap   -> symbol 'S'
GAP_FRM  = 10500   # frame gap  (between repetitions)
REPEATS  = 18      # number of frame repetitions

# ── Core functions ───────────────────────────────────────────────────────────

def predict_sequence(N):
    """Return the 19-symbol sequence string for call number N, or None if unknown."""
    if not 1 <= N <= 999:
        return None
    d1  = N // 100
    d23 = N % 100
    if d1 not in D1_CONTRIB or d23 not in D23_CONTRIB:
        return None
    syms = {0:'0', 1:'1', 2:'S'}
    result = []
    for i in range(19):
        v = (BASE[i] + D1_CONTRIB[d1][i] + D23_CONTRIB[d23][i]) % 3
        result.append(syms[v])
    return ''.join(result)

def sequence_to_raw(seq):
    """Convert 19-symbol sequence to list of RAW_Data integers (us)."""
    gap_map = {'0': GAP_0, '1': GAP_1, 'S': GAP_S}
    raw = []
    for sym in seq:
        raw.append(PULSE)
        raw.append(-gap_map[sym])
    # trailing sync pulse + frame gap
    raw.append(PULSE)
    raw.append(-GAP_S)
    return raw

def make_sub(N, freq_hz=303875000):
    """Generate complete .sub file content for call number N."""
    seq = predict_sequence(N)
    if seq is None:
        return None, f"Call {N:03d}: d23={N%100} not in lookup table (need capture)"

    frame_raw = sequence_to_raw(seq)

    # Build RAW_Data lines (Flipper limit: 512 values per line)
    # One full repetition = 20 pulse+gap pairs * 2 = 40 values + frame_gap pair = 42
    one_frame = frame_raw + [PULSE, -GAP_FRM]
    all_values = []
    for i in range(REPEATS):
        all_values.extend(one_frame)
    # Remove final frame gap, replace with longer end gap
    all_values = all_values[:-2]

    lines = []
    chunk = []
    for v in all_values:
        chunk.append(str(v))
        if len(chunk) >= 512:
            lines.append('RAW_Data: ' + ' '.join(chunk))
            chunk = []
    if chunk:
        lines.append('RAW_Data: ' + ' '.join(chunk))

    content = f"""Filetype: Flipper SubGhz RAW File
Version: 1
Frequency: {freq_hz}
Preset: FuriHalSubGhzPresetOok270Async
Protocol: RAW
""" + '\n'.join(lines) + '\n'

    return content, None

def generatable_calls():
    """List all call numbers 001-999 that can be generated."""
    result = []
    for N in range(1, 1000):
        if N // 100 in D1_CONTRIB and N % 100 in KNOWN_D23:
            result.append(N)
    return result

# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    if '--list' in args:
        calls = generatable_calls()
        print(f"Generatable calls ({len(calls)}/999):")
        for i, N in enumerate(calls):
            print(f"{N:>4}", end='\n' if (i+1)%20==0 else ' ')
        print()
        return

    if '--all' in args:
        calls = generatable_calls()
        os.makedirs('indyme_calls', exist_ok=True)
        ok, fail = 0, 0
        for N in calls:
            content, err = make_sub(N)
            if content:
                fname = f"indyme_calls/Ind{N:03d}.sub"
                with open(fname, 'w') as f:
                    f.write(content)
                ok += 1
            else:
                print(f"SKIP {N:03d}: {err}")
                fail += 1
        print(f"Generated {ok} files in ./indyme_calls/  ({fail} skipped)")
        return

    for arg in args:
        try:
            N = int(arg)
        except ValueError:
            print(f"Error: '{arg}' is not a number")
            continue

        content, err = make_sub(N)
        if err:
            print(f"Cannot generate {N:03d}: {err}")
            continue

        fname = f"Ind{N:03d}.sub"
        with open(fname, 'w') as f:
            f.write(content)
        seq = predict_sequence(N)
        print(f"Generated {fname}  (sequence: {seq})")

if __name__ == '__main__':
    main()
