

# """
# receipt.py — Professional PDF receipt generator for Baiskeli Centre.
# """
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, HRFlowable, Table, TableStyle
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.lib.pagesizes import A5
# from reportlab.lib.units import mm
# from reportlab.lib import colors
# from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
# from datetime import datetime
# import io
# import os

# # ── Shop constants (edit here) ─────────────────────────────────
# SHOP_NAME    = "Baiskeli Centre"
# SHOP_ADDRESS = "Kipande Road| Globe Roundabout, Nairobi"
# SHOP_PHONE   = "0746 726 202"
# SHOP_EMAIL   = "www.baiskelicentre.co.ke"
# LOGO_PATH    = "Assets/logo.png"
# # ───────────────────────────────────────────────────────────────


# def _styles():
#     base = getSampleStyleSheet()
#     return {
#         "title": ParagraphStyle("title", parent=base["Normal"],
#                                 fontSize=16, fontName="Helvetica-Bold",
#                                 alignment=TA_CENTER, spaceAfter=2),
#         "shop_sub": ParagraphStyle("shop_sub", parent=base["Normal"],
#                                    fontSize=8, alignment=TA_CENTER, spaceAfter=1,
#                                    textColor=colors.HexColor("#555555")),
#         "heading": ParagraphStyle("heading", parent=base["Normal"],
#                                   fontSize=9, fontName="Helvetica-Bold",
#                                   spaceAfter=2),
#         "normal": ParagraphStyle("normal", parent=base["Normal"],
#                                  fontSize=8.5, spaceAfter=1),
#         "small": ParagraphStyle("small", parent=base["Normal"],
#                                 fontSize=7.5, textColor=colors.HexColor("#666666")),
#         "total": ParagraphStyle("total", parent=base["Normal"],
#                                 fontSize=12, fontName="Helvetica-Bold",
#                                 alignment=TA_RIGHT, spaceBefore=4),
#         "footer": ParagraphStyle("footer", parent=base["Normal"],
#                                  fontSize=7.5, alignment=TA_CENTER,
#                                  textColor=colors.HexColor("#888888")),
#         "discount": ParagraphStyle("discount", parent=base["Normal"],
#                                    fontSize=8.5, alignment=TA_RIGHT,
#                                    textColor=colors.HexColor("#cc0000")),
#     }


# def generate_pdf_receipt(
#     receipt_no,
#     items,
#     total,
#     customer_name="Walk-in",
#     payment_method="Cash",
#     discount=0.0,
#     amount_paid=None,
#     repair_info=None
# ):
#     """
#     items: list of {"name": str, "quantity": int/float, "price": float}
#     repair_info: optional dict with "bike", "issue", "phone"
#     """
#     buffer = io.BytesIO()
#     doc = SimpleDocTemplate(
#         buffer,
#         pagesize=A5,
#         rightMargin=12*mm, leftMargin=12*mm,
#         topMargin=10*mm, bottomMargin=10*mm
#     )

#     s = _styles()
#     content = []

#     # ── LOGO ──────────────────────────────────────────────────
#     if os.path.exists(LOGO_PATH):
#         try:
#             logo = Image(LOGO_PATH, width=50*mm, height=30*mm)
#             logo.hAlign = "CENTER"
#             content.append(logo)
#             content.append(Spacer(1, 2*mm))
#         except Exception:
#             pass

#     # ── SHOP HEADER ───────────────────────────────────────────
#     content.append(Paragraph(SHOP_NAME, s["title"]))
#     content.append(Paragraph(SHOP_ADDRESS, s["shop_sub"]))
#     content.append(Paragraph(f"📞 {SHOP_PHONE}   ✉ {SHOP_EMAIL}", s["shop_sub"]))
#     content.append(Spacer(1, 3*mm))
#     content.append(HRFlowable(width="100%", thickness=1.5, color=colors.black))
#     content.append(Spacer(1, 2*mm))

