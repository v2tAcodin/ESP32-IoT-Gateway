import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_hardware_block_diagram(output_path):
    fig, ax = plt.subplots(figsize=(17, 9.5), dpi=300)
    ax.set_facecolor("#F8FAFC")
    fig.patch.set_facecolor("#F8FAFC")

    # =========================================================================
    # 1. TIÊU ĐỀ & PHỤ ĐỀ SƠ ĐỒ
    # =========================================================================
    fig.suptitle(
        "SƠ ĐỒ KHỐI KẾT NỐI PHẦN CỨNG HỆ THỐNG IOT GIÁM SÁT MỰC NƯỚC (STM32 & ESP32-C3)",
        fontsize=16,
        fontweight="bold",
        color="#0F172A",
        y=0.968
    )

    ax.text(
        0.5, 0.932,
        "Mô hình liên kết các khối phần cứng vật lý: Khối Cấp Nguồn • Khối Cảm Biến Thủy Tĩnh • Khối Đo Lường Biên (STM32) • Khối Gateway (ESP32) • Khối Thu Phát Vô Tuyến RF",
        ha="center", va="center", fontsize=10, fontstyle="italic", color="#475569", transform=ax.transAxes
    )

    # =========================================================================
    # 2. HÀM VẼ KHỐI PHẦN CỨNG CHUYÊN NGHIỆP
    # =========================================================================
    def draw_module(x, y, w, h, title, subtitle, header_color, bg_color, items, border_color=None):
        if not border_color:
            border_color = header_color
        
        # Thân khối
        body = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.012,rounding_size=0.018",
            facecolor=bg_color, edgecolor=border_color,
            linewidth=1.8, transform=ax.transAxes, zorder=2
        )
        ax.add_patch(body)

        # Thanh tiêu đề khối
        header_h = 0.075
        header = patches.FancyBboxPatch(
            (x, y + h - header_h), w, header_h,
            boxstyle="round,pad=0.012,rounding_size=0.018",
            facecolor=header_color, edgecolor=header_color,
            linewidth=1, transform=ax.transAxes, zorder=3
        )
        ax.add_patch(header)

        # Chữ tiêu đề & phụ đề
        ax.text(
            x + w / 2.0, y + h - 0.026,
            title,
            ha="center", va="center", fontsize=9.2, fontweight="bold",
            color="#FFFFFF", transform=ax.transAxes, zorder=4
        )
        ax.text(
            x + w / 2.0, y + h - 0.053,
            subtitle,
            ha="center", va="center", fontsize=7.5, fontstyle="italic",
            color="#F1F5F9", transform=ax.transAxes, zorder=4
        )

        # Các mục chi tiết bên trong khối
        y_cursor = y + h - header_h - 0.024
        for it in items:
            badge_title, badge_desc, b_col, b_bg, badge_h = it
            badge = patches.FancyBboxPatch(
                (x + 0.010, y_cursor - badge_h), w - 0.020, badge_h,
                boxstyle="round,pad=0.006,rounding_size=0.010",
                facecolor=b_bg, edgecolor="#CBD5E1",
                linewidth=0.8, transform=ax.transAxes, zorder=3
            )
            ax.add_patch(badge)
            ax.text(
                x + 0.018, y_cursor - 0.013,
                badge_title,
                ha="left", va="center", fontsize=7.6, fontweight="bold",
                color=b_col, transform=ax.transAxes, zorder=4
            )
            ax.text(
                x + 0.018, y_cursor - 0.029,
                badge_desc,
                ha="left", va="center", fontsize=6.8,
                color="#475569", transform=ax.transAxes, zorder=4
            )
            y_cursor -= (badge_h + 0.011)

    # =========================================================================
    # 3. ĐỊNH NGHĨA TỌA ĐỘ VÀ VẼ CÁC KHỐI PHẦN CỨNG
    # =========================================================================

    x_col1 = 0.035   # Khối Nguồn & Cảm biến (w = 0.20)
    w_col1 = 0.20

    x_col2 = 0.295   # Khối STM32F103 (w = 0.27)
    w_col2 = 0.27

    x_col3 = 0.620   # Khối ESP32-C3 (w = 0.24)
    w_col3 = 0.24

    x_col4 = 0.885   # Khối RF Không Dây (w = 0.088)
    w_col4 = 0.088

    # --- KHỐI 1A: KHỐI CẤP NGUỒN ĐA MỨC (Y: 0.57 -> 0.89, H = 0.32) ---
    draw_module(
        x=x_col1, y=0.57, w=w_col1, h=0.32,
        title="KHỐI CẤP NGUỒN ĐA MỨC",
        subtitle="(POWER SUPPLY UNIT)",
        header_color="#DC2626", bg_color="#FEF2F2",
        items=[
            ("Adapter 12V DC / 2A", "Nguồn nuôi công nghiệp cho đầu dò áp suất", "#DC2626", "#FFFFFF", 0.043),
            ("Nguồn Cấp USB 5V DC", "Cấp cho bo STM32 và ESP32 qua cáp nạp", "#D97706", "#FFFFFF", 0.043),
            ("Mạch Hạ Áp LDO 3.3V DC", "Cung cấp điện áp ổn định cho vi điều khiển", "#2563EB", "#FFFFFF", 0.043),
            ("Tuyến Mass Chung (0V)", "Common GND liên kết đồng mức tham chiếu", "#0F172A", "#F1F5F9", 0.043)
        ]
    )

    # --- KHỐI 1B: KHỐI CẢM BIẾN THỦY TĨNH (Y: 0.17 -> 0.49, H = 0.32) ---
    draw_module(
        x=x_col1, y=0.17, w=w_col1, h=0.32,
        title="KHỐI CẢM BIẾN THỦY TĨNH",
        subtitle="(SUBMERSIBLE LEVEL SENSOR)",
        header_color="#0284C7", bg_color="#F0F9FF",
        items=[
            ("Chân Tín Hiệu: OUT (Analog)", "Điện áp ngõ ra tuyến tính 0.00V – 3.30V DC", "#D97706", "#FFFBEB", 0.044),
            ("Đầu Dò Thả Chìm Inox 316L", "Màng silicon piezo-resistive (Pascal P=ρ·g·h)", "#0284C7", "#FFFFFF", 0.043),
            ("Thang Đo Mực Nước: 0 – 5m", "Áp suất 0–0.5 Bar (0–500 cm nước)", "#0369A1", "#FFFFFF", 0.043),
            ("Cực Nguồn Nuôi Cảm Biến", "Dây Đỏ (+12V DC) / Dây Đen (Mass GND)", "#DC2626", "#FFFFFF", 0.043)
        ]
    )

    # --- KHỐI 2: KHỐI VI ĐIỀU KHIỂN XỬ LÝ BIÊN (STM32F103) (Y: 0.17 -> 0.89, H = 0.72) ---
    # Chân PA0 được đặt ở vị trí thứ 6 để thẳng hàng tuyệt đối với Chân OUT của Cảm Biến
    draw_module(
        x=x_col2, y=0.17, w=w_col2, h=0.72,
        title="KHỐI ĐO LƯỜNG & XỬ LÝ BIÊN",
        subtitle="EDGE MCU: STM32F103C8T6 (ARM CORTEX-M3 @ 72 MHz)",
        header_color="#0F766E", bg_color="#F0FDFA",
        items=[
            ("Bộ Xử Lý ARM Cortex-M3", "72 MHz, 64KB Flash, 20KB SRAM, DMA Engine", "#0F766E", "#FFFFFF", 0.042),
            ("Cổng Nạp SWD (PA13/PA14)", "ST-Link V2 Programming & Debug thời gian thực", "#64748B", "#FFFFFF", 0.042),
            ("Chân PC13 (Heartbeat LED)", "Nhấp nháy nhịp tim chu kỳ 1s (Active-Low)", "#E11D48", "#FFFFFF", 0.042),
            ("Chân PA9 (USART1_TX)", "Truyền chuỗi JSON sang ESP32 (115200 8N1)", "#059669", "#ECFDF5", 0.045),
            ("Chân PA10 (USART1_RX)", "Nhận lệnh phản hồi / cấu hình từ Gateway", "#2563EB", "#EFF6FF", 0.045),
            ("Chân PA0 (ADC1_IN0)", "Nhận áp Analog 0–3.3V từ Cảm biến (12-bit ADC)", "#D97706", "#FFFBEB", 0.045),
            ("Thuật Toán Xử Lý Số 4 Tầng", "Auto-Calib + Oversample 32x + Bù 0.12V + EMA", "#0F766E", "#FFFFFF", 0.042),
            ("Chân Nguồn: 3.3V, 5V & GND", "Được bảo vệ chống ESD và chống sụt áp", "#0F172A", "#F1F5F9", 0.042)
        ]
    )

    # --- KHỐI 3: KHỐI CẦU NỐI IOT GATEWAY (ESP32-C3) (Y: 0.17 -> 0.89, H = 0.72) ---
    draw_module(
        x=x_col3, y=0.17, w=w_col3, h=0.72,
        title="KHỐI CẦU NỐI IOT GATEWAY",
        subtitle="WIRELESS GATEWAY: ESP32-C3 (RISC-V @ 160 MHz)",
        header_color="#4338CA", bg_color="#EEF2FF",
        items=[
            ("Lõi RISC-V 32-bit Single-Core", "160 MHz, 400KB SRAM, 4MB Flash tích hợp", "#4338CA", "#FFFFFF", 0.042),
            ("Cổng USB Type-C (5V DC)", "Nguồn cấp và nạp Firmware / Log console", "#D97706", "#FFFFFF", 0.042),
            ("Khối Wi-Fi 2.4 GHz RF MAC", "Baseband 802.11 b/g/n, công suất phát +20dBm", "#7C3AED", "#FAF5FF", 0.042),
            ("Chân GPIO 4 (UART1_RX)", "Lắng nghe gói JSON từ STM32 (115200 8N1)", "#059669", "#ECFDF5", 0.045),
            ("Chân GPIO 5 (UART1_TX)", "Phát lệnh điều khiển / ACK sang STM32", "#2563EB", "#EFF6FF", 0.045),
            ("Bộ Đệm RingBuffer 2048 B", "FreeRTOS Task gom gói theo ký tự '\\n'", "#4338CA", "#FFFFFF", 0.042),
            ("Ngăn Xếp Mạng LwIP & MQTT", "Client MQTT v3.1.1 (Topic: stm32_sensor_data)", "#B45309", "#FFFFFF", 0.042),
            ("Chân Nguồn: 5V, 3.3V & GND", "Mass nối thông với Common Ground 0V", "#0F172A", "#F1F5F9", 0.042)
        ]
    )

    # --- KHỐI 4: KHỐI THU PHÁT VÔ TUYẾN RF (Y: 0.28 -> 0.81, H = 0.53) ---
    draw_module(
        x=x_col4, y=0.28, w=w_col4, h=0.53,
        title="KHỐI RF",
        subtitle="WIRELESS",
        header_color="#7C3AED", bg_color="#FAF5FF",
        items=[
            ("Ăng-ten PCB", "2.4 GHz tích hợp", "#7C3AED", "#FFFFFF", 0.043),
            ("Wi-Fi STA", "802.11 b/g/n", "#7C3AED", "#FFFFFF", 0.043),
            ("Phát Cloud", "HiveMQ Broker", "#B45309", "#FFFFFF", 0.043),
            ("Mở Rộng:", "LoRa RFM95", "#64748B", "#FFFFFF", 0.043),
            ("Băng Tần", "868 / 915 MHz", "#64748B", "#FFFFFF", 0.043)
        ]
    )

    # =========================================================================
    # 4. VẼ CÁC ĐƯỜNG KẾT NỐI VẬT LÝ & BUS GIAO TIẾP
    # =========================================================================

    # --- 4.1. Tuyến Nguồn +12V DC từ Khối Nguồn xuống Cảm biến ---
    ax.annotate(
        "", xy=(x_col1 + w_col1 / 2.0, 0.49), xytext=(x_col1 + w_col1 / 2.0, 0.57),
        xycoords="axes fraction", textcoords="axes fraction",
        arrowprops=dict(arrowstyle="->", color="#DC2626", lw=2.8)
    )
    ax.text(
        x_col1 + w_col1 / 2.0, 0.530,
        "ĐƯỜNG NGUỒN +12V DC (DÂY ĐỎ)",
        color="#DC2626", fontsize=7.2, fontweight="bold", ha="center", va="center",
        bbox=dict(boxstyle="round,pad=0.22", facecolor="#FEF2F2", edgecolor="#FECACA", lw=0.9),
        zorder=5
    )

    # --- 4.2. Tuyến Nguồn 5V USB từ Khối Nguồn sang STM32 và ESP32 ---
    ax.plot([x_col1 + w_col1, 0.260, 0.260, x_col2], [0.73, 0.73, 0.81, 0.81],
            color="#D97706", lw=2.0, linestyle="-", transform=ax.transAxes, zorder=5)
    ax.annotate(
        "", xy=(x_col2, 0.81), xytext=(0.260, 0.81),
        xycoords="axes fraction", textcoords="axes fraction",
        arrowprops=dict(arrowstyle="->", color="#D97706", lw=2.0)
    )
    ax.text(
        0.260, 0.835,
        "+5V USB",
        color="#D97706", fontsize=7.0, fontweight="bold", ha="center", va="center",
        bbox=dict(boxstyle="round,pad=0.15", facecolor="#FFFBEB", edgecolor="#FDE68A", lw=0.8),
        zorder=6
    )

    # --- 4.3. Tuyến Tín Hiệu Tương Tự (Analog) 0.00V - 3.30V (Sensor OUT -> STM32 PA0) ---
    # Cả Sensor OUT và STM32 PA0 đều nằm ở Y ~ 0.38 (ĐƯỜNG NỐI THẲNG NGANG HOÀN TOÀN!)
    y_analog = 0.382
    ax.annotate(
        "", xy=(x_col2, y_analog), xytext=(x_col1 + w_col1, y_analog),
        xycoords="axes fraction", textcoords="axes fraction",
        arrowprops=dict(arrowstyle="->", color="#D97706", lw=3.2),
        zorder=5
    )
    ax.text(
        (x_col1 + w_col1 + x_col2) / 2.0, y_analog + 0.044,
        "TÍN HIỆU ANALOG 0–3.3V\n(Sensor OUT → PA0)",
        color="#B45309", fontsize=7.2, fontweight="bold", ha="center", va="center",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#FFFBEB", edgecolor="#F59E0B", lw=1.1),
        zorder=6
    )

    # --- 4.4. Tuyến Truyền Thông UART PA9 (TX) -> GPIO 4 (RX) ---
    # STM32 PA9 ở y ~ 0.54, ESP32 GPIO 4 ở y ~ 0.54 (ngang hàng chính xác!)
    y_uart_tx = 0.54
    ax.annotate(
        "", xy=(x_col3, y_uart_tx), xytext=(x_col2 + w_col2, y_uart_tx),
        xycoords="axes fraction", textcoords="axes fraction",
        arrowprops=dict(arrowstyle="->", color="#059669", lw=3.2),
        zorder=5
    )
    ax.text(
        (x_col2 + w_col2 + x_col3) / 2.0, y_uart_tx + 0.046,
        "BUS UART (3.3V CMOS)\nBaud 115200 8N1 (JSON)\n(PA9 TX → GPIO 4 RX)",
        color="#047857", fontsize=7.2, fontweight="bold", ha="center", va="center",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#ECFDF5", edgecolor="#10B981", lw=1.1),
        zorder=6
    )

    # --- 4.5. Tuyến Phản Hồi UART Tùy Chọn GPIO 5 (TX) -> PA10 (RX) ---
    # ESP32 GPIO 5 ở y ~ 0.44, STM32 PA10 ở y ~ 0.44 (ngang hàng chính xác!)
    y_uart_rx = 0.44
    ax.annotate(
        "", xy=(x_col2 + w_col2, y_uart_rx), xytext=(x_col3, y_uart_rx),
        xycoords="axes fraction", textcoords="axes fraction",
        arrowprops=dict(arrowstyle="->", color="#2563EB", lw=2.0, linestyle="--"),
        zorder=5
    )
    ax.text(
        (x_col2 + w_col2 + x_col3) / 2.0, y_uart_rx - 0.038,
        "Lệnh Phản Hồi / ACK\n(GPIO 5 TX → PA10 RX)",
        color="#1D4ED8", fontsize=6.8, fontstyle="italic", ha="center", va="center",
        bbox=dict(boxstyle="round,pad=0.18", facecolor="#EFF6FF", edgecolor="#93C5FD", lw=0.8),
        zorder=6
    )

    # --- 4.6. Tuyến RF từ ESP32 sang Khối Ăng-ten và Sóng Ra Ngoài ---
    y_rf = 0.65
    ax.annotate(
        "", xy=(x_col4, y_rf), xytext=(x_col3 + w_col3, y_rf),
        xycoords="axes fraction", textcoords="axes fraction",
        arrowprops=dict(arrowstyle="->", color="#7C3AED", lw=2.8),
        zorder=5
    )
    ax.text(
        (x_col3 + w_col3 + x_col4) / 2.0, y_rf + 0.034,
        "Đường RF\n50Ω",
        color="#7C3AED", fontsize=6.8, fontweight="bold", ha="center", va="center"
    )

    # Vẽ sóng vô tuyến phát ra ngoài không gian
    for offset in [0.012, 0.024, 0.036]:
        arc = patches.Arc(
            (x_col4 + w_col4 + 0.005, y_rf), offset * 2.2, offset * 2.2,
            angle=0, theta1=-45, theta2=45,
            color="#7C3AED", lw=2.2, transform=ax.transAxes
        )
        ax.add_patch(arc)
    ax.text(
        x_col4 + w_col4 + 0.032, y_rf,
        "Sóng Wi-Fi\n2.4 GHz\n(STA Mode)",
        color="#6D28D9", fontsize=7.4, fontweight="bold", ha="left", va="center", transform=ax.transAxes
    )

    # =========================================================================
    # 5. TUYẾN MASS CHUNG (COMMON GROUND BUS - 0V)
    # =========================================================================
    bus_y = 0.118
    # Đường bus ngang màu đen đậm ở đáy
    ax.plot([0.015, 0.850], [bus_y, bus_y], color="#0F172A", lw=3.8, linestyle="-", transform=ax.transAxes, zorder=6)
    
    # 1. Từ Nguồn 12V / Adapter (Đi vòng ngoài bên trái: x=0.015, không cắt xuyên qua khối Cảm biến!)
    ax.plot([x_col1, 0.015, 0.015], [0.60, 0.60, bus_y], color="#0F172A", lw=1.8, linestyle="--", transform=ax.transAxes, zorder=5)
    ax.plot(0.015, bus_y, marker="o", color="#0F172A", markersize=6, transform=ax.transAxes, zorder=7)
    ax.text(0.014, 0.45, "Mass 12V\n(0V DC)", color="#0F172A", fontsize=6.5, fontweight="bold", ha="right", va="center")

    # 2. Từ Cảm Biến Thủy Tĩnh (Thả thẳng từ đáy khối Cảm biến)
    x_gnd_sensor = x_col1 + w_col1 / 2.0
    ax.plot([x_gnd_sensor, x_gnd_sensor], [0.17, bus_y], color="#0F172A", lw=1.8, linestyle="--", transform=ax.transAxes, zorder=5)
    ax.plot(x_gnd_sensor, bus_y, marker="o", color="#0F172A", markersize=6, transform=ax.transAxes, zorder=7)

    # 3. Từ STM32 (Thả thẳng từ đáy khối STM32)
    x_gnd_stm32 = x_col2 + w_col2 / 2.0
    ax.plot([x_gnd_stm32, x_gnd_stm32], [0.17, bus_y], color="#0F172A", lw=1.8, linestyle="--", transform=ax.transAxes, zorder=5)
    ax.plot(x_gnd_stm32, bus_y, marker="o", color="#0F172A", markersize=6, transform=ax.transAxes, zorder=7)

    # 4. Từ ESP32 (Thả thẳng từ đáy khối ESP32)
    x_gnd_esp32 = x_col3 + w_col3 / 2.0
    ax.plot([x_gnd_esp32, x_gnd_esp32], [0.17, bus_y], color="#0F172A", lw=1.8, linestyle="--", transform=ax.transAxes, zorder=5)
    ax.plot(x_gnd_esp32, bus_y, marker="o", color="#0F172A", markersize=6, transform=ax.transAxes, zorder=7)

    # Nhãn thanh Bus Mass chung với khung nền OPAQUE che đường kẻ bên dưới
    ax.text(
        0.440, bus_y,
        "   THANH BUS MASS CHUNG TOÀN HỆ THỐNG (COMMON GROUND BUS: 0V REFERENCE)   ",
        color="#0F172A", fontsize=8.0, fontweight="bold", ha="center", va="center",
        bbox=dict(boxstyle="round,pad=0.28", facecolor="#E2E8F0", edgecolor="#334155", lw=1.4),
        zorder=8
    )

    # =========================================================================
    # 6. KHUNG LƯU Ý KỸ THUẬT PHẦN CỨNG BẮT BUỘC (BOTTOM NOTICE CALLOUT)
    # =========================================================================
    callout = patches.FancyBboxPatch(
        (0.025, 0.018), 0.955, 0.065,
        boxstyle="round,pad=0.01,rounding_size=0.012",
        facecolor="#FEF3C7", edgecolor="#F59E0B",
        linewidth=1.3, transform=ax.transAxes, zorder=2
    )
    ax.add_patch(callout)

    notice_text = (
        "QUY TẮC THIẾT KẾ PHẦN CỨNG BẮT BUỘC:\n"
        "1. ĐẤU NỐI COMMON GND: Phải nối thông điểm 0V giữa Nguồn 12V, Cảm biến, STM32 và ESP32 để triệt tiêu nhiễu thả nổi và sai số đo ADC.\n"
        "2. TƯƠNG THÍCH MỨC ĐIỆN ÁP: Tín hiệu cảm biến 0–3.3V tương thích trực tiếp ngõ vào PA0 (ADC 12-bit); Giao tiếp UART PA9 ↔ GPIO 4 chuẩn 3.3V CMOS an toàn 100%."
    )
    ax.text(
        0.5, 0.050,
        notice_text,
        ha="center", va="center", fontsize=7.5, fontweight="bold", color="#92400E", transform=ax.transAxes, zorder=3
    )

    # =========================================================================
    # 7. HOÀN THIỆN VÀ XUẤT FILE
    # =========================================================================
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated hardware connection block diagram successfully at: {output_path}")

if __name__ == "__main__":
    out_dir = r"D:\Embedded\esp32\docs"
    out_file = os.path.join(out_dir, "hardware_block_diagram.png")
    draw_hardware_block_diagram(out_file)
    # Đồng thời ghi đè lên system_block_diagram.png để mọi liên kết cũ cũng tự động cập nhật
    draw_hardware_block_diagram(os.path.join(out_dir, "system_block_diagram.png"))
    # Và cả ở thư mục gốc esp32 nếu có
    if os.path.exists(r"D:\Embedded\esp32\system_block_diagram.png"):
        draw_hardware_block_diagram(r"D:\Embedded\esp32\system_block_diagram.png")
