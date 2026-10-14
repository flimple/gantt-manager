import customtkinter as ctk

def resolve_bg(widget):
    w = widget
    while w is not None:
        try:
            color = w.cget("fg_color")
            if color != "transparent":
                return w._apply_appearance_mode(color)
        except Exception:
            pass
        w = w.master
    return "#000000"


# ── Molette : une seule liaison <MouseWheel> pour toute l'application ──────
# bind_all vise le tag "all" (toute l'application) : détruire un widget ne retire
# PAS son handler. Une liaison par panneau s'accumulait donc à chaque projet
# ouvert. On garde une seule liaison et une liste de zones inscrites, purgée des
# widgets détruits à chaque inscription et à chaque coup de molette.
_WHEEL_ZONES : list = []
_WHEEL_ROOT : list = [None]


def _prune_wheel_zones():
    kept = []
    for zone in _WHEEL_ZONES:
        try:
            if zone[0].winfo_exists():
                kept.append(zone)
        except Exception:
            pass
    _WHEEL_ZONES[:] = kept


def _dispatch_wheel(event):
    # Sous Windows <MouseWheel> va au widget qui a le focus, pas à celui sous la
    # souris : c'est donc le pointeur qui désigne la zone à faire défiler. Si
    # plusieurs zones sont imbriquées, la plus profonde gagne.
    _prune_wheel_zones()
    try:
        pointed = _WHEEL_ROOT[0].winfo_containing(event.x_root, event.y_root)
    except Exception:
        return
    if pointed is None:
        return
    target, best = str(pointed), None
    for container, handler in _WHEEL_ZONES:
        name = str(container)
        if (target == name or target.startswith(name + ".")) and (best is None or len(name) > len(best[0])):
            best = (name, handler)
    if best is not None:
        best[1](event)


def _register_wheel(container, handler):
    """handler(event) est appelé quand la molette tourne et que le pointeur est dans container."""
    _prune_wheel_zones()
    _WHEEL_ZONES.append((container, handler))
    root = container.winfo_toplevel()
    if _WHEEL_ROOT[0] is not root:
        _WHEEL_ROOT[0] = root
        root.bind_all("<MouseWheel>", _dispatch_wheel)   # sans add="+" : remplace l'ancienne

def create_viewport(parent_frame, horizontal: bool = False) -> ctk.CTkFrame:
    container = ctk.CTkFrame(parent_frame, fg_color="transparent")
    container.pack(fill="both", expand=True)
    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)

    canvas = ctk.CTkCanvas(container, highlightthickness=0, bd=0, bg=resolve_bg(parent_frame))
    vbar = ctk.CTkScrollbar(container, orientation="vertical", command=canvas.yview)
    scrollable_frame = ctk.CTkFrame(canvas, fg_color="transparent")

    canvas.grid(row=0, column=0, sticky="nsew")
    vbar.grid(row=0, column=1, sticky="ns")
    canvas.configure(yscrollcommand=vbar.set)

    if horizontal:
        hbar = ctk.CTkScrollbar(container, orientation="horizontal", command=canvas.xview)
        hbar.grid(row=1, column=0, sticky="ew")
        canvas.configure(xscrollcommand=hbar.set)

    window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    def _fit(_event=None):
        width = canvas.winfo_width()
        if horizontal:
            # never narrower than the viewport, but grow if content is wider
            width = max(width, scrollable_frame.winfo_reqwidth())
        canvas.itemconfig(window_id, width=width)
        canvas.configure(scrollregion=canvas.bbox("all"))

    scrollable_frame.bind("<Configure>", _fit)
    canvas.bind("<Configure>", _fit)

    def _on_wheel(e):
        step = int(-e.delta / 120) * 2
        shift_held = bool(e.state & 0x1)
        if horizontal and shift_held:
            if canvas.xview() != (0.0, 1.0):
                canvas.xview_scroll(step, "units")
        elif canvas.yview() != (0.0, 1.0):
            canvas.yview_scroll(step, "units")

    _register_wheel(container, _on_wheel)

    return scrollable_frame



#region AI Code

import calendar
import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import font as tkfont
from math import ceil, sqrt
 
