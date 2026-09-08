import json
import os
from datetime import datetime, timezone
from typing import List, Optional

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


SPEAKER_POSTS_META_SEED = {"lastChecked": "2026-09-07", "checkFrequency": "Biweekly (automated)"}

SPEAKER_POSTS_SEED = [
    {"name": "Jessica Shepherd", "linkedin": "linkedin.com/in/jessica-shepherd-md-mba-facog-5ba9ab66", "instagram": "@jessicashepherdmd", "photo": "", "status": "confirmed", "note": "",
     "posts": [{"platform": "linkedin", "type": "Repost", "date": "2026-07-17", "snippet": "Bringing the heat to #brilliance26! So excited", "url": "https://linkedin.com/posts/jessica-shepherd-md-mba-facog-5ba9ab66_brilliance26-activity-7483953557306621952-DMQn"}]},
    {"name": "Candace Doby", "linkedin": "linkedin.com/in/candacedoby", "instagram": "@candacedoby", "photo": "", "status": "confirmed", "note": "",
     "posts": [{"platform": "linkedin", "type": "Repost", "date": "2026-07-17", "snippet": "Excited to be in the room with so much brilliance and share some of my own", "url": "https://linkedin.com/posts/candacedoby_excited-to-be-in-the-room-with-so-much-brilliance-activity-7484079419981017088-2kKj"}]},
    {"name": "Therese Gopaul-Robinson", "linkedin": "linkedin.com/in/theresegopaul-robinson", "instagram": "@therese_gopaulrobinson", "photo": "", "status": "confirmed", "note": "",
     "posts": [{"platform": "linkedin", "type": "Photo", "date": "2026-07-21", "snippet": "Keynote recap: \"The Work Behind the Work\" at Vituity's Brilliance '26", "url": "https://linkedin.com/posts/theresegopaul-robinson_brilliance26-womeninhealthcare-healthcareleadership-activity-7485328835605897216-gsX0"}]},
    {"name": "Cheldin Barlatt Rumer", "linkedin": "linkedin.com/in/cheldinbarlatt", "instagram": "@cheldinbarlatt", "photo": "", "status": "confirmed", "note": "",
     "posts": [{"platform": "linkedin", "type": "Text", "date": "2026-06-24", "snippet": "ATLANTA, HERE I COME! I can't wait for #Brilliance26 from Vituity — \"Women Creating the Future of Health\"", "url": "https://linkedin.com/posts/cheldinbarlatt_brilliance26-brilliance26-womeninhealthcare-activity-7475665634199212033-oJXI"}]},
    {"name": "Irena \"Ren\" Vitkovitsky", "linkedin": "linkedin.com/in/irena-vitkovitsky-44688b97", "instagram": "", "photo": "", "status": "confirmed", "note": "",
     "posts": [{"platform": "linkedin", "type": "Text", "date": "2026-08-04", "snippet": "As Vice President of Operations at Vituity, I am thrilled to speak at our upcoming event, Brilliance26, Women Creating the Future of Health, at the Hilton Atlanta on October 15! In our session on \"Clinical Leadership,\" Nicole Braxley and Payton McGowen and I will discuss how physician leaders can transition from clinical execution to strategic design.", "url": "https://www.linkedin.com/posts/irena-vitkovitsky-44688b97_brilliance26-clinicalleadership-physicianleaders-activity-7490459260162555904-9_Tw"}]},
    {"name": "Alicia O'Brien", "linkedin": "linkedin.com/in/alicia-c-obrien", "instagram": "", "photo": "", "status": "pending", "note": "", "posts": []},
    {"name": "Allison Kassir", "linkedin": "linkedin.com/in/allison-kassir-a3690725", "instagram": "", "photo": "", "status": "pending", "note": "", "posts": []},
    {"name": "Diane L. Martin", "linkedin": "linkedin.com/in/dianelmartin", "instagram": "", "photo": "", "status": "confirmed", "note": "",
     "posts": [{"platform": "linkedin", "type": "Text", "date": "2026-07-28", "snippet": "Women in Health takes the national stage. It's an honor to be invited by Imamu Tomlinson, MD, MBA, CEO, Vituity and Tennille Lowery to participate in a meaningful #Brilliance26 panel.", "url": "https://linkedin.com/posts/dianelmartin_brilliance26-womeninhealthcare-healthcareleadership-activity-7487899674251739136-ooK-"}]},
    {"name": "Maureen Bell", "linkedin": "linkedin.com/in/maureen-bell-58536754", "instagram": "", "photo": "", "status": "confirmed", "note": "",
     "posts": [{"platform": "linkedin", "type": "Carousel", "date": "2026-04-15", "snippet": "The room was packed for our Becker's Healthcare \"Leading with #BRILLIANCE\" panel!... Women are #creatingthefuture of #health. I would love to continue this discussion at #BRILLIANCE26 in Atlanta.", "url": "https://www.linkedin.com/posts/maureen-bell-md-58536754_brilliance-womeninleadership-creatingthefuture-activity-7450317101933694976-ARoK"}]},
    {"name": "Nicole \"Nicki\" Braxley", "linkedin": "linkedin.com/in/nicole-braxley-21449325b", "instagram": "", "photo": "", "status": "pending", "note": "", "posts": []},
    {"name": "Nicole Franks", "linkedin": "linkedin.com/in/nicole-m-franks-md-4759b09", "instagram": "", "photo": "", "status": "pending", "note": "", "posts": []},
    {"name": "Payton McGowen (Hoffner)", "linkedin": "linkedin.com/in/payton-mcgowen-hoffner-aa08b0174", "instagram": "", "photo": "", "status": "pending", "note": "", "posts": []},
    {"name": "Tamika Newson", "linkedin": "linkedin.com/in/tamikanewson", "instagram": "", "photo": "", "status": "confirmed", "note": "",
     "posts": [{"platform": "linkedin", "type": "Repost", "date": "2026-07-18", "snippet": "What an honor to be a part of this event with these amazing and accomplished women! #Brilliance26", "url": "https://linkedin.com/posts/tamikanewson_what-an-honor-to-be-a-part-of-this-event-activity-7484235593133101056-NOVx"}]},
    {"name": "Alina Moran", "linkedin": "linkedin.com/in/alinamoran", "instagram": "", "photo": "", "status": "pending", "note": "", "posts": []},
    {"name": "Angie Cosca", "linkedin": "linkedin.com/in/angeline-cosca", "instagram": "", "photo": "", "status": "pending", "note": "", "posts": []},
    {"name": "Andrea Turner", "linkedin": "linkedin.com/in/andrea-turner-jd-mba-cnmt-6621641a2", "instagram": "", "photo": "", "status": "pending", "note": "", "posts": []},
    {"name": "Debra Green Oliphant", "linkedin": "linkedin.com/in/debra-green-oliphant", "instagram": "", "photo": "", "status": "pending", "note": "", "posts": []},
    {"name": "Lara Khouri", "linkedin": "linkedin.com/in/lara-m-khouri", "instagram": "", "photo": "", "status": "pending", "note": "", "posts": []},
    {"name": "Nanea Reeves", "linkedin": "linkedin.com/in/naneareeves", "instagram": "", "photo": "", "status": "pending", "note": "", "posts": []},
    {"name": "Sara Duarte Rico", "linkedin": "linkedin.com/in/sara-rico", "instagram": "", "photo": "", "status": "pending", "note": "", "posts": []},
    {"name": "Judith Joseph", "linkedin": "linkedin.com/in/drjudithjosephmdmba", "instagram": "@drjudithjoseph", "photo": "", "status": "pending", "note": "", "posts": []},
    {"name": "Lauren Smith", "linkedin": "linkedin.com/in/lauren-smith-md-mba-2a71402", "instagram": "", "photo": "", "status": "confirmed", "note": "",
     "posts": [{"platform": "linkedin", "type": "Text", "date": "2026-08-31", "snippet": "I'm delighted to be speaking at Brilliance26, Women Creating the Future of Health, hosted by Vituity at the Hilton Atlanta October 15.", "url": "https://www.linkedin.com/posts/lauren-smith-md-mba-2a71402_brilliance26-healthcareleadership-womeninhealth-activity-7500292833564643328-xuNp"}]},
    {"name": "Maria Sexton", "linkedin": "linkedin.com/in/mariasexton", "instagram": "", "photo": "", "status": "pending", "note": "", "posts": []},
    {"name": "Yolanda Milton Christopher", "linkedin": "linkedin.com/in/yolandamilton", "instagram": "@yolandachristopher", "photo": "", "status": "pending", "note": "", "posts": []},
]


