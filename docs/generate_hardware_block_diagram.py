import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# IEEE / Academic Minimalist Styling
plt.rcParams["font.family"] = "DejaVu Sans"


def draw_gnd_symbol(ax, x, y, color="#1E293B", scale=1.0):
    """Draw a standard IEC/IEEE electrical ground symbol at (x, y) in axes coordinates."""
    w1, w2, w3 = 0.011 * scale, 0.007 * scale, 0.003 * scale
    dy = 0.009 * scale
    ax.plot([x, x], [y, y - dy], color=color, lw=1.4, transform=ax.transAxes, zorder=6)
    ax.plot([x - w1, x + w1], [y - dy, y - dy], color=color, lw=1.6, transform=ax.transAxes, zorder=6)
    ax.plot([x - w2, x + w2], [y - 2 * dy, y - 2 * dy], color=color, lw=1.4, transform=ax.transAxes, zorder=6)
    ax.plot([x - w3, x + w3], [y - 3 * dy, y - 3 * dy], color=color, lw=1.2, transform=ax.transAxes, zorder=6)


def draw_antenna_symbol(ax, x, y, color="#1E3A5F"):
    """Draw a crisp IEEE RF antenna symbol pointing upward from (x, y)."""
    ax.plot([x, x], [y, y + 0.055], color=color, lw=1.8, transform=ax.transAxes, zorder=6)
    ax.plot([x - 0.016, x, x + 0.016], [y + 0.078, y + 0.042, y + 0.078], color=color, lw=1.6, transform=ax.transAxes, zorder=6)
    ax.plot([x - 0.016, x + 0.016], [y + 0.078, y + 0.078], color=color, lw=1.4, transform=ax.transAxes, zorder=6)
    # Minimal RF arcs
    for r in [0.022, 0.036]:
        arc = patches.Arc(
            (x + 0.018, y + 0.068), r * 1.4, r * 2.1,
            angle=0, theta1=-40, theta2=40,
            color="#475569", lw=1.3, transform=ax.transAxes, zorder=6
        )
        ax.add_patch(arc)


def draw_block(ax, x, y, w, h, title, subtitle, lines, accent="#1E3A5F", fill="#FFFFFF"):
    """Draw an IEEE-style clean technical block with subtle top header strip."""
    rect = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.002,rounding_size=0.008",
        facecolor=fill, edgecolor=accent, linewidth=1.6,
        transform=ax.transAxes, zorder=3
    )
    ax.add_patch(rect)

    # Header band
    hh = 0.072
    header = patches.Rectangle(
        (x, y + h - hh), w, hh,
        facecolor="#F1F5F9", edgecolor="none",
        transform=ax.transAxes, zorder=3.5
    )
    ax.add_patch(header)
    ax.plot([x, x + w], [y + h - hh, y + h - hh], color=accent, lw=1.0, transform=ax.transAxes, zorder=4)

    ax.text(
        x + w / 2, y + h - 0.025, title,
        ha="center", va="center", fontsize=9.2, fontweight="bold",
        color="#0F172A", transform=ax.transAxes, zorder=5
    )
    ax.text(
        x + w / 2, y + h - 0.052, subtitle,
        ha="center", va="center", fontsize=7.6, fontstyle="italic",
        color="#475569", transform=ax.transAxes, zorder=5
    )

    # Concise technical bullet specs
    if lines:
        usable_h = h - hh - 0.032
        step = usable_h / max(len(lines), 1)
        y_top = y + h - hh - 0.022 - step / 2
        for i, line in enumerate(lines):
            ax.text(
                x + 0.014, y_top - i * step, f"• {line}",
                ha="left", va="center", fontsize=8.0, color="#1E293B",
                transform=ax.transAxes, zorder=5
            )


