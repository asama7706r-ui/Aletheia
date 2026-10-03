"""Run the frozen scorer on the dev set (development only): W10 is switched off, because the dev worlds
are the dev set itself.  Usage:  python score_dev.py <worlds> <data> <key> <outputs> <report>"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scorer"))
import ref_v3  # noqa: E402
import score_v3  # noqa: E402

ref_v3.DEV_HASHES.clear()
score_v3.main(*sys.argv[1:])
