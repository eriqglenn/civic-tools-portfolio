"""Update primary notification templates without changing other ZIP parts."""
from pathlib import Path
from zipfile import ZipFile
import importlib.util
import json
import shutil
from lxml import etree

ROOT = Path(__file__).resolve().parents[2]
PRIMARY = {"mls": ["MLS_Owner_Notification_Letter.docx"],
           "mls_renewal": ["MLS_Renewal_SFR_Letters_to_owners.docx", "MLS_Renewal_NO_SFR_Letters_to_owners.docx"],
           }
for version in ("26", "30"):
    suite = ROOT / ("RCA_Wizard_Suite v1_" + version)
    spec = importlib.util.spec_from_file_location("property_letters", suite / "Wizard_Files/core/property_letters.py")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    audit = suite / "build/property_lot_size_audit"
    records = []
    for wizard, names in PRIMARY.items():
        for name in names:
            path = suite / "Wizard_Files/templates" / wizard / name
            backup = audit / "templates_before" / wizard / name
            backup.parent.mkdir(parents=True, exist_ok=True)
            if not backup.exists():
                shutil.copy2(path, backup)
            with ZipFile(path) as archive:
                entries = [(info, archive.read(info.filename)) for info in archive.infolist()]
            original = dict((info.filename, data) for info, data in entries)
            root = etree.fromstring(original["word/document.xml"])
            count = helper.prepare_property_review(root)
            if count == 0 and helper.TOKEN in "".join(root.itertext()):
                continue
            assert count == 1, (path, count)
            updated = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
            temporary = path.with_suffix(".docx.tmp")
            with ZipFile(temporary, "w") as archive:
                for info, data in entries:
                    archive.writestr(info, updated if info.filename == "word/document.xml" else data)
            with ZipFile(temporary) as archive:
                for info, data in entries:
                    if info.filename != "word/document.xml":
                        assert archive.read(info.filename) == data, info.filename
            temporary.replace(path)
            records.append({"wizard": wizard, "template": name, "review_sentences_updated": count,
                            "other_zip_parts_unchanged": True})
    (audit / "template_changes.json").write_text(json.dumps(records, indent=2))
    print(version, records)