#     # ── RECEIPT META ──────────────────────────────────────────
#     meta_data = [
#         ["Receipt No:", f"#{receipt_no}"],
#         ["Date:", datetime.now().strftime("%d %b %Y  %H:%M")],
#         ["Customer:", customer_name],
#         ["Payment:", payment_method],
#     ]
#     if repair_info:
#         meta_data.append(["Bike:", repair_info.get("bike", "")])
#         if repair_info.get("phone"):
#             meta_data.append(["Phone:", repair_info["phone"]])
#         if repair_info.get("issue"):
#             meta_data.append(["Issue:", repair_info["issue"]])

#     meta_table = Table(meta_data, colWidths=[28*mm, None])
#     meta_table.setStyle(TableStyle([
#         ("FONTSIZE", (0, 0), (-1, -1), 8),
#         ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
#         ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#333333")),
#         ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
#         ("TOPPADDING", (0, 0), (-1, -1), 1.5),
#     ]))
#     content.append(meta_table)
#     content.append(Spacer(1, 3*mm))
#     content.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa")))
#     content.append(Spacer(1, 2*mm))

#     # ── ITEMS TABLE ───────────────────────────────────────────
#     item_rows = [["Item", "Qty", "Unit", "Total"]]
#     subtotal = 0
#     for item in items:
#         name  = item.get("name", "")
#         qty   = item.get("quantity", 1)
#         price = item.get("price", 0)
#         line  = float(qty) * float(price)
#         subtotal += line
#         item_rows.append([
#             Paragraph(name, s["small"]),
#             str(qty),
#             f"{float(price):,.2f}",
#             f"{line:,.2f}",
#         ])

#     item_table = Table(item_rows, colWidths=[55*mm, 12*mm, 22*mm, 24*mm])
#     item_table.setStyle(TableStyle([
#         ("FONTSIZE",      (0, 0), (-1, -1), 8),
#         ("FONTNAME",      (0, 0), (-1,  0), "Helvetica-Bold"),
#         ("BACKGROUND",    (0, 0), (-1,  0), colors.HexColor("#f0f0f0")),
#         ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
#         ("ALIGN",         (1, 0), (-1, -1), "RIGHT"),
#         ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
#         ("TOPPADDING",    (0, 0), (-1, -1), 2),
#     ]))
#     content.append(item_table)
#     content.append(Spacer(1, 3*mm))
#     content.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa")))
#     content.append(Spacer(1, 2*mm))

#     # ── TOTALS ────────────────────────────────────────────────
#     totals_data = []
#     if discount and float(discount) > 0:
#         totals_data.append(["Subtotal:", f"KES {subtotal:,.2f}"])
#         totals_data.append(["Discount:", f"- KES {float(discount):,.2f}"])

#     totals_data.append(["TOTAL:", f"KES {total:,.2f}"])

#     if amount_paid and float(amount_paid) > 0:
#         totals_data.append(["Amount Paid:", f"KES {float(amount_paid):,.2f}"])
#         change = float(amount_paid) - float(total)
#         if change >= 0:
#             totals_data.append(["Change:", f"KES {change:,.2f}"])

#     totals_table = Table(totals_data, colWidths=[None, 35*mm])
#     total_row_idx = next(i for i, r in enumerate(totals_data) if r[0] == "TOTAL:")
#     totals_table.setStyle(TableStyle([
#         ("FONTSIZE",      (0, 0), (-1, -1), 9),
#         ("ALIGN",         (0, 0), (-1, -1), "RIGHT"),
#         ("FONTNAME",      (0, total_row_idx), (-1, total_row_idx), "Helvetica-Bold"),
#         ("FONTSIZE",      (0, total_row_idx), (-1, total_row_idx), 11),
#         ("LINEABOVE",     (0, total_row_idx), (-1, total_row_idx), 1, colors.black),
#         ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
#         ("TOPPADDING",    (0, 0), (-1, -1), 2),
#     ]))
#     content.append(totals_table)
#     content.append(Spacer(1, 5*mm))

#     # ── FOOTER ────────────────────────────────────────────────
#     content.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa")))
#     content.append(Spacer(1, 2*mm))
#     content.append(Paragraph("Thank you for choosing Baiskeli Centre! 🚴", s["footer"]))
#     content.append(Paragraph("Keep this receipt for your records.", s["footer"]))

