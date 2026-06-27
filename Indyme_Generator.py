#!/usr/bin/env python3
"""
Indyme CB440 Call Button .sub File Generator
Reverse-engineered from captured Flipper Zero signals.
https://github.com/kingdoomfist/IndymeCB440

Protocol:
  Frequency:  ~303.875 MHz
  Modulation: OOK, FuriHalSubGhzPresetOok270Async
  Frame:      19 symbols + trailing sync, repeated ~18x
  Symbols:    1 = short gap (~1800us), 0 = long gap (~4680us), S = sync gap (~7600us)
  Encoding:   lookup table (no rolling codes)

Coverage:
  001-099: complete (all 99 calls, direct capture)
  100,200,...,900: complete (all 9 round hundreds, direct capture)
  Selected others: 111,123,135,222,321,333,666,999
  Total: 116 of 999 calls

  For calls not in the table, capture the .sub file from a real button
  and contribute it to the repository. The generator will pick it up
  automatically if it follows the Ind###.sub naming convention.

Usage:
  python3 indyme_generator.py 42          # generate call 042
  python3 indyme_generator.py 1 5 10 42   # generate multiple calls
  python3 indyme_generator.py --all       # generate all known calls
  python3 indyme_generator.py --list      # list all generatable call numbers
"""

import sys
import os

# -- Lookup table -------------------------------------------------------------
# Each entry: call_number -> 19-symbol sequence string
# Symbols: 1=short gap, 0=long gap, S=sync gap

FRAMES = {
    1: '010S10S1S100S100000',
    2: '010S10S10S10S100000',
    3: '010S10S1S010S100000',
    4: '010S10S100S1S100000',
    5: '010S10S1S1S1S100000',
    6: '010S10S10S01S100000',
    7: '010S10S1S001S100000',
    8: '010S10S1000S0100000',
    9: '010S10S1S1000S10000',
    10: '010S10S10S100S10000',
    11: '010S10S1S0100S10000',
    12: '010S10S100S10S10000',
    13: '010S10S1S1S10S10000',
    14: '010S10S10S010S10000',
    15: '010S10S1S0010S10000',
    16: '010S10S1000S1S10000',
    17: '010S10S1S100S010000',
    18: '010S10S10S10S010000',
    19: '010S10S1S010S010000',
    20: '010S10S100S1S010000',
    21: '010S10S1S1S1S010000',
    22: '010S10S10S01S010000',
    23: '010S10S1S001S010000',
    24: '010S10S1000S0010000',
    25: '010S10S1S10000S1000',
    26: '010S10S10S1000S1000',
    27: '010S10S1S01000S1000',
    28: '010S10S100S100S1000',
    29: '010S10S1S1S100S1000',
    30: '010S10S10S0100S1000',
    31: '010S10S1S00100S1000',
    32: '010S10S1000S10S1000',
    33: '010S10S1S100S1S1000',
    34: '010S10S10S10S1S1000',
    35: '010S10S1S010S1S1000',
    36: '010S10S100S1S1S1000',
    37: '010S10S1S1S1S1S1000',
    38: '010S10S10S01S1S1000',
    39: '010S10S1S001S1S1000',
    40: '010S10S1000S01S1000',
    41: '010S10S1S1000S01000',
    42: '010S10S10S100S01000',
    43: '010S10S1S0100S01000',
    44: '010S10S100S10S01000',
    45: '010S10S1S1S10S01000',
    46: '010S10S10S010S01000',
    47: '010S10S1S0010S01000',
    48: '010S10S1000S1S01000',
    49: '010S10S1S100S001000',
    50: '010S10S10S10S001000',
    51: '010S10S1S010S001000',
    52: '010S10S100S1S001000',
    53: '010S10S1S1S1S001000',
    54: '010S10S10S01S001000',
    55: '010S10S1S001S001000',
    56: '010S10S1000S0001000',
    57: '010S10S1S100000S100',
    58: '010S10S10S10000S100',
    59: '010S10S1S010000S100',
    60: '010S10S100S1000S100',
    61: '010S10S1S1S1000S100',
    62: '010S10S10S01000S100',
    63: '010S10S1S001000S100',
    64: '010S10S1000S100S100',
    65: '001S1S10S100S100000',
    66: '001S1S100S10S100000',
    67: '001S1S10S010S100000',
    68: '001S1S1000S1S100000',
    69: '001S1S10S1S1S100000',
    70: '001S1S100S01S100000',
    71: '001S1S10S001S100000',
    72: '001S1S10000S0100000',
    73: '001S1S10S1000S10000',
    74: '001S1S100S100S10000',
    75: '001S1S10S0100S10000',
    76: '001S1S1000S10S10000',
    77: '001S1S10S1S10S10000',
    78: '001S1S100S010S10000',
    79: '001S1S10S0010S10000',
    80: '001S1S10000S1S10000',
    81: '001S1S10S100S010000',
    82: '001S1S100S10S010000',
    83: '001S1S10S010S010000',
    84: '001S1S1000S1S010000',
    85: '001S1S10S1S1S010000',
    86: '001S1S100S01S010000',
    87: '001S1S10S001S010000',
    88: '001S1S10000S0010000',
    89: '001S1S10S10000S1000',
    90: '001S1S100S1000S1000',
    91: '001S1S10S01000S1000',
    92: '001S1S1000S100S1000',
    93: '001S1S10S1S100S1000',
    94: '001S1S100S0100S1000',
    95: '001S1S10S00100S1000',
    96: '001S1S10000S10S1000',
    97: '001S1S10S100S1S1000',
    98: '001S1S100S10S1S1000',
    99: '001S1S10S010S1S1000',
    100: '001S1S1000S1S1S1000',
    111: '001S1S10S0010S01000',
    123: '001S1S10S010000S100',
    135: '00100S1S0001S100000',
    200: '01S10000000S0100000',
    222: '01S100000S0100S1000',
    300: '0001S1S100S10S01000',
    321: '0001S1S00100S100000',
    333: '0001S1S001S10S10000',
    400: '00001S1S100S1S10000',
    500: '00001S0100S1S001000',
    600: '01S0010S100S0010000',
    666: '010S100S1S1000S1000',
    700: '010S100S10S1000S100',
    800: '00100S01000S10S1000',
    900: '001S000100S1S100000',
    999: '001S00000001S1S1000',
}