# (light, dark) palette, same tokens as theme.py
_TL_PAL = {
    "panel":   ("#FFFFFF", "#1C222B"),
    "head":    ("#E9EFF7", "#202733"),   # gantt_header_bg
    "border":  ("#D8DFE9", "#323B4A"),
    "strong":  ("#B9C4D3", "#46526A"),   # border_strong
    "grid":    ("#E3E8F0", "#2B3340"),   # gantt_grid
    "weekend": ("#F0F3F8", "#171C24"),   # gantt_weekend
    "today":   ("#D6455D", "#F0788A"),   # gantt_today
    "muted":   ("#5B6778", "#9AA6B8"),   # text_muted
    "dim":     ("#7A869A", "#6F7B8E"),   # text_comment
    "card":    ("#F7F9FC", "#252C38"),   # bg_card
    "hover":   ("#EAF1FA", "#2A3342"),   # bg_hover_row
    "text":    ("#1B2430", "#E6EAF0"),   # text_default
    "h1":      ("#1B3A5C", "#EAF2FC"),   # text_h1
    "ghost":   ("#3F78B8", "#8FB4DF"),   # btn_ghost_text
    "blue":    ("#3A86D9", "#5B9BE6"),   # accent_blue
    "blue_hv": ("#234770", "#78AEEE"),   # btn_primary_hover
    "on_blue": ("#FFFFFF", "#0B1220"),   # btn_primary_text
    "margin":  ("#E9A3AE", "#8A4553"),   # notebook margin line
}
_TL_MODES = {"Days": 48, "Weeks": 18, "Months": 5}   # pixels per day for each view
_TL_DEFAULT_DAYS = 89   # default window: the current week + 90 days
_TL_FONT = "Segoe UI"
_WD = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")
 
 
def _tl_colors() -> dict:
    i = 1 if ctk.get_appearance_mode() == "Dark" else 0
    return {k: v[i] for k, v in _TL_PAL.items()}
 
 
def _tl_mode(value) -> str:
    """Accepts 'Days'/'Day', 'Weeks'/'Week', 'Months'/'Month' (any case)."""
    v = str(value).strip().capitalize()
    if not v.endswith("s"):
        v += "s"
    return v if v in _TL_MODES else "Weeks"
 
 
def _segments(start: date, n_days: int, key) -> list:
    """Split the day range into runs that share the same key(date). Returns (first_idx, last_idx)."""
    segs, i0, prev = [], 0, key(start)
    for i in range(1, n_days):
        k = key(start + timedelta(days=i))
        if k != prev:
            segs.append((i0, i - 1))
            i0, prev = i, k
    segs.append((i0, n_days - 1))
    return segs
 
 
