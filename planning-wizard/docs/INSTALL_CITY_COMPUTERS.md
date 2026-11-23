# Using RCA Wizard Suite v1.30 on a work computer

The Windows package includes Python and the wizard's supporting libraries.
You do not need to install Python separately. Automatic PDF generation uses
desktop Microsoft Word and Excel, or LibreOffice. Word and Excel in a web browser
cannot perform the current desktop conversion.

## Open the packaged application

1. Copy `RCA_Wizard_Suite_v1.30_Windows.zip` to the work computer through an
   approved file-transfer method.
2. Right-click it, choose **Extract All**, and select a fresh folder you can
   write to, such as a folder in Documents. Do not run it inside the ZIP or
   extract over an older version.
3. Open the extracted `RCA_Wizard_Suite_v1.30` folder and double-click
   **RCA Wizard Suite.exe**.
4. Keep **RCA Wizard Tools.exe**, **_internal**, and **Wizard_Files** beside it.
   Copy the entire folder whenever you move the application.

`Run Wizard.bat` belongs to a source install and starts Python. It is not the
launcher in the packaged ZIP. Optional **Create Desktop Shortcut.bat** creates
a shortcut to the packaged EXE.

If the organization blocks or quarantines the application, give the package
and exact message to IT for review. Installing Python or moving files around
does not establish that the application is approved.

## Check PDF generation before using a live case

On the home screen, select **Check PDF setup**. The wizard creates two temporary
samples and tries an actual PDF export with desktop Word and desktop Excel.
It does not open or change case files. Each test has a 60-second limit.

Use **Copy report** or **Save report** to share the result when requesting help.
The report includes the suite version, launch mode, runtime path, engine preference
and actual application errors. It is not sent anywhere automatically.

- **Word and Excel pass:** try the RCA again. If that case still fails, share
  `wizard_error_log.txt` from its output folder as well as the setup report.
- **Automation component cannot load:** the wizard's supporting library could
  not load. Use the complete packaged folder, including `_internal`. In a source
  install, the Windows dependencies must be installed in the Python actually
  running the wizard. The report identifies that Python.
- **Word/Excel cannot start or export:** open the desktop applications normally
  and complete any setup or sign-in prompts. If they work manually but automation
  still fails, share the report with support/IT; it retains the actual error.
- **Only browser Office is available:** automatic Office PDF export is unavailable
  on that computer. An approved desktop Office/LibreOffice installation or an
  IT-hosted Windows session is needed for the current automatic packet workflow.

Registry discovery is only a hint. v1.17 attempts Office conversion even when
those hints are absent. Workbook PDF export uses Excel independently of Word.

The optional `RCA_OFFICE_ENGINE` preference can force `msoffice` or `libreoffice`.
Normally it should be unset or `auto`. The report displays its value; a forced
LibreOffice preference will not fall back to Word/Excel.

## Pasted paths and error reports

In v1.19, typing/pasting a workbook, attachment or output path updates the actual
selection, as Browse does. Earlier versions of MBL and both renewal wizards could
show edited text while still using an old selection. Clearing a field now clears
that selection. The instructional templates and calculation formulas are unchanged.

New errors include the suite version, launch mode and runtime. Send the newest
error entry, not only older entries from the same append-only error log. A pass
on a development computer does not establish this computer's PDF capability.

## Access denied on an old packet working folder

v1.18 fixes the failure at `shutil.rmtree(work)` for `_renewal_packet_work` and
the corresponding working folders in the other wizards. Each packet now uses
a new system temporary folder. Leave the old case-folder workspace alone and
retry the RCA in the current version; deleting the old folder is not required.

That error happened before Office conversion. If the next attempt reports a
Word/Excel export error, run **Check PDF setup** and share its report together
with the latest `wizard_error_log.txt`.

## HCAD records

The package includes the HCAD downloader and browser automation library. It uses
installed Google Chrome, internet access and manual completion of HCAD verification.
Workplace browser policies may affect whether it can run. If it cannot, download
the property-record PDFs manually and attach them to the case. HCAD automation
is separate from the Word/Excel conversion needed to generate an RCA packet.

## Updating and source installs

Extract a new package into a fresh folder. Use the current installed templates;
reapply any intentional local template replacements through **Manage Templates**.
Real case workbook and attachment selections carry over through session memory.

Only developers/source users need `Run Wizard.bat` and `install_requirements.bat`.
The source requirements include pywin32 on Windows for Office automation. The
packaged build includes it already. Build a new distribution with
`Build Package.bat` on the development computer, not on the planner's computer.

The 637 document checks validate document structure. They do not establish that
Word/Excel automation works on every work computer. Run **Check PDF setup** and
check a sample RCA on each work-computer setup before relying on automatic PDFs.


## MLS application intake

The regular MLS wizard includes **Import Application PDF / Fill Calculation Sheet**. See APPLICATION_IMPORT.md for the review workflow. Local scan reading uses Windows OCR through the bundled PowerShell helper; parcel lookup needs Internet access. Handwriting and record discrepancies require planner review.
