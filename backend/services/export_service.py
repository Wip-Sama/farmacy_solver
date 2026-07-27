import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, date, timedelta
from PIL import Image, ImageDraw, ImageFont

def generate_schedule_png(
    year: int,
    rows: List[Dict[str, Any]],
    output_path: str,
    mode: str = "normal",
    orientation: str = "vertical",
    pharmacy_label: str = "names",
    pharmacy_name_map: Dict[int, str] = None
):
    """
    Renders a formatted dark-mode PNG image table of the schedule according to mode (tiny/compact/normal/extended),
    orientation (vertical/horizontal), and pharmacy label format (names vs ids). Highlights festivities and weekends in red.
    Watermarked with 'UNICAL Demacs Pharmacy Solver'.
    """
    mode = (mode or "normal").lower()
    orientation = (orientation or "vertical").lower()
    pharmacy_label = (pharmacy_label or "names").lower()
    is_horizontal = orientation in ["horizontal", "row"]
    p_map = pharmacy_name_map or {}

    def get_pharm_display_name(p_dict: dict) -> str:
        p_id = p_dict.get("id")
        if pharmacy_label == "ids":
            return f"F{p_id}"
        
        # Check settings map first
        if p_id in p_map and p_map[p_id]:
            return p_map[p_id]
        
        p_name = p_dict.get("name")
        if p_name and not (p_name.startswith("F") and p_name[1:].isdigit()):
            return p_name
            
        return f"F{p_id}"

    def get_pharm_header_name(fid: int) -> str:
        if pharmacy_label == "ids":
            return f"F{fid}"
        name = p_map.get(fid)
        if name and not (name.startswith("F") and name[1:].isdigit()):
            return name[:12]
        return f"F{fid}"

    # Color Palette (Dark Mode with RED Highlights for Festivities & Weekends)
    bg_color = (15, 23, 42)             # Slate 900
    card_color = (30, 41, 59)           # Slate 800
    header_bg = (51, 65, 85)            # Slate 700
    text_color = (241, 245, 249)         # Slate 100
    subtext_color = (148, 163, 184)      # Slate 400
    primary_color = (56, 189, 248)       # Sky 400

    # RED Highlight Palette (User: "The highlight should be always red")
    red_highlight_bg = (120, 24, 28)     # Dark Red fill for festivity/weekend rows
    red_highlight_light = (145, 32, 36)  # Slightly lighter red for matrix cells
    red_border = (239, 68, 68)           # Vibrant Red indicator bar
    red_text = (252, 165, 165)           # Light Crimson Red text

    grid_line = (71, 85, 105)            # Slate 600
    centro_badge = (37, 99, 235)         # Blue
    marina_badge = (13, 148, 136)        # Teal
    check_color = (34, 197, 94)          # Emerald green for checks

    # Font setup
    try:
        font_title = ImageFont.truetype("arial.ttf", 20)
        font_header = ImageFont.truetype("arial.ttf", 13)
        font_body = ImageFont.truetype("arial.ttf", 12)
        font_small = ImageFont.truetype("arial.ttf", 10)
    except IOError:
        font_title = ImageFont.load_default()
        font_header = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Expand rows for extended mode if needed
    rendered_rows = []
    if mode == "extended":
        dow_letters = ["L", "M", "M", "G", "V", "S", "D"]
        for r in rows:
            w_num = r.get("week", 1)
            w_date_str = r.get("date", "")
            try:
                base_d = datetime.strptime(w_date_str, "%Y-%m-%d").date()
            except Exception:
                base_d = date(year, 1, 1)
            
            fest_str = r.get("festivity")
            pharms = r.get("pharmacies", [])
            for day_i in range(7):
                d_curr = base_d + timedelta(days=day_i)
                dow_char = dow_letters[d_curr.weekday()]
                rendered_rows.append({
                    "week": w_num,
                    "date": d_curr.strftime("%Y-%m-%d"),
                    "giorno": dow_char,
                    "is_weekend": d_curr.weekday() >= 5,
                    "festivity": fest_str if day_i == 0 else None,
                    "pharmacies": pharms,
                    "status": r.get("status", "future")
                })
    else:
        for r in rows:
            w_date_str = r.get("date", "")
            is_wknd = False
            try:
                dt = datetime.strptime(w_date_str, "%Y-%m-%d").date()
                is_wknd = dt.weekday() >= 5
            except Exception:
                pass
            rendered_rows.append({
                **r,
                "is_weekend": is_wknd
            })

    watermark_text = "UNICAL Demacs Pharmacy Solver"

    if is_horizontal:
        # Horizontal Matrix Layout (Months across columns 1..12, Days down rows 1..31)
        col_width = 180
        width = 40 + (12 * col_width)
        row_height = 24
        header_height = 80
        num_rows = 31
        height = header_height + 30 + (num_rows * row_height) + 40

        img = Image.new("RGB", (width, height), bg_color)
        draw = ImageDraw.Draw(img)

        # Title Header with Watermark
        draw.rectangle([(0, 0), (width, header_height)], fill=card_color)
        draw.text((20, 15), f"{watermark_text} - Anno {year} (Orizzontale)", fill=primary_color, font=font_title)
        draw.text((20, 45), f"Modo: {mode} | Etichette: {pharmacy_label} | Generato da {watermark_text}", fill=subtext_color, font=font_small)

        # Table Headers (Months)
        y_hdr = header_height
        draw.rectangle([(0, y_hdr), (width, y_hdr + 28)], fill=header_bg)
        draw.text((8, y_hdr + 6), "Giorno", fill=text_color, font=font_header)

        months_names = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
        for m_idx, m_name in enumerate(months_names):
            x_pos = 40 + (m_idx * col_width)
            draw.text((x_pos + 6, y_hdr + 6), m_name, fill=primary_color, font=font_header)

        # Build day lookup for month/day
        date_map = {}
        for r in rendered_rows:
            d_str = r.get("date")
            if d_str:
                try:
                    dt = datetime.strptime(d_str, "%Y-%m-%d").date()
                    date_map[(dt.month, dt.day)] = r
                except Exception:
                    pass

        y_curr = y_hdr + 28
        for d in range(1, 32):
            r_bg = card_color if d % 2 == 0 else bg_color
            draw.rectangle([(0, y_curr), (width, y_curr + row_height)], fill=r_bg)
            draw.line([(0, y_curr + row_height), (width, y_curr + row_height)], fill=grid_line, width=1)
            draw.text((12, y_curr + 4), str(d), fill=text_color, font=font_body)

            for m in range(1, 13):
                x_pos = 40 + ((m - 1) * col_width)
                draw.line([(x_pos, y_curr), (x_pos, y_curr + row_height)], fill=grid_line, width=1)
                
                item = date_map.get((m, d))
                if item:
                    # RED Highlight for both Festivities AND Weekends
                    is_fest = bool(item.get("festivity") and item.get("festivity") != "-")
                    is_wknd = False
                    try:
                        dt = date(year, m, d)
                        is_wknd = dt.weekday() >= 5
                    except Exception:
                        pass

                    if is_fest or is_wknd:
                        draw.rectangle([(x_pos + 1, y_curr + 1), (x_pos + col_width - 1, y_curr + row_height - 1)], fill=red_highlight_bg if is_fest else red_highlight_light)

                    pharms = item.get("pharmacies", [])
                    p_disp = "-".join(get_pharm_display_name(p) for p in pharms)
                    txt_color = red_text if (is_fest or is_wknd) else text_color
                    draw.text((x_pos + 4, y_curr + 4), p_disp[:22], fill=txt_color, font=font_small)

            y_curr += row_height

        # Footer Watermark
        draw.text((20, height - 25), watermark_text, fill=subtext_color, font=font_small)

    else:
        # Vertical Layout (Column-based)
        row_height = 32
        header_height = 80
        footer_height = 40
        num_rows = max(len(rendered_rows), 1)
        height = header_height + 32 + (num_rows * row_height) + footer_height

        if mode == "compact":
            width = 1350 if pharmacy_label == "names" else 1150
        elif mode == "tiny":
            width = 850
        elif mode == "extended":
            width = 1150
        else:  # normal
            width = 1000

        img = Image.new("RGB", (width, height), bg_color)
        draw = ImageDraw.Draw(img)

        # Title Header with Watermark
        draw.rectangle([(0, 0), (width, header_height)], fill=card_color)
        draw.text((24, 16), f"{watermark_text} - Anno {year}", fill=primary_color, font=font_title)
        draw.text((24, 46), f"Modo: {mode} | Etichette: {pharmacy_label} | Generato da {watermark_text}", fill=subtext_color, font=font_small)

        y_hdr = header_height
        draw.rectangle([(0, y_hdr), (width, y_hdr + 32)], fill=header_bg)

        if mode == "compact":
            col_wk, col_date, col_fest, col_p_start = 16, 85, 200, 360
            col_p_width = 95 if pharmacy_label == "names" else 75
            draw.text((col_wk, y_hdr + 8), "Wk", fill=text_color, font=font_header)
            draw.text((col_date, y_hdr + 8), "Data Inizio", fill=text_color, font=font_header)
            draw.text((col_fest, y_hdr + 8), "Festività", fill=text_color, font=font_header)
            for i in range(1, 11):
                h_name = get_pharm_header_name(i)
                draw.text((col_p_start + (i - 1) * col_p_width, y_hdr + 8), h_name, fill=text_color, font=font_header)
        elif mode == "extended":
            col_wk, col_date, col_dow, col_fest, col_pharm = 16, 85, 190, 240, 520
            draw.text((col_wk, y_hdr + 8), "Wk", fill=text_color, font=font_header)
            draw.text((col_date, y_hdr + 8), "Data", fill=text_color, font=font_header)
            draw.text((col_dow, y_hdr + 8), "Giorno", fill=text_color, font=font_header)
            draw.text((col_fest, y_hdr + 8), "Festività", fill=text_color, font=font_header)
            draw.text((col_pharm, y_hdr + 8), "Farmacie di Turno", fill=text_color, font=font_header)
        elif mode == "tiny":
            col_wk, col_date, col_fest, col_pharm = 16, 85, 200, 420
            draw.text((col_wk, y_hdr + 8), "Wk", fill=text_color, font=font_header)
            draw.text((col_date, y_hdr + 8), "Data Inizio", fill=text_color, font=font_header)
            draw.text((col_fest, y_hdr + 8), "Festività", fill=text_color, font=font_header)
            draw.text((col_pharm, y_hdr + 8), "Farmacie di Turno", fill=text_color, font=font_header)
        else: # normal
            col_wk, col_date, col_fest, col_pharm = 16, 85, 200, 440
            draw.text((col_wk, y_hdr + 8), "Wk", fill=text_color, font=font_header)
            draw.text((col_date, y_hdr + 8), "Data Inizio", fill=text_color, font=font_header)
            draw.text((col_fest, y_hdr + 8), "Festività", fill=text_color, font=font_header)
            draw.text((col_pharm, y_hdr + 8), "Farmacie di Turno", fill=text_color, font=font_header)

        y_curr = y_hdr + 32

        for idx, row in enumerate(rendered_rows):
            fest_val = row.get("festivity") or "-"
            is_fest = fest_val != "-" and bool(fest_val)
            is_wknd = bool(row.get("is_weekend")) or (row.get("giorno") in ["S", "D"])

            # RED Row background highlight for festivity & weekend
            if is_fest or is_wknd:
                r_bg = red_highlight_bg if is_fest else red_highlight_light
            else:
                r_bg = card_color if idx % 2 == 0 else bg_color

            draw.rectangle([(0, y_curr), (width, y_curr + row_height)], fill=r_bg)
            
            # Left vertical red indicator bar for festivities
            if is_fest:
                draw.rectangle([(0, y_curr), (6, y_curr + row_height)], fill=red_border)

            draw.line([(0, y_curr + row_height), (width, y_curr + row_height)], fill=grid_line, width=1)

            draw.text((col_wk, y_curr + 8), f"{row.get('week', '')}", fill=primary_color, font=font_body)
            draw.text((col_date, y_curr + 8), str(row.get('date', '')), fill=subtext_color, font=font_body)

            if mode == "extended":
                dow_val = str(row.get('giorno', ''))
                dow_col = red_text if dow_val in ["S", "D"] else text_color
                draw.text((col_dow, y_curr + 8), dow_val, fill=dow_col, font=font_body)

            draw.text((col_fest, y_curr + 8), str(fest_val)[:22], fill=red_text if (is_fest or is_wknd) else subtext_color, font=font_body)

            pharmacies = row.get("pharmacies", [])
            assigned_ids = {p.get("id") for p in pharmacies if isinstance(p, dict)}

            if mode == "compact":
                col_p_w = 95 if pharmacy_label == "names" else 75
                for i in range(1, 11):
                    x_col = col_p_start + (i - 1) * col_p_w
                    if i in assigned_ids:
                        draw.text((x_col + 8, y_curr + 8), "✓", fill=check_color, font=font_body)
            elif mode == "tiny":
                p_disp = "-".join(get_pharm_display_name(p) for p in pharmacies)
                draw.text((col_pharm, y_curr + 8), p_disp, fill=text_color, font=font_body)
            else:
                x_pharm = col_pharm
                for p in pharmacies:
                    p_disp = get_pharm_display_name(p)
                    loc = p.get("location", "")
                    badge_bg = centro_badge if loc == "centro" else marina_badge
                    p_text = f"{p_disp} ({loc})" if (loc and pharmacy_label == "names") else p_disp
                    draw.rectangle([(x_pharm, y_curr + 4), (x_pharm + 130, y_curr + 26)], fill=badge_bg)
                    draw.text((x_pharm + 6, y_curr + 7), p_text, fill=(255, 255, 255), font=font_small)
                    x_pharm += 138

            y_curr += row_height

        # Footer Watermark
        draw.text((24, height - 25), watermark_text, fill=subtext_color, font=font_small)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    logging.info(f"Generated schedule PNG chart ({mode}, {orientation}, label={pharmacy_label}) at {output_path}")

