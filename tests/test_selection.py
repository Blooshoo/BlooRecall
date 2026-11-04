"""Opt-in allocation policy; no model/network needed."""
import os
import unittest
from pathlib import Path
from test_bloorecall import CorpusHarness, write, FakeEmbedder
from bloorecall.corpus import walk_corpus
from bloorecall.indexer import refresh

class SelectionTests(CorpusHarness):
    def roots(self, cap=8, quota=3):
        self.config['corpus_roots']=[dict(path=str(self.corpus),label='projects',selection='balanced',max_files=cap,max_files_per_project=quota)]
    def test_balance_determinism_and_burst(self):
        self.roots()
        for name in ('a','b','worktree'):
            write(self.corpus/name/'README.md', 'owned project locator')
            for i in range(12):
                p=write(self.corpus/name/'upstream'/f'{i}.md','upstream text');os.utime(p,(200+i,200+i))
        before=walk_corpus(self.config)
        first=[str(s.path) for s in before.sources]
        self.assertEqual(first,[str(s.path) for s in walk_corpus(self.config).sources])
        for i in range(50):write(self.corpus/'worktree'/'burst'/f'{i}.md','new burst')
        after=walk_corpus(self.config)
        for name in ('a','b'):
            self.assertEqual({s.path for s in before.sources if s.project=='projects/'+name},{s.path for s in after.sources if s.project=='projects/'+name})
        self.assertLessEqual(len(after.sources),8)
        for name in ('a','b','worktree'):
            self.assertIn(self.corpus/name/'README.md',{s.path for s in after.sources})
            self.assertLessEqual(sum(s.project=='projects/'+name for s in after.sources),3)
    def test_explicit_roots_still_have_safety_gates(self):
        paths=[]
        for name in ('secrets/README.md','.hidden/README.md','safe/credential.md','safe/big.md'):
            paths.append(write(self.corpus/name,'x'*300000 if 'big' in name else 'private prose'))
        link=self.corpus/'alias';link.symlink_to(self.corpus/'secrets',target_is_directory=True)
        paths.append(link/'README.md')
        self.config['corpus_roots']=[dict(path=str(p),selection='balanced',max_files=1) for p in paths]
        self.assertEqual(walk_corpus(self.config).sources,[])
    def test_content_gate_applies_to_reserved_readme(self):
        self.roots();write(self.corpus/'owned'/'README.md','api_key = '+ 'A'*30)
        result=refresh(self.config,embedder=FakeEmbedder())
        self.assertEqual(result['secret_blocked'],1)
    def test_cross_root_budget_drop_can_be_owned_by_later_root(self):
        a=write(self.corpus/'one'/'README.md','one');b=write(self.corpus/'two'/'README.md','two')
        self.config['corpus_roots']=[dict(path=str(self.corpus),label='first',max_files=1),dict(path=str(a),label='explicit',max_files=1),dict(path=str(b),label='explicit',max_files=1)]
        rows=walk_corpus(self.config).sources
        self.assertEqual(len(rows),2)
        self.assertEqual(len({s.path for s in rows}),2)
    def test_new_worktree_cannot_expand_its_quota(self):
        self.roots(cap=100, quota=3)
        for name in ("a", "b"):
            for i in range(8):write(self.corpus/name/f"{i}.md", "owned docs")
        before={s.path for s in walk_corpus(self.config).sources if s.project in {"projects/a", "projects/b"}}
        for i in range(100):write(self.corpus/"new-worktree"/f"{i}.md", "copied docs")
        after=walk_corpus(self.config).sources
        self.assertEqual(before,{s.path for s in after if s.project in {"projects/a", "projects/b"}})
        self.assertEqual(sum(s.project=="projects/new-worktree" for s in after),3)
    def test_invalid_selection_config_refused(self):
        import json
        from bloorecall.config import load_config
        self.roots()
        p=self.index_dir/"config.json"
        for key,value in (("selection","all"),("max_files_per_project",0),("max_depth",-1)):
            original=self.config["corpus_roots"][0].copy()
            self.config["corpus_roots"][0][key]=value
            p.write_text(json.dumps(self.config))
            with self.assertRaises(RuntimeError):load_config(p)
            self.config["corpus_roots"][0]=original
    def test_old_config_newest_unchanged(self):
        self.config['corpus_roots'][0]['max_files']=1
        files=list(self.corpus.rglob('*.*'))
        newest=max(files,key=lambda p:(p.stat().st_mtime,str(p)))
        self.assertEqual(walk_corpus(self.config).sources[0].path,newest)
