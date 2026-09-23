import contextlib
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'init_project_memory.py'
spec = importlib.util.spec_from_file_location('memory', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='memory-v02-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'project with spaces'
        self.root.mkdir()

    def init(self, **kw):
        return m.initialize(self.root, date.today().isoformat(), **kw)

    def candidate(self, content='Confirmed new state\n'):
        directory = self.root / '.project-memory-candidates'
        directory.mkdir(exist_ok=True)
        target = directory / 'candidate.md'
        target.write_text(content, encoding='utf-8')
        return target

    def command(self, *args):
        return subprocess.run([sys.executable, '-B', str(SCRIPT), '--root', str(self.root), *args],
                              capture_output=True, text=True, encoding='utf-8', timeout=20)

    def test_initialize_and_idempotent_repair(self):
        first = self.init()
        before = {p.name: p.read_bytes() for p in self.root.iterdir() if p.is_file()}
        second = self.init()
        after = {p.name: p.read_bytes() for p in self.root.iterdir() if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(second['changed'], [])
        self.assertEqual(set(first['changed']), {'AGENTS.md', *m.RECORDS, m.META, '.gitignore'})
        self.assertTrue(m.check(self.root)['ok'])

    def test_v01_custom_rules_and_history_are_preserved(self):
        agents = b'\xef\xbb\xbf# Other project rules\r\nKeep UTF-8 and custom rules.\r\n'
        (self.root / 'AGENTS.md').write_bytes(agents)
        for name in m.RECORDS:
            (self.root / name).write_text('Existing history: ' + name, encoding='utf-8')
        self.init()
        self.assertTrue((self.root / 'AGENTS.md').read_bytes().startswith(agents))
        for name in m.RECORDS:
            self.assertEqual((self.root / name).read_text(), 'Existing history: ' + name)
        backups = list((self.root / m.BACKUPS).iterdir())
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), agents)

    def test_managed_block_refresh_preserves_surrounding_rules(self):
        original = 'before\n' + m.BEGIN + '\nold rules\n' + m.END + '\nafter\n'
        (self.root / 'AGENTS.md').write_text(original, encoding='utf-8')
        self.init()
        result = (self.root / 'AGENTS.md').read_text(encoding='utf-8')
        self.assertTrue(result.startswith('before\n'))
        self.assertTrue(result.endswith('\nafter\n'))
        self.assertEqual(result.count(m.BEGIN), 1)

    def test_full_preflight_empty_record_no_changes(self):
        (self.root / 'findings.md').write_bytes(b'')
        with self.assertRaises(m.MemoryError):
            self.init()
        self.assertEqual([p.name for p in self.root.iterdir()], ['findings.md'])

    def test_directory_shaped_record_rejected(self):
        (self.root / 'progress.md').mkdir()
        with self.assertRaises(m.MemoryError):
            self.init()
        self.assertFalse((self.root / 'AGENTS.md').exists())

    def test_non_utf8_rejected_without_overwrite(self):
        (self.root / 'findings.md').write_bytes(b'\xff\xfe')
        with self.assertRaises(m.MemoryError):
            self.init()
        self.assertEqual((self.root / 'findings.md').read_bytes(), b'\xff\xfe')

    def test_ambiguous_markers_prevent_all_mutations(self):
        value = m.BEGIN + '\nunclosed'
        (self.root / 'AGENTS.md').write_text(value, encoding='utf-8')
        with self.assertRaises(m.MemoryError):
            self.init()
        self.assertEqual((self.root / 'AGENTS.md').read_text(), value)
        self.assertFalse((self.root / 'PROJECT_CONTEXT.md').exists())

    def test_today_default_and_invalid_date(self):
        self.assertEqual(self.command().returncode, 0)
        self.assertIn(date.today().isoformat(), (self.root / 'PROJECT_CONTEXT.md').read_text())
        self.assertNotEqual(self.command('--date', 'YYYY-MM-DD').returncode, 0)

    def test_root_home_and_skill_directory_rejected(self):
        for path in [Path(self.root.anchor), Path.home(), SCRIPT.parent.parent]:
            with self.assertRaises(m.MemoryError):
                m.project_root(path)

    def test_status_check_are_readonly_and_bounded(self):
        self.init()
        before = {p.name: p.stat().st_mtime_ns for p in self.root.iterdir()}
        with patch.object(m, 'read_file', wraps=m.read_file) as reader:
            value = m.status(self.root, 'PROJECT_CONTEXT.md')
            names = [c.args[0].name for c in reader.call_args_list]
        self.assertEqual(names, [m.META, 'PROJECT_CONTEXT.md'])
        self.assertEqual(len(value['sha256']), 64)
        self.assertTrue(m.check(self.root)['ok'])
        self.assertEqual(before, {p.name: p.stat().st_mtime_ns for p in self.root.iterdir()})

    def test_stale_hash_rejected_without_change(self):
        self.init()
        old = (self.root / 'PROJECT_CONTEXT.md').read_bytes()
        with self.assertRaises(m.MemoryError):
            m.update_record(self.root, 'PROJECT_CONTEXT.md', self.candidate(), '0' * 64)
        self.assertEqual((self.root / 'PROJECT_CONTEXT.md').read_bytes(), old)

    def test_successful_write_has_original_backup(self):
        self.init()
        target = self.root / 'PROJECT_CONTEXT.md'
        old = target.read_bytes()
        m.update_record(self.root, target.name, self.candidate(), m.digest(old))
        self.assertEqual(target.read_text(), 'Confirmed new state\n')
        self.assertEqual(next((self.root / m.BACKUPS).iterdir()).read_bytes(), old)

    def test_progress_append_preserves_prior_entries(self):
        self.init()
        target = self.root / 'progress.md'
        old = target.read_bytes()
        m.update_record(self.root, target.name, self.candidate('Dated checkpoint\n'), m.digest(old), True)
        self.assertTrue(target.read_bytes().startswith(old))
        self.assertTrue(target.read_text(encoding='utf-8').endswith('Dated checkpoint\n'))

    def test_read_returns_matching_content_and_hash(self):
        self.init()
        result = m.status(self.root, 'PROJECT_CONTEXT.md', True)
        self.assertEqual(m.digest(result['content'].encode('utf-8')), result['sha256'])
        self.assertNotIn('content', m.status(self.root, 'PROJECT_CONTEXT.md'))

    def test_oversized_context_rejected(self):
        self.init()
        sha = m.status(self.root, 'PROJECT_CONTEXT.md')['sha256']
        for content in ['x' * 6001, 'x\n' * 101]:
            with self.assertRaises(m.MemoryError):
                m.update_record(self.root, 'PROJECT_CONTEXT.md', self.candidate(content), sha)
        self.assertEqual(m.status(self.root, 'PROJECT_CONTEXT.md')['sha256'], sha)

    def test_existing_large_context_preserved_and_warned(self):
        (self.root / 'PROJECT_CONTEXT.md').write_text('x' * 6001)
        self.init()
        result = m.check(self.root)
        self.assertTrue(result['ok'])
        self.assertTrue(result['warnings'])
        self.assertEqual((self.root / 'PROJECT_CONTEXT.md').stat().st_size, 6001)

    def test_lock_conflict_and_release(self):
        self.init()
        with m.project_lock(self.root):
            with self.assertRaises(m.MemoryError):
                self.init()
        self.assertFalse((self.root / m.LOCK).exists())

    def test_actual_concurrent_writers_exactly_one_succeeds(self):
        self.init()
        sha = m.status(self.root, 'PROJECT_CONTEXT.md')['sha256']
        candidate = self.candidate()
        args = ('--mode', 'write', '--expected-sha', sha, '--content-file', str(candidate))
        with ThreadPoolExecutor(max_workers=2) as pool:
            outputs = list(pool.map(lambda _: self.command(*args), range(2)))
        self.assertEqual(sorted(r.returncode for r in outputs), [0, 1])
        self.assertEqual((self.root / 'PROJECT_CONTEXT.md').read_text(), 'Confirmed new state\n')

    def test_creator_race_cannot_truncate_other_writer(self):
        target = self.root / 'progress.md'
        def race(path, **kw):
            target.write_text('Other writer')
            return None
        with patch.object(m, 'read_file', side_effect=race):
            with self.assertRaises(FileExistsError):
                m.put(self.root, target.name, b'New template', None)
        self.assertEqual(target.read_text(), 'Other writer')

    def test_interrupted_replace_keeps_original_and_backup(self):
        self.init()
        target = self.root / 'PROJECT_CONTEXT.md'
        old = target.read_bytes()
        with patch.object(m.os, 'replace', side_effect=OSError('simulated failure')):
            with self.assertRaises(OSError):
                m.update_record(self.root, target.name, self.candidate(), m.digest(old))
        self.assertEqual(target.read_bytes(), old)
        self.assertFalse((self.root / m.LOCK).exists())
        self.assertFalse(list(self.root.glob('.project-memory-tmp-*')))

    def test_independent_roots_and_exact_subfolder_scope(self):
        self.init()
        parent_bytes = (self.root / 'PROJECT_CONTEXT.md').read_bytes()
        child = self.root / 'child'
        child.mkdir()
        with self.assertRaises(m.MemoryError):
            m.status(child, 'PROJECT_CONTEXT.md')
        m.initialize(child, '2026-01-01')
        self.assertEqual((self.root / 'PROJECT_CONTEXT.md').read_bytes(), parent_bytes)
        self.assertNotEqual((child / 'PROJECT_CONTEXT.md').read_bytes(), parent_bytes)

    def test_external_candidate_refused(self):
        self.init()
        external = Path(self.temp.name) / 'external.md'
        external.write_text('outside root')
        with self.assertRaises(m.MemoryError):
            m.update_record(self.root, 'PROJECT_CONTEXT.md', external, '0' * 64)

    def test_symlink_target_refused(self):
        other = Path(self.temp.name) / 'other.md'
        other.write_text('private external record')
        try:
            (self.root / 'findings.md').symlink_to(other)
        except OSError:
            self.skipTest('OS does not permit symlink creation in this environment')
        with self.assertRaises(m.MemoryError):
            self.init()
        self.assertEqual(other.read_text(), 'private external record')

    def test_future_metadata_refuses_downgrade(self):
        (self.root / m.META).write_text(json.dumps({'schema': 3, 'version': '3.0.0'}))
        with self.assertRaises(m.MemoryError):
            self.init()
        self.assertFalse((self.root / 'AGENTS.md').exists())

    def test_ignore_preserves_custom_rules(self):
        original = b'custom-output/\r\n!keep.txt\r\n'
        (self.root / '.gitignore').write_bytes(original)
        self.init()
        result = (self.root / '.gitignore').read_bytes()
        self.assertTrue(result.startswith(original))
        self.assertIn(b'/PROJECT_CONTEXT.md', result)

    def test_privacy_unchanged_does_not_create_ignore(self):
        self.init(privacy=False)
        self.assertFalse((self.root / '.gitignore').exists())

    @unittest.skipUnless(shutil.which('git'), 'Git unavailable')
    def test_git_reports_tracked_memory_without_untracking(self):
        def git(*args):
            return subprocess.run(['git', '-C', str(self.root), *args], capture_output=True, check=True)
        git('init')
        (self.root / 'findings.md').write_text('tracked fixture')
        git('add', 'findings.md')
        self.init()
        self.assertEqual(m.git_privacy(self.root)['state'], 'tracked')
        self.assertIn(b'findings.md', git('ls-files').stdout)
        self.assertEqual(git('check-ignore', 'PROJECT_CONTEXT.md').returncode, 0)


if __name__ == '__main__':
    unittest.main()
