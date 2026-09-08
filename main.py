import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from pydantic import BaseModel

from db import get_db, db_schema

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

CVENT_BASE_URL = "https://web.cvent.com/event/a0662d72-4021-4faa-8fd4-6e7f0942196a/summary"

SEED_NAMES = [
    "Alicia O'Brien", "Allison Kassir", "Candace Doby", "Cheldin Barlatt Rumer", "Diane Martin",
    "Irena Vitkovitsky", "Jessica Shepherd", "Maureen Bell", "Nicole Braxley", "Nicole Franks",
    "Payton McGowen", "Tamika Newson", "Therese Gopaul-Robinson", "Alina Moran", "Andrea Turner",
    "Lara Khouri", "Debra Green", "Nanea Reeves", "Angie Cosca", "Sara Duarte Rico",
    "Yolanda Milton Christopher", "Maria Sexton", "Lauren Smith", "Aisha Terry", "Judith Joseph",
    "Roja Garimella",
]


def name_to_token(name: str) -> str:
    def cap_part(part: str) -> str:
        if not part:
            return part
        if "'" in part:
            return "".join(seg.lower().capitalize() for seg in part.split("'"))
        lower = part.lower()
        if lower.startswith("mc") and len(lower) > 2:
            return "Mc" + lower[2:].capitalize()
        if lower.startswith("mac") and len(lower) > 3:
            return "Mac" + lower[3:].capitalize()
        return lower.capitalize()

    words = name.strip().split()
    return "_".join("-".join(cap_part(p) for p in w.split("-")) for w in words)


def build_url(token: str) -> str:
    return (
        f"{CVENT_BASE_URL}?utm_source=OUT&utm_medium=speaker"
        f"&utm_campaign=BD_2026_Q3_OUT:Brilliance_Outreach_{token}&utm_content=Brilliance"
    )


def init_db():
    with get_db() as conn:
        conn.execute(db_schema())
        conn.commit()
        cur = conn.execute("SELECT COUNT(*) AS c FROM speaker_links")
        row = cur.fetchone()
        count = row["c"] if row is not None else 0
        if not count:
            now = datetime.now(timezone.utc).isoformat()
            for name in SEED_NAMES:
                conn.execute(
                    "INSERT INTO speaker_links (name, token, origin, created_at) VALUES (?, ?, ?, ?)",
                    (name, name_to_token(name), "seed", now),
                )
            conn.commit()


init_db()


class NewSpeaker(BaseModel):
    name: str


def serialize(row) -> dict:
    token = row["token"]
    return {
        "id": row["id"],
        "name": row["name"],
        "token": token,
        "origin": row["origin"],
        "created_at": row["created_at"],
        "url": build_url(token),
    }


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@app.get("/api/links")
def list_links():
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM speaker_links ORDER BY id ASC")
        rows = cur.fetchall()
        return [serialize(r) for r in rows]


@app.post("/api/links")
def create_link(payload: NewSpeaker):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    token = name_to_token(name)
    if not token:
        raise HTTPException(status_code=400, detail="Could not generate a link from that name")

    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        new_id = conn.insert_id(
            "INSERT INTO speaker_links (name, token, origin, created_at) VALUES (?, ?, ?, ?)",
            (name, token, "new", now),
        )
        conn.commit()
        cur = conn.execute("SELECT * FROM speaker_links WHERE id = ?", (new_id,))
        row = cur.fetchone()
        return serialize(row)
