# rubika_font_bot_full.py
# Single-file Rubika font bot implementation (all in one)
# Usage: put your token in TOKEN variable and run with Python 3
# Requires: requests
# Encoding: UTF-8

import requests
import json
import time
import os
import re
from datetime import datetime

# ----------------------------
# CONFIG
# ----------------------------
TOKEN = "DBECE0WVNJVTLXRFGWYQZPQWTAIARCZYYSGHWUNODOHDWQKAEQYCUNPJNLVLTOOJ"  # <-- paste your Rubika bot token here
BASE = f"https://botapi.rubika.ir/v3/{TOKEN}/"
STATE_FILE = "rubika_font_bot_state.json"
POLL = 1.2  # seconds between polls
MAX_REPLY_CHARS = 4000  # cut replies if too long

# ----------------------------
# Utilities
# ----------------------------
_persian_re = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]')

def is_persian_text(s: str) -> bool:
    return bool(_persian_re.search(s))

def is_english_text(s: str) -> bool:
    return bool(re.search(r'[A-Za-z]', s))

def is_number_text(s: str) -> bool:
    return bool(re.fullmatch(r'\d+', s.strip()))

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"offset": None}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"offset": None}

def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)
    except Exception as e:
        print("save_state error:", e)

def post(method: str, payload: dict, timeout=20):
    url = BASE + method
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        return r
    except Exception as e:
        print("HTTP request failed:", e)
        return None