def init_db():
    with get_db() as conn:
        for stmt in db_schema():
            conn.execute(stmt)
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

        cur = conn.execute("SELECT COUNT(*) AS c FROM speaker_posts")
        row = cur.fetchone()
        count = row["c"] if row is not None else 0
        if not count:
            for s in SPEAKER_POSTS_SEED:
                conn.execute(
                    "INSERT INTO speaker_posts (name, linkedin, instagram, photo, status, note, posts) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (s["name"], s["linkedin"], s["instagram"], s["photo"], s["status"], s["note"], json.dumps(s["posts"])),
                )
            cur = conn.execute("SELECT COUNT(*) AS c FROM speaker_posts_meta")
            if not cur.fetchone()["c"]:
                conn.execute(
                    "INSERT INTO speaker_posts_meta (id, last_checked, check_frequency) VALUES (1, ?, ?)",
                    (SPEAKER_POSTS_META_SEED["lastChecked"], SPEAKER_POSTS_META_SEED["checkFrequency"]),
                )
            conn.commit()


init_db()


class NewSpeaker(BaseModel):
    name: str


class UpdateSpeaker(BaseModel):
    name: str


class SpeakerPost(BaseModel):
    platform: str
    type: Optional[str] = ""
    date: Optional[str] = ""
    snippet: Optional[str] = ""
    url: Optional[str] = ""


