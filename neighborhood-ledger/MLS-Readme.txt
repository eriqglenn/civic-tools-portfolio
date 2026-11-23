HPW PROJECTS
Neighborhood map shows live Engage Houston capital projects intersecting the
selected official Super Neighborhood boundary. Construction is shown by default;
Include design projects adds design work. Click a project to open its details panel with scope, dates and
its official record. Refresh HPW checks all five layers again. Failed or over
90-day-old source layers are reported as unavailable, with no cache fallback.

Open Resident requests > Applications > Special Minimum Lot Size (MLS).
Start application opens the wizard. Continue application resumes the most recently
saved application for your neighborhood. My requests lists individual drafts.

CODEX ASSISTANT PROTOTYPE
With the official Codex Windows desktop runtime installed and your ChatGPT plan
connected, choose Codex with Ledger tools in AI settings. Typed questions and
Chat use the same selected neighborhood and source controls. A Codex turn can
check news, a supplied 311 case, or deed-index entries and return cited results
and editable drafts. Ledger keeps the last four questions and answers for a
follow-up in the current session. OpenAI GPT-Live handles spoken conversations.
Choose Standard Ledger to use the previous engine on computers without Codex.

OPENAI LIVE VOICE
Open Neighborhood assistant > AI settings > Voice settings to save a project
key with GPT-Live access and choose a microphone. Select Chat on Today or
beside Send to talk on that screen. Select End chat on the same button to stop.
The key is encrypted for the Windows account. API voice usage is billed to
that project. Codex uses the separately connected ChatGPT plan for lookups.
Speak directly to GPT-Live. You can interrupt it or switch the microphone in
AI settings > Voice settings. End chat releases the mic and closes the connection. Live audio is
sent to OpenAI. When a question needs Ledger information, the transcribed
question goes to Codex with the selected neighborhood and source controls.
Written sources and editable drafts appear in the assistant. To replace or
remove the voice key later, choose AI settings > Voice settings.

ASSISTANT LAYOUT UPDATE
The message box and Send button stay visible at the bottom of the assistant.
Answers appear above them in a separate scrolling area. Enter sends a question;
Shift+Enter adds a new line. Sources & options holds record selection, live
lookup settings and record previews. Live source checks can be expanded below
an answer. A failed request restores your question for retrying.
Each question is checked independently; this update changes the layout, not
conversation memory. Saved work and the existing AI connection are preserved.

CURRENT NEWS AND SEPARATE NO-AI EDITION
In Neighborhood assistant, choose Find current news for this neighborhood.
Each request fetches live publisher, City and selected council-district sources.
Stories need a publication date within 30 days; no saved-cache fallback is used.
Duplicate coverage is grouped. Up to 12 stories are provided, prioritizing the
selected neighborhood, then its districts, then City-wide announcements.
Unrelated City incident reports without a neighborhood match are excluded.
The assistant summarizes headlines/excerpts, not complete article bodies.
Publication dates, linked headlines and individual source outcomes are shown.
These on-demand searches do not alter saved News records; use News > Refresh
to update that screen. No search guarantees complete publisher coverage.

A separate No-AI installer is provided alongside this edition. It removes the
assistant and sign-in and uses a separate program, shortcut and data folder.
The existing AI edition and its saved work are preserved.

NEWS GROUPING AND ASSISTANT LOOKUPS — IN-PLACE UPDATE
News groups repeated links and closely matching coverage into one card.
Expand More coverage and source copies to open the other outlets. Reports
with different counts, publication dates more than one day apart, or explicit
later developments are kept separate unless they are versions of the same link.
Original records and newsletter selections remain saved. Grouping is conservative
and may leave uncertain duplicates separate. AI evidence uses the same grouping.
Validation: 290 automated regression tests passed. Browser tests covered
grouped news, related-source links, editable follow-up drafts and explicit saving.
A live ChatGPT call selected the 311 tool and drafted from a fictional case;
a separate live City lookup correctly returned no match for a test number.

Live lookup results include failed or ambiguous checks. Follow-up drafts open
in an editable form; review and click Save to keep one. Nothing is sent.