# ----------------------------
# Jalali converter (gregorian -> jalali)
# Implementation adapted to be self-contained (valid for common ranges)
# ----------------------------
def gregorian_to_jalali(gy, gm, gd):
    g_d_m = [0,31,59,90,120,151,181,212,243,273,304,334]
    if (gy > 1600):
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621
    if (gm > 2):
        gy2 = gy + 1
    else:
        gy2 = gy
    days = 365*gy + (gy2+3)//4 - (gy2+99)//100 + (gy2+399)//400 - 80 + gd + g_d_m[gm-1]
    jy += 33*(days//12053)
    days %= 12053
    jy += 4*(days//1461)
    days %= 1461
    if (days > 365):
        jy += (days-1)//365
        days = (days-1)%365
    if days < 186:
        jm = 1 + days//31
        jd = 1 + (days%31)
    else:
        jm = 7 + (days-186)//30
        jd = 1 + (days-186)%30
    return jy, jm, jd

def now_jalali():
    dt = datetime.now()
    jy, jm, jd = gregorian_to_jalali(dt.year, dt.month, dt.day)
    hh = dt.hour
    mm = dt.minute
    return f"{jy:04d}/{jm:02d}/{jd:02d} {hh:02d}:{mm:02d}"

# ----------------------------
# Font transformation collections
# These collections include many of the styles you provided.
# Each function returns a plain string (no labels).
# ----------------------------

# --- English fonts (examples collected from your requested sets) ---
def en_original(s): return s
def en_upper(s): return s.upper()
def en_lower(s): return s.lower()
def en_title(s): return s.title()
def en_swapcase(s): return s.swapcase()
def en_spaced(s): return " ".join(list(s))
def en_double_spaced(s): return "  ".join(list(s))
def en_fullwidth(s):
    out = []
    for ch in s:
        o = ord(ch)
        if 0x21 <= o <= 0x7E:
            out.append(chr(o + 0xFF00 - 0x20))
        else:
            out.append(ch)
    return ''.join(out)

SMALLCAPS_MAP = {
    'a':'ᴀ','b':'ʙ','c':'ᴄ','d':'ᴅ','e':'ᴇ','f':'ꜰ','g':'ɢ','h':'ʜ','i':'ɪ',
    'j':'ᴊ','k':'ᴋ','l':'ʟ','m':'ᴍ','n':'ɴ','o':'ᴏ','p':'ᴘ','q':'ǫ','r':'ʀ',
    's':'s','t':'ᴛ','u':'ᴜ','v':'ᴠ','w':'ᴡ','x':'x','y':'ʏ','z':'ᴢ'
}
def en_smallcaps(s):
    return ''.join(SMALLCAPS_MAP.get(ch.lower(), ch) for ch in s)

# bold/italic/unicode families (examples)
def en_bold_unicode(s):
    out=[]
    for ch in s:
        if 'A' <= ch <= 'Z':
            out.append(chr(0x1D400 + (ord(ch)-ord('A'))))
        elif 'a' <= ch <= 'z':
            out.append(chr(0x1D41A + (ord(ch)-ord('a'))))
        else:
            out.append(ch)
    return ''.join(out)

def en_italic_unicode(s):
    out=[]
    for ch in s:
        if 'a' <= ch <= 'z':
            out.append(chr(0x1D44E + (ord(ch)-ord('a'))))
        elif 'A' <= ch <= 'Z':
            out.append(chr(0x1D434 + (ord(ch)-ord('A'))))
        else:
            out.append(ch)
    return ''.join(out)

def en_monospace(s):
    return ''.join(chr(0x1D670 + (ord(ch)-ord('a'))) if 'a'<=ch<='z' else (chr(0x1D7F6 + ord(ch)-48) if '0'<=ch<='9' else ch) for ch in s.lower())

def en_double_struck(s):
    out=[]
    for ch in s:
        if 'A'<=ch<='Z':
            out.append(chr(0x1D538 + (ord(ch)-ord('A'))))
        elif 'a'<=ch<='z':
            out.append(chr(0x1D552 + (ord(ch)-ord('a'))))
        else:
            out.append(ch)
    return ''.join(out)

def en_circled(s):
    out=[]
    circ = "ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩ"
    for ch in s:
        if ch.isalpha():
            idx = ord(ch.lower())-97
            if 0 <= idx < 26:
                out.append(circ[idx])
            else:
                out.append(ch)
        else:
            out.append(ch)
    return ''.join(out)

def en_unicode_variants(s):
    # a few other font families (subset)
    funcs = [en_original, en_upper, en_lower, en_title, en_swapcase,
             en_spaced, en_double_spaced, en_fullwidth, en_smallcaps,
             en_bold_unicode, en_italic_unicode, en_double_struck,
             en_circled]
    results = []
    for fn in funcs:
        try:
            results.append(fn(s))
        except Exception:
            continue
    return results

# join / wrapper helpers (these create many non-overlapping variants)
def wrap_star(s): return f"★ {s} ★"
def wrap_bracket(s): return f"[{s}]"
def wrap_square(s): return f""
def wrap_cute(s): return f"꧁{s}꧂"
def wrap_flower(s): return f"✿{s}✿"
def wrap_circle(s): return f"◦{s}◦"
def join_dot(s): return '·'.join(list(s))
def join_dash(s): return '-'.join(list(s))
def join_underscore(s): return '_'.join(list(s))
def join_pipe(s): return '|'.join(list(s))
def join_bullet(s): return '•'.join(list(s))
def quote_double(s): return f"\"{s}\""
def quote_single(s): return f"'{s}'"

# --- Persian fonts (many styles inspired by user's samples) ---
def pers_original(s): return s
def pers_tatweel_between_chars(s):
    parts = s.split(' ')
    out=[]
    for p in parts:
        out.append('ـ'.join(list(p)))
    return ' '.join(out)

def pers_zwnj_spread(s):
    parts=s.split(' ')
    out=[]
    for p in parts:
        out.append('\u200c'.join(list(p)))
    return ' '.join(out)

PERS_DIAC = ''.join(['\u0651','\u064E','\u0650','\u0652','\u0654'])  # sample diacritics
def pers_with_diacritics(s):
    out=[]
    for ch in s:
        if _persian_re.match(ch):
            out.append(ch + PERS_DIAC)
        else:
            out.append(ch)
    return ''.join(out)

def pers_heavy(s):
    core = pers_tatweel_between_chars(s)
    core = pers_with_diacritics(core)
    return core

def pers_wrapped_variants(s):
    wraps = [("『","』"),("【","】"),("★","★"),("✿","✿"),("꧁","꧂"),("◦","◦")]
    res=[]
    for l,r in wraps:
        res.append(f"{l}{s}{r}")
    return res

# a set of Persian ornamental variants using characters user provided
def pers_fancy_set(s):
    res=[]
    # simple decorative insertions and repeating diacritics
    res.append(s)  # original
    res.append('ـ'.join(list(s)))
    res.append('\u200c'.join(list(s)))
    res.append(''.join(ch + '\u064E' for ch in s))  # small vowel mark
    res.append(''.join(ch + '\u0650' for ch in s))
    res.extend(pers_wrapped_variants(s))
    # some custom fancy ones from user's list
    extra = [
        "༺","༻","✦","✶","❂","❄","✿","꧁","꧂","『","』","【","】","◦"
    ]
    for sym in extra:
        res.append(f"{sym}{s}{sym}")
    # handcrafted glyph adornments (safe ascii + marks)
    res.append('◌'.join(list(s)))
    res.append('•'.join(list(s)))
    return list(dict.fromkeys(res))  # unique

# --- Number fonts (many variants users listed) ---
NUMBER_VARIANTS = [
    ("0⃣1⃣2⃣3⃣4⃣5⃣6⃣7⃣8⃣9⃣", lambda ch: "0⃣1⃣2⃣3⃣4⃣5⃣6⃣7⃣8⃣9⃣"[int(ch)*2:int(ch)*2+2]),
    ("⓪①②③④⑤⑥⑦⑧⑨", lambda ch: "⓪①②③④⑤⑥⑦⑧⑨"[int(ch)]),
    ("０１２３４５６７８９", lambda ch: "０１２３４５６７８９"[int(ch)]),
    ("⒪⑴⑵⑶⑷⑸⑹⑺⑻⑼", lambda ch: "⒪⑴⑵⑶⑷⑸⑹⑺⑻⑼"[int(ch)]),
    ("₀₁₂₃₄₅₆₇₈₉", lambda ch: "₀₁₂₃₄₅₆₇₈₉"[int(ch)]),
    ("⁰¹²³⁴⁵⁶⁷⁸⁹", lambda ch: "⁰¹²³⁴⁵⁶⁷⁸⁹"[int(ch)]),
    ("𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗", lambda ch: "𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗"[int(ch)]),
    ("𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡", lambda ch: "𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡"[int(ch)]),
    ("𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵", lambda ch: "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"[int(ch)]),
]

def make_number_variants(s):
    out=[]
    digits = ''.join(ch for ch in s if ch.isdigit())
    if digits=="":
        return [s]
    for name, fn in NUMBER_VARIANTS:
        try:
            transformed = ''.join(fn(ch) if ch.isdigit() else ch for ch in s)
            out.append(transformed)
        except Exception:
            continue
    # ensure uniqueness
    return list(dict.fromkeys(out))

# ----------------------------
# Build final lists exactly as user requested:
# - When input is English -> produce EN list (no descriptive labels), many fonts
# - When Persian -> produce Persian fonts (only Persian glyphs)
# - When numbers -> produce numeric fonts
# The user asked for many variants and no extra labels in each item; we'll return
# each variant on its own line prefixed only by numbering markers like: ❲ 1 ❳ <font>
# ----------------------------

def build_english_fonts(text):
    variants = []
    # base families (we'll produce at least ~40 unique variants by combining families + wrappers)
    base_funcs = [
        en_original, en_upper, en_lower, en_title, en_swapcase,
        en_spaced, en_double_spaced, en_fullwidth, en_smallcaps,
        en_bold_unicode, en_italic_unicode, en_double_struck, en_circled
    ]
    for fn in base_funcs:
        try:
            variants.append(fn(text))
        except Exception:
            continue
    # add wrappers / joins
    joiners = [join_dot, join_dash, join_underscore, join_pipe, join_bullet]
    wrappers = [wrap_star, wrap_bracket, wrap_square, wrap_cute, wrap_flower, wrap_circle]
    for j in joiners:
        try:
            variants.append(j(text))
        except Exception:
            pass
    for w in wrappers:
        try:
            variants.append(w(text))
        except Exception:
            pass
    # add more stylistic families using simple translations/compositions
    # --- small stylings from user examples
    # fullwidth + bracket combos
    try:
        variants.append(en_fullwidth(text))
        variants.append(en_circled(text))
        variants.append(en_bold_unicode(text))
    except Exception:
        pass
    # spaced smallcaps
    try:
        sc = en_smallcaps(text)
        variants.append(sc)
        variants.append(" ".join(list(sc)))
    except Exception:
        pass
    # add alternating case
    try:
        alt = ''.join(ch.upper() if i%2==0 else ch.lower() for i,ch in enumerate(text))
        variants.append(alt)
    except Exception:
        pass
    # add repeating/duplicated characters (wide)
    try:
        variants.append(' '.join(ch*2 for ch in text))
    except Exception:
        pass
    # fill up to 40 by creating composed variants deterministically
    i = 0
    composed = []
    while len(variants) + len(composed) < 40 and i < len(wrappers):
        w = wrappers[i % len(wrappers)]
        j = joiners[i % len(joiners)]
        try:
            composed.append(w(j(text)))
        except Exception:
            pass
        i += 1
    allv = variants + composed
    # unique and preserve order
    seen = set(); final=[]
    for v in allv:
        if not v: continue
        if v in seen: continue
        seen.add(v); final.append(v)
        if len(final) >= 40: break
    return final

def build_persian_fonts(text):
    # produce many Persian-only variants (do not produce latin letters)
    base = pers_fancy_set(text)
    # add heavy, tatweel, zwnj, diacritics
    extras = [pers_tatweel_between_chars, pers_zwnj_spread, pers_with_diacritics, pers_heavy]
    for fn in extras:
        try:
            base.append(fn(text))
        except Exception:
            pass
    # add wrappers from pers_wrapped_variants
    base.extend(pers_wrapped_variants(text))
    # deduplicate and keep order; ensure we produce at least 30 variants when possible
    seen=set(); final=[]
    for v in base:
        if not v: continue
        # remove any Latin letters inside (safety)
        if re.search(r'[A-Za-z]', v):
            continue
        if v in seen: continue
        seen.add(v); final.append(v)
        if len(final) >= 40:
            break
    # If still small, add some decorated repeats based on user examples
    if len(final) < 40:
        decorations = ["★","✿","༺","༻","❂","◦","✶","✦","꧁","꧂"]
        for d in decorations:
            s = f"{d}{text}{d}"
            if s not in seen:
                seen.add(s); final.append(s)
                if len(final) >= 40: break
    return final

def build_number_fonts(text):
    return make_number_variants(text)

# ----------------------------
# Message format helpers
# ----------------------------
def format_variants_list(variants):
    # produce numbered list as requested: each line => ❲ n ❳ <variant>
    lines = []
    n = 1
    for v in variants:
        # ensure we do not include newlines inside v
        v_single = v.replace('\n',' ')
        lines.append(f"❲ {n} ❳ {v_single}")
        n += 1
    return "\n".join(lines)

# ----------------------------
# Bot behaviour
# ----------------------------
def handle_start_message(chat_id):
    # start text required by user (without user id)
    start_text = f"🗨 خوش آمدید به ربات فونت ساز|زیبا نویس |𝐄𝐑𝐈𝐊 📢\n📅 {now_jalali()}\n🅰️ کلمه مورد نظر را ارسال کنید."
    send_message(chat_id, start_text)

def send_message(chat_id, text):
    if not text:
        return None
    # cut long messages into chunks if needed to avoid API issues
    if len(text) > MAX_REPLY_CHARS:
        # naive split by lines
        parts = []
        cur = []
        cur_len = 0
        for line in text.splitlines():
            if cur_len + len(line) + 1 > MAX_REPLY_CHARS:
                parts.append("\n".join(cur))
                cur = [line]
                cur_len = len(line)+1
            else:
                cur.append(line)
                cur_len += len(line)+1
        if cur:
            parts.append("\n".join(cur))
    else:
        parts = [text]
    last_resp = None
    for part in parts:
        r = post("sendMessage", {"chat_id": chat_id, "text": part})
        last_resp = r
        # small delay to avoid flooding
        time.sleep(0.12)
    return last_resp

def process_new_message(chat_id, text, sender_id=None):
    txt = text.strip()
    if txt == "":
        return
    # if user sends /start or equivalent, send welcome
    if txt.lower() in ("/start", "start"):
        handle_start_message(chat_id)
        return

    # determine type
    if is_number_text(txt):
        variants = build_number_fonts(txt)
    elif is_persian_text(txt):
        variants = build_persian_fonts(txt)
    else:
        # english
        variants = build_english_fonts(txt)

    # format as numbered list (one per line). The user wanted plain variant lines.
    formatted = format_variants_list(variants)
    send_message(chat_id, formatted)

# ----------------------------
# Main loop: polls getUpdates and processes NewMessage
# ----------------------------
def get_updates(offset=None, limit=20):
    payload = {"limit": limit}
    if offset:
        payload["offset_id"] = offset
    r = post("getUpdates", payload)
    return r

def main():
    if TOKEN == "PUT_YOUR_TOKEN_HERE":
        print("ERROR: Please set TOKEN variable to your bot token.")
        return

    print("🤖 Rubika Font Bot starting...")
    state = load_state()
    offset = state.get("offset")
    first_run = (offset is None)
    print("📌 offset start:", offset, "first_run:", first_run)

    while True:
        try:
            resp = get_updates(offset)
            if resp is None:
                time.sleep(POLL)
                continue
            raw = resp.text or ""
            try:
                j = resp.json()
            except Exception as e:
                # sometimes API returns HTML or empty; skip and wait
                print("❌ getUpdates: invalid JSON:", e, "RAW:", (raw[:200] + "..."))
                time.sleep(POLL)
                continue

            if not isinstance(j, dict):
                print("❌ Unexpected getUpdates response:", j)
                time.sleep(POLL)
                continue

            # normalize
            data = None
            if j.get("status") == "OK" and "data" in j:
                data = j["data"]
            elif j.get("ok") or j.get("result"):
                data = {"updates": j.get("result") or []}
            else:
                print("❌ Unexpected getUpdates shape:", j)
                time.sleep(POLL)
                continue

            updates = data.get("updates", []) or []
            next_off = data.get("next_offset_id") or data.get("next_start_id")

            # first run: set offset to next_off to avoid processing old messages
            if first_run:
                if next_off:
                    offset = next_off
                    state["offset"] = offset
                    save_state(state)
                    print("🚀 first run — start from offset:", offset)
                else:
                    if updates:
                        # fall back to last message id
                        last = updates[-1].get("new_message", {}).get("message_id") or updates[-1].get("message_id")
                        if last:
                            offset = str(last)
                            state["offset"] = offset
                            save_state(state)
                            print("🚀 first run — start from last message_id:", offset)
                first_run = False
                time.sleep(POLL)
                continue

            # process updates
            for upd in updates:
                try:
                    utype = upd.get("type")
                    if utype not in ("NewMessage", "StartedBot"):
                        # skip other event types for now
                        continue
                    chat_id = upd.get("chat_id")
                    if not chat_id:
                        continue
                    if utype == "StartedBot":
                        # user pressed start on bot -> send welcome
                        handle_start_message(chat_id)
                    else:
                        msg = upd.get("new_message") or {}
                        mid = msg.get("message_id")
                        text = (msg.get("text") or "").strip()
                        if not text:
                            continue
                        print(f"📩 ({mid}) {chat_id}: {text}")
                        process_new_message(chat_id, text, sender_id=msg.get("sender_id"))
                except Exception as e:
                    print("❌ error processing update:", e)
                    continue

            # update offset
            if next_off:
                offset = next_off
            else:
                if updates:
                    last = updates[-1].get("new_message", {}).get("message_id") or updates[-1].get("message_id")
                    if last:
                        offset = str(last)

            if offset:
                state["offset"] = offset
                save_state(state)
                # show small log
                print("⚡ offset updated:", offset)

            time.sleep(POLL)

        except KeyboardInterrupt:
            print("⏹ stopped by user")
            break
        except Exception as e:
            print("❌ main loop exception:", e)
            time.sleep(2)

if __name__ == "__main__":
    main()