class SpeakerPostEntry(BaseModel):
    name: str
    linkedin: Optional[str] = ""
    instagram: Optional[str] = ""
    photo: Optional[str] = ""
    status: str = "pending"
    note: Optional[str] = ""
    posts: List[SpeakerPost] = []


class SpeakerPostsMeta(BaseModel):
    lastChecked: str
    checkFrequency: str = "Biweekly (automated)"


class SpeakerPostsPayload(BaseModel):
    meta: SpeakerPostsMeta
    speakers: List[SpeakerPostEntry]


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


@app.patch("/api/links/{link_id}")
def update_link(link_id: int, payload: UpdateSpeaker):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    token = name_to_token(name)
    if not token:
        raise HTTPException(status_code=400, detail="Could not generate a link from that name")

    with get_db() as conn:
        cur = conn.execute("SELECT * FROM speaker_links WHERE id = ?", (link_id,))
        if cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="Speaker not found")
        conn.execute(
            "UPDATE speaker_links SET name = ?, token = ? WHERE id = ?",
            (name, token, link_id),
        )
        conn.commit()
        cur = conn.execute("SELECT * FROM speaker_links WHERE id = ?", (link_id,))
        return serialize(cur.fetchone())


@app.delete("/api/links/{link_id}")
def delete_link(link_id: int):
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM speaker_links WHERE id = ?", (link_id,))
        if cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="Speaker not found")
        conn.execute("DELETE FROM speaker_links WHERE id = ?", (link_id,))
        conn.commit()
        return {"ok": True}


def serialize_speaker_post(row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "linkedin": row["linkedin"],
        "instagram": row["instagram"],
        "photo": row["photo"],
        "status": row["status"],
        "note": row["note"],
        "posts": json.loads(row["posts"]),
    }


@app.get("/api/speaker-posts")
def list_speaker_posts():
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM speaker_posts ORDER BY id ASC")
        speakers = [serialize_speaker_post(r) for r in cur.fetchall()]
        cur = conn.execute("SELECT * FROM speaker_posts_meta WHERE id = 1")
        meta_row = cur.fetchone()
        meta = (
            {"lastChecked": meta_row["last_checked"], "checkFrequency": meta_row["check_frequency"]}
            if meta_row is not None
            else {"lastChecked": "", "checkFrequency": "Biweekly (automated)"}
        )
        return {"meta": meta, "speakers": speakers}


@app.put("/api/speaker-posts")
def replace_speaker_posts(payload: SpeakerPostsPayload):
    """Full replace, called by the automated biweekly refresh. Wipes and re-inserts every speaker."""
    with get_db() as conn:
        conn.execute("DELETE FROM speaker_posts")
        for s in payload.speakers:
            conn.execute(
                "INSERT INTO speaker_posts (name, linkedin, instagram, photo, status, note, posts) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    s.name,
                    s.linkedin or "",
                    s.instagram or "",
                    s.photo or "",
                    s.status,
                    s.note or "",
                    json.dumps([p.model_dump() for p in s.posts]),
                ),
            )
        cur = conn.execute("SELECT COUNT(*) AS c FROM speaker_posts_meta WHERE id = 1")
        if cur.fetchone()["c"]:
            conn.execute(
                "UPDATE speaker_posts_meta SET last_checked = ?, check_frequency = ? WHERE id = 1",
                (payload.meta.lastChecked, payload.meta.checkFrequency),
            )
        else:
            conn.execute(
                "INSERT INTO speaker_posts_meta (id, last_checked, check_frequency) VALUES (1, ?, ?)",
                (payload.meta.lastChecked, payload.meta.checkFrequency),
            )
        conn.commit()
        return {"ok": True, "count": len(payload.speakers)}
