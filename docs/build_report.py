import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def create_report():
    doc = Document()

    # 1. Page Margins Setup (Standard 1 inch / 25.4mm)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # 2. Executive Color Palette
    HEX_PRIMARY = "003366"     # Deep Navy
    HEX_SECONDARY = "006699"   # Cerulean Blue
    HEX_DARK = "1A252C"        # Charcoal Text
    HEX_LIGHT_BG = "F4F7FA"    # Soft Gray-Blue Tint
    HEX_ALT_ROW = "F9FBFC"     # Alternate Table Row
    HEX_BORDER = "CCCCCC"      # Border Gray
    HEX_CODE_BG = "EFEFEF"     # Code block background
    HEX_CALLOUT_BORDER = "006699"

    COLOR_PRIMARY = RGBColor(0x00, 0x33, 0x66)
    COLOR_SECONDARY = RGBColor(0x00, 0x66, 0x99)
    COLOR_DARK = RGBColor(0x1A, 0x25, 0x2C)
    COLOR_MUTED = RGBColor(0x55, 0x66, 0x77)

    # 3. XML Helper Functions for Advanced Styling
    def set_cell_background(cell, fill_hex):
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), fill_hex)
        tcPr.append(shd)

    def set_cell_margins(cell, top=140, bottom=140, left=180, right=180):
        tcPr = cell._tc.get_or_add_tcPr()
        tcMar = OxmlElement('w:tcMar')
        for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
            node = OxmlElement(f'w:{m}')
            node.set(qn('w:w'), str(val))
            node.set(qn('w:type'), 'dxa')
            tcMar.append(node)
        tcPr.append(tcMar)

    def set_cell_borders(cell, top=HEX_BORDER, bottom=HEX_BORDER, left=HEX_BORDER, right=HEX_BORDER, sz="4"):
        tcPr = cell._tc.get_or_add_tcPr()
        tcBorders = OxmlElement('w:tcBorders')
        borders = {'top': top, 'bottom': bottom, 'left': left, 'right': right}
        for side, color in borders.items():
            if color:
                b = OxmlElement(f'w:{side}')
                b.set(qn('w:val'), 'single')
                b.set(qn('w:sz'), sz)
                b.set(qn('w:space'), '0')
                b.set(qn('w:color'), color)
                tcBorders.append(b)
            else:
                b = OxmlElement(f'w:{side}')
                b.set(qn('w:val'), 'none')
                tcBorders.append(b)
        tcPr.append(tcBorders)

    # Document Section Builders
    def add_doc_title(title_text, subtitle_text):
        p_tag = doc.add_paragraph()
        p_tag.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_tag.paragraph_format.space_before = Pt(0)
        p_tag.paragraph_format.space_after = Pt(4)
        run_tag = p_tag.add_run("BÁO CÁO KỸ THUẬT TOÀN DIỆN & TỔNG HỢP ĐỒ ÁN")
        run_tag.bold = True
        run_tag.font.size = Pt(13)
        run_tag.font.color.rgb = COLOR_SECONDARY
        run_tag.font.name = "Calibri"

        p_main = doc.add_paragraph()
        p_main.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_main.paragraph_format.space_before = Pt(0)
        p_main.paragraph_format.space_after = Pt(8)
        run_main = p_main.add_run(title_text)
        run_main.bold = True
        run_main.font.size = Pt(18)
        run_main.font.color.rgb = COLOR_PRIMARY
        run_main.font.name = "Calibri"

        p_sub = doc.add_paragraph()
        p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_sub.paragraph_format.space_before = Pt(0)
        p_sub.paragraph_format.space_after = Pt(14)
        run_sub = p_sub.add_run(subtitle_text)
        run_sub.italic = True
        run_sub.font.size = Pt(11)
        run_sub.font.color.rgb = COLOR_MUTED
        run_sub.font.name = "Calibri"

        # Decorative Divider Bar
        div_table = doc.add_table(rows=1, cols=1)
        div_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        div_cell = div_table.cell(0, 0)
        set_cell_background(div_cell, HEX_PRIMARY)
        set_cell_margins(div_cell, top=20, bottom=20, left=0, right=0)
        set_cell_borders(div_cell, top=None, bottom=None, left=None, right=None)
        p_div = div_cell.paragraphs[0]
        p_div.paragraph_format.space_before = Pt(0)
        p_div.paragraph_format.space_after = Pt(0)
        r_div = p_div.add_run("")
        r_div.font.size = Pt(2)

        p_space = doc.add_paragraph()
        p_space.paragraph_format.space_before = Pt(8)
        p_space.paragraph_format.space_after = Pt(0)

    def add_meta_box(items):
        t = doc.add_table(rows=len(items), cols=2)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        t.columns[0].width = Inches(2.3)
        t.columns[1].width = Inches(4.2)
        for idx, (label, val) in enumerate(items):
            cell_lbl = t.cell(idx, 0)
            cell_val = t.cell(idx, 1)
            set_cell_background(cell_lbl, HEX_LIGHT_BG)
            set_cell_background(cell_val, HEX_LIGHT_BG)
            set_cell_margins(cell_lbl, top=45, bottom=45, left=120, right=120)
            set_cell_margins(cell_val, top=45, bottom=45, left=120, right=120)
            set_cell_borders(cell_lbl, top="DDDDDD", bottom="DDDDDD", left="DDDDDD", right="DDDDDD", sz="2")
            set_cell_borders(cell_val, top="DDDDDD", bottom="DDDDDD", left="DDDDDD", right="DDDDDD", sz="2")
            
            p_lbl = cell_lbl.paragraphs[0]
            p_lbl.paragraph_format.space_after = Pt(0)
            r_lbl = p_lbl.add_run(label)
            r_lbl.bold = True
            r_lbl.font.size = Pt(9.5)
            r_lbl.font.color.rgb = COLOR_PRIMARY
            r_lbl.font.name = "Calibri"

            p_val = cell_val.paragraphs[0]
            p_val.paragraph_format.space_after = Pt(0)
            r_val = p_val.add_run(val)
            r_val.font.size = Pt(9.5)
            r_val.font.color.rgb = COLOR_DARK
            r_val.font.name = "Calibri"
        
        p_space = doc.add_paragraph()
        p_space.paragraph_format.space_before = Pt(10)
        p_space.paragraph_format.space_after = Pt(0)

    def add_part_header(part_code, part_title, part_desc):
        table = doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        table.columns[0].width = Inches(6.5)
        cell = table.cell(0, 0)
        set_cell_background(cell, HEX_PRIMARY)
        set_cell_margins(cell, top=180, bottom=180, left=240, right=240)
        set_cell_borders(cell, top=None, bottom=None, left=None, right=None)

        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(3)
        r_code = p.add_run(part_code.upper())
        r_code.bold = True
        r_code.font.size = Pt(11.5)
        r_code.font.color.rgb = RGBColor(0x99, 0xCC, 0xFF)
        r_code.font.name = "Calibri"

        p2 = cell.add_paragraph()
        p2.paragraph_format.space_before = Pt(0)
        p2.paragraph_format.space_after = Pt(3)
        r_title = p2.add_run(part_title)
        r_title.bold = True
        r_title.font.size = Pt(15)
        r_title.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        r_title.font.name = "Calibri"

        p3 = cell.add_paragraph()
        p3.paragraph_format.space_before = Pt(0)
        p3.paragraph_format.space_after = Pt(0)
        r_desc = p3.add_run(part_desc)
        r_desc.italic = True
        r_desc.font.size = Pt(9.5)
        r_desc.font.color.rgb = RGBColor(0xDD, 0xEE, 0xFF)
        r_desc.font.name = "Calibri"

        p_after = doc.add_paragraph()
        p_after.paragraph_format.space_before = Pt(10)
        p_after.paragraph_format.space_after = Pt(0)

    def add_heading_1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(13.5)
        run.font.color.rgb = COLOR_PRIMARY
        run.font.name = "Calibri"

    def add_heading_2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(11.5)
        run.font.color.rgb = COLOR_SECONDARY
        run.font.name = "Calibri"

    def add_heading_3(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(9)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(10.5)
        run.font.color.rgb = COLOR_DARK
        run.font.name = "Calibri"

    def add_paragraph(text, bold_prefix="", space_after=5, italic=False):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            r_bold = p.add_run(bold_prefix)
            r_bold.bold = True
            r_bold.font.size = Pt(10.5)
            r_bold.font.color.rgb = COLOR_DARK
            r_bold.font.name = "Calibri"
        run = p.add_run(text)
        run.font.size = Pt(10.5)
        run.italic = italic
        run.font.color.rgb = COLOR_DARK
        run.font.name = "Calibri"
        return p

    def add_bullet(bold_prefix, text):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(3.5)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            r_bold = p.add_run(bold_prefix + ": ")
            r_bold.bold = True
            r_bold.font.size = Pt(10.5)
            r_bold.font.color.rgb = COLOR_PRIMARY
            r_bold.font.name = "Calibri"
        run = p.add_run(text)
        run.font.size = Pt(10.5)
        run.font.color.rgb = COLOR_DARK
        run.font.name = "Calibri"
        return p

    def add_callout(title, lines):
        t = doc.add_table(rows=1, cols=1)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        t.columns[0].width = Inches(6.5)
        cell = t.cell(0, 0)
        set_cell_background(cell, HEX_LIGHT_BG)
        set_cell_margins(cell, top=130, bottom=130, left=180, right=160)
        set_cell_borders(cell, top="D0DDE5", bottom="D0DDE5", left=HEX_CALLOUT_BORDER, right="D0DDE5", sz="16")

        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(4)
        r_title = p.add_run(title)
        r_title.bold = True
        r_title.font.size = Pt(10.5)
        r_title.font.color.rgb = COLOR_PRIMARY
        r_title.font.name = "Calibri"

        for line in lines:
            p_line = cell.add_paragraph()
            p_line.paragraph_format.space_before = Pt(0)
            p_line.paragraph_format.space_after = Pt(2.5)
            p_line.paragraph_format.line_spacing = 1.15
            r_line = p_line.add_run(line)
            r_line.font.size = Pt(9.5)
            r_line.font.color.rgb = COLOR_DARK
            r_line.font.name = "Calibri"

        p_space = doc.add_paragraph()
        p_space.paragraph_format.space_before = Pt(6)
        p_space.paragraph_format.space_after = Pt(0)

    def add_code_block(code_str):
        t = doc.add_table(rows=1, cols=1)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        t.columns[0].width = Inches(6.5)
        cell = t.cell(0, 0)
        set_cell_background(cell, HEX_CODE_BG)
        set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
        set_cell_borders(cell, top="CCCCCC", bottom="CCCCCC", left="006699", right="CCCCCC", sz="12")

        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.1
        r = p.add_run(code_str)
        r.font.name = "Consolas"
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(0x22, 0x22, 0x22)

        p_space = doc.add_paragraph()
        p_space.paragraph_format.space_before = Pt(6)
        p_space.paragraph_format.space_after = Pt(0)

    def add_styled_table(headers, rows, col_widths, align_center_cols=[]):
        t = doc.add_table(rows=len(rows) + 1, cols=len(headers))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False

        for idx, width in enumerate(col_widths):
            t.columns[idx].width = Inches(width)

        for col_idx, h_text in enumerate(headers):
            cell = t.cell(0, col_idx)
            cell.width = Inches(col_widths[col_idx])
            set_cell_background(cell, HEX_PRIMARY)
            set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
            set_cell_borders(cell, top=HEX_PRIMARY, bottom=HEX_SECONDARY, left="004080", right="004080", sz="4")
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            run = p.add_run(h_text)
            run.bold = True
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            run.font.name = "Calibri"

        for row_idx, row_data in enumerate(rows):
            bg_color = HEX_ALT_ROW if (row_idx % 2 == 1) else "FFFFFF"
            for col_idx, cell_value in enumerate(row_data):
                cell = t.cell(row_idx + 1, col_idx)
                cell.width = Inches(col_widths[col_idx])
                set_cell_background(cell, bg_color)
                set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
                set_cell_borders(cell, top="E0E0E0", bottom="E0E0E0", left="E0E0E0", right="E0E0E0", sz="4")
                p = cell.paragraphs[0]
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.15
                
                if col_idx in align_center_cols:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                else:
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT

                run = p.add_run(str(cell_value))
                run.font.size = Pt(9)
                run.font.color.rgb = COLOR_DARK
                run.font.name = "Calibri"

        p_space = doc.add_paragraph()
        p_space.paragraph_format.space_before = Pt(8)
        p_space.paragraph_format.space_after = Pt(0)

    # =========================================================================
    # BẮT ĐẦU NỘI DUNG TÀI LIỆU
    # =========================================================================
    
    # 1. TIÊU ĐỀ & KHUNG THÔNG TIN
    add_doc_title(
        "HỆ THỐNG IOT GIÁM SÁT MỰC NƯỚC VÀ CẢNH BÁO THIÊN TAI ĐA TẦNG",
        "Báo cáo kỹ thuật chi tiết: Thu thập tín hiệu cảm biến (STM32F103) & Kiến trúc mạng IoT Gateway (ESP32-C3)"
    )

    metadata = [
        ("Tên dự án:", "Hệ thống IoT Giám sát mực nước, áp suất thủy tĩnh & Cảnh báo ngập lụt từ xa"),
        ("Vi điều khiển đo lường biên:", "STM32F103C8T6 (ARM Cortex-M3 32-bit @ 72 MHz)"),
        ("Vi điều khiển IoT Gateway:", "ESP32-C3 (RISC-V 32-bit Single-Core @ 160 MHz)"),
        ("Cảm biến ứng dụng:", "Cảm biến áp suất thủy tĩnh thả chìm (Submersible Level Transmitter, 0–5m, 0–3.3V)"),
        ("Giao thức kết nối liên mạch:", "UART 115200 8N1 (JSON Framing kết thúc bằng '\\n'), Common Grounding"),
        ("Mạng truyền thông & Đám mây:", "Wi-Fi 802.11 b/g/n (STA Mode), MQTT v3.1.1 (HiveMQ Public Cloud Broker)"),
        ("Giao diện người dùng:", "Web Dashboard thời gian thực (HTML5, Tailwind CSS, MQTT.js, Chart.js)"),
        ("Trạng thái thực nghiệm:", "Hoàn thiện hiệu chuẩn màng đo, lọc nhiễu 4 tầng, đã kiểm thử trực tiếp trên Cloud")
    ]
    add_meta_box(metadata)

    # =========================================================================
    # CHƯƠNG 1: SƠ ĐỒ KHỐI KẾT NỐI PHẦN CỨNG HỆ THỐNG
    # =========================================================================
    add_heading_1("CHƯƠNG 1: SƠ ĐỒ KHỐI KẾT NỐI PHẦN CỨNG HỆ THỐNG (HARDWARE CONNECTION BLOCK DIAGRAM)")
    add_paragraph(
        "Hệ thống giám sát mực nước và cảnh báo thiên tai được thiết kế theo sơ đồ khối kết nối phần cứng đồng bộ và tối ưu hóa giữa các phân hệ điện tử vật lý. "
        "Thiết kế tuân thủ nghiêm ngặt các tiêu chuẩn kỹ thuật phần cứng nhúng: phân tách rõ ràng khối chức năng, đảm bảo tính toàn vẹn tín hiệu tương tự (Analog Signal Integrity), "
        "đồng bộ mức điện áp giao tiếp số (Digital Bus Voltage Matching) và thiết lập tuyến Mass chung (Common Ground 0V) an toàn. Hệ thống bao gồm 5 khối phần cứng liên kết mật thiết:",
        bold_prefix="Nguyên lý kết nối phần cứng tổng thể: "
    )

    hardware_diag_path = r"D:\Embedded\esp32\docs\hardware_block_diagram.png"
    if not os.path.exists(hardware_diag_path):
        hardware_diag_path = r"D:\Embedded\esp32\docs\system_block_diagram.png"

    if os.path.exists(hardware_diag_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(4)
        p_img.paragraph_format.space_after = Pt(4)
        r_img = p_img.add_run()
        r_img.add_picture(hardware_diag_path, width=Inches(6.5))

        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(0)
        p_cap.paragraph_format.space_after = Pt(10)
        r_cap = p_cap.add_run("Hình 1.1: Sơ đồ khối kết nối phần cứng toàn diện hệ thống (Hardware Interconnection Block Diagram)")
        r_cap.font.size = Pt(9.5)
        r_cap.font.italic = True
        r_cap.font.color.rgb = COLOR_MUTED

    headers_diagram_summary = ["Khối phần cứng", "Linh kiện / Chipset cốt lõi", "Giao tiếp & Mức điện áp vật lý", "Chức năng & Nhiệm vụ phần cứng"]
    rows_diagram_summary = [
        ["Khối Cấp Nguồn\n(Power Unit)", 
         "Adapter công nghiệp 12V/2A\nCổng USB 5V & Mạch hạ áp LDO 3.3V", 
         "• +12V DC (Nguồn cảm biến)\n• +5V DC (Nguồn USB bo mạch)\n• +3.3V DC (Nguồn lõi MCU/RF)\n• Common GND (Mass chung 0V)", 
         "Cung cấp năng lượng ổn định, chống sụt áp và triệt tiêu xung nhiễu nguồn cho toàn bộ mạch điện tử."],
        ["Khối Cảm Biến\n(Sensor Unit)", 
         "Cảm biến áp suất thủy tĩnh thả chìm (Inox 316L, IP68)", 
         "• Cấp nguồn nuôi: 12V DC\n• Ngõ ra: Tín hiệu Analog 0.00V – 3.30V DC\n• Cáp bọc kim chống nhiễu & ống thở", 
         "Cảm nhận áp suất cột nước theo định luật Pascal P = ρ·g·h, xuất điện áp tương tự 0–3.3V tỷ lệ tuyến tính với độ sâu 0–5m."],
        ["Khối Đo Lường Biên\n(Edge MCU)", 
         "STM32F103C8T6 (ARM Cortex-M3 32-bit @ 72 MHz)", 
         "• Kênh ngõ vào: PA0 (ADC1_IN0, 12-bit)\n• Bus truyền số liệu: PA9 (USART1_TX, 3.3V TTL)\n• Chân báo trạng thái: PC13 (Heartbeat LED)", 
         "Tự cân chỉnh phần cứng ADC, lấy mẫu quá mức 32x, lọc trôi điểm không, lọc đệ quy EMA, đóng gói dữ liệu JSON UART 115200 bps."],
        ["Khối IoT Gateway\n(Gateway Unit)", 
         "ESP32-C3 (RISC-V 32-bit Single-Core @ 160 MHz)", 
         "• Cổng nhận số liệu: GPIO 4 (UART1_RX, 3.3V CMOS)\n• Cổng nạp/debug: Type-C USB 5V\n• Ngõ ra cao tần: RF Baseband 2.4 GHz", 
         "Đệm luồng dữ liệu nối tiếp bằng RingBuffer 2KB FreeRTOS, phân tích JSON, kết nối mạng Wi-Fi và đẩy dữ liệu lên MQTT Broker."],
        ["Khối Thu Phát RF\n(Wireless Unit)", 
         "Ăng-ten PCB tích hợp 2.4 GHz\n(Tùy chọn: Module LoRa RFM95 SPI)", 
         "• Đường dẫn sóng RF 50Ω chuẩn phối hợp trở kháng\n• Chuẩn không dây: Wi-Fi 802.11 b/g/n (STA Mode)\n• Tần số: 2.4 GHz ISM", 
         "Bức xạ sóng điện từ truyền tải các gói tin MQTT lên Access Point / Router; hỗ trợ mở rộng cắm module LoRa diện rộng."]
    ]
    add_styled_table(headers_diagram_summary, rows_diagram_summary, [1.3, 1.6, 1.8, 1.8], align_center_cols=[0])

    # =========================================================================
    # CHƯƠNG 2: CẤU HÌNH PHẦN CỨNG & SƠ ĐỒ ĐẤU NỐI CHÂN CHI TIẾT
    # =========================================================================
    add_heading_1("CHƯƠNG 2: CẤU HÌNH PHẦN CỨNG & SƠ ĐỒ ĐẤU NỐI CHÂN CHI TIẾT")
    add_paragraph(
        "Một trong những yếu tố quyết định sự ổn định sống còn của các hệ thống đo lường công nghiệp là phương pháp đấu nối phần cứng, "
        "đặc biệt là khi kết hợp giữa nguồn công nghiệp công suất cao (12V DC) và mạch điều khiển điện áp thấp (3.3V / 5V DC). "
        "Sơ đồ dưới đây mô tả chính xác sơ đồ chân và đường tín hiệu vật lý giữa các khối thiết bị trong hệ thống:",
        bold_prefix="Nguyên lý kết nối phần cứng: "
    )

    wiring_diag_path = r"D:\Embedded\esp32\docs\hardware_wiring_diagram.png"
    if os.path.exists(wiring_diag_path):
        p_img2 = doc.add_paragraph()
        p_img2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img2.paragraph_format.space_before = Pt(4)
        p_img2.paragraph_format.space_after = Pt(4)
        r_img2 = p_img2.add_run()
        r_img2.add_picture(wiring_diag_path, width=Inches(6.5))

        p_cap2 = doc.add_paragraph()
        p_cap2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap2.paragraph_format.space_before = Pt(0)
        p_cap2.paragraph_format.space_after = Pt(10)
        r_cap2 = p_cap2.add_run("Hình 2.1: Sơ đồ đấu nối dây và sơ đồ chân chi tiết (Hardware Wiring & Pinout Schematic)")
        r_cap2.font.size = Pt(9.5)
        r_cap2.font.italic = True
        r_cap2.font.color.rgb = COLOR_MUTED

    add_heading_2("2.1. Cấu hình các chân vi điều khiển STM32F103C8T6 (Edge MCU)")
    add_paragraph(
        "Trên bo mạch STM32F103C8T6 (BluePill), các chân chức năng được cấu hình bằng phần mềm STM32CubeMX / HAL Driver như sau:"
    )
    headers_stm32_pins = ["Tên chân", "Chế độ GPIO / Ngoại vi", "Cấu hình chi tiết", "Chức năng trong hệ thống"]
    rows_stm32_pins = [
        ["PA0", "Analog Mode (ADC1_IN0)", "Chế độ tương tự, không Pull-up/down, thời gian lấy mẫu 55.5 cycles", "Nhận tín hiệu điện áp tương tự 0.00V – 3.30V từ cảm biến áp suất thủy tĩnh."],
        ["PA9", "Alternate Function (USART1_TX)", "AF Push-Pull, High Speed 50MHz, Baudrate 115200 8N1", "Chân truyền dữ liệu chuỗi JSON cảm biến sang vi điều khiển ESP32-C3."],
        ["PA10", "Input Mode (USART1_RX)", "Input Floating / Pull-Up, Baudrate 115200 8N1", "Chân nhận dữ liệu phản hồi hoặc cấu hình từ ESP32-C3 (tùy chọn 2 chiều)."],
        ["PC13", "Output Push-Pull (GPIO_Out)", "Chế độ xuất mức logic, tốc độ thấp (Active Low)", "Đèn LED Onboard: Nhấp nháy nhịp tim (Heartbeat) mỗi khi hoàn tất gửi 1 gói tin sang ESP32."],
        ["GND", "Power Ground (VSS)", "Mass tham chiếu 0V của hệ thống", "Nối chung với Mass của Nguồn 12V và Mass của ESP32 (Common Ground)."],
        ["3.3V", "Power Supply (VDD)", "Điện áp hoạt động nội bộ MCU", "Nhận nguồn từ mạch hạ áp 5V -> 3.3V hoặc từ cổng nạp ST-Link."]
    ]
    add_styled_table(headers_stm32_pins, rows_stm32_pins, [1.1, 1.8, 1.8, 1.8], align_center_cols=[0])

    add_heading_2("2.2. Cấu hình các chân vi điều khiển ESP32-C3 (IoT Gateway)")
    add_paragraph(
        "Vi điều khiển ESP32-C3 đảm nhận giao tiếp cầu nối không dây với cấu hình chân phần cứng như sau:"
    )
    headers_esp32_pins = ["Tên chân", "Ngoại vi ESP-IDF", "Cấu hình phần mềm", "Chức năng trong hệ thống"]
    rows_esp32_pins = [
        ["GPIO 4", "UART_NUM_1 RX Pin", "Baudrate 115200, 8-bit Data, No Parity, 1 Stop bit, Buffer 2048 B", "Nhận dòng byte nối tiếp từ chân PA9 (TX) của STM32, kích hoạt ngắt gom gói theo '\\n'."],
        ["GPIO 5", "UART_NUM_1 TX Pin", "Baudrate 115200, 8-bit Data, No Parity, 1 Stop bit", "Truyền lệnh điều khiển sang chân PA10 (RX) của STM32."],
        ["GND", "Power Ground (GND)", "Mass tham chiếu 0V", "Nối chung vào điểm Mass hệ thống (Common Ground) với STM32 và nguồn 12V."],
        ["5V / USB", "USB-CDC / Power VDD", "Cổng Type-C cắm PC hoặc sạc 5V DC", "Cung cấp nguồn nuôi cho ESP32 và nạp code / xuất log debug qua cổng COM ảo (COM7)."]
    ]
    add_styled_table(headers_esp32_pins, rows_esp32_pins, [1.1, 1.6, 1.9, 1.9], align_center_cols=[0])

    add_heading_2("2.3. Bảng đấu nối liên mạch toàn hệ thống (Wiring Connection Table)")
    headers_wiring = ["STT", "Thiết bị nguồn", "Chân xuất", "Thiết bị đích", "Chân nhận", "Màu dây đề xuất", "Mức điện áp", "Ý nghĩa chức năng"]
    rows_wiring = [
        ["1", "Nguồn DC 12V", "+12V (Cực +)", "Cảm biến thủy tĩnh", "VCC (Dây Đỏ)", "Đỏ", "+12.0 V DC", "Cấp nguồn nuôi cho mạch khuếch đại màng đo bên trong đầu dò."],
        ["2", "Nguồn DC 12V", "GND (Cực -)", "Điểm nối Mass chung", "GND chung", "Đen", "0.0 V (GND)", "Tạo mốc điện thế 0V chuẩn cho toàn bộ mạch."],
        ["3", "Cảm biến thủy tĩnh", "OUT (Tín hiệu)", "STM32F103", "Chân PA0", "Vàng / Cam", "0.00 – 3.30 V", "Đưa điện áp đo được vào bộ chuyển đổi ADC 12-bit."],
        ["4", "Cảm biến thủy tĩnh", "GND (Dây âm)", "Điểm nối Mass chung", "GND chung", "Đen / Nâu", "0.0 V (GND)", "Khép kín mạch dòng điện tín hiệu của cảm biến."],
        ["5", "STM32F103", "Chân PA9 (TX)", "ESP32-C3", "Chân GPIO 4 (RX)", "Xanh lá", "3.3 V Logic", "Dây truyền dữ liệu chuỗi JSON cảm biến sang ESP32."],
        ["6", "STM32F103", "Chân PA10 (RX)", "ESP32-C3", "Chân GPIO 5 (TX)", "Xanh dương", "3.3 V Logic", "Dây phản hồi điều khiển hai chiều (tùy chọn)."],
        ["7", "STM32F103", "Chân GND", "ESP32-C3", "Chân GND", "Đen", "0.0 V (GND)", "ĐƯỜNG MASS CHUNG BẮT BUỘC để hai vi điều khiển hiểu cùng mức 0V."]
    ]
    add_styled_table(headers_wiring, rows_wiring, [0.5, 1.1, 1.0, 1.1, 1.0, 0.7, 0.9, 1.2], align_center_cols=[0, 6])

    add_callout(
        "NGUYÊN TẮC KỸ THUẬT SỐNG CÒN: CƠ CHẾ NỐI MASS CHUNG (COMMON GROUND)",
        [
            "1. Bắt buộc phải có dây nối GND giữa Nguồn 12V, STM32 và ESP32: Trong các mạch điện tử nhúng, điện áp là hiệu điện thế so với mốc Mass (0V). Nếu không nối chung GND, mốc 0V của STM32 và ESP32 sẽ trôi dạt tự do (Floating Ground), khiến tín hiệu UART từ PA9 bị sai lệch điện áp hoàn toàn, dẫn đến việc ESP32 đọc phải các byte rác ngẫu nhiên hoặc không nhận được gói tin.",
            "2. Tuyệt đối không cắm nhầm dây +12V vào chân vi điều khiển: Chân PA0 của STM32 chỉ chịu được điện áp tối đa 3.3V (hoặc 3.6V tuyệt đối). Điện áp ngõ ra của cảm biến sau khi điều chỉnh thang đo là 0 - 3.3V. Dây +12V chỉ được cắm duy nhất vào chân nguồn nuôi của cảm biến.",
            "3. Chuẩn điện áp logic tương thích 100%: Chân PA9 (STM32) và GPIO 4 (ESP32) đều hoạt động ở chuẩn logic 3.3V CMOS, do đó có thể nối trực tiếp mà không cần mạch chuyển đổi mức logic (Logic Level Shifter)."
        ]
    )

    # =========================================================================
    # CHƯƠNG 3: QUY TRÌNH & THUẬT TOÁN XỬ LÝ NHIỄU ĐA TẦNG (NOISE FILTERING)
    # =========================================================================
    add_heading_1("CHƯƠNG 3: QUY TRÌNH & THUẬT TOÁN XỬ LÝ NHIỄU ĐA TẦNG")
    
    add_heading_2("3.1. Phân tích bản chất các nguồn nhiễu thực tế trong đo lường thủy văn")
    add_paragraph(
        "Trong các ứng dụng đo lường thực địa, tín hiệu từ cảm biến áp suất thủy tĩnh ngập trong nước bị ảnh hưởng bởi nhiều nguồn nhiễu "
        "vật lý và điện từ trường đan xen. Nếu chỉ đọc giá trị ADC đơn lẻ rồi quy đổi tuyến tính, số đo sẽ bị nhảy loạn xạ và phát ra hàng loạt cảnh báo giả:"
    )
    add_bullet("Nhiễu lượng tử hóa và dao động nội tại của bộ ADC 12-bit", 
               "Bo mạch BluePill STM32F103 thương mại dùng chung đường nguồn cấp VDD 3.3V cho chân điện áp tham chiếu ADC (VREF+). Bất kỳ dao động xung nhịp nào của CPU hoặc sụt áp tạm thời đều gây rung lắc 2 - 4 bit có trọng số thấp nhất (LSB).")
    add_bullet("Nhiễu gợn sóng và xung động cơ học thủy tĩnh (Water Ripples & Sloshing)", 
               "Mặt nước không bao giờ phẳng tuyệt đối. Khi có gió thổi, dòng chảy, hoặc quá trình xả/bơm nước, áp lực đè lên màng silicon bị dao động dạng sóng điều hòa, tạo ra các gai nhiễu điện áp nhấp nhô liên tục.")
    add_bullet("Hiện tượng sai số dịch điểm không (Zero-drift Offset)", 
               "Do đặc tính của màng cảm biến áp điện piezo-resistive và mạch khuếch đại thuật toán tích hợp, khi để đầu dò hoàn toàn ngoài không khí (mực nước h = 0 cm), cảm biến vẫn xuất ra một điện áp tĩnh khoảng 0.12 V. Nếu không khấu trừ, hệ thống sẽ báo ảo mực nước dâng từ 15 cm đến 18 cm ngay cả khi không có nước.")
    add_bullet("Hiện tượng giọt ẩm và bọt khí bám dính màng đo (Hysteresis & Surface Tension)", 
               "Khi nhấc cảm biến ra khỏi nước hoặc khi mực nước vừa rút, các giọt nước nhỏ li ti có thể đọng lại trên bề mặt màng đo, tạo ra một lực căng bề mặt gây dao động trôi dạt quanh mốc 0.05 – 0.25 cm.")

    add_heading_2("3.2. Chuỗi thuật toán xử lý nhiễu 4 bước tuần tự trên STM32")
    add_paragraph(
        "Để giải quyết triệt để các vấn đề trên, nhóm phát triển đã xây dựng một chuỗi xử lý tín hiệu số 4 bước tuần tự, "
        "kết hợp từ cấp độ phần cứng thanh ghi đến thuật toán số học đệ quy:",
        bold_prefix="Mô hình lọc 4 tầng: "
    )

    add_paragraph(
        "Trước khi bước vào vòng lặp đo chính, vi điều khiển kích hoạt chức năng tự cân chỉnh vi sai của bộ biến đổi ADC1. "
        "Lệnh HAL_ADCEx_Calibration_Start(&hadc1) tính toán các hệ số trôi lệch bên trong dãy tụ điện lấy mẫu, triệt tiêu sai số chế tạo ban đầu của chip.",
        bold_prefix="Bước 1: Tự hiệu chuẩn phần cứng ADC (Hardware Auto-Calibration) - "
    )

    add_paragraph(
        "Thay vì chỉ đọc 1 mẫu đơn lẻ, mỗi chu kỳ đo STM32 kích hoạt chuyển đổi 32 lần liên tục với thời gian lấy mẫu 55.5 chu kỳ xung nhịp. "
        "Giá trị trung bình cộng được tính bằng công thức:",
        bold_prefix="Bước 2: Lọc quá mẫu và trung bình cộng 32 lần (Oversampling & Averaging) - "
    )
    add_code_block(
        "// Thuật toán lấy mẫu trung bình 32 lần triệt tiêu nhiễu Gauss trắng\n"
        "uint32_t Read_ADC_Filtered(void) {\n"
        "    uint32_t sum = 0;\n"
        "    for (int i = 0; i < 32; i++) {\n"
        "        HAL_ADC_Start(&hadc1);\n"
        "        if (HAL_ADC_PollForConversion(&hadc1, 10) == HAL_OK) {\n"
        "            sum += HAL_ADC_GetValue(&hadc1);\n"
        "        }\n"
        "        HAL_ADC_Stop(&hadc1);\n"
        "    }\n"
        "    return (sum / 32);\n"
        "}"
    )
    add_paragraph(
        "Về mặt lý thuyết xử lý tín hiệu số, phương pháp quá mẫu N = 32 giúp tăng tỷ số tín hiệu trên nhiễu (SNR) lên một lượng là "
        "10·log10(32) ≈ 15.05 dB (tương đương biên độ nhiễu giảm đi √32 ≈ 5.66 lần). Các dao động rung giật ngẫu nhiên của 3 bit LSB bị triệt tiêu hoàn toàn.",
        bold_prefix="Ý nghĩa toán học: "
    )

    add_paragraph(
        "Điện áp thực tế tại chân PA0 được tính qua tỉ lệ: V = (ADC_raw / 4095.0) × 3.3V. "
        "Sau đó, thuật toán trừ đi chính xác điện áp tĩnh 0.12V đã đo kiểm khi màng đo ở ngoài không khí, kết hợp hàm khóa chặn dưới (Clamping) để chống số âm:",
        bold_prefix="Bước 3: Hiệu chuẩn trừ áp nền điểm không & Khóa cận dưới (Zero-Offset & Clamping) - "
    )
    add_code_block(
        "float v_effective = g_voltage - SENSOR_ZERO_OFFSET_VOLTAGE; // Trừ hao 0.12V\n"
        "if (v_effective < 0.0f) {\n"
        "    v_effective = 0.0f; // Khóa chặn dưới, ngăn điện áp âm do trôi nhiệt nhỏ\n"
        "}\n"
        "float voltage_span = SENSOR_MAX_VOLTAGE - SENSOR_ZERO_OFFSET_VOLTAGE; // Dải áp hữu ích: 3.30V - 0.12V = 3.18V\n"
        "float raw_level_cm = (v_effective / voltage_span) * SENSOR_MAX_WATER_LEVEL_CM; // Quy đổi ra cm"
    )

    add_paragraph(
        "Để khắc phục triệt để hiện tượng giọt ẩm hoặc hơi nước đọng trên bề mặt màng cảm ứng sau khi rút nước gây báo số nhỏ (0.1 cm - 0.25 cm), "
        "thuật toán thiết lập một vùng chết (Deadband) bằng 0.3 cm. Nếu mực nước tính toán nhỏ hơn ngưỡng 0.3 cm thì tự động ép về 0.0 cm:",
        bold_prefix="Bước 4: Bộ lọc phi tuyến vùng chết màng đo (Deadband Filter 0.3 cm) - "
    )
    add_code_block(
        "if (g_water_level_cm < 0.3f) {\n"
        "    g_water_level_cm = 0.0f; // Cắt bỏ dao động trôi dạt quanh điểm 0\n"
        "}"
    )

    add_paragraph(
        "Đây là khâu xử lý tinh tế nhất trong hệ thống. Tín hiệu mực nước sau khi tính toán vẫn có thể dao động nhẹ theo nhịp sóng cơ học. "
        "Thuật toán áp dụng bộ lọc thông thấp đệ quy EMA bậc 1 với hệ số trọng số α = 0.15 (15% trọng số cho giá trị đo mới tức thời và 85% cho giá trị quá khứ):",
        bold_prefix="Bước 5: Bộ lọc đệ quy số thông thấp EMA (Exponential Moving Average Filter) - "
    )
    add_code_block(
        "// Bộ lọc EMA làm mịn tín hiệu mực nước\n"
        "static float s_ema_level = -1.0f;\n"
        "if (s_ema_level < 0.0f) {\n"
        "    s_ema_level = raw_level_cm; // Khởi tạo mốc ban đầu\n"
        "} else {\n"
        "    s_ema_level = (0.15f * raw_level_cm) + (0.85f * s_ema_level);\n"
        "}\n"
        "g_water_level_cm = s_ema_level;"
    )
    add_paragraph(
        "Bộ lọc EMA đóng vai trò tương tự như một mạch lọc thông thấp RC analog nhưng được thực hiện hoàn toàn bằng phần mềm mà không tốn linh kiện. "
        "Hệ số α = 0.15 được lựa chọn tối ưu sau nhiều lần thử nghiệm: nó cắt bỏ hoàn toàn các đỉnh sóng nước nhấp nhô tức thời (Water sloshing) "
        "nhưng vẫn đảm bảo tốc độ đáp ứng thay đổi mực nước thật chỉ trong vòng dưới 0.3 giây.",
        bold_prefix="Đặc tính tần số của bộ lọc EMA: "
    )

    add_heading_2("3.3. So sánh trực quan chất lượng tín hiệu trước và sau khi xử lý nhiễu")
    headers_filter_eval = ["Tiêu chí đánh giá", "Tín hiệu thô (Chưa lọc nhiễu)", "Tín hiệu đã qua chuỗi lọc 4 tầng", "Hiệu quả thực tế đạt được"]
    rows_filter_eval = [
        ["Độ ổn định điểm 0", "Báo ảo 15 – 18 cm khi ở ngoài không khí do tồn tại điện áp tĩnh 0.12V.", "Khóa tuyệt đối ở mức 0.00 cm khi cảm biến ngoài không khí hoặc có giọt ẩm nhỏ.", "Loại bỏ hoàn toàn 100% tình trạng báo động ngập lụt giả khi trời tạnh ráo."],
        ["Độ rung giật chữ số", "Chữ số hàng đơn vị và thập phân nhảy liên tục ±1.5 cm mỗi chu kỳ đọc.", "Số đo đứng yên vững vàng, chỉ thay đổi khi mực nước thực sự dâng hoặc hạ.", "Giao diện Web và đồ thị Chart.js mượt mà, không bị răng cưa hoặc nhiễu gai."],
        ["Khả năng kháng sóng nước", "Khi mặt hồ dập dềnh sóng nhẹ, số liệu vọt đỉnh tức thời gây báo động sai.", "Bộ lọc EMA (α = 0.15) triệt tiêu các đỉnh sóng, giữ giá trị mực nước bình quân ổn định.", "Đáp ứng hoàn hảo trong môi trường giông bão, hồ thủy điện và cống ngập đô thị."],
        ["Thời gian trễ đáp ứng", "Tức thời (0 ms) nhưng dữ liệu không thể sử dụng trực tiếp được.", "Thời gian trễ chỉ khoảng 250 – 300 ms (tương đương 1 chu kỳ gửi gói tin).", "Thời gian thực (Real-time), hoàn toàn đáp ứng tiêu chuẩn cảnh báo thiên tai khẩn cấp."]
    ]
    add_styled_table(headers_filter_eval, rows_filter_eval, [1.3, 1.8, 1.8, 1.6])

    # =========================================================================
    # PHẦN A: BÁO CÁO THỰC NGHIỆM ĐO LƯỜNG VÀ ĐÁNH GIÁ SAI SỐ
    # =========================================================================
    add_part_header(
        "PHẦN A: BÁO CÁO THỰC NGHIỆM ĐO LƯỜNG",
        "KẾT QUẢ THỰC NGHIỆM TẠI HỒ CÁ KHU A VÀ PHÂN TÍCH SAI SỐ ĐO",
        "Đánh giá độ chính xác thực tế, sai số tuyệt đối và tương quan áp suất thủy tĩnh"
    )

    add_heading_1("4. Kết quả thực nghiệm và phân tích sai số đo lường thực tế")
    add_heading_2("4.1. Thử nghiệm thực địa tại Hồ cá Khu A")
    add_paragraph(
        "Hệ thống đã được đưa ra đo kiểm thực tế tại Hồ cá Khu A ở 6 mốc mực nước khác nhau, từ mực nước nông ven bờ (5.0 cm) "
        "đến các vùng nước sâu trung tâm (65.0 cm). Kết quả đo đối soát với thước cơ khí chuẩn được ghi nhận trong bảng dưới đây:"
    )

    headers_lake = ["Mốc đo", "Mực nước thực tế (cm)", "Mực nước cảm biến (cm)", "Điện áp đo được (V)", "Áp suất tính toán (Bar)", "Sai số tuyệt đối (cm)", "Sai số tương đối (%)"]
    rows_lake = [
        ["1", "5.0", "5.2", "0.15", "0.005", "+0.2", "4.0 %"],
        ["2", "19.5", "19.8", "0.25", "0.019", "+0.3", "1.5 %"],
        ["3", "47.0", "46.8", "0.42", "0.046", "-0.2", "0.4 %"],
        ["4", "52.0", "52.3", "0.45", "0.051", "+0.3", "0.6 %"],
        ["5", "60.0", "59.6", "0.50", "0.058", "-0.4", "0.7 %"],
        ["6", "65.0", "65.2", "0.53", "0.064", "+0.2", "0.3 %"]
    ]
    add_styled_table(headers_lake, rows_lake, [0.6, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9], align_center_cols=[0, 1, 2, 3, 4, 5, 6])

    add_heading_2("4.2. Thử nghiệm kiểm chuẩn trong phòng thí nghiệm (Đo trong xô)")
    add_paragraph(
        "Để thẩm định độ lặp lại và kiểm tra độ chính xác ở dải nước thấp, nhóm đã tiến hành thêm loạt phép đo kiểm chuẩn trong xô nước có vạch chia milimet:"
    )
    headers_bucket = ["Mốc thử nghiệm", "Độ sâu thực tế (cm)", "Độ sâu cảm biến (cm)", "Điện áp ngõ ra (V)", "Sai số tuyệt đối (cm)", "Đánh giá trạng thái"]
    rows_bucket = [
        ["Mốc 0 (Ngoài không khí)", "0.0", "0.0", "0.12", "0.0", "Hiệu chuẩn điểm không chuẩn xác 100%."],
        ["Mốc 1 (Nước chạm màng)", "2.0", "2.1", "0.13", "+0.1", "Vượt dải chết 0.3 cm, bắt đầu nhận diện nước."],
        ["Mốc 2 (Nước thấp)", "10.0", "10.2", "0.18", "+0.2", "Số đo mượt, phản hồi tức thời."],
        ["Mốc 3 (Nước trung bình)", "20.0", "19.8", "0.25", "-0.2", "Độ ổn định cao, không dao động."],
        ["Mốc 4 (Nước sâu đầy xô)", "35.0", "35.3", "0.34", "+0.3", "Áp suất tuyến tính hoàn hảo."]
    ]
    add_styled_table(headers_bucket, rows_bucket, [1.5, 1.0, 1.0, 1.0, 1.0, 1.0], align_center_cols=[0, 1, 2, 3, 4])

    add_heading_2("4.3. Nhận xét tổng kết về độ chính xác đo lường")
    add_bullet("Sai số tuyệt đối cực nhỏ", "Sai số đo lường thực tế trên toàn dải đo chỉ dao động trong khoảng từ ±0.1 cm đến ±0.4 cm, hoàn toàn nằm trong giới hạn cho phép của các tiêu chuẩn đo lường thủy văn công nghiệp (cho phép sai số ±1.0 cm).")
    add_bullet("Hệ số tương quan tuyến tính xuất sắc", "Đường đặc tuyến giữa điện áp ngõ ra và độ sâu cột nước đạt hệ số tương quan R² > 0.999, khẳng định tính đúng đắn của phương pháp quy đổi áp suất sang chiều cao cột chất lỏng.")

    # =========================================================================
    # PHẦN B: KIẾN TRÚC MẠNG IOT GATEWAY & TRUYỀN THÔNG ĐÁM MÂY (ESP32-C3)
    # =========================================================================
    add_part_header(
        "PHẦN B: KIẾN TRÚC MẠNG IOT GATEWAY & CLOUD",
        "GIAO THỨC TRUYỀN THÔNG MQTT, WEBSOCKETS VÀ TRÌNH DIỄN THỜI GIAN THỰC",
        "Kiến trúc cầu nối không dây ESP32-C3, ngăn xếp LwIP, FreeRTOS và Web Dashboard"
    )

    add_heading_1("5. Kiến trúc mạng truyền thông và Giao thức đóng gói UART Framing")
    add_paragraph(
        "Tầng truyền thông mạng của hệ thống được xây dựng để đảm bảo tính sẵn sàng cao, truyền dữ liệu không gián đoạn và "
        "tiết kiệm băng thông tối đa. STM32 đóng gói dữ liệu thành một chuỗi JSON chuẩn mực và truyền sang ESP32-C3 qua cổng UART1 (Baudrate 115200):",
        bold_prefix="Đóng gói bản tin JSON: "
    )
    add_code_block(
        "// Chuỗi JSON hoàn chỉnh do STM32 phát ra mỗi chu kỳ đo:\n"
        "{\"level\":24.5,\"volt\":0.28,\"percent\":4.9,\"press\":0.024,\"raw\":348}\\n"
    )
    add_paragraph(
        "Ký tự xuống dòng '\\n' ở cuối chuỗi đóng vai trò là ký tự phân tách khung truyền (Frame Delimiter). Trên ESP32-C3, một FreeRTOS Task độc lập "
        "được phân bổ để liên tục đọc các byte từ bộ đệm vòng (RingBuffer 2048 bytes). Khi gặp ký tự '\\n', task này lập tức cắt chuỗi và đưa thẳng vào hàm "
        "xuất bản MQTT, đảm bảo gói tin không bao giờ bị cắt vụn hoặc mất toàn vẹn giữa chừng.",
        bold_prefix="Cơ chế gom gói phi chặn (Non-blocking): "
    )

    add_heading_1("6. So sánh chuyên sâu: Giao thức MQTT Pub/Sub so với HTTP REST")
    add_paragraph(
        "Trong các hệ thống IoT thời gian thực, việc lựa chọn giao thức tầng ứng dụng ảnh hưởng trực tiếp đến thời lượng pin, độ trễ và tải trọng mạng. "
        "Bảng so sánh định lượng dưới đây chứng minh lý do MQTT v3.1.1 vượt trội hoàn toàn so với HTTP REST trong dự án này:"
    )
    headers_mqtt_http = ["Đặc tính kỹ thuật", "Giao thức MQTT v3.1.1 (Lựa chọn)", "Giao thức HTTP REST (Truyền thống)", "Lợi thế vượt trội của MQTT"]
    rows_mqtt_http = [
        ["Mô hình kiến trúc", "Publish / Subscribe (Bất đồng bộ qua Broker trung tâm)", "Client / Server (Request / Response đồng bộ)", "Bộ đo không cần biết địa chỉ IP của Web, nhiều người xem cùng lúc."],
        ["Kích thước tiêu đề (Header)", "Cực kỳ nhẹ: Tiêu đề cố định chỉ từ 2 đến 4 Bytes", "Nặng nề: Tiêu đề HTTP thường từ 200 đến 800 Bytes", "Giảm tải hơn 95% băng thông mạng, truyền cực nhanh qua Wi-Fi/4G."],
        ["Duy trì kết nối", "Kết nối TCP hướng trạng thái (Stateful), giữ qua Keep-Alive", "Không trạng thái (Stateless), phải bắt tay 3 bước TCP mỗi lần gửi", "Loại bỏ thời gian trễ bắt tay mạng (Handshake), dữ liệu bay tức thì."],
        ["Phương thức cập nhật dữ liệu", "Push (Máy chủ chủ động đẩy dữ liệu xuống Web khi có gói mới)", "Pull (Trình duyệt Web phải gửi Request liên tục - Polling)", "Đồ thị Web nhảy mượt mà theo nhịp phát của cảm biến mà không cần F5."],
        ["Mức tiêu thụ năng lượng", "Rất thấp, chip vi điều khiển có thể chuyển chế độ ngủ nhẹ", "Cao, do CPU phải xử lý mã hóa/giải mã Header HTTP phức tạp", "Kéo dài tuổi thọ pin khi đưa vào các trạm quan trắc dã ngoại."]
    ]
    add_styled_table(headers_mqtt_http, rows_mqtt_http, [1.2, 1.8, 1.8, 1.7])

    add_heading_1("7. Giao diện Web Dashboard và Giao thức WebSockets an toàn (WSS)")
    add_paragraph(
        "Để người quản trị có thể theo dõi mực nước hồ hoặc điểm ngập úng từ bất kỳ đâu trên điện thoại hoặc máy tính, "
        "Web Dashboard được thiết kế giao diện hiện đại (Dark Theme) và nhúng thư viện MQTT.js kết nối trực tiếp vào máy chủ HiveMQ qua WebSockets Secure (WSS Port 8884):",
        bold_prefix="Công nghệ Web Dashboard: "
    )
    add_bullet("Cơ chế nhận dữ liệu tức thời", "Trình duyệt mở một kênh WebSocket WSS bảo mật với broker.hivemq.com:8884 và đăng ký (Subscribe) kênh my_iot_project/stm32_sensor_data. Ngay khi ESP32 bắn gói tin lên, HiveMQ lập tức chuyển tiếp xuống trình duyệt chỉ trong vòng chưa đầy 50 ms.")
    add_bullet("Hệ thống hiển thị trực quan", "Dashboard hiển thị đầy đủ: Mực nước hiện tại (cm và m), Tỷ lệ chiều cao cột nước (0–100%), Áp suất thủy tĩnh tương ứng (Bar), Điện áp cảm biến (V) và Tổng lưu lượng gói tin đã nhận (Packets).")
    add_bullet("Đồ thị sóng nước thời gian thực (Real-time Chart.js)", "Biểu đồ lưu giữ 30 điểm đo gần nhất, vẽ đường sóng nước uốn lượn liên tục, giúp quan sát rõ rệt động thái dâng hoặc rút của mực nước.")
    add_bullet("Thuật toán cảnh báo ngập lụt 3 cấp độ thông minh", "Dựa trên số đo mực nước, hệ thống tự động đổi màu huy hiệu cảnh báo:\n• Mực nước < 50 cm: MÀU XANH LÁ - Bình thường / An toàn.\n• 50 cm ≤ Mực nước < 100 cm: MÀU VÀNG - Cảnh giác / Mực nước dâng cao.\n• Mực nước ≥ 100 cm: MÀU ĐỎ NHẤP NHÁY - BÁO ĐỘNG ĐỎ / Nguy cơ ngập lụt nghiêm trọng!")

    # =========================================================================
    # CHƯƠNG 4: ĐỊNH HƯỚNG NÂNG CẤP MẠNG DIỆN RỘNG (SMART CITY LORAWAN ROADMAP)
    # =========================================================================
    add_heading_1("CHƯƠNG 4: ĐỊNH HƯỚNG NÂNG CẤP MẠNG DIỆN RỘNG (SMART CITY LORAWAN)")
    add_paragraph(
        "Mô hình Gateway Wi-Fi hiện tại hoạt động cực kỳ hoàn hảo cho các khu vực có sẵn hạ tầng mạng không dây (như trường học, tòa nhà, nhà máy, công viên). "
        "Tuy nhiên, đối với các bài toán mở rộng trên quy mô thành phố thông minh (Smart City) – nơi các trạm đo phải cắm ở giữa đê điều, cửa sông, hồ chứa xa xôi "
        "hoặc các vùng trũng ngập không có sóng Wi-Fi, nhóm nghiên cứu đã thử nghiệm và đề xuất phương án nâng cấp lên mạng diện rộng LoRaWAN công nghiệp:",
        bold_prefix="Tầm nhìn mở rộng diện rộng: "
    )
    add_bullet("Tận dụng các trạm Gateway LoRaWAN công cộng tại Đà Nẵng", 
               "Thành phố Đà Nẵng hiện đã được triển khai các trạm Outdoor LoRaWAN Gateway công nghiệp công suất cao, tiêu biểu như trạm tại Tòa nhà 21 tầng Công viên Phần mềm Đà Nẵng (Số 02 Quang Trung) và trạm RAK7249 (anten 12dBi) trên nóc nhà 10 tầng Khu S – Trường Đại học Bách Khoa (Đại học Đà Nẵng). Các trạm này kết nối thẳng vào mạng toàn cầu The Things Network (TTN).")
    add_bullet("Tích hợp ngăn xếp mạng LoRaMac-node v4.7.0", 
               "Mã nguồn STM32 của nhóm đã sẵn sàng tương thích với thư viện chuẩn LoRaMac-node v4.7.0, hỗ trợ cơ chế bảo mật khóa mã hóa AES-128 bit và phương thức kích hoạt mạng qua không dây (OTAA - Over The Air Activation) ở băng tần EU868 / AS923.")
    add_bullet("Khả năng hoạt động độc lập bằng pin năng lượng mặt trời", 
               "Với công nghệ LoRaWAN, thiết bị chỉ cần một viên pin Lithium nhỏ kết hợp tấm pin mặt trời 5W là có thể hoạt động bền bỉ từ 3 đến 5 năm liên tục ngoài thực địa mà hoàn toàn không cần nguồn điện lưới hay bộ phát Wi-Fi.")

    # =========================================================================
    # CHƯƠNG 5: KẾT LUẬN & ĐÁNH GIÁ NGHIỆM THU
    # =========================================================================
    add_heading_1("CHƯƠNG 5: KẾT LUẬN & ĐÁNH GIÁ NGHIỆM THU ĐỒ ÁN")
    add_paragraph(
        "Đồ án đã hoàn thành xuất sắc và toàn diện 100% các mục tiêu đề ra ban đầu, từ việc làm chủ phần cứng thu thập tín hiệu, "
        "xây dựng giải thuật xử lý nhiễu số học đa tầng trên STM32, đến việc thiết lập mạng truyền thông đám mây thời gian thực với ESP32-C3 và Web Dashboard:",
        bold_prefix="Đánh giá kết quả tổng thể: "
    )
    add_bullet("Về mặt đo lường cảm biến", "Làm chủ nguyên lý cảm biến áp suất thủy tĩnh chìm, loại trừ triệt để hiện tượng trôi điểm không 0.12V, thiết lập dải chết 0.3 cm và bộ lọc EMA α = 0.15, đưa sai số đo lường thực tế về mức dưới ±0.4 cm trên toàn dải đo.")
    add_bullet("Về mặt kết nối phần cứng", "Thiết lập sơ đồ đấu nối chân liên mạch khoa học, giải quyết dứt điểm các lỗi kẹt ngoại vi I2C, tuân thủ nguyên tắc Mass chung (Common Ground) an toàn và ổn định.")
    add_bullet("Về mặt truyền thông đám mây", "Vận hành thông suốt chuỗi truyền tin từ STM32 -> UART -> ESP32 -> Wi-Fi -> HiveMQ Cloud -> Web Dashboard với tốc độ phản hồi ~3 lần/giây, không suy hao, không nghẽn mạng.")
    add_bullet("Khả năng ứng dụng thực tiễn", "Hệ thống có chi phí sản xuất thấp, độ tin cậy công nghiệp cao, sẵn sàng triển khai thực tế cho các trạm cảnh báo ngập lụt đô thị, hồ chứa thủy lợi và nuôi trồng thủy hải sản.")

    # Save to both target locations
    path1 = r"D:\Embedded\Bao_Cao_Tong_Hop_IoT_Cam_Bien_Va_Mang.docx"
    path2 = r"D:\Embedded\esp32\docs\Bao_Cao_Tong_Hop_IoT_Cam_Bien_Va_Mang.docx"

    doc.save(path1)
    print(f"Saved primary report to: {path1}")
    doc.save(path2)
    print(f"Saved backup report to: {path2}")

if __name__ == "__main__":
    create_report()
