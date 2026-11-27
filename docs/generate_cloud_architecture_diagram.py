import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

plt.rcParams["font.family"] = "DejaVu Sans"


def draw_layer_box(ax, x, y, w, h, label):
    """Draw a subtle dashed IEEE architectural layer boundary."""
    rect = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.002,rounding_size=0.010",
        facecolor="#F8FAFC", edgecolor="#94A3B8", linewidth=1.1, linestyle="--",
        transform=ax.transAxes, zorder=1
    )
    ax.add_patch(rect)
    ax.text(
        x + 0.012, y + h - 0.022, label,
        ha="left", va="center", fontsize=7.8, fontweight="bold",
        color="#475569", transform=ax.transAxes, zorder=2
    )


def draw_node(ax, x, y, w, h, title, subtitle, specs, accent="#1E3A5F"):
    """Draw a clean, low-text academic architecture block."""
    rect = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.002,rounding_size=0.008",
        facecolor="#FFFFFF", edgecolor=accent, linewidth=1.5,
        transform=ax.transAxes, zorder=3
    )
    ax.add_patch(rect)

    hh = 0.068
    header = patches.Rectangle(
        (x, y + h - hh), w, hh,
        facecolor="#F1F5F9", edgecolor="none",
        transform=ax.transAxes, zorder=3.5
    )
    ax.add_patch(header)
    ax.plot([x, x + w], [y + h - hh, y + h - hh], color=accent, lw=0.9, transform=ax.transAxes, zorder=4)

    ax.text(
        x + w / 2, y + h - 0.023, title,
        ha="center", va="center", fontsize=8.8, fontweight="bold",
        color="#0F172A", transform=ax.transAxes, zorder=5
    )
    ax.text(
        x + w / 2, y + h - 0.049, subtitle,
        ha="center", va="center", fontsize=7.3, fontstyle="italic",
        color="#475569", transform=ax.transAxes, zorder=5
    )

    if specs:
        usable_h = h - hh - 0.024
        step = usable_h / len(specs)
        y_top = y + h - hh - 0.014 - step / 2
        for i, sp in enumerate(specs):
            ax.text(
                x + 0.012, y_top - i * step, f"• {sp}",
                ha="left", va="center", fontsize=7.7, color="#1E293B",
                transform=ax.transAxes, zorder=5
            )


