import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

plt.rcParams["font.family"] = "DejaVu Sans"


def draw_gnd_symbol(ax, x, y, color="#0F172A", scale=1.0):
    w1, w2, w3 = 0.011 * scale, 0.007 * scale, 0.003 * scale
    dy = 0.010 * scale
    ax.plot([x, x], [y, y - dy], color=color, lw=1.5, transform=ax.transAxes, zorder=6)
    ax.plot([x - w1, x + w1], [y - dy, y - dy], color=color, lw=1.8, transform=ax.transAxes, zorder=6)
    ax.plot([x - w2, x + w2], [y - 2 * dy, y - 2 * dy], color=color, lw=1.5, transform=ax.transAxes, zorder=6)
    ax.plot([x - w3, x + w3], [y - 3 * dy, y - 3 * dy], color=color, lw=1.2, transform=ax.transAxes, zorder=6)


def draw_ic_box(ax, x, y, w, h, title, subtitle, left_pins=None, right_pins=None, accent="#1E3A5F"):
    """Draw an electronic schematic component block with explicit pin stubs and labels."""
    rect = patches.Rectangle(
        (x, y), w, h,
        facecolor="#FFFFFF", edgecolor=accent, linewidth=1.7,
        transform=ax.transAxes, zorder=3
    )
    ax.add_patch(rect)

    hh = 0.082
    header = patches.Rectangle(
        (x, y + h - hh), w, hh,
        facecolor="#F1F5F9", edgecolor="none",
        transform=ax.transAxes, zorder=3.5
    )
    ax.add_patch(header)
    ax.plot([x, x + w], [y + h - hh, y + h - hh], color=accent, lw=1.0, transform=ax.transAxes, zorder=4)

    ax.text(x + w / 2, y + h - 0.028, title, ha="center", va="center",
            fontsize=9.2, fontweight="bold", color="#0F172A", transform=ax.transAxes, zorder=5)
    ax.text(x + w / 2, y + h - 0.058, subtitle, ha="center", va="center",
            fontsize=7.4, fontstyle="italic", color="#475569", transform=ax.transAxes, zorder=5)

    pin_coords = {}
    if left_pins:
        for pin_name, py_frac in left_pins:
            py = y + py_frac * (h - hh)
            ax.plot(x, py, marker="o", markersize=4.5, markerfacecolor="#FFFFFF",
                    markeredgecolor="#0F172A", markeredgewidth=1.3, transform=ax.transAxes, zorder=7)
            ax.text(x + 0.010, py, pin_name, ha="left", va="center",
                    fontsize=7.8, fontweight="bold", color="#0F172A", transform=ax.transAxes, zorder=6)
            pin_coords[("L", pin_name)] = (x, py)

    if right_pins:
        for pin_name, py_frac in right_pins:
            py = y + py_frac * (h - hh)
            ax.plot(x + w, py, marker="o", markersize=4.5, markerfacecolor="#FFFFFF",
                    markeredgecolor="#0F172A", markeredgewidth=1.3, transform=ax.transAxes, zorder=7)
            ax.text(x + w - 0.010, py, pin_name, ha="right", va="center",
                    fontsize=7.8, fontweight="bold", color="#0F172A", transform=ax.transAxes, zorder=6)
            pin_coords[("R", pin_name)] = (x + w, py)

    return pin_coords


