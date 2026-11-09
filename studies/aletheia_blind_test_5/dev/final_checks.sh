#!/usr/bin/env bash
# The last full run of every check before sealing blind test 5 (dev only, not sealed).
# Usage: bash dev/final_checks.sh LOG_DIR   (from aletheia_blind_test_5/)
# Each step's output goes to LOG_DIR/NN_name.txt; summary.txt says PASS or FAIL per step.
cd "$(dirname "$0")/.." || exit 1
LOG=${1:-dev/final_run}
mkdir -p "$LOG"
SUM="$LOG/summary.txt"
: > "$SUM"
FP=scorer/dev_fingerprints.json

step() {  # step NAME COMMAND...
  local name=$1; shift
  local t0=$SECONDS
  "$@" > "$LOG/$name.txt" 2>&1
  local rc=$?
  echo "$name: $([ $rc -eq 0 ] && echo PASS || echo "FAIL (exit $rc)") ($((SECONDS - t0)) s)" | tee -a "$SUM"
}

step 01_lang_tests bash -c "cd ../language_v0 && python -I tests/run_tests.py"
step 02_lang_copy bash -c "cmp lang/reader_v0.py ../language_v0/reader_v0.py && cmp lang/SPEC_v0.5.md ../language_v0/SPEC_v0.5.md"
step 03_check_seed python -I seed/check_seed.py
step 04_test_certs python -I dev/test_certs.py
step 05_make_dev python -I dev/make_dev.py

# the dev worlds are themselves in the fingerprints (V11), so validate and score them with the file aside
mv "$FP" "$LOG/fp_aside.json"
step 06_validate_dev python -I scorer/validate_v5.py dev/batch_dev --quick
step 07_procedure_cli python -I procedure/procedure_v5.py run dev/batch_dev/worlds "$LOG/outputs_cli.json"
step 08_score_cli python -I scorer/score_v5.py dev/batch_dev "$LOG/outputs_cli.json" "$LOG/report_cli.json"
mv "$LOG/fp_aside.json" "$FP"

step 09_mutation python -I dev/mutation_test.py
echo "done" >> "$SUM"