def get_timeline_table(parent, start_date: date | None = None, end_date: date | None = None,
                       view_mode: str = "Weeks", names_width: int = 220, row_height: int = 36,
                       header_height: int = 56, corner_radius: int = 10, padding: int = 8,
                       pack_now: bool = True):
    """
    Builds the Gantt timeline table.
 
    Returns (timeline_frame, pack_data, tasks_rect, task_names_rect):
      timeline_frame  : the whole table (CTkFrame, rounded). Hide with .pack_forget(), show with .pack(**pack_data)
      pack_data       : dict of pack options the frame was packed with
      tasks_rect      : tk.Canvas, the scrolling grid. Add task nodes with
                        tasks_rect.create_window(x, y, window=widget, anchor="nw")
      task_names_rect : CTkFrame, the left panel. Pack one row per task/category with height=row_height
 
    Extra helpers attached to timeline_frame:
      set_view(view_mode=None, start_date=None, end_date=None)   change view / range and redraw
      date_to_x(date), row_to_y(row_index), day_width()          positions for placing nodes
      scroll_to_date(date)                                       horizontal scroll
      start_date(), default_range()                              range shown now / the default one
      row_height                                                 the row height in pixels
    """
    today = date.today()
    first = start_date or today - timedelta(days=today.weekday())
    state = {"start": first, "end": end_date or first + timedelta(days=_TL_DEFAULT_DAYS),
             "mode": _tl_mode(view_mode)}
 
    # side="left" + expand: sits between a left panel and a right panel packed with side="left"/"right"
    pack_data = {"side": "left", "fill": "both", "expand": True, "padx": padding, "pady": padding}
    container = ctk.CTkFrame(parent, fg_color=_TL_PAL["panel"], corner_radius=corner_radius,
                             border_width=1, border_color=_TL_PAL["border"])
    # the square header/body areas are inset so they don't poke out of the rounded corners
    inset = ceil(corner_radius - (corner_radius - 1) / sqrt(2)) if corner_radius else 1
    body = ctk.CTkFrame(container, fg_color="transparent", corner_radius=0, border_width=0)
    body.pack(fill="both", expand=True, padx=inset, pady=inset)
    body.grid_rowconfigure(1, weight=1)
    body.grid_columnconfigure(2, weight=1)
 
    # ── header row ───────────────────────────────────────────
    names_head = tk.Canvas(body, width=names_width, height=header_height, highlightthickness=0, bd=0)
    head_cv = tk.Canvas(body, height=header_height, highlightthickness=0, bd=0, xscrollincrement=24)
    corner = tk.Frame(body, width=16, height=header_height)
    names_head.grid(row=0, column=0, sticky="nsew")
    head_cv.grid(row=0, column=2, sticky="ew")
    corner.grid(row=0, column=3, sticky="nsew")
 
    sep = tk.Frame(body, width=1)
    sep.grid(row=0, column=1, rowspan=3, sticky="ns")
 
    # ── body: names panel + timeline canvas ──────────────────
    names_cv = tk.Canvas(body, width=names_width, highlightthickness=0, bd=0, yscrollincrement=row_height // 2)
    names_cv.grid(row=1, column=0, sticky="ns")
    names_rect = ctk.CTkFrame(names_cv, width=names_width, height=1, corner_radius=0, border_width=0, fg_color=_TL_PAL["panel"])
    names_win = names_cv.create_window(0, 0, window=names_rect, anchor="nw", width=names_width)
 
    tasks = tk.Canvas(body, highlightthickness=0, bd=0, yscrollincrement=row_height // 2, xscrollincrement=24)
    tasks.grid(row=1, column=2, sticky="nsew")
 
    # ── scrollbars (vertical moves both body canvases, horizontal moves body + header) ──
    def _yview(*a):
        names_cv.yview(*a)
        tasks.yview(*a)
 
    def _xview(*a):
        tasks.xview(*a)
        head_cv.xview(*a)
 
    sb = dict(fg_color="transparent", button_color=_TL_PAL["strong"], button_hover_color=_TL_PAL["dim"])
    vbar = ctk.CTkScrollbar(body, orientation="vertical", command=_yview, **sb)
    hbar = ctk.CTkScrollbar(body, orientation="horizontal", command=_xview, **sb)
    vbar.grid(row=1, column=3, sticky="ns")
    hbar.grid(row=2, column=2, sticky="ew")
    names_cv.configure(yscrollcommand=vbar.set)
    tasks.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)
 
    # ── drawing ──────────────────────────────────────────────
    def _redraw():
        if not container.winfo_exists():
            return
        c = _tl_colors()
        mode = state["mode"]
        day_w = _TL_MODES[mode]
        start = state["start"]
        n_days = max((state["end"] - start).days + 1, 1)
        total_w = n_days * day_w
        draw_w = max(total_w, tasks.winfo_width())
        content_h = ceil(max(names_rect.winfo_reqheight(), 1) / row_height) * row_height
        H = max(content_h, tasks.winfo_height())
        top_h = 24
 
        for w in (names_head, head_cv, corner):
            w.configure(bg=c["head"])
        sep.configure(bg=c["border"])
        names_cv.configure(bg=c["panel"])
        tasks.configure(bg=c["panel"])
        names_head.delete("all")
        head_cv.delete("all")
        tasks.delete("tl")
 
        # header: top band + bottom band depend on the view
        keys = {
            "Days":   (lambda d: d.isocalendar()[:2], lambda d: d),
            "Weeks":  (lambda d: (d.year, d.month),   lambda d: d.isocalendar()[:2]),
            "Months": (lambda d: d.year,              lambda d: (d.year, d.month)),
        }[mode]
        top_segs = _segments(start, n_days, keys[0])
        bot_segs = _segments(start, n_days, keys[1])
 
        def top_label(i0, i1):
            a, b = start + timedelta(days=i0), start + timedelta(days=i1)
            if mode == "Days":
                if a.month == b.month:
                    return f"{a:%b} {a.day} \u2013 {b.day}"
                return f"{a:%b} {a.day} \u2013 {b:%b} {b.day}"
            if mode == "Weeks":
                return f"{a:%B %Y}" if (i1 - i0 + 1) * day_w > 110 else f"{a:%b}"
            return str(a.year)
 
        def bot_label(d):
            if mode == "Days":
                return f"{_WD[d.weekday()]} {d.day}"
            if mode == "Weeks":
                return f"{d:%b} {d.day}"
            return f"{d:%b}"
 
        names_head.create_text(14, header_height - 9, text="Task", anchor="sw", fill=c["muted"], font=(_TL_FONT, 10))
        names_head.create_line(0, header_height - 1, names_width, header_height - 1, fill=c["border"])
        head_cv.create_line(0, header_height - 1, draw_w, header_height - 1, fill=c["border"])
        head_cv.create_line(0, top_h, draw_w, top_h, fill=c["grid"])
 
        for i0, i1 in top_segs:
            x0 = i0 * day_w
            head_cv.create_line(x0, 0, x0, header_height, fill=c["grid"])
            head_cv.create_text(x0 + 8, top_h / 2, text=top_label(i0, i1), anchor="w", fill=c["muted"], font=(_TL_FONT, 9))
 
        for i0, i1 in bot_segs:
            x0, x1 = i0 * day_w, (i1 + 1) * day_w
            d = start + timedelta(days=i0)
            color = c["muted"]
            if mode == "Days":
                color = c["today"] if d == today else (c["dim"] if d.weekday() >= 5 else c["muted"])
            head_cv.create_line(x0, top_h, x0, header_height, fill=c["grid"])
            y = (top_h + header_height) / 2
            if mode == "Days":
                head_cv.create_text((x0 + x1) / 2, y, text=bot_label(d), fill=color, font=(_TL_FONT, 9))
            else:
                head_cv.create_text(x0 + 8, y, text=bot_label(d), anchor="w", fill=color, font=(_TL_FONT, 9))
 
        # body: weekend shading, vertical + horizontal grid, today line
        if mode != "Months":
            for i in range(n_days):
                if (start + timedelta(days=i)).weekday() >= 5:
                    tasks.create_rectangle(i * day_w, 0, (i + 1) * day_w, H, fill=c["weekend"], outline="", tags="tl")
        for i0, _ in bot_segs:
            tasks.create_line(i0 * day_w, 0, i0 * day_w, H, fill=c["grid"], tags="tl")
        tasks.create_line(total_w, 0, total_w, H, fill=c["grid"], tags="tl")
        for y in range(row_height, H + row_height, row_height):
            tasks.create_line(0, y, draw_w, y, fill=c["grid"], tags="tl")
        if start <= today <= state["end"]:
            x = ((today - start).days + 0.5) * day_w
            tasks.create_line(x, 0, x, H, fill=c["today"], width=2, tags="tl")
            head_cv.create_oval(x - 3, header_height - 9, x + 3, header_height - 3, fill=c["today"], outline="")
        tasks.tag_lower("tl")   # keep grid under any node you draw on the canvas
 
        tasks.configure(scrollregion=(0, 0, total_w, H))
        head_cv.configure(scrollregion=(0, 0, total_w, header_height))
        names_cv.configure(scrollregion=(0, 0, names_width, H))
        names_cv.itemconfig(names_win, height=H)
 
    job = {"id": None}
 
    def _schedule(_e=None):
        if job["id"] is None:
            job["id"] = container.after(30, _run)
 
    def _run():
        job["id"] = None
        _redraw()
 
    tasks.bind("<Configure>", _schedule)
    names_rect.bind("<Configure>", _schedule)
 
    # canvas items don't follow CTk's theme automatically, so watch the appearance mode
    last = {"mode": ctk.get_appearance_mode()}
 
    def _watch():
        if not container.winfo_exists():
            return
        if ctk.get_appearance_mode() != last["mode"]:
            last["mode"] = ctk.get_appearance_mode()
            _redraw()
        container.after(300, _watch)
 
    container.after(300, _watch)
 
    # ── mouse wheel: scroll when the pointer is over the table (Shift = horizontal) ──
    def _wheel(e):
        step = int(-e.delta / 120) * 2
        if e.state & 0x1:
            if tasks.xview() != (0.0, 1.0):
                _xview("scroll", step, "units")
        elif tasks.yview() != (0.0, 1.0):
            _yview("scroll", step, "units")

    _register_wheel(container, _wheel)
 
    # ── helpers for the main script ──────────────────────────
    def set_view(view_mode=None, start_date=None, end_date=None):
        if view_mode is not None:
            state["mode"] = _tl_mode(view_mode)
        if start_date is not None:
            state["start"] = start_date
        if end_date is not None:
            state["end"] = end_date
        _redraw()
        _xview("moveto", 0)
 
    def scroll_to_date(d: date):
        total = max((state["end"] - state["start"]).days + 1, 1) * _TL_MODES[state["mode"]]
        _xview("moveto", max(0.0, ((d - state["start"]).days * _TL_MODES[state["mode"]] - 60) / total))
 
    def default_range():
        # The window the table starts with, so a caller can go back to it
        monday = date.today() - timedelta(days=date.today().weekday())
        return monday, monday + timedelta(days=_TL_DEFAULT_DAYS)

    container.set_view = set_view
    container.start_date = lambda: state["start"]
    container.default_range = default_range
    container.date_to_x = lambda d: (d - state["start"]).days * _TL_MODES[state["mode"]]
    container.row_to_y = lambda i: i * row_height
    container.day_width = lambda: _TL_MODES[state["mode"]]
    container.scroll_to_date = scroll_to_date
    container.row_height = row_height
 
    if pack_now:
        container.pack(**pack_data)
    _schedule()
    return container, pack_data, tasks, names_rect
 
 
# ════════════════════════════════════════════════════════════════════
#  Shared helpers for the calendar and the to-do list
# ════════════════════════════════════════════════════════════════════
_WD_FULL = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
 
 
def _make_card(parent, corner_radius: int, padding: int):
    """Rounded container + an inset body frame (so square children don't poke out of the corners)."""
    pack_data = {"side": "left", "fill": "both", "expand": True, "padx": padding, "pady": padding}
    container = ctk.CTkFrame(parent, fg_color=_TL_PAL["panel"], corner_radius=corner_radius,
                             border_width=1, border_color=_TL_PAL["border"])
    inset = ceil(corner_radius - (corner_radius - 1) / sqrt(2)) if corner_radius else 1
    body = ctk.CTkFrame(container, fg_color="transparent", corner_radius=0, border_width=0)
    body.pack(fill="both", expand=True, padx=inset, pady=inset)
    return container, body, pack_data
 
 
def _debounce(widget, fn, ms: int = 30):
    job = {"id": None}
 
    def run():
        job["id"] = None
        if widget.winfo_exists():
            fn()
 
    def schedule(_e=None):
        if job["id"] is None:
            job["id"] = widget.after(ms, run)
    return schedule
 
 
def _watch_theme(widget, redraw):
    """Canvas drawings don't follow CTk's theme, so redraw when the appearance mode changes."""
    last = {"m": ctk.get_appearance_mode()}
 
    def tick():
        if not widget.winfo_exists():
            return
        if ctk.get_appearance_mode() != last["m"]:
            last["m"] = ctk.get_appearance_mode()
            redraw()
        widget.after(300, tick)
    widget.after(300, tick)
 
 
def _bind_wheel(container, cv):
    def wheel(e):
        if cv.yview() != (0.0, 1.0):
            cv.yview_scroll(int(-e.delta / 120) * 2, "units")
    _register_wheel(container, wheel)
 
 
def _pick(color, i: int) -> str:
    """A (light, dark) pair resolves by theme index; a single hex string is used as is."""
    return color[i] if isinstance(color, (tuple, list)) else color
 
 
def _text_on(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[k:k + 2], 16) for k in (0, 2, 4))
    return "#0B1220" if 0.299 * r + 0.587 * g + 0.114 * b > 150 else "#FFFFFF"
 
 