def draw_wiring_diagram(output_path):
    fig, ax = plt.subplots(figsize=(13.5, 6.4), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    ax.text(
        0.5, 0.955,
        "SƠ ĐỒ ĐẤU NỐI CHÂN PHẦN CỨNG CHI TIẾT (HARDWARE PINOUT & WIRING SCHEMATIC)",
        ha="center", va="center", fontsize=11.5, fontweight="bold", color="#0F172A", transform=ax.transAxes
    )

    # Zero-crossing layout: Power & Sensor GND pins exit cleanly on the LEFT
    p_pins = draw_ic_box(
        ax, 0.055, 0.62, 0.175, 0.24,
        "NGUỒN 12V DC", "Adapter 12V / 2A",
        left_pins=[("GND (0V)", 0.35)],
        right_pins=[("+12V (VCC)", 0.55)],
        accent="#334155"
    )

    s_pins = draw_ic_box(
        ax, 0.055, 0.22, 0.175, 0.30,
        "CẢM BIẾN THỦY TĨNH", "0–5 m | 0–3.3V Out",
        left_pins=[("GND (0V)", 0.25)],
        right_pins=[("VCC (+12V)", 0.78), ("OUT (0–3.3V)", 0.38)],
        accent="#1E3A5F"
    )

    m_pins = draw_ic_box(
        ax, 0.39, 0.22, 0.23, 0.64,
        "STM32F103C8T6", "Edge MCU (3.3V CMOS)",
        left_pins=[("3.3V / 5V USB", 0.85), ("PA0 (ADC1_IN0)", 0.42), ("GND", 0.12)],
        right_pins=[("PA9 (USART1_TX)", 0.72), ("PA10 (USART1_RX)", 0.50), ("PC13 (LED 5s)", 0.28), ("GND", 0.12)],
        accent="#1E3A5F"
    )

    e_pins = draw_ic_box(
        ax, 0.75, 0.22, 0.21, 0.64,
        "ESP32-C3 GATEWAY", "RISC-V (3.3V CMOS)",
        left_pins=[("5V (USB Type-C)", 0.88), ("GPIO 4 (UART1_RX)", 0.72), ("GPIO 5 (UART1_TX)", 0.50), ("GND", 0.12)],
        right_pins=[("RF 2.4 GHz", 0.60)],
        accent="#1E3A5F"
    )

    # Net 1: +12V DC (Power right -> Sensor VCC right) routed tightly at x = 0.268
    p_vcc = p_pins[("R", "+12V (VCC)")]
    s_vcc = s_pins[("R", "VCC (+12V)")]
    x_12v = 0.268
    ax.plot([p_vcc[0], x_12v, x_12v, s_vcc[0]], [p_vcc[1], p_vcc[1], s_vcc[1], s_vcc[1]],
            color="#991B1B", lw=2.0, transform=ax.transAxes, zorder=5)
    ax.annotate("", xy=(s_vcc[0] + 0.004, s_vcc[1]), xytext=(x_12v, s_vcc[1]),
                xycoords="axes fraction", textcoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color="#991B1B", lw=2.0), zorder=5)
    ax.text(x_12v + 0.010, 0.60, "+12V DC\n(Dây Đỏ)",
            ha="left", va="center", fontsize=7.5, fontweight="bold", color="#991B1B", transform=ax.transAxes)

    # Net 2: Analog 0-3.3V (Sensor OUT -> STM32 PA0) — clean step at x = 0.298, label sits in pure open space!
    s_out = s_pins[("R", "OUT (0–3.3V)")]
    m_pa0 = m_pins[("L", "PA0 (ADC1_IN0)")]
    x_mid_an = 0.298
    ax.plot([s_out[0], x_mid_an, x_mid_an], [s_out[1], s_out[1], m_pa0[1]],
            color="#0F172A", lw=2.0, transform=ax.transAxes, zorder=5)
    ax.annotate("", xy=(m_pa0[0] - 0.004, m_pa0[1]), xytext=(x_mid_an, m_pa0[1]),
                xycoords="axes fraction", textcoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color="#0F172A", lw=2.0), zorder=5)
    ax.text(0.344, m_pa0[1] + 0.022, "Analog 0–3.3V\n(Dây Vàng)",
            ha="center", va="bottom", fontsize=7.4, fontweight="bold", color="#0F172A", transform=ax.transAxes)

    # Net 3: UART1 TX -> RX (STM32 PA9 -> ESP32 GPIO 4)
    m_pa9 = m_pins[("R", "PA9 (USART1_TX)")]
    e_g4 = e_pins[("L", "GPIO 4 (UART1_RX)")]
    ax.annotate("", xy=(e_g4[0] - 0.004, e_g4[1]), xytext=(m_pa9[0] + 0.004, m_pa9[1]),
                xycoords="axes fraction", textcoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color="#1E3A5F", lw=2.0), zorder=5)
    ax.text((m_pa9[0] + e_g4[0]) / 2, m_pa9[1] + 0.022, "UART1 TX → RX",
            ha="center", va="bottom", fontsize=7.8, fontweight="bold", color="#1E3A5F", transform=ax.transAxes)
    ax.text((m_pa9[0] + e_g4[0]) / 2, m_pa9[1] - 0.020, "115200 8N1 (3.3V)",
            ha="center", va="top", fontsize=7.1, color="#475569", transform=ax.transAxes)

    # Net 4: UART1 Feedback (ESP32 GPIO 5 -> STM32 PA10)
    m_pa10 = m_pins[("R", "PA10 (USART1_RX)")]
    e_g5 = e_pins[("L", "GPIO 5 (UART1_TX)")]
    ax.annotate("", xy=(m_pa10[0] + 0.004, m_pa10[1]), xytext=(e_g5[0] - 0.004, e_g5[1]),
                xycoords="axes fraction", textcoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color="#64748B", lw=1.4, linestyle="--"), zorder=5)
    ax.text((m_pa10[0] + e_g5[0]) / 2, m_pa10[1] + 0.020, "TX → RX (Tùy chọn)",
            ha="center", va="bottom", fontsize=7.1, fontstyle="italic", color="#64748B", transform=ax.transAxes)

    # Net 5: Common Ground (0V) — ZERO WIRE CROSSINGS!
    y_gnd = 0.115
    x_gnd_left = 0.025
    p_gnd = p_pins[("L", "GND (0V)")]
    s_gnd = s_pins[("L", "GND (0V)")]
    m_gnd_l = m_pins[("L", "GND")]
    m_gnd_r = m_pins[("R", "GND")]
    e_gnd = e_pins[("L", "GND")]

    ax.plot([p_gnd[0], x_gnd_left, x_gnd_left], [p_gnd[1], p_gnd[1], y_gnd],
            color="#0F172A", lw=1.6, transform=ax.transAxes, zorder=5)
    ax.plot([s_gnd[0], x_gnd_left], [s_gnd[1], s_gnd[1]],
            color="#0F172A", lw=1.6, transform=ax.transAxes, zorder=5)
    ax.plot(x_gnd_left, s_gnd[1], marker="o", markersize=4, color="#0F172A", transform=ax.transAxes, zorder=6)

    x_gnd_m_l = 0.355
    x_gnd_e = 0.72
    ax.plot([x_gnd_left, x_gnd_e], [y_gnd, y_gnd], color="#0F172A", lw=2.0, transform=ax.transAxes, zorder=5)

    ax.plot([m_gnd_l[0], x_gnd_m_l, x_gnd_m_l], [m_gnd_l[1], m_gnd_l[1], y_gnd],
            color="#0F172A", lw=1.6, transform=ax.transAxes, zorder=5)
    ax.plot(x_gnd_m_l, y_gnd, marker="o", markersize=4, color="#0F172A", transform=ax.transAxes, zorder=6)

    ax.plot([m_gnd_r[0], e_gnd[0]], [m_gnd_r[1], e_gnd[1]],
            color="#0F172A", lw=1.6, transform=ax.transAxes, zorder=5)
    ax.plot([x_gnd_e, x_gnd_e], [e_gnd[1], y_gnd],
            color="#0F172A", lw=1.6, transform=ax.transAxes, zorder=5)
    ax.plot(x_gnd_e, e_gnd[1], marker="o", markersize=4, color="#0F172A", transform=ax.transAxes, zorder=6)
    ax.text((m_gnd_r[0] + e_gnd[0]) / 2 - 0.012, m_gnd_r[1] + 0.018, "Common GND",
            ha="center", va="bottom", fontsize=7.2, fontweight="bold", color="#0F172A", transform=ax.transAxes)

    draw_gnd_symbol(ax, 0.50, y_gnd, color="#0F172A", scale=1.05)
    ax.text(
        0.50, 0.038,
        "COMMON GROUND BUS (0V) — Nối chung Mass: Nguồn 12V = Cảm biến = STM32F103 = ESP32-C3 (Dây Đen)",
        ha="center", va="center", fontsize=7.8, fontweight="bold", color="#334155", transform=ax.transAxes
    )

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="#FFFFFF")
    plt.close()
    print(f"Generated IEEE-style wiring schematic: {output_path}")


if __name__ == "__main__":
    draw_wiring_diagram(r"D:\Embedded\esp32\docs\hardware_wiring_diagram.png")
