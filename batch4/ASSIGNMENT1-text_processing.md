# Assignment: Unstructured Data Processing — Enhancement Tasks

Each task below extends one of the four demo scripts. Add your code **at the bottom** of
the corresponding file (or in a new file in the same folder) and call it from a
`if __name__ == "__main__"` block so it runs standalone.

---

## Demo 1 — `01_text_html_logs_processing.py`
**Topic: Clinical Notes, HTML EHR Pages, System Logs**

### Task 1 — Pydantic Validation for Extracted Clinical Data

The demo extracts vitals, medications, and patient info as plain dicts.  
Add Pydantic models to validate and type-check the extracted data.

**What to do:**

1. Install: `pip install pydantic`
2. Create the following Pydantic models:
   - `VitalSigns` — fields: `bp_systolic`, `bp_diastolic` (int), `heart_rate` (int),
     `temperature_celsius` (float), `spo2_percent` (float). Add a validator that raises
     an error if `spo2_percent < 80` (physiologically implausible).
   - `ClinicalNote` — fields: `note_id` (str), `date` (date), `patient_mrn` (str),
     `vitals` (VitalSigns | None), `medications` (list[str]).
3. After the demo's extraction runs, pass the extracted dicts through your models.
4. Print a summary: how many notes validated cleanly vs raised `ValidationError`.

**Stretch goal:** add a `@field_validator` on `date` that rejects dates in the future.

### Task 2 - Chronological order validation:
 After loading all notes, write a function
   `validate_chronological_order(notes: list[ClinicalNote]) -> None` that:
   - Checks whether the `date` fields are strictly non-decreasing across the list.
   - Prints `OK — notes are in chronological order` if they are.
   - Otherwise prints each out-of-order pair:
     ```
     [WARN] Note 003 (2024-03-20) precedes Note 002 (2024-03-22) — order violated
     ```
   - Raises a `ValueError` if any date is more than 30 days out of sequence
     (likely a data entry error rather than a filing quirk).


## Demo 2 — `02_pdf_processing.py`
**Topic: Machine-Readable PDFs (Lab Reports, Discharge Summaries)**

### Task 3 — Inspect PDF Table Structure

Before parsing lab values, it helps to understand what tables pdfplumber actually found
and what each one contains.

**What to do:**

1. After calling `extract_with_pdfplumber()` on `lab_report_CGH_0431.pdf`, loop over
   the returned `tables` list.
2. For each table, **print its title** by searching the page text for the last non-empty
   line that appears *above* the table's bounding box. If no title can be determined,
   print `"(untitled table)"`.
3. Identify the table whose first header cell contains `"Hematology"` (case-insensitive).
   Load its rows into a **pandas DataFrame** using the first row as column headers.
4. Print `df.head()` and `df.dtypes` so participants can see the raw types before
   any cleaning.

**Hint:** `pdfplumber` page objects expose `.extract_words()` with bounding-box info —
compare each word's `top` coordinate against the table's `bbox[1]` to find text above it.

---

### Task 4 — Pydantic Models for Lab Results and Discharge Records

The demo stores parsed lab rows and medication lists as plain dicts.  
Introduce Pydantic models so downstream code can rely on typed, validated data.

**What to do:**

1. Create a `LabResult` model with fields:
   - `test_name` (str), `result_numeric` (float | None), `unit` (str),
     `reference_range` (str), `flag` (str), `is_abnormal` (bool).
   - Add a `@model_validator` that sets `is_abnormal = True` whenever
     `flag` contains `"HIGH"`, `"LOW"`, or `"CRITICAL"`.
2. Create a `Medication` model matching the dict produced by
   `extract_medication_list_from_pdf()`: `item`, `drug`, `dose`, `route`, `frequency`.
3. Create a `LabReport` model that holds `patient_info` (dict) and
   `results` (list[LabResult]).
4. Run validation over the lab report and print:
   - Total results parsed, number valid, number that failed validation.
   - List of abnormal results with their flags.


## Demo 3 — `03_chat_email_processing.py`
**Topic: Chat Transcripts and Referral Emails**

### Task 5 — PHI Redaction and Audit Report

The demo *detects* PHI (names, MRNs, phone numbers) but leaves the original text
unchanged. Add a redaction step and produce an audit trail.

**What to do:**

1. Write a `redact_phi(text: str) -> tuple[str, list[dict]]` function that:
   - Replaces every detected PHI span with a type tag, e.g. `[MRN]`, `[PHONE]`, `[NAME]`.
   - Returns the redacted text **and** a list of dicts
     `{"type": ..., "original": ..., "position": (start, end)}`.
2. Run redaction over the full chat transcript and each email body.
3. Print a redaction audit report:
   ```
   === PHI Redaction Audit ===
   chat_transcript.txt : 7 spans redacted  (3× MRN, 2× NAME, 2× PHONE)
   referral_email.eml  : 4 spans redacted  (1× MRN, 2× NAME, 1× EMAIL)
   ```
4. Save the fully-redacted transcript to `data/chat_transcript_redacted.txt`.

**Note:** reuse the PHI patterns already defined in the demo — no new libraries needed.

---

## Demo 4 — `04_ocr_scanned_pdfs.py`
**Topic: OCR from Scanned PDFs and Prescription Images**

### Task 6 — Add PaddleOCR as a Third OCR Engine

The demo compares Tesseract and EasyOCR. Add PaddleOCR to the comparison so
participants see how a third engine handles the same prescription images.

**What to do:**

1. Install: `pip install paddlepaddle paddleocr` (CPU version is fine for this task).
2. Write a `run_paddleocr(image_path: Path) -> tuple[str, float]` function that:
   - Runs PaddleOCR on the image.
   - Returns the joined text and the mean confidence score across all detected boxes.
3. Integrate it into the existing side-by-side comparison section so the output shows
   three columns: `Tesseract | EasyOCR | PaddleOCR`.
4. Run on both `scanned_prescription.png` and `handwritten_prescription.png`.

**Note:** PaddleOCR downloads model weights on first run (~100 MB). Do this before class.

---

### Task 7 — OCR Confidence Score Comparison Chart

Both Tesseract and EasyOCR return per-word or per-box confidence scores, but the demo
only prints the extracted text. Surface those scores visually.

**What to do:**

1. **Tesseract:** call `pytesseract.image_to_data(..., output_type=Output.DICT)` to get
   per-word confidence. Filter out entries where `conf == -1`.
2. **EasyOCR:** each result tuple is `(bbox, text, confidence)` — collect the confidence
   values directly.
3. Draw a **side-by-side box plot** (or violin plot): one box per engine per image,
   showing the distribution of word-level confidence scores.
4. Add a second panel: a **bar chart** of the fraction of words above 80 % confidence
   for each engine/image combination.
5. Save as `data/ocr_confidence.png`.

**Stretch goal:** flag any word below 50 % confidence in the printed OCR output by
wrapping it in `[?word?]` so reviewers know where errors are likely.