#     doc.build(content)
#     buffer.seek(0)
#     return buffer

"""
receipt.py — Thermal-style supermarket receipt for Baiskeli Centre.
Canvas-drawn for precise layout. Drop-in replacement.
"""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.lib import colors
from datetime import datetime
import io
import os

# ── Shop constants ────────────────────────────────────────────
SHOP_NAME    = "BAISKELI CENTRE"
SHOP_ADDRESS = "Kipande Road  |  Globe Roundabout"
SHOP_PHONE   = "0746 726 202"
SHOP_WEB     = "www.baiskelicentre.co.ke"
LOGO_PATH    = "Assets/logo.png"
# ─────────────────────────────────────────────────────────────

# ── Receipt column on A5 page (80 mm wide, centred) ───────────
ROLL_W  = 82 * mm
PAGE_W, PAGE_H = A5
MARGIN  = (PAGE_W - ROLL_W) / 2
L       = MARGIN
R       = MARGIN + ROLL_W
CX      = MARGIN + ROLL_W / 2

# ── Palette ───────────────────────────────────────────────────
BLACK  = colors.HexColor("#111111")
DGREY  = colors.HexColor("#333333")
MGREY  = colors.HexColor("#777777")
LGREY  = colors.HexColor("#F0F0F0")
WHITE  = colors.white
ACCENT = colors.HexColor("#C1121F")   # Baiskeli red

# ── Fonts ─────────────────────────────────────────────────────
FB = "Helvetica-Bold"
FN = "Helvetica"
FI = "Helvetica-Oblique"


# ── Primitives ────────────────────────────────────────────────
def txt(c, x, y, s, font=FN, size=8, color=BLACK, align="left"):
    c.setFont(font, size)
    c.setFillColor(color)
    s = str(s)
    if align == "center":
        c.drawCentredString(x, y, s)
    elif align == "right":
        c.drawRightString(x, y, s)
    else:
        c.drawString(x, y, s)

def hline(c, y, dashed=False, color=None, width=0.5):
    c.setLineWidth(width)
    c.setStrokeColor(color or colors.HexColor("#CCCCCC"))
    c.setDash([2, 3] if dashed else [])
    c.line(L + 1*mm, y, R - 1*mm, y)
    c.setDash([])

def filled_rect(c, x, y, w, h, fill_color):
    c.setFillColor(fill_color)
    c.rect(x, y, w, h, fill=1, stroke=0)


# ── HEADER: logo + shop name + address ───────────────────────
def draw_header(c, sale_id, customer, payment, rtype, y):
    # White top band
    filled_rect(c, L, y - 22*mm, ROLL_W, 22*mm, WHITE)

    # Logo on the left
    if os.path.exists(LOGO_PATH):
        try:
            c.drawImage(
                LOGO_PATH,
                L + 2*mm, y - 19*mm,
                width=18*mm, height=16*mm,
                preserveAspectRatio=True, mask="auto"
            )
        except Exception:
            pass

    # Shop name & contact stacked to the right of logo
    tx = L + 22*mm
    txt(c, tx, y - 6*mm,  SHOP_NAME,    font=FB, size=11, color=BLACK)
    txt(c, tx, y - 11*mm, SHOP_ADDRESS, font=FN, size=6.5, color=DGREY)
    txt(c, tx, y - 15*mm, f"Tel: {SHOP_PHONE}", font=FN, size=6.5, color=DGREY)
    txt(c, tx, y - 19*mm, SHOP_WEB,     font=FI, size=6.5, color=ACCENT)

    y -= 22*mm

    # Red receipt-type banner
    filled_rect(c, L, y - 7*mm, ROLL_W, 7*mm, ACCENT)
    txt(c, CX, y - 4.8*mm, rtype, font=FB, size=7.5, color=WHITE, align="center")
    y -= 9*mm

    hline(c, y, color=colors.HexColor("#AAAAAA"), width=0.8)
    y -= 4*mm

    # ── Meta table (2×2 grid: label / value) ─────────────────
    def meta_pair(label, val, lx, cy):
        txt(c, lx,          cy,          label, font=FN,  size=6,   color=MGREY)
        txt(c, lx,          cy - 3.8*mm, val,   font=FB,  size=7.5, color=BLACK)

    col2 = CX + 2*mm
    meta_pair("RECEIPT NO",  f"#{sale_id}",                        L + 2*mm, y)
    meta_pair("DATE",        datetime.now().strftime("%d %b %Y  %H:%M"), col2, y)
    y -= 10*mm
    meta_pair("CUSTOMER",    customer,                              L + 2*mm, y)
    meta_pair("PAYMENT",     payment,                               col2,     y)
    y -= 10*mm

    hline(c, y, dashed=True, width=0.8)
    return y - 4*mm


