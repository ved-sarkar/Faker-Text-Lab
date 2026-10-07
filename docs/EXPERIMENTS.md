# Usage and implementation notes

## Tagged replacement

`faker_replacement.py` reads an Excel workbook at module scope, applies replacement to every column, adds count and mapping columns, and writes another workbook. Importing it also performs this file I/O. It replaces explicit tags; it does not discover arbitrary personal information. Generated names and phone strings are fictional substitutes, but may coincidentally resemble real people or numbers.

The example CSV is manually authored, contains only placeholders, and has no actual phone number. To explore the original script, save it as an Excel workbook named `output156.xlsx` in a disposable working directory. The `Original_Text` column produces `Original_Text_replaced`, which is the column expected by the second script.

## Redaction comparison experiment

`llm faker.py` creates directories, configures a log file, and loads its hardcoded workbook at module scope. Its main routine calls `from_pretrained` for GPT-Neo 1.3B and 2.7B; executing it can download large model files. No weights or dataset are bundled here.

Known limitations visible in the source:

- Capitalized-word detection is only a broad heuristic; its ten-digit phone regex misses many formats.
- The processing function replaces the language-model return value with a regex result. Model-labeled summaries are therefore not evidence of model redaction quality.
- Logs and output tables retain original text and replacement mappings. Replacing values does not by itself make those artifacts safe to share.
- Model identifiers containing `/` become path components in output filenames; required parent directories are not created consistently.
- No fixed seed, benchmark corpus, independently labeled ground truth, or validated accuracy result is supplied.

The original source was copied unchanged. The original notebook, spreadsheets, logs, and results were excluded. No operational or privacy guarantee is implied by the example, output names, or charts.
