import os
import docx
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def create_report():
    doc = Document()

    # =========================================================================
    # 1. CẤU HÌNH TRANG A4 CHUẨN IN 2 MẶT & FONT TIMES NEW ROMAN 13PT
    # =========================================================================
    for section in doc.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(2.0)
        section.left_margin = Cm(2.8)
        section.right_margin = Cm(2.0)
        section.different_first_page_header_footer = False

        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        fr1 = fp.add_run("Trang ")
        fr1.font.name = "Times New Roman"
        fr1.font.size = Pt(10.5)
        fr1.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

        fldSimple = OxmlElement('w:fldSimple')
        fldSimple.set(qn('w:instr'), 'PAGE')
        fp._p.append(fldSimple)

    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(13)
    normal_style.font.color.rgb = RGBColor(0x00, 0x00, 0x00)
    rPr = normal_style.element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.append(rFonts)
    rFonts.set(qn('w:ascii'), 'Times New Roman')
    rFonts.set(qn('w:hAnsi'), 'Times New Roman')
    rFonts.set(qn('w:cs'), 'Times New Roman')
    normal_style.paragraph_format.line_spacing = 1.3
    normal_style.paragraph_format.space_before = Pt(0)
    normal_style.paragraph_format.space_after = Pt(5)

    COLOR_BLACK = RGBColor(0x00, 0x00, 0x00)
    COLOR_DARK = RGBColor(0x1A, 0x1A, 0x1A)
    HEX_TH_BG = "E8ECEF"
    HEX_CODE_BG = "F5F5F5"
    HEX_BORDER = "444444"

    # =========================================================================
    # 2. CÁC HÀM HỖ TRỢ ĐỊNH DẠNG CHUẨN MẪU BÁO CÁO
    # =========================================================================
    def style_run(run, size=13, bold=False, italic=False, font_name="Times New Roman", color=COLOR_BLACK):
        run.font.name = font_name
        run.font.size = Pt(size)
        run.bold = bold
        run.italic = italic
        run.font.color.rgb = color
        rPr_el = run._r.get_or_add_rPr()
        rf = rPr_el.find(qn('w:rFonts'))
        if rf is None:
            rf = OxmlElement('w:rFonts')
            rPr_el.append(rf)
        rf.set(qn('w:ascii'), font_name)
        rf.set(qn('w:hAnsi'), font_name)
        rf.set(qn('w:cs'), font_name)
        return run

    def set_cell_background(cell, fill_hex):
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), fill_hex)
        tcPr.append(shd)

    def set_cell_margins(cell, top=75, bottom=75, left=105, right=105):
        tcPr = cell._tc.get_or_add_tcPr()
        tcMar = OxmlElement('w:tcMar')
        for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
            node = OxmlElement(f'w:{m}')
            node.set(qn('w:w'), str(val))
            node.set(qn('w:type'), 'dxa')
            tcMar.append(node)
        tcPr.append(tcMar)

    def set_cell_borders(cell, color=HEX_BORDER, sz="4"):
        tcPr = cell._tc.get_or_add_tcPr()
        tcBorders = OxmlElement('w:tcBorders')
        for side in ('top', 'bottom', 'left', 'right'):
            b = OxmlElement(f'w:{side}')
            b.set(qn('w:val'), 'single')
            b.set(qn('w:sz'), sz)
            b.set(qn('w:space'), '0')
            b.set(qn('w:color'), color)
            tcBorders.append(b)
        tcPr.append(tcBorders)

    def set_repeat_table_header(row):
        trPr = row._tr.get_or_add_trPr()
        tblHeader = OxmlElement('w:tblHeader')
        trPr.append(tblHeader)

    def prevent_row_split(row):
        trPr = row._tr.get_or_add_trPr()
        cantSplit = OxmlElement('w:cantSplit')
        trPr.append(cantSplit)

    def add_h1(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.3
        p.paragraph_format.keep_with_next = True
        style_run(p.add_run(text), size=14, bold=True)
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.3
        p.paragraph_format.keep_with_next = True
        style_run(p.add_run(text), size=13, bold=True)
        return p

    def add_body(text, bold_prefix="", indent=True, space_after=6):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.3
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(space_after)
        if indent:
            p.paragraph_format.first_line_indent = Cm(0.75)
        if bold_prefix:
            style_run(p.add_run(bold_prefix), size=13, bold=True)
        style_run(p.add_run(text), size=13)
        return p

    def add_bullet(bold_prefix, text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.3
        p.paragraph_format.left_indent = Cm(1.0)
        p.paragraph_format.first_line_indent = Cm(-0.4)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(4)
        style_run(p.add_run("–  "), size=13)
        if bold_prefix:
            style_run(p.add_run(bold_prefix + ": "), size=13, bold=True)
        style_run(p.add_run(text), size=13)
        return p

    def add_equation(eq_text, eq_num):
        t = doc.add_table(rows=1, cols=2)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        t.columns[0].width = Cm(14.0)
        t.columns[1].width = Cm(2.2)
        for c in (t.cell(0, 0), t.cell(0, 1)):
            tcPr = c._tc.get_or_add_tcPr()
            tcBorders = OxmlElement('w:tcBorders')
            for side in ('top', 'bottom', 'left', 'right'):
                b = OxmlElement(f'w:{side}')
                b.set(qn('w:val'), 'none')
                tcBorders.append(b)
            tcPr.append(tcBorders)
            set_cell_margins(c, top=35, bottom=35, left=40, right=40)
        p0 = t.cell(0, 0).paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p0.paragraph_format.line_spacing = 1.3
        p0.paragraph_format.space_after = Pt(0)
        style_run(p0.add_run(eq_text), size=13, italic=True)
        p1 = t.cell(0, 1).paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p1.paragraph_format.line_spacing = 1.3
        p1.paragraph_format.space_after = Pt(0)
        style_run(p1.add_run(f"({eq_num})"), size=13)

        sp = doc.add_paragraph()
        sp.paragraph_format.space_before = Pt(0)
        sp.paragraph_format.space_after = Pt(4)

    def add_figure(img_path, fig_num, caption_text, width_cm=15.5):
        if os.path.exists(img_path):
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(6)
            p_img.paragraph_format.space_after = Pt(4)
            p_img.paragraph_format.keep_with_next = True
            p_img.add_run().add_picture(img_path, width=Cm(width_cm))

            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_before = Pt(0)
            p_cap.paragraph_format.space_after = Pt(8)
            p_cap.paragraph_format.line_spacing = 1.2
            style_run(p_cap.add_run(f"Hình {fig_num}. "), size=12, bold=True, italic=True)
            style_run(p_cap.add_run(caption_text), size=12, italic=True)

    def add_academic_table(table_num, caption_text, headers, rows, col_widths_cm, center_cols=None, font_size=11.0):
        if center_cols is None:
            center_cols = []
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(8)
        p_cap.paragraph_format.space_after = Pt(4)
        p_cap.paragraph_format.line_spacing = 1.2
        p_cap.paragraph_format.keep_with_next = True
        style_run(p_cap.add_run(f"Bảng {table_num}. "), size=12, bold=True)
        style_run(p_cap.add_run(caption_text), size=12, italic=False)

        t = doc.add_table(rows=len(rows) + 1, cols=len(headers))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False

        for idx, w in enumerate(col_widths_cm):
            t.columns[idx].width = Cm(w)

        set_repeat_table_header(t.rows[0])
        prevent_row_split(t.rows[0])
        for c_idx, h_text in enumerate(headers):
            cell = t.cell(0, c_idx)
            cell.width = Cm(col_widths_cm[c_idx])
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_background(cell, HEX_TH_BG)
            set_cell_margins(cell, top=80, bottom=80, left=95, right=95)
            set_cell_borders(cell, color=HEX_BORDER, sz="6")
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.15
            style_run(p.add_run(h_text), size=font_size, bold=True)

        for r_idx, row_data in enumerate(rows):
            prevent_row_split(t.rows[r_idx + 1])
            for c_idx, val in enumerate(row_data):
                cell = t.cell(r_idx + 1, c_idx)
                cell.width = Cm(col_widths_cm[c_idx])
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                set_cell_margins(cell, top=60, bottom=60, left=95, right=95)
                set_cell_borders(cell, color=HEX_BORDER, sz="4")
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx in center_cols else WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.15
                style_run(p.add_run(str(val)), size=font_size)

        sp = doc.add_paragraph()
        sp.paragraph_format.space_before = Pt(0)
        sp.paragraph_format.space_after = Pt(6)

    def add_code_block(code_str, title=None):
        if title:
            p_t = doc.add_paragraph()
            p_t.paragraph_format.space_before = Pt(6)
            p_t.paragraph_format.space_after = Pt(2)
            p_t.paragraph_format.keep_with_next = True
            style_run(p_t.add_run(title), size=12, bold=True, italic=True)

        t = doc.add_table(rows=1, cols=1)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        t.columns[0].width = Cm(16.2)
        cell = t.cell(0, 0)
        set_cell_background(cell, HEX_CODE_BG)
        set_cell_margins(cell, top=75, bottom=75, left=115, right=115)
        set_cell_borders(cell, color="999999", sz="4")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.12
        style_run(p.add_run(code_str), size=9.3, font_name="Courier New", color=COLOR_DARK)

        sp = doc.add_paragraph()
        sp.paragraph_format.space_before = Pt(0)
        sp.paragraph_format.space_after = Pt(6)

    # =========================================================================
    # PHẦN ĐẦU BÁO CÁO (THEO ĐÚNG MẪU QUY ĐỊNH)
    # =========================================================================
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(4)
    p_title.paragraph_format.space_after = Pt(10)
    p_title.paragraph_format.line_spacing = 1.3
    style_run(
        p_title.add_run("THIẾT KẾ VÀ TRIỂN KHAI HỆ THỐNG IOT GIÁM SÁT MỰC NƯỚC, LƯU TRỮ CƠ SỞ DỮ LIỆU ĐÁM MÂY VÀ CẢNH BÁO NGẬP LỤT ĐA TẦNG"),
        size=15.5, bold=True
    )

    p_authors = doc.add_paragraph()
    p_authors.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_authors.paragraph_format.space_before = Pt(0)
    p_authors.paragraph_format.space_after = Pt(3)
    p_authors.paragraph_format.line_spacing = 1.3
    style_run(p_authors.add_run("Tên sinh viên thực hiện: "), size=13, bold=True)
    style_run(p_authors.add_run(".........................................................................................."), size=13)

    p_email = doc.add_paragraph()
    p_email.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_email.paragraph_format.space_before = Pt(0)
    p_email.paragraph_format.space_after = Pt(12)
    p_email.paragraph_format.line_spacing = 1.3
    style_run(p_email.add_run("Địa chỉ email: "), size=13, bold=True)
    style_run(p_email.add_run(".........................................................................................................."), size=13)

    # Tóm tắt (~220 từ, súc tích, chuẩn học thuật)
    p_abs = doc.add_paragraph()
    p_abs.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_abs.paragraph_format.line_spacing = 1.3
    p_abs.paragraph_format.space_before = Pt(4)
    p_abs.paragraph_format.space_after = Pt(6)
    style_run(p_abs.add_run("Tóm tắt— "), size=13, bold=True, italic=True)
    style_run(
        p_abs.add_run(
            "Báo cáo này trình bày thiết kế và triển khai một hệ thống IoT giám sát mực nước, áp suất thủy tĩnh và cảnh báo ngập lụt đa tầng. "
            "Ở tầng đo lường biên, cảm biến áp suất thủy tĩnh thả chìm (dải đo 0–5 m, ngõ ra 0–3,3 V) được đọc qua vi điều khiển STM32F103C8T6 "
            "(xung nội HSI 8 MHz) áp dụng chuỗi xử lý số gồm tự hiệu chuẩn ADC, quá mẫu 32 lần mỗi 100 ms, bù điểm không 0,12 V, lọc thông thấp "
            "thích nghi Adaptive EMA (α = 0,80 khi biến động lớn; α = 0,15 khi ổn định) cùng dải chống rung 0,2 cm, và truyền bản tin JSON mỗi 5 giây "
            "qua UART1. Ở tầng cầu nối, ESP32-C3 đảm nhận vai trò IoT Gateway với bộ tách khung UART lọc nhiễu 2 chế độ, tự kết nối lại Wi-Fi vô hạn, "
            "xuất bản MQTT v3.1.1 (QoS 1) lên HiveMQ Broker kèm Heartbeat 15 giây và Last Will and Testament (LWT). Ở tầng đám mây và giao diện, dịch vụ "
            "Backend v3.0 (Gunicorn/Flask + MQTT Worker) chạy kiến trúc CSDL hai chế độ (Dual-Mode) lưu trữ bền vững trên Supabase PostgreSQL (dự phòng "
            "SQLite WAL khi chạy cục bộ), triển khai trên Render kèm UptimeRobot duy trì mỗi 5 phút, kết hợp Web Dashboard trên GitHub Pages hỗ trợ cảnh "
            "báo Hysteresis, lọc lịch sử cố định khung giờ (UTC+7) và tải báo cáo qua Blob. Kết quả đo đối soát trên 11 mốc trong dải 0–65 cm đạt sai số "
            "từ −0,4 cm đến +0,3 cm (MAE = 0,22 cm, RMSE = 0,24 cm, y = 0,9979x + 0,13 cm, R² = 0,99989), đáp ứng ngưỡng ±1,0 cm theo WMO-No. 168."
        ),
        size=13, italic=True
    )

    p_kw = doc.add_paragraph()
    p_kw.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_kw.paragraph_format.line_spacing = 1.3
    p_kw.paragraph_format.space_before = Pt(0)
    p_kw.paragraph_format.space_after = Pt(12)
    style_run(p_kw.add_run("Từ khóa: "), size=13, bold=True)
    style_run(
        p_kw.add_run(
            "IoT thủy văn, giám sát mực nước, cảm biến áp suất thủy tĩnh, STM32F103C8T6, ESP32-C3, "
            "Adaptive EMA, MQTT LWT, Supabase PostgreSQL, SQLite WAL, Render Cloud, Web Dashboard, Hysteresis."
        ),
        size=13, italic=True
    )

    # =========================================================================
    # 1. GIỚI THIỆU
    # =========================================================================
    add_h1("1. Giới thiệu")

    add_h2("1.1. Đặt vấn đề và tính cấp thiết của đề tài")
    add_body(
        "Tại Việt Nam, đặc biệt ở khu vực miền Trung, các đợt mưa lớn cực đoan, triều cường và ngập úng cục bộ xảy ra ngày càng thường xuyên. "
        "Trong công tác phòng chống thiên tai, quản lý hồ chứa thủy lợi, vận hành trạm bơm tiêu thoát nước và nuôi trồng thủy sản, việc theo dõi "
        "diễn biến mực nước theo thời gian thực đóng vai trò quan trọng để phát cảnh báo sớm và giảm thiểu thiệt hại. Tuy vậy, tại nhiều điểm đo "
        "vừa và nhỏ, việc quan trắc vẫn dựa vào thước thủy chuẩn đọc thủ công hoặc các thiết bị chuyên dụng nhập khẩu có chi phí đầu tư cao."
    )
    add_body(
        "Phương pháp đo thủ công khó duy trì liên tục vào ban đêm hay trong điều kiện mưa bão, thiếu chuỗi số liệu lịch sử có độ phân giải thời gian "
        "cao phục vụ phân tích tốc độ dâng/rút nước, và không có khả năng cảnh báo từ xa. Sự phổ biến của các vi điều khiển nhúng giá thành hợp lý "
        "(như STM32F103 và ESP32-C3) cùng hạ tầng đám mây cho phép xây dựng các trạm quan trắc mực nước IoT nhỏ gọn, dễ nhân rộng và đáp ứng yêu cầu "
        "chính xác cơ bản trong thủy văn [2]."
    )
    add_body(
        "Trong quá trình phát triển và thử nghiệm mô hình ban đầu, nhóm nhận thấy bốn bài toán kỹ thuật chính cần được giải quyết đồng bộ: "
        "(1) tín hiệu điện áp từ cảm biến áp suất thủy tĩnh ngoài thực địa chịu nhiễu ADC, gợn sóng mặt nước và có điện áp nền điểm không khoảng 0,12 V; "
        "(2) cầu nối không dây ESP32 dễ ngừng kết nối khi điểm phát Wi-Fi/Hotspot bị gián đoạn tạm thời và cần cơ chế nhận biết thiết bị mất nguồn; "
        "(3) cần máy chủ Backend độc lập lưu trữ dữ liệu vào cơ sở dữ liệu quan hệ thay vì lưu tạm trên trình duyệt, đồng thời bảo vệ các API quản trị "
        "trên môi trường công khai; (4) giao diện giám sát cần lọc được lịch sử theo ngày/giờ chuẩn múi giờ Việt Nam (UTC+7), giữ cố định khung giờ khi "
        "đối chiếu nhiều ngày và xuất được tập tin báo cáo phục vụ nghiên cứu."
    )

    add_h2("1.2. Mục tiêu và phạm vi thực hiện")
    add_body(
        "Đề tài hướng tới bốn mục tiêu kỹ thuật cụ thể xuyên suốt từ nút đo biên đến giao diện người dùng:"
    )
    add_bullet(
        "Tầng đo lường và xử lý tín hiệu biên (STM32F103C8T6)",
        "Thiết kế kết nối phần cứng tuân thủ tuyến Mass chung (Common Ground), hiệu chuẩn điểm không 0,12 V cho cảm biến áp suất thủy tĩnh (0–5 m, "
        "ngõ ra 0–3,3 V) và xây dựng chuỗi lọc số thích nghi 5 bước nhằm đạt sai số nhỏ hơn ngưỡng ±1,0 cm của WMO-No. 168 [2] trong phạm vi kiểm thử."
    )
    add_bullet(
        "Tầng IoT Gateway tự phục hồi (ESP32-C3)",
        "Xây dựng firmware ESP-IDF với bộ tách khung JSON UART lọc nhiễu 2 chế độ, cơ chế tự kết nối lại Wi-Fi vô hạn, xuất bản MQTT v3.1.1 (QoS 1) "
        "và cơ chế Heartbeat 15 giây kết hợp Last Will and Testament (LWT) [7]."
    )
    add_bullet(
        "Tầng Backend đám mây và CSDL Dual-Mode (Supabase PostgreSQL / SQLite WAL)",
        "Xây dựng dịch vụ Backend v3.0 (Python 3.11, Flask/Gunicorn, MQTT Worker) hỗ trợ tự động chuyển đổi giữa Supabase PostgreSQL (lưu trữ đám mây "
        "bền vững tách rời khỏi container ứng dụng) và SQLite WAL (khi chạy cục bộ), triển khai trên Render kết hợp UptimeRobot duy trì mỗi 5 phút; "
        "bảo vệ API quản trị bằng mã xác thực (X-Admin-Token), chống đọc tệp tùy ý, hỗ trợ Downsampling, Gap Detection và xuất báo cáo đa định dạng."
    )
    add_bullet(
        "Tầng Web Dashboard đa thiết bị",
        "Triển khai giao diện Web công khai trên GitHub Pages hỗ trợ hiển thị Live qua WebSockets Secure (WSS), cảnh báo 3 mức có trễ Hysteresis kèm "
        "chế độ Fail-Safe, lưu trạng thái qua F5, tra cứu lịch sử chuẩn UTC+7 có khóa khung giờ và tải báo cáo an toàn qua luồng Blob."
    )

    add_h2("1.3. Bố cục báo cáo và phân công nhiệm vụ")
    add_body(
        "Báo cáo gồm năm phần chính cùng danh mục tài liệu tham khảo và phụ lục mã nguồn. Phần 1 trình bày đặt vấn đề, mục tiêu và phân công nhiệm vụ. "
        "Phần 2 tổng quan các phương pháp đo mực nước, giao thức truyền thông IoT và các công trình liên quan. Phần 3 mô tả chi tiết phương pháp thiết kế "
        "phần cứng, thuật toán xử lý tín hiệu trên STM32, firmware ESP32-C3, Backend Cloud và Web Dashboard. Phần 4 trình bày kết quả kiểm chuẩn phòng "
        "thí nghiệm, thực nghiệm tại Hồ cá Khu A, kết quả kiểm thử vận hành hệ thống cùng thảo luận hạn chế và hướng mở rộng LoRaWAN. Phần 5 tóm tắt "
        "kết luận của đề tài."
    )
    add_body(
        "Bảng 1 thể hiện mẫu phân công nhiệm vụ và tỷ lệ phần trăm đóng góp của các thành viên trong nhóm thực hiện (phần thông tin thành viên được để "
        "trống để nhóm tự điền chính xác theo thực tế)."
    )

    add_academic_table(
        table_num=1,
        caption_text="Phân công nhiệm vụ của nhóm",
        headers=["Tên thành viên", "Nhiệm vụ", "Phần trăm đóng góp"],
        rows=[
            ["", "", ""],
            ["", "", ""],
            ["", "", ""],
            ["", "", ""]
        ],
        col_widths_cm=[5.2, 7.6, 3.4],
        center_cols=[2],
        font_size=12
    )

    # =========================================================================
    # 2. CÁC NGHIÊN CỨU/PHƯƠNG PHÁP LIÊN QUAN
    # =========================================================================
    add_h1("2. Các nghiên cứu/phương pháp liên quan")

    add_h2("2.1. Các phương pháp đo mực nước trong quan trắc thủy văn")
    add_body(
        "Các hệ thống quan trắc mực nước hiện nay chủ yếu sử dụng bốn nguyên lý đo phổ biến: phao cơ học, cảm biến siêu âm không tiếp xúc, radar vi "
        "sóng và cảm biến áp suất thủy tĩnh thả chìm [1], [2]. Theo hướng dẫn thực hành thủy văn WMO-No. 168 của Tổ chức Khí tượng Thế giới, yêu cầu "
        "độ chính xác phổ thông cho phép đo mực nước là ±1,0 cm (và tới ±3 mm đối với trạm ghi liên tục phục vụ xây dựng đường quan hệ lưu lượng) [2]."
    )
    add_body(
        "Cảm biến phao cơ học có cấu tạo đơn giản và giá thành thấp nhưng dễ kẹt cơ khí khi gặp rác nổi hoặc bùn cát. Cảm biến siêu âm (như HC-SR04 "
        "hoặc JSN-SR04T) được sử dụng rộng rãi trong nhiều nghiên cứu IoT do không tiếp xúc trực tiếp với dòng chảy [3], [4]; tuy nhiên, sóng siêu âm "
        "nhạy cảm với biến đổi nhiệt độ không khí (làm thay đổi vận tốc âm), gió mạnh, sương mù, mưa lớn và hiện tượng phản xạ đa đường trong kênh "
        "hẹp [4]. Cảm biến radar vi sóng (24–80 GHz) khắc phục tốt điều kiện thời tiết và cho độ chính xác cao, nhưng giá thành còn lớn đối với các hệ "
        "thống giám sát chi phí thấp."
    )
    add_body(
        "Cảm biến áp suất thủy tĩnh thả chìm đo trực tiếp áp suất do cột nước tác dụng lên màng silicon theo định luật Pascal [1]:"
    )
    add_equation("P = ρ · g · h", "1")
    add_body(
        "trong đó P là áp suất thủy tĩnh (Pa), ρ ≈ 1000 kg/m³ là khối lượng riêng nước ngọt, g ≈ 9,80665 m/s² là gia tốc trọng trường và h là chiều cao "
        "cột nước (m); quy đổi thực dụng 1 Bar ≈ 1019,72 cm H₂O. Đầu dò vỏ Inox 316L đạt chuẩn IP68 tích hợp ống thở cân bằng áp suất khí quyển dọc "
        "theo dây cáp nên không bị ảnh hưởng bởi mưa, bọt bề mặt hay vật cản trên mặt thoáng, dù cần lưu ý vệ sinh định kỳ để tránh bùn cặn bám vào "
        "lỗ màng đo. Bảng 2 tổng hợp ưu nhược điểm của bốn công nghệ cảm biến nêu trên."
    )

    add_academic_table(
        table_num=2,
        caption_text="So sánh các công nghệ cảm biến đo mực nước phổ biến [1], [2], [4]",
        headers=["Tiêu chí", "Phao cơ học", "Siêu âm (Ultrasonic)", "Radar vi sóng", "Áp suất thủy tĩnh thả chìm"],
        rows=[
            ["Nguyên lý đo", "Cơ khí / công tắc từ", "Thời gian phản xạ sóng âm", "Sóng điện từ 24–80 GHz", "Áp suất cột nước P = ρ·g·h"],
            ["Sai số tham khảo", "Thấp (±2–5 cm)", "Trung bình (±0,5–3 cm)", "Rất cao (±0,1–0,3 cm)", "Cao (±0,25–0,5% toàn thang)"],
            ["Ảnh hưởng thời tiết", "Ít ảnh hưởng", "Nhạy với nhiệt độ, mưa, gió", "Ít bị ảnh hưởng", "Không ảnh hưởng bởi mưa/sương"],
            ["Bảo trì thực địa", "Dễ kẹt do rác/bùn", "An toàn khi lũ (không tiếp xúc)", "Ít phải bảo trì", "Cần chống cặn bùn bám màng đo"],
            ["Chi phí đầu tư", "Rất thấp", "Thấp", "Cao", "Trung bình – Phù hợp IoT"]
        ],
        col_widths_cm=[3.0, 2.8, 3.4, 3.1, 3.9],
        center_cols=[],
        font_size=10.8
    )

    add_h2("2.2. Các công trình IoT giám sát mực nước liên quan")
    add_body(
        "Nhiều nhóm nghiên cứu đã công bố các hệ thống giám sát mực nước và cảnh báo lũ dựa trên vi điều khiển nhúng kết hợp mạng không dây. "
        "Subramaniam và cộng sự [5] xây dựng hệ thống Flood Observatory System (FOS) giám sát mực nước từ xa và phát cảnh báo sớm nhằm giảm chi phí "
        "đầu tư hạ tầng chống ngập. Kang và cộng sự [3] phát triển hệ thống phát hiện mực nước siêu âm tiết kiệm năng lượng (UWLD) sử dụng hai vi điều "
        "khiển kết hợp năng lượng mặt trời và cơ chế nhắm hai mục tiêu (mặt suối và mặt đường) đẩy dữ liệu lên đám mây. Panagopoulos và cộng sự [4] "
        "đánh giá thực địa cảm biến siêu âm đo mực nước tại suối đô thị, chỉ ra ảnh hưởng của điều kiện môi trường và sự cần thiết của lọc số để loại "
        "bỏ gai nhiễu. Bảng 3 đối chiếu một số đặc trưng chính giữa các hệ thống đã công bố và giải pháp đề xuất trong báo cáo này."
    )

    add_academic_table(
        table_num=3,
        caption_text="Đối chiếu một số hệ thống giám sát mực nước IoT đã công bố và giải pháp đề xuất",
        headers=["Nghiên cứu / Hệ thống", "Cảm biến sử dụng", "Vi điều khiển & Truyền thông", "Lưu trữ & Tính năng nổi bật"],
        rows=[
            ["Subramaniam và cs. [5] (2010)", "Cảm biến mực nước tại chỗ", "Hệ thống nhúng / Mạng không dây từ xa", "Cảnh báo lũ sớm theo ngưỡng cố định cho khu vực xa trung tâm."],
            ["Kang và cs. [3] (2021)", "Siêu âm nhắm 2 mục tiêu", "2 vi điều khiển + nguồn mặt trời + Cloud", "Tối ưu năng lượng, giám sát đồng thời mực suối và ngập mặt đường."],
            ["Panagopoulos và cs. [4] (2021)", "Siêu âm lắp trên kênh đô thị", "Trạm tự động + truyền dữ liệu từ xa", "Đánh giá sai số thực địa dài hạn trong dòng chảy đô thị biến động."],
            ["Hệ thống đề xuất (Đề tài này)", "Áp suất thủy tĩnh 0–5 m (0–3,3 V)", "STM32F103 + ESP32-C3 (UART, Wi-Fi, MQTT LWT)", "Lọc Adaptive EMA, Supabase PostgreSQL / SQLite WAL (Render + UptimeRobot), Hysteresis, xuất Excel/CSV/.db."]
        ],
        col_widths_cm=[3.6, 3.2, 4.1, 5.3],
        center_cols=[],
        font_size=10.8
    )

    add_h2("2.3. Giao thức truyền thông IoT và lưu trữ chuỗi thời gian")
    add_body(
        "Trong truyền thông IoT, Naik [6] đã so sánh định lượng các giao thức MQTT, CoAP, AMQP và HTTP, cho thấy MQTT v3.1.1 (chuẩn OASIS [7]) có "
        "ưu thế rõ rệt về kích thước tiêu đề nhỏ (2–4 byte cố định so với 200–800 byte của HTTP), mô hình Publish/Subscribe bất đồng bộ, hỗ trợ QoS "
        "và cơ chế Last Will and Testament (LWT). Khi kết hợp với WebSockets Secure (RFC 6455 [8]) trên cổng TLS 8884 của Broker, trình duyệt Web có "
        "thể nhận gói tin đẩy trực tiếp thay vì gửi yêu cầu thăm dò liên tục. Bảng 4 tóm tắt sự phân chia vai trò giữa MQTT v3.1.1 và HTTP REST trong "
        "kiến trúc lai của hệ thống."
    )

    add_academic_table(
        table_num=4,
        caption_text="So sánh và phân vai giữa MQTT v3.1.1 và HTTP REST trong hệ thống [6], [7]",
        headers=["Đặc tính kỹ thuật", "MQTT v3.1.1 (Tầng thiết bị & Live)", "HTTP REST (Tầng truy vấn CSDL)", "Vai trò kết hợp trong hệ thống"],
        rows=[
            ["Mô hình giao tiếp", "Publish / Subscribe qua Broker trung tâm", "Client / Server (Request / Response)", "ESP32 gửi 1 lần lên Broker; Backend và nhiều trình duyệt nhận song song."],
            ["Kích thước Header", "Nhẹ: tiêu đề cố định 2–4 byte", "Lớn: tiêu đề văn bản 200–800 byte", "Giảm băng thông và tải xử lý ở nút biên ESP32-C3."],
            ["Quản lý kết nối", "TCP hướng trạng thái, Keep-Alive + LWT", "Không trạng thái (Stateless)", "MQTT phát hiện rớt mạng tự động; REST phục vụ lọc lịch sử và tải tệp."],
            ["Cập nhật giao diện", "Đẩy chủ động qua WSS 8884 [8]", "Truy vấn theo bộ lọc ngày/giờ", "Phối hợp hiển thị Live tức thời với phân tích dữ liệu lịch sử."]
        ],
        col_widths_cm=[3.1, 4.3, 4.2, 4.6],
        center_cols=[],
        font_size=10.8
    )

    add_body(
        "Về lưu trữ dữ liệu chuỗi thời gian, việc kết hợp kiến trúc hai chế độ (Dual-Mode) giữa PostgreSQL đám mây (Supabase) khi triển khai trực tuyến "
        "và SQLite chế độ Write-Ahead Logging (WAL) [10] khi vận hành ngoại tuyến cục bộ giúp giải quyết đồng thời hai yêu cầu: dữ liệu trên Cloud không "
        "bị mất khi container ứng dụng khởi động lại hoặc redeploy, trong khi môi trường cục bộ vẫn gọn nhẹ, đọc/ghi đồng thời không khóa nghẽn và dễ "
        "dàng xuất toàn bộ dữ liệu ra một tập tin SQLite (.db) duy nhất phục vụ phân tích ngoại tuyến."
    )

    # =========================================================================
    # 3. PHƯƠNG PHÁP THỰC HIỆN
    # =========================================================================
    add_h1("3. Phương pháp thực hiện")

    add_h2("3.1. Kiến trúc phần cứng và sơ đồ đấu nối chân hệ thống")
    add_body(
        "Hệ thống tách biệt tầng đo lường biên (STM32F103C8T6) và tầng truyền thông không dây (ESP32-C3) để tránh nhiễu chuyển mạch RF ảnh hưởng trực "
        "tiếp đến quá trình lấy mẫu ADC và giúp mô-đun hóa firmware. Hình 1 mô tả sơ đồ khối phần cứng tổng thể gồm năm khối liên kết tuần tự từ trái "
        "sang phải: Khối Cấp nguồn, Khối Cảm biến thủy tĩnh, Vi điều khiển biên STM32F103C8T6 (vận hành ở xung nội HSI 8 MHz [11]), IoT Gateway "
        "ESP32-C3 (RISC-V 160 MHz [12]) và Khối Ăng-ten 2,4 GHz. Toàn bộ mạch được tham chiếu trên một thanh Mass chung (Common GND 0 V) ở đáy sơ đồ."
    )

    add_figure(
        r"D:\Embedded\esp32\docs\hardware_block_diagram.png",
        fig_num=1,
        caption_text="Sơ đồ khối phần cứng tổng thể của hệ thống giám sát mực nước IoT (STM32F103 & ESP32-C3).",
        width_cm=15.8
    )

    add_body(
        "Chức năng, linh kiện cốt lõi và thông số điện áp giao tiếp của từng khối trong Hình 1 được tổng hợp trong Bảng 5."
    )

    add_academic_table(
        table_num=5,
        caption_text="Tổng hợp chức năng và thông số 5 khối phần cứng của hệ thống",
        headers=["Khối phần cứng", "Linh kiện / Chipset cốt lõi", "Mức điện áp & Giao tiếp", "Nhiệm vụ kỹ thuật chính"],
        rows=[
            ["Khối Cấp nguồn", "Adapter 12V/2A, nguồn USB 5V, mạch LDO 3,3V", "+12V DC (cảm biến), +5V USB, +3,3V MCU, Common GND 0V", "Cấp nguồn ổn định và thiết lập mốc tham chiếu 0 V chung toàn mạch."],
            ["Khối Cảm biến", "Cảm biến áp suất thủy tĩnh Inox 316L (IP68)", "Nguồn nuôi +12V DC; ngõ ra Analog tuyến tính 0,00–3,30V", "Đo áp suất cột nước dải 0–5 m (0–0,5 Bar) theo định luật Pascal."],
            ["Vi điều khiển biên", "STM32F103C8T6 (Cortex-M3, chạy HSI 8 MHz) [11]", "PA0 (ADC1 12-bit), PA9 (USART1_TX 3,3V), PC13 (LED 5s)", "Lấy mẫu 32× mỗi 100 ms, bù 0,12 V, lọc Adaptive EMA, phát JSON 5s/gói."],
            ["IoT Gateway", "ESP32-C3 (RISC-V 32-bit @ 160 MHz) [12]", "GPIO 4 (UART1_RX 3,3V), USB Type-C (COM7), RF 2,4 GHz", "Đệm RingBuffer 2 KB, parser JSON lọc nhiễu, Wi-Fi Auto-Reconnect, đẩy MQTT."],
            ["Khối RF & Đám mây", "Ăng-ten PCB 2,4 GHz (mở rộng LoRa RFM95)", "Đường RF 50 Ω, chuẩn Wi-Fi 802.11 b/g/n (STA Mode)", "Truyền gói MQTT lên HiveMQ Broker và đồng bộ về Backend trên Render."]
        ],
        col_widths_cm=[3.0, 3.9, 4.4, 4.9],
        center_cols=[],
        font_size=10.8
    )

    add_body(
        "Sơ đồ đấu nối chân chi tiết được thể hiện tại Hình 2, tách biệt rõ đường nguồn +12 V DC (dây đỏ) cấp riêng cho cảm biến, đường tín hiệu "
        "Analog 0–3,3 V (dây vàng) nối từ chân OUT vào PA0 của STM32, bus nối tiếp UART1 chuẩn 3,3 V CMOS (PA9 → GPIO 4 và tùy chọn GPIO 5 → PA10), "
        "và tuyến Mass chung nối kín giữa bốn khối thiết bị. Bảng 6 và Bảng 7 trình bày cấu hình chân chi tiết của STM32F103C8T6 và ESP32-C3, trong "
        "khi Bảng 8 liệt kê danh sách từng cặp dây đấu nối liên mạch."
    )

    add_figure(
        r"D:\Embedded\esp32\docs\hardware_wiring_diagram.png",
        fig_num=2,
        caption_text="Sơ đồ đấu nối chân phần cứng chi tiết giữa nguồn 12V DC, cảm biến thủy tĩnh, STM32F103 và ESP32-C3.",
        width_cm=15.8
    )

    add_academic_table(
        table_num=6,
        caption_text="Cấu hình các chân ngoại vi trên vi điều khiển biên STM32F103C8T6 [11]",
        headers=["Chân", "Chế độ ngoại vi", "Thông số cấu hình", "Chức năng trong hệ thống"],
        rows=[
            ["PA0", "Analog (ADC1_IN0)", "12-bit (0–4095), không Pull-up/down, lấy mẫu 32×", "Đọc điện áp Analog 0,00–3,30 V từ cảm biến thủy tĩnh."],
            ["PA9", "AF Push-Pull (USART1_TX)", "High Speed, Baudrate 115200 bps, khung 8N1", "Truyền chuỗi JSON 5 trường sang ESP32 mỗi 5 giây."],
            ["PA10", "Input (USART1_RX)", "Input Floating / Pull-Up, Baudrate 115200 8N1", "Nhận lệnh phản hồi hoặc cấu hình từ Gateway (tùy chọn)."],
            ["PC13", "GPIO Output Push-Pull", "Active-Low, đảo trạng thái mỗi chu kỳ phát 5 s", "LED báo nhịp hoạt động khi hoàn tất gửi gói tin."],
            ["GND / 3.3V", "Nguồn & Mass tham chiếu", "Nguồn lõi 3,3 V từ LDO/ST-Link, Mass chung 0 V", "Cấp nguồn và đồng bộ mốc điện thế với ESP32 và cảm biến."]
        ],
        col_widths_cm=[2.2, 3.8, 4.9, 5.3],
        center_cols=[0],
        font_size=10.8
    )

    add_academic_table(
        table_num=7,
        caption_text="Cấu hình các chân và ngoại vi trên vi điều khiển Gateway ESP32-C3 [12]",
        headers=["Chân", "Ngoại vi ESP-IDF", "Thông số cấu hình phần mềm", "Chức năng trong hệ thống"],
        rows=[
            ["GPIO 4", "UART_NUM_1 RX", "115200 8N1, RingBuffer 2048 B, Parser 2 chế độ", "Nhận luồng byte JSON từ PA9 của STM32, lọc byte rác."],
            ["GPIO 5", "UART_NUM_1 TX", "115200 8N1, chuẩn mức logic 3,3 V CMOS", "Gửi lệnh điều khiển / ACK xuống STM32 (mở rộng)."],
            ["GND", "Power Ground", "Nối trực tiếp vào thanh Mass chung hệ thống 0 V", "Đảm bảo tham chiếu mức logic UART chính xác với STM32."],
            ["USB Type-C", "USB-CDC / 5V VDD", "Cổng COM ảo (COM7), nạp qua PlatformIO", "Cấp nguồn 5 V, nạp firmware và theo dõi log hệ thống."]
        ],
        col_widths_cm=[2.2, 3.4, 5.2, 5.4],
        center_cols=[0],
        font_size=10.8
    )

    add_academic_table(
        table_num=8,
        caption_text="Bảng đấu nối dây liên mạch toàn hệ thống",
        headers=["STT", "Thiết bị nguồn", "Chân xuất", "Thiết bị đích", "Chân nhận", "Màu dây", "Mức điện áp"],
        rows=[
            ["1", "Adapter 12V DC", "+12V (+)", "Cảm biến thủy tĩnh", "VCC", "Đỏ", "+12,0 V DC"],
            ["2", "Adapter 12V DC", "GND (−)", "Bus Mass chung", "Common GND", "Đen", "0,0 V"],
            ["3", "Cảm biến thủy tĩnh", "OUT", "STM32F103C8T6", "PA0 (ADC1_IN0)", "Vàng", "0,00–3,30 V"],
            ["4", "Cảm biến thủy tĩnh", "GND", "Bus Mass chung", "Common GND", "Đen / Nâu", "0,0 V"],
            ["5", "STM32F103C8T6", "PA9 (TX)", "ESP32-C3", "GPIO 4 (RX)", "Xanh lá", "3,3 V CMOS"],
            ["6", "STM32F103C8T6", "PA10 (RX)", "ESP32-C3", "GPIO 5 (TX)", "Xanh dương", "3,3 V CMOS"],
            ["7", "STM32F103C8T6", "GND", "ESP32-C3", "GND", "Đen", "0,0 V (Bắt buộc)"]
        ],
        col_widths_cm=[1.1, 2.9, 2.1, 2.9, 2.8, 2.0, 2.4],
        center_cols=[0, 5, 6],
        font_size=10.8
    )

    add_body(
        "Trong thiết kế thực tế theo Hình 2 và Bảng 8, việc nối chung Mass (Common Ground) giữa nguồn 12 V, cảm biến, STM32 và ESP32 là yêu cầu bắt "
        "buộc để tránh hiện tượng điện thế thả nổi gây sai lệch ADC và lỗi khung UART. Chân PA9 (STM32) và GPIO 4 (ESP32-C3) cùng sử dụng chuẩn 3,3 V "
        "CMOS nên đấu nối trực tiếp an toàn. Đối với phiên bản mạch in (PCB) triển khai lâu dài ngoài trời có dây cáp cảm biến dài đi cạnh đường nguồn "
        "12 V, nhóm khuyến nghị bổ sung một điện trở hạn dòng nối tiếp (1–4,7 kΩ) kèm diode TVS/kẹp áp 3,3 V tại ngõ vào PA0 để bảo vệ chân ADC trước "
        "xung quá áp hoặc sự cố chập dây."
    )

    add_h2("3.2. Thuật toán thu thập dữ liệu và xử lý nhiễu 5 bước trên STM32F103")
    add_body(
        "Tín hiệu tương tự tại chân PA0 chịu đồng thời nhiễu lượng tử hóa ADC 12-bit (dao động 2–4 bit LSB do dùng chung nguồn VDD 3,3 V), nhiễu gợn "
        "sóng mặt nước và sai số dịch điểm không (khi đầu dò ngoài không khí vẫn xuất điện áp tĩnh đo kiểm được là 0,12 V). Firmware STM32 chạy ở xung "
        "nội HSI 8 MHz (trích đoạn mã nguồn ở Phụ lục A và đã đồng bộ vào kho lưu trữ stm32_sensor_node/Core/Src/main.c) thực hiện chuỗi xử lý số 5 "
        "bước theo chu kỳ lấy mẫu nền 100 ms kết hợp truyền UART phi chặn mỗi 5 giây:"
    )
    add_bullet(
        "Bước 1 – Tự hiệu chuẩn phần cứng ADC",
        "Gọi HAL_ADCEx_Calibration_Start(&hadc1) ngay khi khởi động để bù sai lệch tụ lấy mẫu nội tại của bộ ADC1."
    )
    add_bullet(
        "Bước 2 – Lọc quá mẫu trung bình 32 lần (Oversampling 32×)",
        "Hàm Read_ADC_Filtered() đọc 32 mẫu ADC liên tiếp mỗi 100 ms và lấy trung bình cộng, giúp cải thiện tỷ số tín hiệu trên nhiễu thêm "
        "ΔSNR = 10·log₁₀(32) ≈ 15,05 dB (giảm biên độ nhiễu Gauss trắng đi √32 ≈ 5,66 lần)."
    )
    add_bullet(
        "Bước 3 – Khấu trừ điện áp điểm không (0,12 V) và quy đổi tuyến tính",
        "Điện áp tại PA0 tính theo V = (ADC_raw / 4095) × 3,30 V. Thuật toán trừ đi điện áp nền điểm không V₀ = 0,12 V (đã đo kiểm khi cảm biến khô "
        "ngoài không khí), khóa chặn dưới không âm và quy đổi ra mực nước thô h_raw trên dải áp hữu ích V_span = 3,30 − 0,12 = 3,18 V ứng với "
        "H_max = 500,0 cm theo công thức (2):"
    )
    add_equation("h_raw = [(V − 0,12) / (3,30 − 0,12)] · 500,0 ,   với 0 ≤ h_raw ≤ 500,0 cm", "2")
    add_bullet(
        "Bước 4 – Bộ lọc thông thấp đệ quy thích nghi (Adaptive EMA)",
        "Tính biên độ biến động s = |h_raw − h_ema[k−1]| và chuyển mạch hệ số trọng số α theo công thức (3):"
    )
    add_equation("h_ema[k] = (1 − α) · h_ema[k−1] + α · h_raw ,   α = 0,80 nếu s > 2,0 cm ; α = 0,15 nếu s ≤ 2,0 cm", "3")
    add_body(
        "Với chu kỳ cập nhật nội bộ 100 ms, khi có bước nhảy mực nước lớn (> 2,0 cm), bộ lọc bám được trên 80–90% giá trị mới chỉ trong 100–200 ms "
        "đầu tiên; khi sai lệch rút xuống dưới 2,0 cm, hệ số chuyển về α = 0,15 để làm mịn sóng nước và hội tụ 95–99% trong khoảng 1,5–2,0 giây. "
        "Kết hợp với chu kỳ phát UART 5 giây/gói, độ trễ hiển thị thực tế tới người dùng nằm trong khoảng 0–5 giây.",
        indent=False
    )
    add_bullet(
        "Bước 5 – Dải chống rung chữ số 0,2 cm và truyền JSON phi chặn 5 giây",
        "Biến hiển thị g_water_level_cm chỉ cập nhật khi |h_ema[k] − g_water_level_cm| ≥ 0,2 cm (hoặc khi giá trị đang bằng 0), giúp khóa chống rung "
        "chữ số thập phân quanh vị trí ổn định. Lưu ý rằng cơ chế Deadband 0,2 cm này chỉ giữ nguyên giá trị cũ khi biến thiên nhỏ chứ không ép cưỡng "
        "bức về 0; mốc 0,0 cm đạt được nhờ bước khấu trừ V₀ = 0,12 V và khóa cận dưới ở Bước 3. STM32 sử dụng HAL_GetTick() để phát chuỗi JSON 5 trường "
        "({\"level\", \"volt\", \"percent\", \"press\", \"raw\"}\\n) qua UART1 định kỳ 5.000 ms, giảm hơn 93% số bản tin so với tốc độ phát ~3 gói/giây "
        "của phiên bản thử nghiệm ban đầu. Bảng 9 tóm tắt so sánh giữa tín hiệu thô, EMA tĩnh và chuỗi lọc thích nghi 5 bước."
    )

    add_academic_table(
        table_num=9,
        caption_text="So sánh đặc tính tín hiệu giữa tín hiệu thô, EMA tĩnh và chuỗi lọc thích nghi 5 bước",
        headers=["Tiêu chí", "Tín hiệu thô", "EMA tĩnh (v1, α = 0,15)", "Chuỗi lọc thích nghi 5 bước (v3)"],
        rows=[
            ["Điểm 0 ngoài không khí", "Báo lệch ~18 cm do áp tĩnh 0,12 V.", "Ổn định 0,0 cm nhờ bù 0,12 V.", "Ổn định 0,0 cm nhờ bù 0,12 V và khóa cận dưới."],
            ["Đáp ứng khi đổi nhanh", "Nhảy tức thời nhưng nhiễu ±1,5 cm.", "Chậm bám khi mực nước đổi đột ngột.", "Đạt >80–90% bước nhảy trong 100–200 ms; hội tụ mịn ~1,5–2,0 s."],
            ["Độ ổn định chữ số", "Nhảy liên tục từng chu kỳ đọc.", "Còn dao động nhẹ ±0,1 cm.", "Deadband 0,2 cm giữ chữ số thập phân ổn định."],
            ["Tần suất truyền tin", "Không kiểm soát.", "~3 gói/s (~260.000 mẫu/ngày).", "1 gói/5 giây (17.280 mẫu/ngày); độ trễ hiển thị Web 0–5 s."]
        ],
        col_widths_cm=[3.2, 3.6, 4.1, 5.3],
        center_cols=[],
        font_size=10.8
    )

    add_h2("3.3. Thiết kế Firmware IoT Gateway tự phục hồi trên ESP32-C3")
    add_body(
        "Luồng dữ liệu xuyên suốt từ nút đo biên đến trình duyệt Web được tổ chức theo kiến trúc phân tầng như minh họa trong Hình 3, gồm bốn tầng: "
        "Tầng Biên & Gateway (STM32F103 + ESP32-C3), Tầng Định tuyến Broker (HiveMQ), Tầng Xử lý & Lưu trữ Cloud (Render + Gunicorn + SQLite WAL, "
        "được duy trì kết nối bởi UptimeRobot mỗi 5 phút) và Tầng Ứng dụng (GitHub Pages Web Dashboard). Từ HiveMQ Broker, gói tin cảm biến được phân "
        "nhánh đồng thời sang Render Backend (TCP 1883) để lưu trữ và sang Web Dashboard (WSS 8884) để hiển thị thời gian thực."
    )

    add_figure(
        r"D:\Embedded\esp32\docs\cloud_architecture_v3.png",
        fig_num=3,
        caption_text="Kiến trúc phân tầng hệ thống IoT giám sát mực nước Cloud và luồng dữ liệu thủy văn (phiên bản V3.0).",
        width_cm=15.8
    )

    add_body(
        "Firmware ESP32-C3 (ESP-IDF/FreeRTOS, trích đoạn tại Phụ lục B) được hoàn thiện với bốn cơ chế kỹ thuật chính:"
    )
    add_bullet(
        "Bộ tách khung UART lọc nhiễu 2 chế độ (uart_app.c)",
        "Tác vụ uart_rx_task (stack 4096 byte, ưu tiên 10) đọc byte từ RingBuffer 2048 byte và chốt gói JSON khi gặp ký tự xuống dòng ('\\n'/'\\r') "
        "hoặc dấu '}' kết thúc đối tượng JSON hợp lệ (line_idx > 10 && line_buf[0] == '{'). Mọi byte rác đứng trước '{' bị bỏ qua để tránh ghép chuỗi "
        "lỗi; hai bộ đếm UART_RX và MQTT_PUB theo dõi số gói nhận và xuất bản."
    )
    add_bullet(
        "Tự động kết nối lại Wi-Fi vô hạn (wifi_app.c)",
        "Loại bỏ giới hạn số lần thử lại tại sự kiện WIFI_EVENT_STA_DISCONNECTED: mỗi khi mất kết nối Wi-Fi/Hotspot, ESP32 tự xóa cờ trạng thái và gọi "
        "lại esp_wifi_connect() liên tục cho đến khi nhận lại địa chỉ IP. Trong app_main(), MQTT Client chỉ được khởi tạo sau khi đã có IP hợp lệ."
    )
    add_bullet(
        "Giám sát trạng thái Gateway qua Heartbeat 15 giây & MQTT LWT (mqtt_app.c)",
        "Mỗi 15 giây, ESP32 xuất bản gói Heartbeat JSON lên kênh my_iot_project/stm32_sensor_data/status (QoS 1, retain = 0 để không lưu tin online cũ "
        "khi rút nguồn). Đồng thời phiên MQTT đăng ký LWT offline với keepalive = 15 s. Theo đặc tả OASIS MQTT v3.1.1 [7], Broker sẽ phát bản tin LWT "
        "khi quá 1,5 × keepalive không nhận tín hiệu (tương đương tối đa ~22,5 giây); phía Web Dashboard bổ sung Watchdog 40 giây làm lớp dự phòng."
    )
    add_bullet(
        "Tách biệt cấu hình bí mật khỏi kho mã nguồn công khai",
        "Tệp chứa thông tin đăng nhập Wi-Fi (wifiesp32/main/app_config.h) được loại khỏi git tracking và đưa vào .gitignore, thay bằng tệp mẫu "
        "app_config.example.h để tránh lộ mật khẩu mạng trên kho lưu trữ GitHub công khai."
    )

    add_h2("3.4. Thiết kế Backend Service v3.0, CSDL Dual-Mode (Supabase PostgreSQL / SQLite WAL) và triển khai Cloud")
    add_body(
        "Dịch vụ Backend v3.0 (wifiesp32/data_logger/service.py) tích hợp ba thành phần trong cùng tiến trình: MQTT Background Worker lắng nghe "
        "broker.hivemq.com:1883, lớp quản lý cơ sở dữ liệu hai chế độ (DualDBConnection) và máy chủ REST API viết bằng Flask chạy dưới WSGI server "
        "Gunicorn trên nền Python 3.11.11 (cấu hình gunicorn --workers 1 --threads 4 để đảm bảo chỉ có đúng một MQTT Worker ghi dữ liệu, kèm ép nạp "
        "sẵn bảng mã encodings.idna trên luồng chính để tránh xung đột đa luồng trong gthread)."
    )
    add_body(
        "Khi biến môi trường DATABASE_URL được cấu hình trên Render, lớp DualDBConnection tự động kết nối tới cơ sở dữ liệu đám mây Supabase PostgreSQL "
        "thông qua Shared/Session Pooler (cổng 5432, tương thích IPv4 với Render, bắt buộc mã hóa SSL sslmode=require) bằng thư viện psycopg2-binary, "
        "tự động ánh xạ tham số truy vấn '?' sang '%s', sử dụng kiểu BIGINT cho mốc thời gian Unix epoch mili-giây (received_at) và khởi tạo sẵn bảng "
        "measurements cùng hai chỉ mục idx_received_at và idx_simulated. Nhờ tách hoàn toàn dữ liệu sang Supabase, hệ thống khắc phục dứt điểm hạn chế "
        "ổ đĩa tạm thời (ephemeral disk) của gói Render Free: dữ liệu không bao giờ bị mất khi cập nhật mã nguồn hay khởi động lại container. Ngược lại, "
        "khi chạy cục bộ không có DATABASE_URL, dịch vụ tự động chuyển sang SQLite WAL (rainfall_data.db) [10]. Ngoài ra, tiện ích migrate_to_supabase.py "
        "được cung cấp sẵn để di trú hàng loạt dữ liệu thật từ SQLite lên Supabase theo từng lô 1.000 bản ghi có lọc trùng."
    )
    add_body(
        "Tại luồng MQTT nền, mỗi gói tin được lọc trùng trong < 1,0 giây (Deduplication), kiểm duyệt đủ 5 trường JSON không chứa NaN/Inf và raw ADC "
        "thuộc [0, 4095], kết hợp tự kết nối lại theo Exponential Backoff (1 s → 60 s). Về bảo mật API trên môi trường công khai, các endpoint ghi/xóa "
        "(/api/database/clear, /api/simulate, /api/import/indexeddb) yêu cầu xác thực mã quản trị qua header X-Admin-Token (đối chiếu hằng thời gian "
        "bằng hmac.compare_digest với ADMIN_API_KEY, tự khóa fail-closed trên Render nếu chưa đặt khóa). Endpoint /api/backup/download/<filename> kiểm "
        "tra os.path.basename kết hợp regex ^rainfall_data_backup_\\d{8}_\\d{6}\\.db$ chống Path Traversal. Khi chạy trên Supabase, nút tải tệp CSDL "
        "(/api/database/download) và cơ chế tự sao lưu trước khi xóa sẽ tự động xuất nhanh một bản chụp SQLite (.db) từ PostgreSQL trả về cho người dùng. "
        "Bảng 10 tổng hợp hệ thống 11 REST API của Backend v3.0."
    )

    add_academic_table(
        table_num=10,
        caption_text="Danh sách các REST API và cơ chế xử lý dữ liệu của Backend Service v3.0",
        headers=["Endpoint REST API", "Phương thức", "Chức năng & Cơ chế bảo mật / xử lý"],
        rows=[
            ["/api/status", "GET / HEAD", "Trả trạng thái Online / Mất dữ liệu (timeout 2 phút), loại CSDL (db_engine: PostgreSQL Supabase hoặc SQLite WAL), tổng mẫu; đồng thời là endpoint cho UptimeRobot ping mỗi 5 phút."],
            ["/api/measurements", "GET", "Truy vấn phân trang (limit/offset), sắp xếp tăng/giảm, lọc thời gian & nguồn dữ liệu, tự tính tốc độ thay đổi mực nước (cm/h)."],
            ["/api/stats", "GET", "Thống kê tổng mẫu, trung bình, Max và Min kèm mốc giờ UTC+7; tự động loại trừ mẫu lỗi cảm biến ngoài dải [0,08 V; 3,35 V]."],
            ["/api/series", "GET", "Cung cấp chuỗi vẽ biểu đồ lịch sử: tự động Downsampling (~800 điểm khi > 1.500 mẫu) và Gap Detection chèn null khi đứt quãng > max(10 s, 2·T_avg)."],
            ["/api/export.xlsx", "GET", "Xuất báo cáo Excel 3 Sheet: Du_Lieu_Chi_Tiet, Tong_Hop_Theo_Gio (kèm tốc độ dâng/rút Max) và Tong_Hop_Theo_Ngay."],
            ["/api/export.csv", "GET", "Xuất tệp CSV gắn UTF-8 BOM (utf-8-sig) hiển thị đúng tiếng Việt trên Microsoft Excel."],
            ["/api/database/download", "GET", "Tải tệp CSDL SQLite (rainfall_data.db); tự động xuất bản chụp SQLite snapshot từ Supabase khi đang chạy PostgreSQL."],
            ["/api/simulate\n/api/import/indexeddb", "POST\n(Admin)", "Yêu cầu X-Admin-Token: sinh 50 mẫu thử nghiệm (is_simulated = 1) hoặc nhập dữ liệu cũ từ IndexedDB."],
            ["/api/database/clear\n/api/backup/download/<f>", "POST / GET\n(Admin)", "Yêu cầu X-Admin-Token và mã xác nhận 'XOA'; tự xuất bản sao lưu .db trước khi xóa; endpoint tải backup lọc regex chống Path Traversal."]
        ],
        col_widths_cm=[4.2, 2.0, 10.0],
        center_cols=[1],
        font_size=10.6
    )

    add_body(
        "Dịch vụ Backend được triển khai trên Render (render.yaml tại Phụ lục C) tại địa chỉ https://esp32-iot-gateway.onrender.com, kết nối trực tiếp "
        "tới Supabase PostgreSQL và được UptimeRobot gửi yêu cầu HTTP HEAD/GET định kỳ mỗi 5 phút tới /api/status để duy trì tiến trình luôn hoạt động. "
        "Web Dashboard được phát hành công khai trên GitHub Pages tại https://v2tacodin.github.io/ESP32-IoT-Gateway/, tự động kết nối máy chủ Render "
        "Cloud cho mọi thiết bị từ xa hoặc tự chuyển sang địa chỉ nội bộ khi chạy cục bộ trên cổng 5000."
    )

    add_h2("3.5. Thiết kế Web Dashboard và thuật toán cảnh báo Hysteresis")
    add_body(
        "Web Dashboard gồm hai khu vực: Giám sát thời gian thực (Live) và Trung tâm Cơ sở dữ liệu Thủy văn. Khu vực Live kết nối trực tiếp HiveMQ "
        "WSS 8884 [8] để cập nhật 3 thẻ thông số (Mực nước cm/m, Áp suất thủy tĩnh Bar/% cột nước, Điện áp & Sức khỏe ADC), 4 huy hiệu trạng thái "
        "trên Header (Cảnh báo mực nước, ESP32 Gateway kèm Watchdog 40 s, Backend API, Tổng gói tin) và biểu đồ 30 điểm gần nhất (đã tắt animation "
        "để giảm tải trình duyệt). Khi tải lại trang (F5) hoặc chuyển thẻ (visibilitychange), giao diện khôi phục nhanh trạng thái từ localStorage "
        "và đồng bộ lại đúng 30 bản ghi mới nhất từ SQLite (/api/measurements)."
    )
    add_body(
        "Để chống nhấp nháy cảnh báo khi mực nước dao động quanh ngưỡng, giao diện cài đặt thuật toán cảnh báo 3 mức có khoảng trễ Hysteresis mặc định "
        "Δ = 5,0 cm (có thể tùy chỉnh trong Cài Đặt) cùng chế độ an toàn sự cố Fail-Safe như trình bày ở Bảng 11. Ngưỡng báo 'Mất dữ liệu' được đặt "
        "mặc định là 2 phút (tương đương 24 chu kỳ truyền 5 giây liên tiếp không có gói mới), cân bằng giữa tốc độ phát hiện sự cố và khả năng dung "
        "thứ các dao động mạng ngắn."
    )

    add_academic_table(
        table_num=11,
        caption_text="Quy tắc cảnh báo ngập lụt 3 mức có trễ Hysteresis (Δ = 5,0 cm) và chế độ Fail-Safe",
        headers=["Trạng thái", "Điều kiện kích hoạt (Mặc định)", "Điều kiện hạ mức (Hysteresis)", "Ý nghĩa vận hành"],
        rows=[
            ["AN TOÀN", "h < 80,0 cm (cảm biến khỏe, online)", "Trở về An toàn khi h rút xuống < 75,0 cm.", "Hoạt động bình thường, chống nhấp nháy quanh 80 cm."],
            ["CẢNH BÁO", "80,0 cm ≤ h < 200,0 cm", "Hạ từ Nguy hiểm về Cảnh báo khi h < 195,0 cm.", "Mực nước dâng cao, cần theo dõi sát diễn biến."],
            ["NGUY HIỂM", "h ≥ 200,0 cm", "Thoát báo động đỏ khi h rút xuống < 195,0 cm.", "Nguy cơ ngập lụt nghiêm trọng."],
            ["LỖI CẢM BIẾN", "V < 0,08 V (đứt dây) hoặc V > 3,35 V (chập)", "Tự khôi phục khi V trở về [0,08 V; 3,35 V].", "Cảnh báo hỏng phần cứng; loại mẫu khỏi thống kê."],
            ["MẤT DỮ LIỆU", "Quá 2 phút không nhận gói tin mới", "Tự khôi phục khi nhận được mẫu mới.", "Fail-Safe: không báo 'An toàn' khi mất tín hiệu."]
        ],
        col_widths_cm=[2.8, 4.3, 4.4, 4.7],
        center_cols=[0],
        font_size=10.8
    )

    add_body(
        "Tại khu vực Trung tâm Cơ sở dữ liệu, người dùng lọc theo nguồn dữ liệu (Dữ liệu thật / Giả lập / Tất cả), chọn ngày hoặc khoảng ngày qua "
        "Flatpickr (DD/MM/YYYY) với các nút chọn nhanh (Hôm nay, Hôm qua, Tháng này, Tất cả). Mọi mốc lọc ngày/giờ được quy đổi tường minh theo múi "
        "giờ Việt Nam UTC+7 (sử dụng Date.UTC với độ lệch −7 giờ) để đảm bảo kết quả truy vấn chính xác ngay cả khi thiết bị của người xem đặt múi giờ "
        "khác. Khung giờ chọn (Từ Giờ – Đến Giờ) được giữ cố định khi chuyển đổi giữa các ngày và tự động ràng buộc Từ Giờ ≤ Đến Giờ. Các nút xuất "
        "Excel (.xlsx), CSV (UTF-8 BOM) và tải SQLite (.db) đều dùng luồng bất đồng bộ Fetch + Blob để không bị trình duyệt chặn tải tệp chéo tên miền."
    )

    # =========================================================================
    # 4. THỰC NGHIỆM VÀ KẾT QUẢ
    # =========================================================================
    add_h1("4. Thực nghiệm và kết quả")

    add_h2("4.1. Kiểm chuẩn đo lường trong phòng thí nghiệm")
    add_body(
        "Trước khi thử nghiệm ngoài trời, cụm đo lường (cảm biến áp suất thủy tĩnh + STM32F103C8T6 cấu hình bù điểm không V₀ = 0,12 V) được kiểm chuẩn "
        "trong phòng thí nghiệm bằng xô nước có vạch chia milimet tại 5 mốc độ sâu từ 0,0 cm đến 35,0 cm (đo 1 lần tại mỗi mốc sau khi tín hiệu ổn "
        "định). Kết quả đối soát được ghi nhận trong Bảng 12."
    )

    add_academic_table(
        table_num=12,
        caption_text="Kết quả kiểm chuẩn độ sâu mực nước trong phòng thí nghiệm (Đo trong xô chia vạch)",
        headers=["Mốc kiểm chuẩn", "Độ sâu thực (cm)", "Độ sâu đo (cm)", "Điện áp (V)", "Sai số (cm)", "Ghi chú trạng thái"],
        rows=[
            ["Mốc 0 (Ngoài không khí)", "0,0", "0,0", "0,12", "0,0", "Khớp điện áp nền điểm 0 (V₀ = 0,12 V)."],
            ["Mốc 1 (Nước chạm màng)", "2,0", "2,1", "0,13", "+0,1", "Nhận diện tốt ở mực nước nông."],
            ["Mốc 2 (Nước thấp)", "10,0", "10,2", "0,18", "+0,2", "Số đo ổn định, không rung chữ số thập phân."],
            ["Mốc 3 (Nước trung bình)", "20,0", "19,8", "0,25", "−0,2", "Sai số nhỏ, tín hiệu mượt."],
            ["Mốc 4 (Nước đầy xô)", "35,0", "35,3", "0,34", "+0,3", "Đáp ứng tuyến tính theo chiều sâu."]
        ],
        col_widths_cm=[3.7, 2.1, 2.1, 1.9, 1.9, 4.5],
        center_cols=[1, 2, 3, 4],
        font_size=10.8
    )

    add_h2("4.2. Thực nghiệm thực địa tại Hồ cá Khu A và phân tích sai số")
    add_body(
        "Cụm đo lường tiếp tục được đưa ra kiểm chứng thực địa tại Hồ cá Khu A ở 6 mốc độ sâu từ 5,0 cm đến 65,0 cm trong điều kiện mặt hồ có gợn "
        "sóng nhẹ, đối chiếu trực tiếp với thước cơ khí chuẩn đặt cùng vị trí đầu dò. Số liệu thực đo được tổng hợp trong Bảng 13."
    )

    add_academic_table(
        table_num=13,
        caption_text="Kết quả đo đối soát thực địa tại Hồ cá Khu A",
        headers=["Mốc đo", "Mực nước thực (cm)", "Mực nước đo (cm)", "Điện áp (V)", "Áp suất (Bar)", "Sai số tuyệt đối (cm)", "Sai số tương đối (%)"],
        rows=[
            ["1", "5,0", "5,2", "0,15", "0,005", "+0,2", "4,0 %"],
            ["2", "19,5", "19,8", "0,25", "0,019", "+0,3", "1,5 %"],
            ["3", "47,0", "46,8", "0,42", "0,046", "−0,2", "0,4 %"],
            ["4", "52,0", "52,3", "0,45", "0,051", "+0,3", "0,6 %"],
            ["5", "60,0", "59,6", "0,50", "0,058", "−0,4", "0,7 %"],
            ["6", "65,0", "65,2", "0,53", "0,064", "+0,2", "0,3 %"]
        ],
        col_widths_cm=[1.5, 2.5, 2.5, 2.1, 2.3, 2.7, 2.6],
        center_cols=[0, 1, 2, 3, 4, 5, 6],
        font_size=10.8
    )

    add_body(
        "Hình 4 minh họa đường hồi quy tuyến tính đối soát giữa mực nước đo và mực nước thực tế trên toàn bộ 11 mốc đo (Hình 4a) cùng phân bố sai số "
        "tuyệt đối đặt trong ngưỡng ±1,0 cm theo khuyến nghị của WMO-No. 168 [2] (Hình 4b)."
    )

    add_figure(
        r"D:\Embedded\esp32\docs\experiment_accuracy_chart.png",
        fig_num=4,
        caption_text="Đường hồi quy đối soát mực nước (a) và phân bố sai số tuyệt đối trên 11 mốc đo trong dải 0–65 cm so với ngưỡng WMO-No. 168 [2] (b).",
        width_cm=15.8
    )

    add_body(
        "Phân tích định lượng từ Bảng 12, Bảng 13 và Hình 4 cho thấy đường hồi quy tuyến tính đạt phương trình y = 0,9979x + 0,13 cm (hệ số góc sát "
        "1,0 và độ lệch chặn nhỏ +0,13 cm), với R² = 0,99989, sai số tuyệt đối trung bình MAE = 0,22 cm và sai số toàn phương trung bình RMSE = 0,24 cm. "
        "Sai số cực đại ghi nhận là −0,4 cm tại mốc 60,0 cm, nằm trong giới hạn ±1,0 cm của WMO-No. 168 [2]. Tuy nhiên, cần nhấn mạnh phạm vi thực nghiệm "
        "hiện tại mới bao phủ 0–65 cm (khoảng 13% toàn thang đo 0–500 cm) và mỗi mốc mới đo đơn lẻ một lần; ở các mực nước sâu hơn (1–5 m), sai số "
        "thực tế vẫn bị chi phối bởi sai số độ tuyến tính của bản thân cảm biến thương mại (thường từ 0,25–0,5% toàn thang, tương đương 1,25–2,5 cm)."
    )

    add_h2("4.3. Kết quả kiểm thử vận hành toàn hệ thống trên nền tảng đám mây")
    add_body(
        "Toàn bộ chuỗi truyền tin từ ESP32-C3, HiveMQ Broker, Render Cloud Backend (Gunicorn + Supabase PostgreSQL + UptimeRobot ping mỗi 5 phút) "
        "đến Web Dashboard GitHub Pages đã được kiểm thử thực tế trên môi trường sản xuất. Đối với kho dữ liệu kiểm thử cục bộ (rainfall_data.db), "
        "nhóm tách biệt minh bạch giữa 16.220 mẫu thu thập thật từ cảm biến ngày 23/11/2026 (is_simulated = 0) và 864 mẫu giả lập bổ sung cho 3 ngày "
        "20–22/11/2026 (288 mẫu/ngày, is_simulated = 1) dùng riêng để kiểm thử giao diện lọc đa ngày. Bảng 14 tổng hợp kết quả kiểm thử toàn hệ thống."
    )

    add_academic_table(
        table_num=14,
        caption_text="Tổng hợp kết quả kiểm thử các kịch bản vận hành của hệ thống",
        headers=["Kịch bản kiểm thử", "Điều kiện thử nghiệm", "Kết quả quan sát thực tế", "Đánh giá"],
        rows=[
            ["Tự phục hồi Wi-Fi", "Tắt Hotspot / mang điện thoại ra ngoài vùng phủ sóng rồi quay lại.", "ESP32-C3 tự thử kết nối lại liên tục, tự khôi phục Wi-Fi và MQTT ngay khi có sóng mà không cần reset.", "Đạt"],
            ["Phát hiện mất nguồn (LWT & Watchdog)", "Rút nguồn ESP32-C3 đột ngột khi Dashboard đang mở.", "Broker phát LWT offline sau ~22,5 s (1,5×keepalive = 15 s [7]); Watchdog 40 s của Dashboard dự phòng khi rớt tin.", "Đạt"],
            ["Backend Render + Supabase PostgreSQL", "Kiểm thử GET/HEAD /api/status và redeploy Render khi gắn DATABASE_URL (Session Pooler) + UptimeRobot 5p.", "HTTP 200 OK; db_engine = 'PostgreSQL (Supabase)'; HEAD /api/status = 200 OK; dữ liệu không bị xóa khi Render redeploy.", "Đạt"],
            ["Truy cập đa thiết bị", "Mở link GitHub Pages trên máy tính khác và điện thoại.", "Tự động kết nối API Render, hiển thị Live WSS và lịch sử CSDL không cần cấu hình IP cục bộ.", "Đạt"],
            ["Bền vững F5 & Đồng bộ 30 điểm", "Tải lại trang (F5) hoặc chuyển sang thẻ trình duyệt khác rồi quay lại.", "Khôi phục thẻ Live từ localStorage và đồng bộ lại đúng 30 bản ghi mới nhất từ /api/measurements.", "Đạt"],
            ["Lọc lịch sử UTC+7 & Khóa khung giờ", "Chọn nguồn Giả lập/Tất cả, chọn khung giờ 08:00–11:59 và chuyển các ngày 20–23/11.", "Hiển thị chính xác 288 mẫu/ngày (is_simulated = 1) và 16.220 mẫu thật ngày 23/11; khung giờ được giữ cố định.", "Đạt"],
            ["Bảo mật API & Xuất Snapshot/Báo cáo", "Kiểm thử Path Traversal, gọi /api/database/clear không có Token, và tải Excel/CSV/Snapshot .db từ Supabase.", "Chặn Path Traversal (HTTP 400) và Clear DB không Token (HTTP 403); tải thành công .xlsx, .csv và bản chụp SQLite hợp lệ.", "Đạt"]
        ],
        col_widths_cm=[3.3, 4.4, 6.8, 1.7],
        center_cols=[3],
        font_size=10.5
    )

    add_h2("4.4. Thảo luận, hạn chế hiện tại và hướng mở rộng mạng diện rộng LoRaWAN")
    add_body(
        "Nhờ kết hợp Render Cloud (kèm UptimeRobot ping mỗi 5 phút) với cơ sở dữ liệu tách rời Supabase PostgreSQL (500 MB miễn phí), hai giới hạn lớn "
        "nhất của gói triển khai miễn phí là trạng thái tự ngủ sau 15 phút và ổ đĩa tạm thời (ephemeral disk) đã được khắc phục. Tuy nhiên, hệ thống "
        "vẫn còn bốn hạn chế kỹ thuật cần tiếp tục cải tiến khi đưa vào vận hành thực tế quy mô lớn:"
    )
    add_bullet(
        "Xác thực tầng MQTT Broker",
        "Hiện hệ thống sử dụng HiveMQ Public Broker không có mật khẩu nhằm thuận tiện cho kiểm thử, do đó người ngoài biết tên topic có thể gửi gói "
        "tin giả. Khi vận hành thực tế cần chuyển sang HiveMQ Cloud Serverless (có TLS 8883/8884 và tài khoản xác thực — các biến cấu hình đã được "
        "chuẩn bị sẵn trong service.py)."
    )
    add_bullet(
        "Chưa có bộ đệm lưu tạm (Store-and-Forward) trên ESP32-C3",
        "Khi Wi-Fi bị mất sóng, ESP32 tự kết nối lại được nhưng các gói tin đo trong khoảng thời gian đứt mạng hiện bị bỏ qua thay vì lưu đệm vào "
        "RAM/Flash để gửi bù, và mốc thời gian bản ghi hiện lấy theo đồng hồ server lúc nhận (received_at)."
    )
    add_bullet(
        "Phạm vi kiểm chuẩn cảm biến",
        "Thực nghiệm mới thực hiện trên dải 0–65 cm (13% dải đo) và đo 1 lần/mốc; cần bổ sung phép đo lặp nhiều lần (tính độ lệch chuẩn) và kiểm thử "
        "ở độ sâu lớn hơn (1–5 m) cũng như đánh giá độ trôi dài hạn khi bùn cặn bám vào màng đo."
    )
    add_bullet(
        "Mở rộng vùng phủ sóng bằng mạng diện rộng LoRaWAN",
        "Kết nối Wi-Fi 2,4 GHz chỉ phù hợp khu vực có sẵn hạ tầng mạng hoặc sóng 4G/Hotspot. Với các trạm đo ngoài đê điều và hồ chứa xa khu dân cư, "
        "STM32 có thể tích hợp thêm module LoRa RFM95 (SPI) chạy ngăn xếp LoRaMac-node theo đặc tả LoRaWAN 1.0.4 [9] (mã hóa AES-128, kích hoạt OTAA), "
        "tận dụng các Outdoor LoRaWAN Gateway công cộng tại Đà Nẵng (như trạm tại Công viên Phần mềm số 02 Quang Trung và trạm RAK7249 tại Khu S – "
        "Trường Đại học Bách Khoa, Đại học Đà Nẵng) kết hợp chế độ ngủ sâu và nguồn pin mặt trời 5 W."
    )

    # =========================================================================
    # 5. KẾT LUẬN
    # =========================================================================
    add_h1("5. Kết luận")
    add_body(
        "Đồ án đã hoàn thành việc thiết kế, lắp ráp phần cứng, lập trình firmware, xây dựng dịch vụ Backend đám mây và giao diện Web Dashboard cho hệ "
        "thống IoT giám sát mực nước và cảnh báo ngập lụt đa tầng. Các kết quả chính đạt được gồm:"
    )
    add_bullet(
        "Về đo lường và xử lý tín hiệu biên (STM32F103C8T6)",
        "Xây dựng mạch giao tiếp cảm biến áp suất thủy tĩnh 0–5 m theo nguyên tắc Common Ground và chuỗi lọc thích nghi 5 bước (Auto-Calib, quá mẫu "
        "32× mỗi 100 ms, bù điểm không 0,12 V, Adaptive EMA α = 0,80/0,15, Deadband 0,2 cm, truyền JSON 5 giây/gói). Kết quả kiểm chuẩn trên 11 mốc "
        "trong dải 0–65 cm đạt MAE = 0,22 cm, RMSE = 0,24 cm, sai số cực đại −0,4 cm, đáp ứng ngưỡng ±1,0 cm của WMO-No. 168 [2]."
    )
    add_bullet(
        "Về truyền thông IoT Gateway (ESP32-C3)",
        "Hoàn thiện bộ tách khung UART lọc nhiễu 2 chế độ, cơ chế tự kết nối lại Wi-Fi vô hạn, giám sát trạng thái thiết bị qua Heartbeat 15 giây, "
        "MQTT LWT (~22,5 giây) kết hợp Watchdog 40 giây, và tách thông tin Wi-Fi khỏi kho mã nguồn công khai."
    )
    add_bullet(
        "Về hạ tầng Backend Cloud, Supabase PostgreSQL và Web Dashboard",
        "Triển khai thành công Backend v3.0 (Gunicorn + Flask + MQTT Worker) với kiến trúc CSDL hai chế độ Supabase PostgreSQL (đám mây bền vững qua "
        "Session Pooler SSL) và SQLite WAL (cục bộ), chạy trên Render kết hợp UptimeRobot duy trì mỗi 5 phút, bảo vệ API quản trị bằng X-Admin-Token "
        "và lọc Path Traversal; đồng thời phát hành Web Dashboard trên GitHub Pages hỗ trợ cảnh báo Hysteresis, Fail-Safe (2 phút), đồng bộ F5, lọc "
        "lịch sử chuẩn UTC+7 có khóa khung giờ và tải báo cáo đa định dạng (Excel 3 sheet, CSV BOM, snapshot SQLite)."
    )
    add_body(
        "Hệ thống có cấu trúc mô-đun rõ ràng, chi phí hợp lý và lưu trữ bền vững trên nền tảng đám mây, tạo nền tảng thuận lợi để nâng cấp thêm xác "
        "thực TLS cho MQTT Broker, bộ đệm store-and-forward trên nút biên và mạng diện rộng LoRaWAN trong các giai đoạn phát triển tiếp theo."
    )

    # =========================================================================
    # TÀI LIỆU THAM KHẢO (100% NGUỒN THẬT ĐÃ KIỂM CHỨNG, CHUẨN IEEE)
    # =========================================================================
    add_h1("Tài liệu tham khảo")
    references = [
        "[1] J. Fraden, Handbook of Modern Sensors: Physics, Designs, and Applications, 5th ed. Cham, Switzerland: Springer, 2016.",
        "[2] World Meteorological Organization (WMO), Guide to Hydrological Practices, Volume I: Hydrology – From Measurement to Hydrological Information, 6th ed., WMO-No. 168. Geneva, Switzerland: WMO, 2008.",
        "[3] S. Kang, D. S. K. David, M. Yang, Y. C. Yu, and S. Ham, \"Energy-efficient ultrasonic water level detection system with dual-target monitoring,\" Sensors, vol. 21, no. 7, art. no. 2241, Mar. 2021.",
        "[4] Y. Panagopoulos, A. Papadopoulos, G. Poulis, E. Nikiforakis, and E. Dimitriou, \"Assessment of an ultrasonic water stage monitoring sensor operating in an urban stream,\" Sensors, vol. 21, no. 14, art. no. 4689, Jul. 2021.",
        "[5] S. K. Subramaniam, V. R. Gannapathy, S. Subramonian, and A. H. Hamidon, \"Flood level indicator and risk warning system for remote location monitoring using flood observatory system,\" WSEAS Trans. Syst. Control, vol. 5, no. 3, pp. 153–163, Mar. 2010.",
        "[6] N. Naik, \"Choice of effective messaging protocols for IoT systems: MQTT, CoAP, AMQP and HTTP,\" in Proc. IEEE Int. Systems Engineering Symposium (ISSE), Vienna, Austria, pp. 1–7, Oct. 2017.",
        "[7] OASIS Standard, \"MQTT Version 3.1.1,\" Organization for the Advancement of Structured Information Standards (OASIS), Oct. 2014. [Online]. Available: http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html",
        "[8] I. Fette and A. Melnikov, \"The WebSocket Protocol,\" Internet Engineering Task Force (IETF), RFC 6455, Dec. 2011.",
        "[9] LoRa Alliance, \"LoRaWAN Link Layer Specification,\" Technical Specification TS001-1.0.4, Oct. 2020.",
        "[10] SQLite Consortium, \"Write-Ahead Logging (WAL) in SQLite,\" SQLite Technical Documentation. [Online]. Available: https://www.sqlite.org/wal.html",
        "[11] STMicroelectronics, \"STM32F103x8, STM32F103xB Medium-density performance line ARM-based 32-bit MCU Datasheet,\" DocID13587 Rev. 17, Aug. 2015.",
        "[12] Espressif Systems, \"ESP32-C3 Technical Reference Manual,\" Version 1.0, Shanghai, China, 2023. [Online]. Available: https://www.espressif.com/en/support/documents/technical-documents"
    ]
    for ref in references:
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_ref.paragraph_format.line_spacing = 1.25
        p_ref.paragraph_format.left_indent = Cm(0.95)
        p_ref.paragraph_format.first_line_indent = Cm(-0.95)
        p_ref.paragraph_format.space_before = Pt(0)
        p_ref.paragraph_format.space_after = Pt(4)
        style_run(p_ref.add_run(ref), size=12)

    # =========================================================================
    # PHỤ LỤC
    # =========================================================================
    doc.add_page_break()
    add_h1("Phụ lục")

    add_h2("Phụ lục A. Mã nguồn xử lý tín hiệu Adaptive EMA và truyền UART 5 giây trên STM32F103")
    add_body(
        "Trích đoạn từ stm32_sensor_node/Core/Src/main.c (đồng bộ với Doccambien/Core/Src/main.c, HSI 8 MHz, bù 0,12 V, Adaptive EMA, Deadband 0,2 cm):",
        indent=False
    )
    add_code_block(
        "#define SENSOR_ZERO_OFFSET_VOLTAGE 0.12f\n"
        "#define SENSOR_MAX_VOLTAGE         3.30f\n"
        "#define SENSOR_MAX_WATER_LEVEL_CM  500.0f\n"
        "#define ADC_SAMPLE_COUNT           32\n"
        "#define BAR_TO_CM_WATER            1019.72f\n\n"
        "uint32_t Read_ADC_Filtered(void) {\n"
        "  uint32_t sum = 0;\n"
        "  for (int i = 0; i < ADC_SAMPLE_COUNT; i++) {\n"
        "    HAL_ADC_Start(&hadc1);\n"
        "    if (HAL_ADC_PollForConversion(&hadc1, 10) == HAL_OK)\n"
        "      sum += HAL_ADC_GetValue(&hadc1);\n"
        "    HAL_ADC_Stop(&hadc1);\n"
        "  }\n"
        "  return (sum / ADC_SAMPLE_COUNT);\n"
        "}\n\n"
        "// Trong vong lap while(1) chu ky 100 ms:\n"
        "g_adc_raw = Read_ADC_Filtered();\n"
        "g_voltage = ((float)g_adc_raw / 4095.0f) * 3.3f;\n"
        "float v_eff = g_voltage - SENSOR_ZERO_OFFSET_VOLTAGE;\n"
        "if (v_eff < 0.0f) v_eff = 0.0f;\n"
        "float raw_cm = (v_eff / (SENSOR_MAX_VOLTAGE - SENSOR_ZERO_OFFSET_VOLTAGE)) * SENSOR_MAX_WATER_LEVEL_CM;\n"
        "if (raw_cm > SENSOR_MAX_WATER_LEVEL_CM) raw_cm = SENSOR_MAX_WATER_LEVEL_CM;\n\n"
        "static float s_ema = -1.0f;\n"
        "if (s_ema < 0.0f) s_ema = raw_cm;\n"
        "else {\n"
        "  float step = (raw_cm > s_ema) ? (raw_cm - s_ema) : (s_ema - raw_cm);\n"
        "  s_ema = (step > 2.0f) ? (0.20f * s_ema + 0.80f * raw_cm) : (0.85f * s_ema + 0.15f * raw_cm);\n"
        "}\n"
        "float diff = (s_ema > g_water_level_cm) ? (s_ema - g_water_level_cm) : (g_water_level_cm - s_ema);\n"
        "if (diff >= 0.2f || g_water_level_cm == 0.0f) g_water_level_cm = s_ema;\n"
        "g_pressure_bar = g_water_level_cm / BAR_TO_CM_WATER;\n\n"
        "if (s_last_tx_tick == 0 || (HAL_GetTick() - s_last_tx_tick) >= 5000) {\n"
        "  s_last_tx_tick = HAL_GetTick();\n"
        "  snprintf(uart_tx_buf, sizeof(uart_tx_buf),\n"
        "    \"{\\\"level\\\":%.1f,\\\"volt\\\":%.2f,\\\"percent\\\":%.1f,\\\"press\\\":%.3f,\\\"raw\\\":%lu}\\n\",\n"
        "    g_water_level_cm, g_voltage, water_percent, g_pressure_bar, g_adc_raw);\n"
        "  HAL_UART_Transmit(&huart1, (uint8_t*)uart_tx_buf, strlen(uart_tx_buf), 100);\n"
        "  HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);\n"
        "}\n"
        "HAL_Delay(100);",
        title="Trích đoạn mã nguồn STM32F103C8T6 (main.c)"
    )

    add_h2("Phụ lục B. Mã nguồn Robust UART Parser, Wi-Fi Auto-Reconnect và MQTT LWT trên ESP32-C3")
    add_code_block(
        "// 1. Robust UART Parser (uart_app.c)\n"
        "if (byte_in == '\\n' || byte_in == '\\r') {\n"
        "  if (line_idx > 0) {\n"
        "    line_buf[line_idx] = '\\0'; s_uart_rx_count++;\n"
        "    mqtt_app_publish(NULL, line_buf); line_idx = 0;\n"
        "  }\n"
        "} else if (line_idx > 10 && line_buf[0] == '{' && byte_in == '}') {\n"
        "  line_buf[line_idx++] = '}'; line_buf[line_idx] = '\\0'; s_uart_rx_count++;\n"
        "  mqtt_app_publish(NULL, line_buf); line_idx = 0;\n"
        "} else if (!(line_idx == 0 && byte_in != '{') && line_idx < (UART_BUF_SIZE - 1)) {\n"
        "  line_buf[line_idx++] = (char)byte_in;\n"
        "}\n\n"
        "// 2. Wi-Fi Auto-Reconnect vo han (wifi_app.c)\n"
        "else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {\n"
        "  xEventGroupClearBits(s_wifi_event_group, WIFI_CONNECTED_BIT);\n"
        "  s_retry_num++;\n"
        "  esp_wifi_connect();\n"
        "}\n\n"
        "// 3. Cau hinh MQTT LWT & Keepalive 15s (mqtt_app.c)\n"
        "esp_mqtt_client_config_t mqtt_cfg = {\n"
        "  .broker.address.uri = MQTT_BROKER_URI,\n"
        "  .session = {\n"
        "    .last_will = {\n"
        "      .topic = MQTT_TOPIC_DATA \"/status\",\n"
        "      .msg = \"{\\\"gateway\\\":\\\"ESP32-C3\\\",\\\"status\\\":\\\"offline\\\"}\",\n"
        "      .qos = 1, .retain = 0,\n"
        "    },\n"
        "    .keepalive = 15,\n"
        "  },\n"
        "};",
        title="Trích đoạn mã nguồn ESP32-C3 Gateway (ESP-IDF FreeRTOS)"
    )

    add_h2("Phụ lục C. Lược đồ CSDL Supabase PostgreSQL / SQLite v3.0 và cấu hình triển khai Render")
    add_code_block(
        "-- Luoc do bang measurements tren Supabase PostgreSQL (Dual-Mode voi SQLite WAL)\n"
        "CREATE TABLE IF NOT EXISTS measurements (\n"
        "    id           BIGSERIAL PRIMARY KEY,\n"
        "    received_at  BIGINT           NOT NULL,  -- Unix epoch UTC (ms)\n"
        "    level_cm     DOUBLE PRECISION NOT NULL,  -- Muc nuoc (cm)\n"
        "    volt         DOUBLE PRECISION NOT NULL,  -- Dien ap cam bien (V)\n"
        "    percent      DOUBLE PRECISION NOT NULL,  -- Ty le cot nuoc (%)\n"
        "    press_bar    DOUBLE PRECISION NOT NULL,  -- Ap suat thuy tinh (Bar)\n"
        "    raw_adc      INTEGER          NOT NULL,  -- Gia tri ADC 12-bit [0..4095]\n"
        "    is_simulated INTEGER DEFAULT 0,          -- 0: That, 1: Gia lap\n"
        "    created_at   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP\n"
        ");\n"
        "CREATE INDEX IF NOT EXISTS idx_received_at ON measurements(received_at);\n"
        "CREATE INDEX IF NOT EXISTS idx_simulated   ON measurements(is_simulated);\n\n"
        "# Tep render.yaml (Python 3.11 + Gunicorn 1 worker + Supabase DATABASE_URL)\n"
        "services:\n"
        "  - type: web\n"
        "    name: esp32-water-monitor\n"
        "    runtime: python\n"
        "    rootDir: wifiesp32/data_logger\n"
        "    buildCommand: pip install -r requirements.txt\n"
        "    startCommand: gunicorn --workers 1 --threads 4 --bind 0.0.0.0:$PORT service:app",
        title="Lược đồ Supabase PostgreSQL v3.0 và tệp cấu hình render.yaml"
    )

    path1 = r"D:\Embedded\Bao_Cao_Tong_Hop_IoT_Cam_Bien_Va_Mang.docx"
    path2 = r"D:\Embedded\esp32\docs\Bao_Cao_Tong_Hop_IoT_Cam_Bien_Va_Mang.docx"

    for label, target in [("primary report", path1), ("repo backup report", path2)]:
        try:
            doc.save(target)
            print(f"Saved {label} to: {target}")
        except PermissionError:
            fallback = target.replace(".docx", "_Moi.docx")
            doc.save(fallback)
            print(f"WARNING: {target} is open in Word. Saved {label} to: {fallback}")


if __name__ == "__main__":
    create_report()
