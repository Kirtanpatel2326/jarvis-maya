"""Stage 7: Maya Personal Memory + Proactive Brain.
Stores explicit preferences/facts and user-authorized recurring jobs.
This service never sends messages, emails, calls, or executes destructive actions by itself;
those actions must still pass through Maya's control/approval layer.
"""
import json, os, sqlite3, threading, uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

DB_PATH = os.getenv("MAYA_PROACTIVE_DB", os.path.join(os.path.dirname(__file__), "maya_proactive.db"))
LOCK = threading.Lock()

class MayaProactiveBrain:
    def __init__(self, db_path=DB_PATH):
        self.db_path=db_path; self._init()
    def _conn(self):
        c=sqlite3.connect(self.db_path, check_same_thread=False); c.row_factory=sqlite3.Row; return c
    def _init(self):
        with LOCK, self._conn() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS memories(
                id TEXT PRIMARY KEY, kind TEXT NOT NULL, key TEXT NOT NULL,
                value_json TEXT NOT NULL, confidence REAL DEFAULT 1.0,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                UNIQUE(kind,key))""")
            c.execute("""CREATE TABLE IF NOT EXISTS routines(
                id TEXT PRIMARY KEY, name TEXT NOT NULL, prompt TEXT NOT NULL,
                schedule TEXT NOT NULL, enabled INTEGER DEFAULT 1,
                requires_approval INTEGER DEFAULT 1, last_run TEXT,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")
    @staticmethod
    def now(): return datetime.now(timezone.utc).isoformat()
    def remember(self, kind, key, value, confidence=1.0):
        now=self.now(); mid=str(uuid.uuid4())
        with LOCK, self._conn() as c:
            c.execute("""INSERT INTO memories(id,kind,key,value_json,confidence,created_at,updated_at)
                       VALUES(?,?,?,?,?,?,?) ON CONFLICT(kind,key) DO UPDATE SET value_json=excluded.value_json,confidence=excluded.confidence,updated_at=excluded.updated_at""",
                      (mid,kind,key,json.dumps(value,ensure_ascii=False),confidence,now,now))
        return self.get_memory(kind,key)
    def get_memory(self,kind,key):
        with self._conn() as c: r=c.execute("SELECT * FROM memories WHERE kind=? AND key=?",(kind,key)).fetchone()
        if not r:return None
        d=dict(r); d["value"]=json.loads(d.pop("value_json")); return d
    def search_memories(self, query, limit=20):
        q=f"%{query.lower()}%"
        with self._conn() as c: rows=c.execute("SELECT * FROM memories WHERE lower(key) LIKE ? OR lower(value_json) LIKE ? ORDER BY updated_at DESC LIMIT ?",(q,q,limit)).fetchall()
        out=[]
        for r in rows:
            d=dict(r); d["value"]=json.loads(d.pop("value_json")); out.append(d)
        return out
    def add_routine(self,name,prompt,schedule,requires_approval=True):
        rid=str(uuid.uuid4()); now=self.now()
        with LOCK,self._conn() as c:
            c.execute("INSERT INTO routines(id,name,prompt,schedule,enabled,requires_approval,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",(rid,name,prompt,schedule,1,int(requires_approval),now,now))
        return self.get_routine(rid)
    def get_routine(self,rid):
        with self._conn() as c:r=c.execute("SELECT * FROM routines WHERE id=?",(rid,)).fetchone()
        return dict(r) if r else None
    def list_routines(self,enabled_only=False):
        with self._conn() as c:
            rows=c.execute("SELECT * FROM routines WHERE enabled=1 ORDER BY created_at DESC" if enabled_only else "SELECT * FROM routines ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]
    def set_routine_enabled(self,rid,enabled):
        with LOCK,self._conn() as c:c.execute("UPDATE routines SET enabled=?,updated_at=? WHERE id=?",(int(enabled),self.now(),rid))
        return self.get_routine(rid)

    def build_context(self, query, limit=6):
        memories=self.search_memories(query,limit)
        if not memories:return ""
        return "\n".join(f"- {m['kind']}/{m['key']}: {m['value']}" for m in memories)