# ── REPAIR INFO BOX ───────────────────────────────────────────
def draw_repair_box(c, info, y):
    if not info:
        return y
    rows = [
        ("BIKE",  info.get("bike", "")),
        ("ISSUE", info.get("issue", "")),
        ("PHONE", info.get("phone", "")),
    ]
    rows = [(lbl, val) for lbl, val in rows if val]
    if not rows:
        return y

    box_h = len(rows) * 8*mm + 5*mm
    filled_rect(c, L + 1*mm, y - box_h, ROLL_W - 2*mm, box_h, LGREY)

    ry = y - 5*mm
    for label, val in rows:
        txt(c, L + 3*mm,  ry, label + ":", font=FB, size=6.5, color=MGREY)
        display = val if len(str(val)) <= 32 else str(val)[:31] + "…"
        txt(c, L + 18*mm, ry, display,     font=FN, size=7.5, color=BLACK)
        ry -= 8*mm

    hline(c, y - box_h - 2*mm, dashed=True)
    return y - box_h - 6*mm


# ── ITEMS TABLE ───────────────────────────────────────────────
def draw_items(c, items, y):
    COL_QTY   = R - 36*mm
    COL_UNIT  = R - 18*mm
    COL_TOTAL = R - 1*mm

    # Header row
    filled_rect(c, L, y - 6.5*mm, ROLL_W, 6.5*mm, colors.HexColor("#222222"))
    txt(c, L + 2*mm, y - 4.5*mm, "DESCRIPTION", font=FB, size=6.5, color=WHITE)
    txt(c, COL_QTY,  y - 4.5*mm, "QTY",         font=FB, size=6.5, color=WHITE, align="right")
    txt(c, COL_UNIT, y - 4.5*mm, "UNIT",         font=FB, size=6.5, color=WHITE, align="right")
    txt(c, COL_TOTAL,y - 4.5*mm, "AMOUNT",       font=FB, size=6.5, color=WHITE, align="right")
    y -= 7.5*mm

    subtotal = 0
    for i, item in enumerate(items):
        name   = str(item.get("name", ""))
        qty    = item.get("quantity", 1)
        price  = float(item.get("price", 0))
        amount = float(qty) * price
        subtotal += amount

        is_service = name.startswith("---") or name.startswith("──")
        if is_service:
            hline(c, y + 1*mm, dashed=True)
            name = name.replace("---", "").replace("──", "").strip()

        row_h = 7.5*mm

        # Zebra stripe
        if i % 2 == 0:
            filled_rect(c, L, y - row_h + 1.5*mm, ROLL_W, row_h, colors.HexColor("#F8F8F8"))

        display = name if len(name) <= 26 else name[:25] + "…"
        txt(c, L + 2*mm, y - 4*mm, display,         font=FB if is_service else FN, size=7.5, color=BLACK)
        txt(c, COL_QTY,  y - 4*mm, str(qty),         font=FN, size=7.5, color=DGREY, align="right")
        txt(c, COL_UNIT, y - 4*mm, f"{price:,.2f}",  font=FN, size=7.5, color=DGREY, align="right")
        txt(c, COL_TOTAL,y - 4*mm, f"{amount:,.2f}", font=FB, size=7.5, color=BLACK,  align="right")

        y -= row_h

    hline(c, y, color=BLACK, width=0.8)
    return y - 3*mm, subtotal