NEIGHBORHOOD ASSISTANT — CHATGPT SIGN-IN PROTOTYPE
Ledger still opens on Today. Open Neighborhood assistant, then AI settings.
Choose Continue with ChatGPT and complete sign-in and permission approval in
your browser. Return to Ledger, choose an available model, then Test connection.
No API key or copied OAuth token is needed for an eligible ChatGPT account.
This local prototype uses OpenAI's documented ChatGPT plan-sharing flow;
availability, models and usage depend on your account and granted permissions.
The connection test sends a short message, with no neighborhood records.
Manage usage opens ChatGPT settings. Continue with ChatGPT also reconnects an
expired session; Use another account starts a new account registration.

API keys remain an optional alternative under a collapsed section. API billing
is separate. Saving that connection explicitly selects it. Ledger never silently
switches from your ChatGPT plan to API billing when a request fails.

Ask about saved public updates, or explicitly include saved concerns and
follow-ups. Preview records shows the selected context before asking. Up to
18 records are selected using text matching and recency, within a size limit.
With live lookups enabled, the assistant can check a supplied 311 case number,
look up a Houston address, or search the deed index by subdivision. It uses
Ledger's existing public connectors and shows the check time and result.
For example: "Check 311 case [your case number] and prepare a follow-up draft."
Saved case references are available only when you include saved concerns and
follow-ups. No contact fields are included. Ambiguous addresses need clarification.
Deed index matches do not establish which restrictions apply to a property.
Current news searches are now available to the assistant. Plat/permit scans and
PDF reading are not AI tools in this build.
Sources may be incomplete or outdated. It does not see other neighborhoods, attached
PDFs, full articles, all City 311 cases, or the complete conversation history.
Each question is independent. AI answers have record references and suggested
next steps. Citation membership is checked; factual correctness still needs
human checking. Download an answer or open a follow-up draft and save it yourself.
It cannot submit City requests, contact departments or take automatic actions.

AI credentials are encrypted with Windows DPAPI for the current Windows account
and kept outside office.sqlite3/workspace exports. Sign in again on another
computer. Ledger stores only its own connection; it never reads Codex or browser
tokens. Sign out revokes its renewable connection and clears local tokens; if
remote revocation fails, Ledger explains how to disconnect in ChatGPT settings.
Dedicated contact fields are omitted, but opted-in free-text notes and locations
may contain personal information and are sent to OpenAI. The API request sets
store=false; this is not a claim of zero provider retention. Connection settings
apply across neighborhoods; each question uses only its selected workspace.
There is no automatic model spending. A local concurrency and request-rate cap
reduces accidental repeated requests; it is not a dollar spending limit.

Validation: automated regression and browser tests cover OAuth state/PKCE,
signed ID-token verification, granted scope, encrypted storage, refresh rotation,
revocation, interrupted streams, model selection and no automatic API fallback.
Browser scenarios used simulated accounts and responses. A live ChatGPT
sign-in and gpt-6.1-sol connection test succeeded on this computer on November 2,
2026. A live answer with a source reference also passed using one fictional
test record. These tests sent no real neighborhood records. Other computers and accounts
must sign in and pass their own connection test.
Official flow: https://developers.openai.com/siwc/token-sharing-open-source

MAP STREET NAMES AND SELECTOR ADDRESSES
The lot selector shows house numbers directly on parcels; hover for the full
address. Older saved projects recover missing street data when reopened.
Map downloads retry missing County street geometry and stop with a clear
message if the primary street cannot be labeled. Existing selections remain.
The Testwood Drive example was checked in the browser and printed PDF.

RESIDENT REQUESTS ACTION CENTER
Resident requests now has Start here, Applications, 311 service requests,
and My requests. Browse 18 programs by purpose or search everyday terms.
The MLS block application opens directly from the Resident requests catalog.
Other programs provide purpose-specific preparation notes, supporting-document
checklists, official City links, follow-up tasks and printable HTML briefs.
These briefs are NOT completed official applications and are not submitted by
Ledger. Complete the City forms and collect any required signatures separately.
Saved preparation drafts are included in the selected neighborhood workspace,
Settings backups and workspace exports. Existing MLS projects and 311 cases
remain available. My requests brings these three kinds of saved work together.
Progress is entered by the user; only the existing 311 lookup checks City status.
Browser checks cover searching, draft saving/reopening, printable export,
follow-ups without duplicates, 311/MLS navigation, mobile layout and separate
neighborhoods. The existing MLS boundary-to-PDF browser workflow also passed.