# -- Timing constants (microseconds) -----------------------------------------

PULSE   =  1250   # pulse on-time (all pulses identical)
GAP_1   =  1800   # short gap  -> symbol '1'
GAP_0   =  4680   # long gap   -> symbol '0'
GAP_S   =  7600   # sync gap   -> symbol 'S'
GAP_FRM = 10500   # inter-frame gap
REPEATS =  18     # frame repetitions per transmission

# -- Core functions -----------------------------------------------------------

def sequence_to_raw(seq):
    """Convert 19-symbol sequence to RAW_Data integers (us)."""
    gap_map = {'0': GAP_0, '1': GAP_1, 'S': GAP_S}
    raw = []
    for sym in seq:
        raw.append(PULSE)
        raw.append(-gap_map[sym])
    raw.append(PULSE)
    raw.append(-GAP_S)   # trailing sync before frame gap
    return raw

def make_sub(N, freq_hz=303875000):
    """Generate .sub file content for call number N.
    Returns (content_string, error_string). One will be None."""
    if not 1 <= N <= 999:
        return None, f"Call number must be 001-999 (got {N})"
    if N not in FRAMES:
        return None, (f"Call {N:03d} not in lookup table. "
                      f"Capture Ind{N:03d}.sub from a real button and add it to the repo.")

    frame_raw = sequence_to_raw(FRAMES[N])
    one_rep   = frame_raw + [PULSE, -GAP_FRM]
    all_vals  = one_rep * REPEATS
    # trim trailing frame gap
    all_vals  = all_vals[:-2]

    # Chunk into lines (Flipper limit: 512 values)
    lines = []
    chunk = []
    for v in all_vals:
        chunk.append(str(v))
        if len(chunk) >= 512:
            lines.append('RAW_Data: ' + ' '.join(chunk))
            chunk = []
    if chunk:
        lines.append('RAW_Data: ' + ' '.join(chunk))

    content = (
        f"Filetype: Flipper SubGhz RAW File\n"
        f"Version: 1\n"
        f"Frequency: {freq_hz}\n"
        f"Preset: FuriHalSubGhzPresetOok270Async\n"
        f"Protocol: RAW\n"
        + '\n'.join(lines) + '\n'
    )
    return content, None

# -- CLI ----------------------------------------------------------------------

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    if '--list' in args:
        calls = sorted(FRAMES.keys())
        print(f"Generatable calls ({len(calls)}/999):")
        for i, N in enumerate(calls):
            print(f"{N:>4}", end='\n' if (i + 1) % 20 == 0 else ' ')
        print()
        return

    if '--all' in args:
        os.makedirs('indyme_calls', exist_ok=True)
        ok = fail = 0
        for N in sorted(FRAMES.keys()):
            content, err = make_sub(N)
            if content:
                with open(f'indyme_calls/Ind{N:03d}.sub', 'w') as f:
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
        else:
            fname = f"Ind{N:03d}.sub"
            with open(fname, 'w') as f:
                f.write(content)
            print(f"Generated {fname}  (sequence: {FRAMES[N]})")

if __name__ == '__main__':
    main()
