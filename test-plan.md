# SoftOne no-save E2E test plan

## Scope

One real supported PDF is parsed, validated through read-only SQL, and used by
the full automatic flow. SoftOne opens, login/readiness and navigation run,
the form is filled, and the test stops before `Καταχώρηση`.

## Code evidence

- `scripts/run_softone_batch_no_save.cmd` invokes `batch --execute` without
  `--allow-save`.
- `src/softone_pilot/batch.py` launches SoftOne, runs startup/navigation, then
  executes the supplier workflow.
- `src/softone_pilot/automation.py` breaks before the `save` action when save
  permission is false.
- `config/softone_workflow.example.json` defines startup, navigation, field
  mappings, validation, save, settlement, and print steps.

## Primary flow: fill one creditor expense without saving

1. Put exactly one ENARTIA or ΕΓΝΑΤΙΑ PDF in the configured inbox, close
   SoftOne, and double-click `run_softone_batch_no_save.cmd`.
   - Pass: SoftOne opens, login/readiness completes, and the automation opens
     `Ειδικά πιστωτών → Νέα Εγγραφή`.
   - Fail: launch, login, parsing, duplicate validation, SQL lookup,
     navigation, or a selector reports `ERROR`.

2. Compare the populated form to the selected PDF and supplier mapping.
   - Pass for ENARTIA VAT `999082935`: series `ΤΙΜΔ-E1`, line `18103`, payment
     `1008`; date, document number, and net amount exactly match the PDF.
   - Pass for ΕΓΝΑΤΙΑ VAT `802408691`: series `ΤΙΜΔ`, line `10007`, payment
     `1008`; date, document number, and net amount exactly match the PDF; the
     description is `ΔΙΟΔΙΑ <previous month> <year>`.
   - Fail: any required field is blank, targets the wrong control, or differs
     from the PDF/mapping.

3. Inspect the console result and the SoftOne form.
   - Pass: JSON contains `"executed": true` and `"save_skipped": true`;
     `executed_steps` does not contain `"save"`, `"saved"` is false, and the
     populated `Νέα Εγγραφή` form remains open. The PDF remains in the inbox.
   - Fail: `save_skipped` is false, `save` appears in executed steps, the form
     closes, the PDF moves to processed, or a new SoftOne record is created.

4. Cancel/close the unsaved form manually.
   - Pass: SoftOne prompts to discard changes or returns to the list without a
     new document.
   - Fail: the document exists in the list after cancellation.

## Evidence to collect

- Full screenshot of the populated SoftOne form before cancellation.
- Full screenshot of the console JSON showing `save_skipped: true`.
- Any failure screenshot path printed by the automation.
- The final `pilot-data\batch-audit.jsonl` event.