NEIGHBORHOOD LEDGER MLS — SPECIAL EDITION
Built from Ledger 13.8. Separate program and records from regular Ledger.

GET STARTED
Run Install-Neighborhood-Ledger AI.exe, then use the Neighborhood Ledger MLS
desktop shortcut. This edition opens on Today. Open the MLS wizard from Resident requests > Applications.

1. Enter the street number, street name and ZIP. Houston, TX is assumed.
2. Select lots on the map or from the property list, then click Continue.
   The boundary is created automatically. You can also draw the proposed area
   and click parcels to correct the selection.
   The block number, street sides, connecting cross streets and full boundary
   description fill automatically. Check or edit them on the next step.
   Older saved applications fill missing details when reopened. Use map details
   refreshes the suggestions; your typed corrections otherwise remain in place.
3. Check the automatically filled block description. Property information
   is used automatically, with no lot-by-lot review checkboxes. Optional
   property details let you correct data or enter separate legal lots.
4. Enter applicant details and the preliminary meeting date; add supporting
   documents. Applicants are not asked for a planner name.
5. Download the application PDF: application information, only the needed
   support/signature sheets, and the address-labeled boundary map.
   Download the map or sign separately. Instructions and working files opens
   the original City instructions and an optional ZIP of all project files.

Work saves automatically on this computer, separately for each selected
Super Neighborhood. Close using Settings > Save and close Ledger.
Internet is required for new public-record searches and map background tiles.
County Clerk document downloads may require your own sign-in.

PRINTING AND SUBMISSION
The application uses the fill-in pages of the supplied
SMLS-Block-NewApp-0821.pdf. The full 9-page original stays available separately
under Instructions and working files.
Generated street names are spelled out. Application addresses and boundary
descriptions use title case; map street labels use uppercase, as in the MLS
wizard. Existing saved applications receive this formatting when downloaded.
Applicant signatures, owner signatures, dates of signing and staff-only fields
remain blank. Gather signatures and have Planning staff confirm eligibility.
The sign is 36 x 24 inches: ask the printer to print at actual size.
It stays marked Draft until a City sign-instruction-letter date is entered.
Follow the City's written instructions before posting.

The map uses the standard MLS portrait layout with no City logo: County/HCAD
parcel geometry, house numbers, land area in square feet and land use inside
each selected property (with linked callouts where needed), street labels, a solid
boundary, north arrow and scale.
It is an applicant reference map, not a survey or an automatically verified
legal-lot subdivision. Confirm all lots on one blockface or two opposing
blockfaces are included. The calculation uses cumulative land area, not owner
count. Unknown restrictions or incomplete areas remain flagged for follow-up.
Live lookup failures show errors; MLS does not substitute an archived lookup.

KEEPING YOUR WORK
Special edition program: %LOCALAPPDATA%\Programs\NeighborhoodLedgerMLS
Special edition records: %LOCALAPPDATA%\NeighborhoodLedgerMLS\Data
Regular Ledger and its Fifth Ward records remain in their original folders.
For a complete transfer/backup of MLS work, close this edition and copy its
whole Data folder, including mls-applications and community subfolders.
The regular Settings database backup covers office records; retain the Data
folder and downloaded packets for MLS projects and attachments.
The packet includes an Application-record.json copy for recovery; the wizard
does not yet import packet ZIPs. Install the application on another computer
before transferring its Data folder. A desktop shortcut alone is not a copy
of the program.

VALIDATION
249 automated regression tests passed. The Windows browser workflow was
checked from address selection and drawing through saved reopening and packet
download, including separate neighborhoods and a narrower window layout.
Live lookup checked with 1042 Sampleoak Street, Houston, TX 77018; County plat
search checked with Oak Forest. These checks do not establish MLS eligibility
for that address. Generated forms, map and sign were visually inspected.

Official source:
https://houstontx.gov/planning/Min-Lot_Size-Min_Bldg_Line.html
https://houstontx.gov/planning/docs_pdfs/MLS-MBL-Application2026/SMLS-Block-NewApp-0821.pdf

Developer build: the bundled Ledger.Audio.dll is built from app/MicrophoneStream.cs
with .NET Framework csc /target:library /out:Ledger.Audio.dll MicrophoneStream.cs.
