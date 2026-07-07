import csv

with open("data.csv", "r", encoding="utf-8") as infile:
    lines = infile.readlines()

with open("data_fixed.csv", "w", newline="", encoding="utf-8") as outfile:
    writer = csv.writer(outfile)
    for line in lines:
        line = line.strip().strip('"')  # remove wrapping quotes
        if line:
            writer.writerow(line.split(","))

print("Done. Check data_fixed.csv")