def draw_cloud_architecture_diagram(output_path):
    fig, ax = plt.subplots(figsize=(13.5, 6.8), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    ax.text(
        0.5, 0.962,
        "KIẾN TRÚC PHÂN TẦNG HỆ THỐNG IOT GIÁM SÁT MỰC NƯỚC CLOUD 24/7 (V3.0)",
        ha="center", va="center", fontsize=11.5, fontweight="bold",
        color="#0F172A", transform=ax.transAxes
    )

    # ================= LAYER CONTAINERS =================
    # Layer 1: Edge & Gateway (Top-Left to Top-Center)
    draw_layer_box(ax, 0.02, 0.54, 0.62, 0.37, "TẦNG BIÊN & GATEWAY (FIELD / EDGE LAYER)")
    # Layer 2: Cloud Broker (Top-Right)
    draw_layer_box(ax, 0.68, 0.54, 0.30, 0.37, "TẦNG ĐỊNH TUYẾN (BROKER LAYER)")
    # Layer 3: Cloud Backend & Storage (Bottom-Left)
    draw_layer_box(ax, 0.02, 0.05, 0.45, 0.40, "TẦNG XỬ LÝ & LƯU TRỮ 24/7 (CLOUD BACKEND)")
    # Layer 4: Application / Presentation (Bottom-Right)
    draw_layer_box(ax, 0.53, 0.05, 0.45, 0.40, "TẦNG ỨNG DỤNG & HIỂN THỊ (PRESENTATION LAYER)")

    # ================= NODES =================
    # 1. Edge Node (STM32)
    draw_node(
        ax, 0.04, 0.57, 0.25, 0.29,
        "EDGE NODE (STM32F103)", "Cảm biến thủy tĩnh 0–5 m",
        [
            "ADC 12-bit, lấy mẫu 32× (100 ms)",
            "Adaptive EMA + Deadband 0.2 cm",
            "Phát JSON 5 trường (chu kỳ 5s)"
        ]
    )

    # 2. IoT Gateway (ESP32-C3)
    draw_node(
        ax, 0.37, 0.57, 0.25, 0.29,
        "IOT GATEWAY (ESP32-C3)", "ESP-IDF / FreeRTOS",
        [
            "Robust UART Parser (2KB Buf)",
            "Wi-Fi Auto-Reconnect vô hạn",
            "MQTT QoS 1 + LWT & Heartbeat 15s"
        ]
    )

    # 3. HiveMQ Cloud Broker
    draw_node(
        ax, 0.70, 0.57, 0.26, 0.29,
        "MQTT BROKER (HIVEMQ)", "broker.hivemq.com",
        [
            "TCP 1883 (ESP32 ↔ Backend)",
            "WSS 8884 (TLS → Web Live)",
            "Topics: .../data & .../status"
        ],
        accent="#334155"
    )

    # 4. Render Cloud Backend (Gunicorn + Flask + SQLite WAL + UptimeRobot)
    draw_node(
        ax, 0.04, 0.08, 0.41, 0.32,
        "RENDER CLOUD BACKEND (SERVICE V3.0)", "esp32-iot-gateway.onrender.com (UptimeRobot 5p)",
        [
            "MQTT Worker: Dedup (<1s), Validate, Backoff 1–60s",
            "Gunicorn (1 worker) + SQLite WAL (UTC ms → UTC+7)",
            "REST API + Admin Token: /status, /measurements, /series",
            "Export: Excel 3-Sheet (.xlsx), CSV BOM, SQLite (.db)"
        ]
    )

    # 5. GitHub Pages Web Dashboard
    draw_node(
        ax, 0.55, 0.08, 0.41, 0.32,
        "WEB DASHBOARD (GITHUB PAGES)", "v2tacodin.github.io/ESP32-IoT-Gateway",
        [
            "Live WSS 30 điểm + Bền vững F5 (localStorage/SQLite)",
            "Cảnh báo Hysteresis (80/200 cm, Δ=5cm) & Fail-Safe (2p)",
            "Tra cứu CSDL Flatpickr (UTC+7) & Khóa khung giờ",
            "Tải báo cáo an toàn Fetch + Blob (.xlsx / .csv / .db)"
        ]
    )

    # ================= CLEAN ORTHOGONAL DATA FLOWS =================
    # 1. Edge -> Gateway (UART1)
    y_top_flow = 0.715
    ax.annotate(
        "", xy=(0.37, y_top_flow), xytext=(0.29, y_top_flow),
        xycoords="axes fraction", textcoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", color="#0F172A", lw=1.8), zorder=6
    )
    ax.text(0.33, y_top_flow + 0.022, "UART1\n115200", ha="center", va="bottom",
            fontsize=7.4, fontweight="bold", color="#0F172A", transform=ax.transAxes)

    # 2. Gateway -> HiveMQ (Wi-Fi / MQTT TCP 1883)
    ax.annotate(
        "", xy=(0.70, y_top_flow), xytext=(0.62, y_top_flow),
        xycoords="axes fraction", textcoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", color="#1E3A5F", lw=1.8), zorder=6
    )
    ax.text(0.66, y_top_flow + 0.025, "MQTT\nTCP:1883", ha="center", va="bottom",
            fontsize=7.0, fontweight="bold", color="#1E3A5F",
            bbox=dict(boxstyle="square,pad=0.12", facecolor="#FFFFFF", edgecolor="none"),
            transform=ax.transAxes, zorder=7)

    # 3. HiveMQ -> Render Backend (Subscribe TCP 1883) routed cleanly at x = 0.38 (clear of layer header!)
    y_mid_bus = 0.495
    x_drop_be = 0.39
    ax.plot([0.78, 0.78, x_drop_be, x_drop_be], [0.57, y_mid_bus, y_mid_bus, 0.40],
            color="#1E3A5F", lw=1.8, transform=ax.transAxes, zorder=5)
    ax.annotate(
        "", xy=(x_drop_be, 0.40), xytext=(x_drop_be, 0.43),
        xycoords="axes fraction", textcoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", color="#1E3A5F", lw=1.8), zorder=6
    )
    ax.text(
        0.585, y_mid_bus, "  MQTT Subscribe 24/7 (TCP 1883)  ",
        ha="center", va="center", fontsize=7.5, fontweight="bold", color="#1E3A5F",
        bbox=dict(boxstyle="square,pad=0.15", facecolor="#FFFFFF", edgecolor="none"),
        transform=ax.transAxes, zorder=7
    )

    # 4. HiveMQ -> Web Dashboard (WSS 8884 Live) — straight vertical arrow at x = 0.87
    ax.annotate(
        "", xy=(0.87, 0.40), xytext=(0.87, 0.57),
        xycoords="axes fraction", textcoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", color="#334155", lw=1.8), zorder=6
    )
    ax.text(
        0.882, 0.495, "WSS 8884\n(Live & LWT)",
        ha="left", va="center", fontsize=7.4, fontweight="bold", color="#334155", transform=ax.transAxes
    )

    # 5. Render Backend <-> Web Dashboard (HTTPS REST API + Blob)
    y_bot_flow = 0.24
    ax.annotate(
        "", xy=(0.55, y_bot_flow), xytext=(0.45, y_bot_flow),
        xycoords="axes fraction", textcoords="axes fraction",
        arrowprops=dict(arrowstyle="<->", color="#0F172A", lw=1.8), zorder=6
    )
    ax.text(0.50, y_bot_flow + 0.025, "HTTPS\nREST API", ha="center", va="bottom",
            fontsize=7.4, fontweight="bold", color="#0F172A", transform=ax.transAxes)
    ax.text(0.50, y_bot_flow - 0.022, "JSON / Blob", ha="center", va="top",
            fontsize=7.0, color="#475569", transform=ax.transAxes)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="#FFFFFF")
    plt.close()
    print(f"Generated IEEE-style cloud architecture diagram: {output_path}")


if __name__ == "__main__":
    draw_cloud_architecture_diagram(r"D:\Embedded\esp32\docs\cloud_architecture_v3.png")
