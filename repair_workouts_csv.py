# repair_workouts_csv.py
import csv, os, math

IN_PATH  = "data/workouts.csv"
OUT_PATH = "data/workouts_clean.csv"
BAD_PATH = "data/workouts_bad_rows.csv"

EXPECTED = ["date","muscle_group","exercise","sets","reps","weight_kg"]

def is_number(x):
    try:
        float(x)
        return True
    except Exception:
        return False

def coerce_int(x):
    # handle "8.0" -> 8
    try:
        return int(round(float(x)))
    except Exception:
        raise

def main():
    if not os.path.exists(IN_PATH):
        print("No data/workouts.csv found.")
        return

    os.makedirs("data", exist_ok=True)

    with open(IN_PATH, newline="") as fin, \
         open(OUT_PATH, "w", newline="") as fout, \
         open(BAD_PATH, "w", newline="") as fbad:

        r = csv.reader(fin)
        w = csv.writer(fout, quoting=csv.QUOTE_MINIMAL, escapechar="\\")
        wb = csv.writer(fbad)

        # write headers
        w.writerow(EXPECTED)
        wb.writerow(["raw_line"])

        # skip original header if present
        first = next(r, None)
        if first is None:
            print("Empty CSV.")
            return
        lower_join = ",".join([str(c).lower() for c in first])
        if "date" not in lower_join or "muscle" not in lower_join:
            # not a header; treat as data
            rows = [first] + list(r)
        else:
            rows = list(r)

        for row in rows:
            # skip empty lines
            if not row or all((str(x).strip()=="" for x in row)):
                continue

            try:
                # Ensure we have at least 3 columns to start parsing
                # row[0] = date, row[1] = muscle_group
                date = str(row[0]).strip()
                group = str(row[1]).strip() if len(row) > 1 else ""

                # Walk from end, pick last three numeric tokens
                indices = []
                for i in range(len(row)-1, 1, -1):
                    token = str(row[i]).strip()
                    if is_number(token):
                        indices.append(i)
                        if len(indices) == 3:
                            break

                if len(indices) < 3:
                    # cannot find numeric tail
                    wb.writerow(["|".join(map(str,row))])
                    continue

                indices = sorted(indices)           # ascending
                i_sets, i_reps, i_w = indices       # three numeric columns in order

                # Join exercise from col 2 up to BEFORE the first numeric tail col
                exercise_parts = row[2:i_sets]
                exercise = ",".join(map(str, exercise_parts)).strip()
                if exercise == "":
                    exercise = "Unknown Exercise"

                sets = coerce_int(row[i_sets])
                reps = coerce_int(row[i_reps])
                weight = float(row[i_w])

                w.writerow([date, group, exercise, sets, reps, weight])

            except Exception:
                wb.writerow(["|".join(map(str,row))])
                continue

    # replace original with cleaned one
    os.replace(OUT_PATH, IN_PATH)
    print("Repaired data/workouts.csv. Any unrepaired lines are in", BAD_PATH)

if __name__ == "__main__":
    main()