# ── TOTALS BLOCK ──────────────────────────────────────────────
def draw_totals(c, subtotal, discount, total, amount_paid, y):
    # Discount line (if any)
    if discount and float(discount) > 0:
        txt(c, L + 2*mm, y - 4*mm,  "Subtotal:",          font=FN, size=7.5, color=MGREY)
        txt(c, R - 2*mm, y - 4*mm,  f"KES {subtotal:,.2f}", font=FN, size=7.5, color=MGREY, align="right")
        y -= 7*mm
        txt(c, L + 2*mm, y - 4*mm,  "Discount:",           font=FN, size=7.5, color=ACCENT)
        txt(c, R - 2*mm, y - 4*mm,  f"- KES {float(discount):,.2f}", font=FN, size=7.5, color=ACCENT, align="right")
        y -= 5*mm
        hline(c, y, color=BLACK, width=0.5)
        y -= 3*mm

    # TOTAL band
    bh = 11*mm
    filled_rect(c, L, y - bh, ROLL_W, bh, BLACK)
    txt(c, L + 3*mm, y - 7*mm, "TOTAL  KES",        font=FB, size=8.5, color=WHITE)
    txt(c, R - 2*mm, y - 7.5*mm, f"{float(total):,.2f}", font=FB, size=14,  color=WHITE, align="right")
    y -= bh + 3*mm

    # Amount paid / change
    if amount_paid and float(amount_paid) > 0:
        txt(c, L + 2*mm, y - 4*mm, "Amount Paid:",        font=FN, size=7.5, color=DGREY)
        txt(c, R - 2*mm, y - 4*mm, f"KES {float(amount_paid):,.2f}", font=FN, size=7.5, color=DGREY, align="right")
        y -= 7*mm
        change = float(amount_paid) - float(total)
        if change >= 0:
            txt(c, L + 2*mm, y - 4*mm, "Change:",             font=FB, size=8,   color=BLACK)
            txt(c, R - 2*mm, y - 4*mm, f"KES {change:,.2f}",  font=FB, size=8,   color=BLACK, align="right")
            y -= 7*mm

    return y - 2*mm


# ── FOOTER ────────────────────────────────────────────────────
def draw_footer(c, y):
    hline(c, y, dashed=True)
    y -= 5*mm
    txt(c, CX, y,         "Thank you for your business!",  font=FB, size=8,   color=BLACK, align="center")
    txt(c, CX, y - 5*mm,  "Ride safe  —  See you soon 🚴", font=FI, size=7,   color=MGREY, align="center")
    y -= 14*mm

    # Decorative barcode
    widths = [1,2,1,3,1,1,2,1,2,1,3,1,2,1,1,2,1,3,1,2,1,1,2,1,2]
    bx = CX - 15*mm
    for i, w in enumerate(widths):
        ww = w * 0.75*mm
        if i % 2 == 0:
            filled_rect(c, bx, y - 7*mm, ww, 7*mm, BLACK)
        bx += ww + 0.4*mm

    txt(c, CX, y - 10*mm, "* BAISKELI CENTRE *", font=FN, size=6.5, color=MGREY, align="center")

    # Bottom red bar
    filled_rect(c, L, 0, ROLL_W, 3.5*mm, ACCENT)


# ══════════════════════════════════════════════════════════════
#  PUBLIC API
# ══════════════════════════════════════════════════════════════
def generate_pdf_receipt(
    receipt_no,
    items,
    total,
    customer_name="Walk-in",
    payment_method="Cash",
    discount=0.0,
    amount_paid=None,
    repair_info=None
):
    buf   = io.BytesIO()
    cv    = canvas.Canvas(buf, pagesize=A5)
    rtype = "★  REPAIR RECEIPT  ★" if repair_info else "★  SALES RECEIPT  ★"

    y = PAGE_H - 8*mm
    y = draw_header(cv, receipt_no, customer_name, payment_method, rtype, y)

    if repair_info:
        y = draw_repair_box(cv, repair_info, y)

    y, subtotal = draw_items(cv, items, y)
    y = draw_totals(cv, subtotal, discount, total, amount_paid, y)
    draw_footer(cv, y)

    cv.save()
    buf.seek(0)
    return buf