def _rrect(cv, x0, y0, x1, y1, r, **kw):
    r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
    pts = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1, x1 - r, y1,
           x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
    return cv.create_polygon(pts, smooth=True, **kw)
 
 
def _ellipsize(font, text: str, max_w: float) -> str:
    if max_w <= 0:
        return ""
    if font.measure(text) <= max_w:
        return text
    while text and font.measure(text + "\u2026") > max_w:
        text = text[:-1]
    return text + "\u2026" if text else ""
 
 
def _add_months(d: date, n: int) -> date:
    m = d.month - 1 + n
    y, m = d.year + m // 12, m % 12 + 1
    return d.replace(year=y, month=m, day=min(d.day, calendar.monthrange(y, m)[1]))
 
 
def _norm_events(events) -> dict:
    """Accepts (date, name), (date, name, color) or {"date","name","color"}. Color: hex or (light, dark)."""
    out = {}
    for e in events or []:
        if isinstance(e, dict):
            d, name, col = e.get("date"), e.get("name", ""), e.get("color")
        else:
            d, name, col = (list(e) + [None])[:3]
        if isinstance(d, datetime):
            d = d.date()
        if isinstance(d, date):
            out.setdefault(d, []).append((str(name), col or _TL_PAL["blue"]))
    return out
 
 
