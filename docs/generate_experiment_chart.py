import os
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "DejaVu Sans"


def draw_experiment_chart(output_path):
    # Real field data at Ho ca Khu A & lab calibration (Bucket)
    lake_true = np.array([5.0, 19.5, 47.0, 52.0, 60.0, 65.0])
    lake_meas = np.array([5.2, 19.8, 46.8, 52.3, 59.6, 65.2])
    lake_err = lake_meas - lake_true

    lab_true = np.array([0.0, 2.0, 10.0, 20.0, 35.0])
    lab_meas = np.array([0.0, 2.1, 10.2, 19.8, 35.3])
    lab_err = lab_meas - lab_true

    all_true = np.concatenate([lab_true, lake_true])
    all_meas = np.concatenate([lab_meas, lake_true * 0 + lake_meas])
    # Linear regression y = a*x + b
    slope, intercept = np.polyfit(all_true, all_meas, 1)
    ss_res = np.sum((all_meas - all_true) ** 2)
    ss_tot = np.sum((all_true - np.mean(all_true)) ** 2)
    r_squared = 1.0 - (ss_res / ss_tot)
    rmse = np.sqrt(np.mean((all_meas - all_true) ** 2))
    mae = np.mean(np.abs(all_meas - all_true))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.8, 4.8), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")

    # ---- Subplot (a): Linearity & Calibration Curve ----
    ax1.set_facecolor("#FFFFFF")
    x_line = np.linspace(0, 70, 100)
    ax1.plot(x_line, x_line, color="#64748B", linestyle="--", lw=1.3, label="Đường chuẩn lý tưởng (y = x)", zorder=2)
    ax1.scatter(lab_true, lab_meas, marker="s", s=52, facecolor="#FFFFFF", edgecolor="#1E3A5F",
                linewidth=1.6, label="Kiểm chuẩn phòng thí nghiệm (Xô)", zorder=4)
    ax1.scatter(lake_true, lake_meas, marker="o", s=56, facecolor="#1E3A5F", edgecolor="#0F172A",
                linewidth=1.1, label="Thực địa tại Hồ cá Khu A", zorder=5)

    ax1.set_title("(a) Đối soát mực nước cảm biến và thước chuẩn", fontsize=10.0, fontweight="bold", color="#0F172A", pad=10)
    ax1.set_xlabel("Mực nước thực tế đo bằng thước chuẩn (cm)", fontsize=8.8, color="#1E293B")
    ax1.set_ylabel("Mực nước đo từ hệ thống cảm biến (cm)", fontsize=8.8, color="#1E293B")
    ax1.set_xlim(-2, 70)
    ax1.set_ylim(-2, 70)
    ax1.grid(True, linestyle=":", color="#CBD5E1", lw=0.8)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.tick_params(labelsize=8.2, colors="#334155")
    ax1.legend(loc="upper left", fontsize=7.8, frameon=True, facecolor="#FFFFFF", edgecolor="#CBD5E1")

    stats_txt = (
        f"y = {slope:.4f}x {intercept:+.2f} cm\n"
        f"$R^2$ = {r_squared:.5f}\n"
        f"MAE = {mae:.2f} cm | RMSE = {rmse:.2f} cm"
    )
    ax1.text(
        0.96, 0.08, stats_txt,
        transform=ax1.transAxes, ha="right", va="bottom", fontsize=7.9,
        color="#0F172A", bbox=dict(boxstyle="round,pad=0.35", facecolor="#F8FAFC", edgecolor="#94A3B8", lw=0.9)
    )

    # ---- Subplot (b): Absolute Error vs WMO-No. 168 Tolerance ----
    ax2.set_facecolor("#FFFFFF")
    x_idx_lab = np.arange(len(lab_true))
    x_idx_lake = np.arange(len(lab_true), len(lab_true) + len(lake_true))
    all_labels = [f"{v:.0f}" for v in lab_true] + [f"{v:.1f}" if v % 1 else f"{v:.0f}" for v in lake_true]

    ax2.axhspan(-1.0, 1.0, color="#F1F5F9", alpha=0.8, zorder=1, label="Ngưỡng chuẩn WMO-No. 168 (±1.0 cm)")
    ax2.axhline(1.0, color="#991B1B", linestyle="--", lw=1.1, zorder=2)
    ax2.axhline(-1.0, color="#991B1B", linestyle="--", lw=1.1, zorder=2)
    ax2.axhline(0.0, color="#334155", lw=1.0, zorder=2)

    ax2.bar(x_idx_lab, lab_err, width=0.52, color="#FFFFFF", edgecolor="#1E3A5F", linewidth=1.4, hatch="///",
            label="Sai số phòng thí nghiệm", zorder=3)
    ax2.bar(x_idx_lake, lake_err, width=0.52, color="#1E3A5F", edgecolor="#0F172A", linewidth=1.0,
            label="Sai số thực địa (Hồ cá Khu A)", zorder=3)

    for idx, val in zip(np.concatenate([x_idx_lab, x_idx_lake]), np.concatenate([lab_err, lake_err])):
        va = "bottom" if val >= 0 else "top"
        offset = 0.04 if val >= 0 else -0.04
        ax2.text(idx, val + offset, f"{val:+.1f}", ha="center", va=va, fontsize=7.5, fontweight="bold", color="#0F172A")

    ax2.set_title("(b) Phân bố sai số tuyệt đối trên các mốc đo", fontsize=10.0, fontweight="bold", color="#0F172A", pad=10)
    ax2.set_xlabel("Mốc mực nước thực tế (cm)", fontsize=8.8, color="#1E293B")
    ax2.set_ylabel("Sai số tuyệt đối Δh = h_đo − h_thực (cm)", fontsize=8.8, color="#1E293B")
    ax2.set_xticks(np.arange(len(all_labels)))
    ax2.set_xticklabels(all_labels, fontsize=8.0)
    ax2.set_ylim(-1.25, 1.25)
    ax2.grid(True, axis="y", linestyle=":", color="#CBD5E1", lw=0.8)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.tick_params(labelsize=8.2, colors="#334155")
    ax2.legend(loc="lower right", fontsize=7.5, frameon=True, facecolor="#FFFFFF", edgecolor="#CBD5E1")

    plt.tight_layout(w_pad=2.5)
    plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="#FFFFFF")
    plt.close()
    print(f"Generated IEEE-style experimental chart: {output_path}")


if __name__ == "__main__":
    draw_experiment_chart(r"D:\Embedded\esp32\docs\experiment_accuracy_chart.png")
