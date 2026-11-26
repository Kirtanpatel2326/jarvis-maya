"""Stage 6: Maya Control Center.
Persistent task state, action history, and approval gates for sensitive actions.
No secrets are stored here; use environment variables for credentials.
"""
import json, os, sqlite3, threading, uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

DB_PATH = os.getenv("MAYA_CONTROL_DB", os.path.join(os.path.dirname(__file__), "maya_control.db"))
_LOCK = threading.Lock()

class MayaControlCenter:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init()

    def _conn(self):
        c = sqlite3.connect(self.db_path, check_same_thread=False)
        c.row_factory = sqlite3.Row
        return c

    def _init(self):
        with _LOCK, self._conn() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY, goal TEXT NOT NULL, status TEXT NOT NULL,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                current_step INTEGER DEFAULT 0, result_json TEXT, metadata_json TEXT
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, step INTEGER,
                action TEXT, args_json TEXT, result_json TEXT, created_at TEXT NOT NULL
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS approvals (
                id TEXT PRIMARY KEY, task_id TEXT, action TEXT NOT NULL,
                details_json TEXT, status TEXT NOT NULL, created_at TEXT NOT NULL,
                resolved_at TEXT
            )""")

    @staticmethod
    def now(): return datetime.now(timezone.utc).isoformat()

    def create_task(self, goal: str, metadata: Optional[Dict[str, Any]]=None):
        tid = str(uuid.uuid4()); now = self.now()
        with _LOCK, self._conn() as c:
            c.execute("INSERT INTO tasks(id,goal,status,created_at,updated_at,metadata_json) VALUES(?,?,?,?,?,?)",
                      (tid, goal, "running", now, now, json.dumps(metadata or {})))
        return self.get_task(tid)

    def update_task(self, task_id, status=None, step=None, result=None):
        fields=[]; vals=[]
        if status is not None: fields += ["status=?"]; vals += [status]
        if step is not None: fields += ["current_step=?"]; vals += [step]
        if result is not None: fields += ["result_json=?"]; vals += [json.dumps(result, ensure_ascii=False)]
        fields += ["updated_at=?"]; vals += [self.now()]; vals += [task_id]
        with _LOCK, self._conn() as c:
            c.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id=?", vals)
        return self.get_task(task_id)

    def get_task(self, task_id):
        with self._conn() as c:
            r=c.execute("SELECT * FROM tasks WHERE id=?",(task_id,)).fetchone()
        if not r: return None
        d=dict(r); d["result"]=json.loads(d.pop("result_json") or "null"); d["metadata"]=json.loads(d.pop("metadata_json") or "{}")
        return d

    def list_tasks(self, limit=25):
        with self._conn() as c:
            rows=c.execute("SELECT * FROM tasks ORDER BY updated_at DESC LIMIT ?",(limit,)).fetchall()
        return [self._task_row(r) for r in rows]

    def _task_row(self,r):
        d=dict(r); d["result"]=json.loads(d.pop("result_json") or "null"); d["metadata"]=json.loads(d.pop("metadata_json") or "{}")
        return d

    def log_action(self, task_id, step, action, args, result):
        with _LOCK, self._conn() as c:
            c.execute("INSERT INTO actions(task_id,step,action,args_json,result_json,created_at) VALUES(?,?,?,?,?,?)",
                      (task_id,step,action,json.dumps(args,ensure_ascii=False),json.dumps(result,ensure_ascii=False),self.now()))

    def history(self, task_id, limit=100):
        with self._conn() as c:
            rows=c.execute("SELECT * FROM actions WHERE task_id=? ORDER BY id DESC LIMIT ?",(task_id,limit)).fetchall()
        out=[]
        for r in rows:
            d=dict(r); d["args"]=json.loads(d.pop("args_json")); d["result"]=json.loads(d.pop("result_json")); out.append(d)
        return out

    def request_approval(self, task_id, action, details=None):
        aid=str(uuid.uuid4()); now=self.now()
        with _LOCK, self._conn() as c:
            c.execute("INSERT INTO approvals(id,task_id,action,details_json,status,created_at) VALUES(?,?,?,?,?,?)",
                      (aid,task_id,action,json.dumps(details or {},ensure_ascii=False),"pending",now))
        return self.get_approval(aid)

    def resolve_approval(self, approval_id, approved):
        status="approved" if approved else "denied"
        with _LOCK, self._conn() as c:
            c.execute("UPDATE approvals SET status=?,resolved_at=? WHERE id=?",(status,self.now(),approval_id))
        return self.get_approval(approval_id)

    def get_approval(self, approval_id):
        with self._conn() as c: r=c.execute("SELECT * FROM approvals WHERE id=?",(approval_id,)).fetchone()
        if not r: return None
        d=dict(r); d["details"]=json.loads(d.pop("details_json") or "{}"); return d

    def pending_approvals(self, task_id=None):
        with self._conn() as c:
            if task_id: rows=c.execute("SELECT * FROM approvals WHERE task_id=? AND status='pending' ORDER BY created_at",(task_id,)).fetchall()
            else: rows=c.execute("SELECT * FROM approvals WHERE status='pending' ORDER BY created_at").fetchall()
        out=[]
        for r in rows:
            d=dict(r); d["details"]=json.loads(d.pop("details_json") or "{}"); out.append(d)
        return out