def _cal_mode(value) -> str:
    v = str(value).strip().lower()
    if v.startswith(("year", "month")):
        return "Year"
    return "Days" if v.startswith("day") else "Weeks"
 
 
# ════════════════════════════════════════════════════════════════════
#  Calendar
# ════════════════════════════════════════════════════════════════════
def get_calendar_grid(parent, view_mode: str = "Weeks", events=None, anchor_date: date | None = None,
                      on_day_click=None, show_nav: bool = True, corner_radius: int = 10,
                      padding: int = 8, pack_now: bool = True):
    """
    Grid-style calendar. Returns (calendar_frame, pack_data).
 
    view_mode:
      "Year"  : 12 mini months; days that have events are filled with the event color
      "Weeks" : one month as a grid of week rows; event names shown as chips inside each day
      "Days"  : one week as 7 tall day columns; full event names (wrapped) listed per day
      ("Months" is accepted as an alias of "Year", so the Days/Weeks/Months selector can drive it too)
 
    events: list of (date, name), (date, name, color) or {"date":..., "name":..., "color":...}
            color is a hex string or a (light, dark) pair; default is the accent blue.
    on_day_click(date): optional callback when a day is clicked.
 
    Helpers attached to calendar_frame:
      set_view(view_mode=None, anchor_date=None, events=None)   change view / date / events, then redraw
      shift(n)        previous (-1) / next (+1): a year, a month or a week depending on the view
      go_today()
    """
    state = {"mode": _cal_mode(view_mode), "anchor": anchor_date or date.today(), "events": _norm_events(events)}
    container, body, pack_data = _make_card(parent, corner_radius, padding)
    hits: list = []
 
    title = None
    if show_nav:
        nav = ctk.CTkFrame(body, fg_color="transparent", height=44, corner_radius=0)
        nav.pack(fill="x")
        nav.pack_propagate(False)
        title = ctk.CTkLabel(nav, text="", font=(_TL_FONT, 18, "bold"), text_color=_TL_PAL["h1"])
        title.pack(side="left", padx=(12, 0))
        kw = dict(height=30, corner_radius=8, border_width=1, fg_color="transparent",
                  border_color=_TL_PAL["strong"], hover_color=_TL_PAL["hover"],
                  text_color=_TL_PAL["ghost"], font=(_TL_FONT, 14))
        nxt = ctk.CTkButton(nav, text="\u203a", width=34, command=lambda: shift(1), **kw)
        nxt.pack(side="right", padx=(4, 12))
        tdy = ctk.CTkButton(nav, text="Today", width=64, command=lambda: go_today(), **kw)
        tdy.pack(side="right", padx=4)
        prv = ctk.CTkButton(nav, text="\u2039", width=34, command=lambda: shift(-1), **kw)
        prv.pack(side="right", padx=4)
 
    cv = tk.Canvas(body, highlightthickness=0, bd=0)
    cv.pack(fill="both", expand=True)
    f_s = tkfont.Font(family=_TL_FONT, size=9)
    f_xs = tkfont.Font(family=_TL_FONT, size=8)
    f_b = tkfont.Font(family=_TL_FONT, size=10, weight="bold")
    f_h = tkfont.Font(family=_TL_FONT, size=13, weight="bold")
 
    def _title_text():
        a, m = state["anchor"], state["mode"]
        if m == "Year":
            return str(a.year)
        if m == "Weeks":
            return f"{calendar.month_name[a.month]} {a.year}"
        s = a - timedelta(days=a.weekday())
        e = s + timedelta(days=6)
        if s.month == e.month:
            return f"{s:%b} {s.day} \u2013 {e.day}, {e.year}"
        return f"{s:%b} {s.day} \u2013 {e:%b} {e.day}, {e.year}"
 
    def draw():
        c = _tl_colors()
        i = 1 if ctk.get_appearance_mode() == "Dark" else 0
        W, H = cv.winfo_width(), cv.winfo_height()
        cv.configure(bg=c["panel"])
        cv.delete("all")
        hits.clear()
        if title is not None:
            title.configure(text=_title_text())
        if W < 60 or H < 60:
            return
        today, a, ev, mode = date.today(), state["anchor"], state["events"], state["mode"]
        cal = calendar.Calendar(firstweekday=0)
 
        if mode == "Year":
            pad, cols, rows = 14, 4, 3
            cw, ch = (W - pad * (cols + 1)) / cols, (H - pad * (rows + 1)) / rows
            for m in range(1, 13):
                r, q = divmod(m - 1, cols)
                x0, y0 = pad + q * (cw + pad), pad + r * (ch + pad)
                _rrect(cv, x0, y0, x0 + cw, y0 + ch, 10, fill=c["card"], outline=c["border"])
                cv.create_text(x0 + 12, y0 + 16, text=calendar.month_name[m], anchor="w", fill=c["h1"], font=f_b)
                dw, top = (cw - 16) / 7, y0 + 50
                dh = (ch - 50 - 8) / 6
                for k, letter in enumerate("MTWTFSS"):
                    cv.create_text(x0 + 8 + dw * (k + .5), y0 + 36, text=letter, fill=c["dim"], font=f_xs)
                for wi, week in enumerate(cal.monthdatescalendar(a.year, m)):
                    for di, d in enumerate(week):
                        if d.month != m:
                            continue
                        cx, cy = x0 + 8 + dw * (di + .5), top + dh * (wi + .5)
                        rad = max(min(dw, dh) / 2 - 1, 4)
                        evs, color, tcol = ev.get(d), None, (c["dim"] if di >= 5 else c["muted"])
                        if evs:
                            color = _pick(evs[0][1], i)
                            tcol = _text_on(color)
                            cv.create_oval(cx - rad, cy - rad, cx + rad, cy + rad, fill=color, outline="")
                        if d == today:
                            cv.create_oval(cx - rad, cy - rad, cx + rad, cy + rad, outline=c["today"], width=2)
                        cv.create_text(cx, cy, text=str(d.day), fill=tcol, font=f_xs)
                        hits.append((cx - dw / 2, cy - dh / 2, cx + dw / 2, cy + dh / 2, d))
 
        elif mode == "Weeks":
            weeks = cal.monthdatescalendar(a.year, a.month)
            pad, head_h = 12, 26
            gx0, gy0 = pad, pad
            cw = (W - 2 * pad) / 7
            rh = (H - 2 * pad - head_h) / len(weeks)
            for di in range(7):
                cv.create_text(gx0 + cw * (di + .5), gy0 + head_h / 2, text=_WD_FULL[di], fill=c["muted"], font=f_s)
            for wi, week in enumerate(weeks):
                for di, d in enumerate(week):
                    x0, y0 = gx0 + cw * di, gy0 + head_h + rh * wi
                    inside = d.month == a.month
                    cv.create_rectangle(x0, y0, x0 + cw, y0 + rh, outline=c["grid"], fill=c["panel"] if inside else c["weekend"])
                    if d == today:
                        cv.create_oval(x0 + 6, y0 + 5, x0 + 28, y0 + 27, fill=c["today"], outline="")
                        cv.create_text(x0 + 17, y0 + 16, text=str(d.day), fill=_text_on(c["today"]), font=f_s)
                    else:
                        cv.create_text(x0 + 17, y0 + 16, text=str(d.day), fill=c["text"] if inside else c["dim"], font=f_s)
                    evs = ev.get(d, [])
                    slots = max(int((rh - 34) // 21), 0)
                    shown = evs[:slots] if len(evs) <= slots else evs[:max(slots - 1, 0)]
                    for k, (name, col) in enumerate(shown):
                        y = y0 + 32 + k * 21
                        color = _pick(col, i)
                        _rrect(cv, x0 + 5, y, x0 + cw - 5, y + 18, 6, fill=color, outline="")
                        cv.create_text(x0 + 11, y + 9, text=_ellipsize(f_xs, name, cw - 22), anchor="w",
                                       fill=_text_on(color), font=f_xs)
                    if len(evs) > len(shown):
                        cv.create_text(x0 + 9, y0 + 32 + len(shown) * 21 + 9, text=f"+{len(evs) - len(shown)} more",
                                       anchor="w", fill=c["muted"], font=f_xs)
                    hits.append((x0, y0, x0 + cw, y0 + rh, d))
 
        else:   # Days: one week, tall columns
            start = a - timedelta(days=a.weekday())
            pad, head_h = 12, 56
            cw = (W - 2 * pad) / 7
            for di in range(7):
                d = start + timedelta(days=di)
                x0, y0, x1, y1 = pad + cw * di, pad, pad + cw * (di + 1), H - pad
                cv.create_rectangle(x0, y0, x1, y1, outline=c["grid"], fill=c["weekend"] if di >= 5 else c["panel"])
                cv.create_text((x0 + x1) / 2, y0 + 16, text=_WD_FULL[di], fill=c["muted"], font=f_s)
                if d == today:
                    cv.create_oval((x0 + x1) / 2 - 15, y0 + 28, (x0 + x1) / 2 + 15, y0 + 52, fill=c["today"], outline="")
                cv.create_text((x0 + x1) / 2, y0 + 40, text=str(d.day), font=f_h,
                               fill=_text_on(c["today"]) if d == today else c["h1"])
                cv.create_line(x0, y0 + head_h, x1, y0 + head_h, fill=c["grid"])
                y, evs = y0 + head_h + 8, ev.get(d, [])
                for k, (name, col) in enumerate(evs):
                    color = _pick(col, i)
                    tid = cv.create_text(x0 + 14, y + 6, text=name, anchor="nw", width=max(cw - 28, 20),
                                         fill=_text_on(color), font=f_s)
                    bx = cv.bbox(tid)
                    h = (bx[3] - bx[1]) if bx else 16
                    if y + h + 12 > y1 - 4:
                        cv.delete(tid)
                        cv.create_text(x0 + 10, y + 8, text=f"+{len(evs) - k} more", anchor="w", fill=c["muted"], font=f_xs)
                        break
                    cv.tag_lower(_rrect(cv, x0 + 6, y, x1 - 6, y + h + 12, 7, fill=color, outline=""), tid)
                    y += h + 18
                hits.append((x0, y0, x1, y1, d))
 
    def on_click(e):
        if on_day_click is None:
            return
        for x0, y0, x1, y1, d in hits:
            if x0 <= e.x <= x1 and y0 <= e.y <= y1:
                on_day_click(d)
                return
 
    def set_view(view_mode=None, anchor_date=None, events=None):
        if view_mode is not None:
            state["mode"] = _cal_mode(view_mode)
        if anchor_date is not None:
            state["anchor"] = anchor_date
        if events is not None:
            state["events"] = _norm_events(events)
        draw()
 
    def shift(n: int):
        a, m = state["anchor"], state["mode"]
        state["anchor"] = _add_months(a, 12 * n) if m == "Year" else _add_months(a, n) if m == "Weeks" else a + timedelta(days=7 * n)
        draw()
 
    def go_today():
        state["anchor"] = date.today()
        draw()
 
    cv.bind("<Configure>", _debounce(container, draw))
    cv.bind("<Button-1>", on_click)
    _watch_theme(container, draw)
    container.set_view, container.shift, container.go_today = set_view, shift, go_today
 
    if pack_now:
        container.pack(**pack_data)
    return container, pack_data
 
 
# ════════════════════════════════════════════════════════════════════
#  To-do list (ruled paper)
# ════════════════════════════════════════════════════════════════════
def get_todo_list(parent, tasks=None, row_height: int = 36, margin_x: int = 44,
                  corner_radius: int = 10, padding: int = 8, pack_now: bool = True):
    """
    Ruled-paper to-do list. Returns (todo_frame, pack_data, items_rect).
 
    items_rect is the scrollable parent: it always matches the width of the list and grows with its
    content (the list scrolls when it gets taller than the window). Pack anything into it with
    fill="x" and it scales with the panel. Rows of height=row_height sit exactly on the ruled lines.
 
    tasks: optional initial list of "text" or ("text", done).
 
    Helpers attached to todo_frame:
      add_task(text, done=False, on_toggle=None) -> row frame   on_toggle(text, done) is called on click;
                                                                 put extra widgets in row.content
      clear()                                                    remove every row
      row_height
    """
    container, body, pack_data = _make_card(parent, corner_radius, padding)
    body.grid_rowconfigure(0, weight=1)
    body.grid_columnconfigure(0, weight=1)
 
    cv = tk.Canvas(body, highlightthickness=0, bd=0, yscrollincrement=row_height // 2)
    vbar = ctk.CTkScrollbar(body, orientation="vertical", command=cv.yview, fg_color="transparent",
                            button_color=_TL_PAL["strong"], button_hover_color=_TL_PAL["dim"])
    cv.configure(yscrollcommand=vbar.set)
    cv.grid(row=0, column=0, sticky="nsew")
    vbar.grid(row=0, column=1, sticky="ns")
 
    items_rect = ctk.CTkFrame(cv, fg_color=_TL_PAL["panel"], corner_radius=0, border_width=0, height=1)
    win = cv.create_window(0, 0, window=items_rect, anchor="nw")
    margin = tk.Frame(cv, width=1)
    margin.place(x=margin_x, y=0, relheight=1)
    margin.lift()
 
    def fit():
        c = _tl_colors()
        w, vh = cv.winfo_width(), cv.winfo_height()
        H = max(items_rect.winfo_reqheight(), vh)
        cv.itemconfig(win, width=w)
        cv.configure(bg=c["panel"], scrollregion=(0, 0, w, H))
        margin.configure(bg=c["margin"])
        cv.delete("paper")
        for y in range(row_height, H + row_height, row_height):
            cv.create_line(0, y, w, y, fill=c["grid"], tags="paper")
        cv.tag_lower("paper")
 
    schedule = _debounce(container, fit)
    cv.bind("<Configure>", schedule)
    items_rect.bind("<Configure>", schedule)
    _watch_theme(container, fit)
    _bind_wheel(container, cv)
 
    f_normal = ctk.CTkFont(family=_TL_FONT, size=14)
    f_done = ctk.CTkFont(family=_TL_FONT, size=14, overstrike=True)
 
    def add_task(text: str, done: bool = False, on_toggle=None):
        # the row's own color is the ruled line; the inner frame leaves a 1px strip of it at the bottom
        row = ctk.CTkFrame(items_rect, height=row_height, corner_radius=0, border_width=0, fg_color=_TL_PAL["grid"])
        row.pack(fill="x")
        row.pack_propagate(False)
        inner = ctk.CTkFrame(row, corner_radius=0, border_width=0, fg_color=_TL_PAL["panel"])
        inner.pack(fill="both", expand=True, pady=(0, 1))
        row.content = inner
        var = ctk.BooleanVar(value=done)
        cb = ctk.CTkCheckBox(inner, text=text, variable=var, font=f_normal, text_color=_TL_PAL["text"],
                             checkbox_width=18, checkbox_height=18, corner_radius=5, border_width=2,
                             fg_color=_TL_PAL["blue"], hover_color=_TL_PAL["blue_hv"],
                             checkmark_color=_TL_PAL["on_blue"], border_color=_TL_PAL["strong"])
 
        def style():
            cb.configure(font=f_done if var.get() else f_normal,
                         text_color=_TL_PAL["dim"] if var.get() else _TL_PAL["text"])
 
        def toggle():
            style()
            if on_toggle:
                on_toggle(text, var.get())
        cb.configure(command=toggle)
        cb.pack(side="left", padx=(margin_x + 14, 10))
        if done:
            style()
        return row
 
    def clear():
        for child in items_rect.winfo_children():
            child.destroy()
 
    for t in tasks or []:
        add_task(*((t,) if isinstance(t, str) else t))
 
    container.add_task, container.clear, container.row_height = add_task, clear, row_height
    if pack_now:
        container.pack(**pack_data)
    schedule()
    return container, pack_data, items_rect


#endregion