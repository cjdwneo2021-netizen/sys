import copy
from dataclasses import replace
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from studybot.config import Config
from studybot.drive import Drive, FOLDER, synchronize
from studybot.extract import chunks, extract_sources
from studybot.model import Deferred, Generator, validate
from studybot.pipeline import generate_notes
from studybot.render import render
from studybot.storage import contained, read_json, write_json, write_text

NOTE = {"markdown": "## 핵심 개념\n변수에 값을 저장한다. [f1:cell-1]",
        "concepts": [{"name": "변수", "explanation": "값을 이름으로 참조한다.", "source_ids": ["f1:cell-1"]}],
        "questions": ["변수명은 어떻게 정할까?"]}

class FakeBackend:
    def __init__(self):
        self.calls = 0
    def generate(self, prompt):
        self.calls += 1
        return copy.deepcopy(NOTE)

class FakeDrive:
    def __init__(self):
        self.item = {"id": "f1", "name": "lesson.ipynb", "mimeType": "application/vnd.google.colaboratory",
                     "modifiedTime": "2020-01-01T00:00:00Z", "version": "1"}
        self.notebook = {"cells": [{"cell_type": "code", "source": ["x = 3"], "outputs": []}]}
        self.downloads = 0
        self.unstable = False
    def info(self, file_id):
        if file_id in ("root", "lecture"):
            return {"id": file_id, "name": "파이썬 3주차", "mimeType": FOLDER}
        result = dict(self.item)
        if self.unstable:
            result["version"] = "2"
        return result
    def children(self, folder_id):
        return [self.info("lecture")] if folder_id == "root" else [self.item]
    def tree(self, folder_id):
        return [dict(self.item, relative=self.item["name"])]
    def download(self, item, limit):
        self.downloads += 1
        return json.dumps(self.notebook).encode()

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = Config(self.root, folder_id="root", idle_seconds=10, model="test", max_calls=8)
        self.now = 1_800_000_000
    def tearDown(self):
        self.temp.cleanup()
    def import_lecture(self):
        drive = FakeDrive()
        self.assertEqual(synchronize(self.config, drive, now=self.now), [])
        self.assertEqual(synchronize(self.config, drive, now=self.now + 11), ["lecture"])
        return drive

    def test_first_observation_and_idle_gate(self):
        drive = FakeDrive()
        synchronize(self.config, drive, now=self.now)
        synchronize(self.config, drive, now=self.now + 5)
        self.assertEqual(drive.downloads, 0)
        self.assertEqual(synchronize(self.config, drive, now=self.now + 11), ["lecture"])
        synchronize(self.config, drive, now=self.now + 30)
        self.assertEqual(drive.downloads, 1)

    def test_change_during_download_is_deferred(self):
        drive = FakeDrive()
        synchronize(self.config, drive, now=self.now)
        drive.unstable = True
        self.assertEqual(synchronize(self.config, drive, now=self.now + 11), [])
        self.assertFalse((self.root / "materials/lecture/manifest.json").exists())

    def test_root_file_is_imported_and_generates_note(self):
        drive = FakeDrive()
        drive.children = lambda folder_id: [dict(drive.item)]
        self.assertEqual(synchronize(self.config, drive, now=self.now), [])
        self.assertEqual(synchronize(self.config, drive, now=self.now + 5), [])
        self.assertEqual(synchronize(self.config, drive, now=self.now + 11), ["f1"])
        manifest = read_json(self.root / "materials/f1/manifest.json")
        self.assertEqual(manifest["title"], "lesson.ipynb")
        self.assertEqual(generate_notes(self.config, Generator(self.config, FakeBackend())), ["f1"])
        self.assertEqual(synchronize(self.config, drive, now=self.now + 20), [])
        self.assertEqual(drive.downloads, 1)

    def test_root_file_change_during_download_is_deferred(self):
        drive = FakeDrive()
        drive.children = lambda folder_id: [dict(drive.item)]
        synchronize(self.config, drive, now=self.now)
        drive.unstable = True
        self.assertEqual(synchronize(self.config, drive, now=self.now + 11), [])
        self.assertFalse((self.root / "materials/f1/manifest.json").exists())

    def test_excel_copy_preserves_cells_formulas_and_cached_values(self):
        path = self.root / "lesson.xlsx의 사본"
        with ZipFile(path, "w") as archive:
            archive.writestr("[Content_Types].xml", '''<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>''')
            archive.writestr("xl/workbook.xml", '''<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="전처리" sheetId="1" r:id="rId1"/></sheets></workbook>''')
            archive.writestr("xl/_rels/workbook.xml.rels", '''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>''')
            archive.writestr("xl/worksheets/sheet1.xml", '''<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><dimension ref="A1:D3"/><sheetData>
<row r="1"><c r="A1" t="inlineStr"><is><t>문서 단어 행렬</t></is></c></row>
<row r="2"><c r="A2"><v>0</v></c><c r="B2" t="b"><v>0</v></c><c r="C2"><f>SUM(A2,3)</f><v>3</v></c><c r="D2"><f>SUM(A2,4)</f><v></v></c></row>
<row r="3"><c r="A3" t="e"><v>#DIV/0!</v></c></row>
</sheetData></worksheet>''')
        sources = extract_sources(self.root, {"files": [{"id": "excel", "name": path.name,
            "path": path.name, "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "status": "downloaded"}]})
        self.assertEqual([source["id"] for source in sources],
                         ["excel:sheet-1:row-1", "excel:sheet-1:row-2", "excel:sheet-1:row-3"])
        self.assertIn("전처리", sources[0]["label"])
        self.assertIn("문서 단어 행렬", sources[0]["text"])
        self.assertIn("A2: 0", sources[1]["text"])
        self.assertIn("B2: False", sources[1]["text"])
        self.assertIn("=SUM(A2,3) [저장된 결과: 3]", sources[1]["text"])
        self.assertIn("저장된 결과 없음; 수식을 재계산하지 않음", sources[1]["text"])
        self.assertIn("#DIV/0! [Excel 오류]", sources[2]["text"])

    def test_code_is_not_executed_and_errors_keep_order(self):
        write_json(self.root / "n.ipynb", {"cells": [
            {"cell_type": "markdown", "source": ["질문"]},
            {"cell_type": "code", "source": ["raise RuntimeError('never execute')"],
             "outputs": [{"output_type": "error", "ename": "ValueError", "evalue": "example"}]}]})
        sources = extract_sources(self.root, {"files": [{"id": "f", "name": "n.ipynb",
                                                         "path": "n.ipynb", "status": "downloaded"}]})
        self.assertEqual([s["id"] for s in sources], ["f:cell-1", "f:cell-2", "f:cell-2:output-1"])

    def test_long_source_split_preserves_content(self):
        sources = [{"id": "abc", "label": "transcript", "text": "가" * 12000}]
        result = chunks(sources, 6000)
        self.assertTrue(all(len(p) <= 6000 for p in result))
        self.assertEqual(sum(p.count("가") for p in result), 12000)
        self.assertTrue(all("[SOURCE abc]" in p for p in result))

    def test_resume_uses_completed_chunk(self):
        self.import_lecture()
        backend = FakeBackend()
        config = replace(self.config, max_calls=1)
        with self.assertRaises(Deferred):
            generate_notes(config, Generator(config, backend))
        self.assertEqual(backend.calls, 1)
        self.assertFalse((self.root / "state/results/lecture.json").exists())
        generate_notes(config, Generator(config, backend))
        self.assertEqual(backend.calls, 2)

    def test_no_change_no_api_and_deterministic_render(self):
        self.import_lecture()
        backend = FakeBackend()
        generate_notes(self.config, Generator(self.config, backend))
        render(self.root)
        calls = backend.calls
        before = (self.root / "downloads/lecture.zip").read_bytes()
        generate_notes(self.config, Generator(self.config, backend))
        render(self.root)
        self.assertEqual(backend.calls, calls)
        self.assertEqual((self.root / "downloads/lecture.zip").read_bytes(), before)
        self.assertIn("notes/lecture.md", (self.root / "README.md").read_text("utf-8"))

    def test_invented_source_rejected(self):
        with self.assertRaises(ValueError):
            validate(NOTE, {"other"})

    def test_manual_readme_preserved(self):
        write_text(self.root / "README.md", "# My course\nManual introduction.\n")
        render(self.root)
        render(self.root)
        text = (self.root / "README.md").read_text("utf-8")
        self.assertIn("Manual introduction.", text)
        self.assertEqual(text.count("<!-- studybot:start -->"), 1)

    def test_daily_budget_shared_between_runs(self):
        self.import_lecture()
        config, backend = replace(self.config, daily_calls=1), FakeBackend()
        for _ in range(2):
            with self.assertRaises(Deferred):
                generate_notes(config, Generator(config, backend))
        self.assertEqual(backend.calls, 1)

    def test_metadata_only_update_does_not_regenerate(self):
        drive = self.import_lecture()
        backend = FakeBackend()
        generate_notes(self.config, Generator(self.config, backend))
        calls = backend.calls
        old_path = read_json(self.root / "materials/lecture/manifest.json")["files"][0]["path"]
        drive.item["version"] = "2"
        drive.notebook["metadata"] = {"colab": {"view": "changed"}}
        synchronize(self.config, drive, now=self.now + 20)
        synchronize(self.config, drive, now=self.now + 31)
        generate_notes(self.config, Generator(self.config, backend))
        self.assertEqual(backend.calls, calls)
        self.assertTrue((self.root / old_path).exists())
        self.assertNotEqual(read_json(self.root / "state/results/lecture.json")["sources"][0]["path"], old_path)

    def test_paths_cannot_escape(self):
        for path in ("../secret", "/tmp/secret"):
            with self.assertRaises(ValueError):
                contained(self.root, path)

    def test_zip_contains_portable_links(self):
        self.import_lecture()
        generate_notes(self.config, Generator(self.config, FakeBackend()))
        with patch.dict(os.environ, {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_REF_NAME": "main"}):
            render(self.root)
        with ZipFile(self.root / "downloads/lecture.zip") as bundle:
            note = bundle.read("study-note.md").decode()
            self.assertIn("https://github.com/owner/repo/blob/main/materials/", note)

    def test_drive_list_paginates(self):
        drive = Drive(session=object())
        calls = []
        def get(path, **params):
            calls.append(params)
            return {"files": [{"id": "b"}]} if params.get("pageToken") else {
                "files": [{"id": "a"}], "nextPageToken": "next"}
        drive.get = get
        self.assertEqual([x["id"] for x in drive.children("root")], ["a", "b"])
        self.assertEqual(calls[1]["pageToken"], "next")

    def test_no_model_key_needed_when_no_lectures(self):
        self.assertEqual(generate_notes(replace(self.config, model="")), [])

if __name__ == "__main__":
    unittest.main()