def draw_hardware_block_diagram(output_path):
    fig, ax = plt.subplots(figsize=(13.5, 6.2), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    # Subtle top title
    ax.text(
        0.5, 0.955,
        "SƠ ĐỒ KHỐI PHẦN CỨNG HỆ THỐNG GIÁM SÁT MỰC NƯỚC IOT (STM32F103 & ESP32-C3)",
        ha="center", va="center", fontsize=11.5, fontweight="bold",
        color="#0F172A", transform=ax.transAxes
    )

    # Block coordinates (strict horizontal alignment, plenty of whitespace)
    # Power block (top-left)
    px, py, pw, ph = 0.04, 0.62, 0.21, 0.25
    draw_block(
        ax, px, py, pw, ph,
        "KHỐI CẤP NGUỒN", "Power Supply Unit",
        ["Adapter 12V DC / 2A", "USB 5V & LDO 3.3V", "Mass chung (0V GND)"],
        accent="#334155", fill="#FFFFFF"
    )

    # Sensor block (bottom-left)
    sx, sy, sw, sh = 0.04, 0.22, 0.21, 0.28
    draw_block(
        ax, sx, sy, sw, sh,
        "CẢM BIẾN THỦY TĨNH", "Submersible Level Sensor",
        ["Dải đo: 0 – 5 m (0–0.5 Bar)", "Nguồn nuôi: +12V DC", "Ngõ ra: 0.00 – 3.30V DC"],
        accent="#1E3A5F", fill="#FFFFFF"
    )

    # STM32 Edge MCU (center-left)
    mx, my, mw, mh = 0.34, 0.22, 0.24, 0.56
    draw_block(
        ax, mx, my, mw, mh,
        "VI ĐIỀU KHIỂN BIÊN", "STM32F103C8T6 (8 MHz HSI)",
        [
            "ADC1_IN0 (PA0, 12-bit)",
            "Oversampling 32× (100 ms)",
            "Bù điểm 0 (0.12V) + Deadband",
            "Lọc Adaptive EMA (α=0.80/0.15)",
            "USART1_TX (PA9, 5s/gói JSON)",
            "LED trạng thái (PC13)"
        ],
        accent="#1E3A5F", fill="#FFFFFF"
    )

    # ESP32-C3 Gateway (center-right)
    ex, ey, ew, eh = 0.67, 0.22, 0.22, 0.56
    draw_block(
        ax, ex, ey, ew, eh,
        "IOT GATEWAY", "ESP32-C3 (RISC-V 160 MHz)",
        [
            "UART1_RX (GPIO 4, 2KB Buf)",
            "Robust JSON Parser & Lọc rác",
            "Wi-Fi STA Auto-Reconnect",
            "MQTT v3.1.1 (QoS 1)",
            "Heartbeat 15s & LWT",
            "USB-CDC Debug (COM7)"
        ],
        accent="#1E3A5F", fill="#FFFFFF"
    )

    # RF Antenna & Cloud Output (far right)
    ant_x, ant_y = 0.945, 0.50
    draw_antenna_symbol(ax, ant_x, ant_y)
    ax.text(
        ant_x, ant_y - 0.04, "Wi-Fi 2.4 GHz\n(802.11 b/g/n)",
        ha="center", va="top", fontsize=7.8, fontweight="bold", color="#1E3A5F", transform=ax.transAxes
    )
    ax.text(
        ant_x, ant_y - 0.135, "MQTT Cloud\n(HiveMQ /\nRender 24/7)",
        ha="center", va="top", fontsize=7.5, color="#475569", transform=ax.transAxes
    )

    # ================= ORTHOGONAL INTERCONNECTIONS =================
    # 1. Power -> Sensor (+12V DC)
    x_mid_left = px + pw / 2
    ax.annotate(
        "", xy=(x_mid_left, sy + sh), xytext=(x_mid_left, py),
        xycoords="axes fraction", textcoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", color="#991B1B", lw=1.8), zorder=5
    )
    ax.text(
        x_mid_left + 0.012, (py + sy + sh) / 2, "+12V DC",
        ha="left", va="center", fontsize=8.0, fontweight="bold", color="#991B1B", transform=ax.transAxes
    )

    # 2. Power -> STM32 & ESP32 (+5V / 3.3V bus routed cleanly above MCU blocks)
    y_pwr_bus = 0.855
    ax.plot([px + pw, mx + mw / 2, ex + ew / 2], [y_pwr_bus, y_pwr_bus, y_pwr_bus],
            color="#334155", lw=1.4, linestyle="--", transform=ax.transAxes, zorder=4)
    # Connect power block right edge at y=0.855? Power block top is 0.87, so y=0.84 is inside!
    # Let's use y=0.84 for clean horizontal exit from Power Block
    ax.lines[-1].remove()
    y_pwr_bus = 0.835
    ax.plot([px + pw, ex + ew / 2], [y_pwr_bus, y_pwr_bus], color="#475569", lw=1.4, linestyle="--", transform=ax.transAxes, zorder=4)
    ax.annotate("", xy=(mx + mw / 2, my + mh), xytext=(mx + mw / 2, y_pwr_bus),
                xycoords="axes fraction", textcoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color="#475569", lw=1.4, linestyle="--"), zorder=5)
    ax.annotate("", xy=(ex + ew / 2, ey + eh), xytext=(ex + ew / 2, y_pwr_bus),
                xycoords="axes fraction", textcoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color="#475569", lw=1.4, linestyle="--"), zorder=5)
    ax.plot(mx + mw / 2, y_pwr_bus, marker="o", markersize=4, color="#475569", transform=ax.transAxes, zorder=6)
    ax.text(
        (px + pw + mx + mw / 2) / 2, y_pwr_bus + 0.022, "Nguồn 5V USB / 3.3V LDO",
        ha="center", va="bottom", fontsize=7.8, color="#475569", transform=ax.transAxes
    )

    # 3. Sensor -> STM32 (Analog 0 - 3.3V)
    y_sig = sy + sh / 2
    ax.annotate(
        "", xy=(mx, y_sig), xytext=(sx + sw, y_sig),
        xycoords="axes fraction", textcoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", color="#0F172A", lw=2.0), zorder=5
    )
    ax.text(
        (sx + sw + mx) / 2, y_sig + 0.028, "Analog 0–3.3V",
        ha="center", va="bottom", fontsize=8.0, fontweight="bold", color="#0F172A", transform=ax.transAxes
    )
    ax.text(
        (sx + sw + mx) / 2, y_sig - 0.025, "OUT → PA0",
        ha="center", va="top", fontsize=7.4, color="#475569", transform=ax.transAxes
    )

    # 4. STM32 -> ESP32 (UART1 TX -> RX)
    y_uart1 = 0.54
    ax.annotate(
        "", xy=(ex, y_uart1), xytext=(mx + mw, y_uart1),
        xycoords="axes fraction", textcoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", color="#1E3A5F", lw=2.0), zorder=5
    )
    ax.text(
        (mx + mw + ex) / 2, y_uart1 + 0.025, "UART1 (JSON)",
        ha="center", va="bottom", fontsize=8.0, fontweight="bold", color="#1E3A5F", transform=ax.transAxes
    )
    ax.text(
        (mx + mw + ex) / 2, y_uart1 - 0.022, "115200 8N1\nPA9 → GPIO 4",
        ha="center", va="top", fontsize=7.2, color="#475569", transform=ax.transAxes
    )

    # 5. ESP32 -> STM32 (Optional UART feedback)
    y_uart2 = 0.36
    ax.annotate(
        "", xy=(mx + mw, y_uart2), xytext=(ex, y_uart2),
        xycoords="axes fraction", textcoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", color="#64748B", lw=1.3, linestyle="--"), zorder=5
    )
    ax.text(
        (mx + mw + ex) / 2, y_uart2 - 0.020, "GPIO 5 → PA10\n(Tùy chọn)",
        ha="center", va="top", fontsize=7.0, fontstyle="italic", color="#64748B", transform=ax.transAxes
    )

    # 6. ESP32 -> RF Antenna (50 Ohm)
    ax.annotate(
        "", xy=(ant_x, ant_y), xytext=(ex + ew, ant_y),
        xycoords="axes fraction", textcoords="axes fraction",
        arrowprops=dict(arrowstyle="-", color="#1E3A5F", lw=1.8), zorder=5
    )
    ax.text(
        (ex + ew + ant_x) / 2, ant_y + 0.022, "RF 50Ω",
        ha="center", va="bottom", fontsize=7.5, fontweight="bold", color="#1E3A5F", transform=ax.transAxes
    )

    # ================= COMMON GROUND BUS (0V REFERENCE) =================
    y_gnd = 0.115
    ax.plot([0.02, ex + ew / 2], [y_gnd, y_gnd], color="#0F172A", lw=2.0, transform=ax.transAxes, zorder=5)

    # Power GND routed cleanly on far left (x=0.02)
    ax.plot([px, 0.02, 0.02], [py + 0.04, py + 0.04, y_gnd], color="#0F172A", lw=1.3, transform=ax.transAxes, zorder=5)
    ax.plot(0.02, y_gnd, marker="o", markersize=4, color="#0F172A", transform=ax.transAxes, zorder=6)

    # Drop lines from Sensor, STM32, ESP32
    for gx in [sx + sw / 2, mx + mw / 2, ex + ew / 2]:
        ax.plot([gx, gx], [0.22, y_gnd], color="#0F172A", lw=1.3, transform=ax.transAxes, zorder=5)
        ax.plot(gx, y_gnd, marker="o", markersize=4, color="#0F172A", transform=ax.transAxes, zorder=6)

    draw_gnd_symbol(ax, 0.46, y_gnd, color="#0F172A", scale=1.05)
    ax.text(
        0.46, 0.038, "TUYẾN MASS CHUNG TOÀN HỆ THỐNG (COMMON GND — 0V REFERENCE)",
        ha="center", va="center", fontsize=8.0, fontweight="bold", color="#334155", transform=ax.transAxes
    )

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="#FFFFFF")
    plt.close()
    print(f"Generated IEEE-style hardware block diagram: {output_path}")


if __name__ == "__main__":
    out_dir = r"D:\Embedded\esp32\docs"
    draw_hardware_block_diagram(os.path.join(out_dir, "hardware_block_diagram.png"))
    draw_hardware_block_diagram(os.path.join(out_dir, "system_block_diagram.png"))
    if os.path.exists(r"D:\Embedded\esp32\system_block_diagram.png"):
        draw_hardware_block_diagram(r"D:\Embedded\esp32\system_block_diagram.png")
