from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "soft" / "SoftFailure_dataset.csv"

OUTPUT_DIR = BASE_DIR / "docs" / "soft"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


df = pd.read_csv(CSV_PATH)

df["time"] = pd.to_datetime(df["Timestamp"], unit="s")

groups = df.groupby(pd.Grouper(key="time", freq="1min"))

file_id = 0

for t, g in groups:

    if g.empty:
        continue

    lines = []
    lines.append(f"Time window start: {t}")

    devices = g[g["Type"] == "Devices"]

    for _, row in devices.iterrows():
        lines.append(
            f"Device {row['ID']} - BER: {row['BER']}, OSNR: {row['OSNR']} dB"
        )

    infra = g[g["Type"] == "Infrastructure"]

    for _, row in infra.iterrows():
        lines.append(
            f"Amplifier {row['ID']} - Input power: {row['InputPower']} dBm, Output power: {row['OutputPower']} dBm"
        )

    if g["Failure"].notna().any():
        lines.append("Failure condition detected during this time window.")
    else:
        lines.append("No failure condition detected during this time window.")

    text = "\n".join(lines)

    with open(OUTPUT_DIR / f"report_{file_id}.txt", "w", encoding="utf-8") as f:
        f.write(text)

    file_id += 1

print(f"Generated {file_id} text reports.")
