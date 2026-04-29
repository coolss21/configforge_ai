import sqlite3
import logging
from typing import Dict, Any, List

logger = logging.getLogger("configforge.runtime")


class SQLiteRuntime:
    def __init__(self):
        self.conn   = sqlite3.connect(":memory:")
        self.cursor = self.conn.cursor()

    def create_database(self, db_schema: Dict[str, Any]) -> tuple:
        tables_created = []
        errors         = []
        for table in db_schema.get("tables", []):
            try:
                table_name = table["name"]
                col_defs   = []
                for field in table["fields"]:
                    f_def = f"{field['name']} {field['type']}"
                    if field.get("primary_key"):
                        f_def += " PRIMARY KEY"
                    if not field.get("nullable", True):
                        f_def += " NOT NULL"
                    if field.get("unique"):
                        f_def += " UNIQUE"
                    if field.get("references"):
                        ref    = field["references"]
                        f_def += f" REFERENCES {ref['table']}({ref['field']})"
                    col_defs.append(f_def)
                self.cursor.execute(f"CREATE TABLE {table_name} ({', '.join(col_defs)});")
                tables_created.append(table_name)
            except Exception as e:
                errors.append(f"Failed to create table {table.get('name')}: {e}")
        return len(errors) == 0, tables_created, errors

    def simulate_endpoint(
        self,
        method: str,
        path: str,
        table_name: str,
        fields: List[dict],
        context: dict,
    ) -> dict:
        """
        Simulate one API endpoint against the in-memory DB.
        context is shared per-entity (holds _seq counter + last_id).
        Result operation label is exactly "METHOD /path".
        """
        op_key = f"{method.upper()} {path}"
        try:
            m = method.upper()

            # Increment unique sequence per call to avoid UNIQUE constraint clashes
            seq = context.get("_seq", 0) + 1
            context["_seq"] = seq

            # Insertable columns (no PK, no raw 'id')
            ins_fields = [
                f for f in fields
                if not f.get("primary_key") and f["name"].lower() != "id"
            ] or fields  # fallback: use all if everything is PK

            ins_cols = [f["name"] for f in ins_fields]

            def _uval(f):
                ft = f.get("type", "TEXT").upper()
                if "INT" in ft:
                    return seq           # unique integer per call
                if "BOOL" in ft:
                    return 1
                return f"val_{f['name']}_{seq}"   # unique string per col per call

            ins_vals = [_uval(f) for f in ins_fields]

            if m == "POST":
                if ins_cols:
                    self.cursor.execute(
                        f"INSERT INTO {table_name} ({', '.join(ins_cols)}) "
                        f"VALUES ({', '.join(['?']*len(ins_cols))})",
                        ins_vals,
                    )
                    row_id = self.cursor.lastrowid
                else:
                    self.cursor.execute(f"INSERT INTO {table_name} DEFAULT VALUES")
                    row_id = self.cursor.lastrowid
                context["last_id"] = row_id
                return {"operation": op_key, "success": True,
                        "message": f"Inserted row id {row_id}"}

            elif m == "GET":
                if "{id}" in path or "/:id" in path:
                    row_id = context.get("last_id", 1)
                    self.cursor.execute(
                        f"SELECT * FROM {table_name} WHERE rowid = ?", (row_id,)
                    )
                    row = self.cursor.fetchone()
                    ok = row is not None
                    return {"operation": op_key, "success": ok,
                            "message": f"Fetched record id {row_id}" if ok
                                       else f"Record {row_id} not found"}
                else:
                    self.cursor.execute(f"SELECT * FROM {table_name}")
                    rows = self.cursor.fetchall()
                    return {"operation": op_key, "success": True,
                            "message": f"Fetched {len(rows)} records"}

            elif m in ("PATCH", "PUT"):
                row_id = context.get("last_id", 1)
                if ins_cols:
                    set_clause = ", ".join([f"{c} = ?" for c in ins_cols])
                    self.cursor.execute(
                        f"UPDATE {table_name} SET {set_clause} WHERE rowid = ?",
                        ins_vals + [row_id],
                    )
                return {"operation": op_key, "success": True,
                        "message": f"Updated record id {row_id}"}

            elif m == "DELETE":
                row_id = context.get("last_id", 1)
                self.cursor.execute(
                    f"DELETE FROM {table_name} WHERE rowid = ?", (row_id,)
                )
                return {"operation": op_key, "success": True,
                        "message": f"Deleted record id {row_id}"}

            else:
                return {"operation": op_key, "success": True,
                        "message": f"Skipped unsupported method {m}"}

        except Exception as exc:
            return {"operation": op_key, "success": False, "message": str(exc)}

    def simulate_crud(self, table_name: str, fields: list) -> list:
        """Legacy: simulate 5 CRUD ops with generic paths."""
        ctx = {}
        ops = [
            ("POST",   f"/api/{table_name}"),
            ("GET",    f"/api/{table_name}"),
            ("GET",    f"/api/{table_name}/{{id}}"),
            ("PATCH",  f"/api/{table_name}/{{id}}"),
            ("DELETE", f"/api/{table_name}/{{id}}"),
        ]
        return [self.simulate_endpoint(m, p, table_name, fields, ctx) for m, p in ops]

    def close(self):
        self.conn.close()
