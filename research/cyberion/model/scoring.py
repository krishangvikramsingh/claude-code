"""Weighted opportunity scoring for Deliverable C. Edit WEIGHTS or SCORES and re-run.
Scores are 1-10 where 10 is always 'better for Cyberion' (e.g. 10 = easy to build,
low capital, short sales cycle, LOW competitive intensity)."""
CRITERIA = ["Severity", "Frequency", "WTP evidence", "Customer ROI", "Dev ease",
            "Time to pilot", "Low capital", "Install ease", "Data availability",
            "Short sales cycle", "Recurring rev", "Market reach", "Low competition",
            "Defensibility", "Fit w/ PackQuote"]
WEIGHTS = [9, 7, 10, 9, 6, 7, 6, 6, 6, 6, 8, 5, 4, 4, 7]
assert sum(WEIGHTS) == 100
SCORES = {
 "O1 PackQuote Margin Control - corrugated (live kraft costing + quote-vs-actual)": [8,9,6,8,7,9,9,9,8,7,8,7,6,6,10],
 "O2 Flexible-packaging laminate costing + quote-vs-actual":                      [8,9,6,8,5,8,9,9,7,6,8,6,6,7,9],
 "O3 Retrofit runtime/downtime/count monitor (non-invasive)":                       [7,9,7,7,6,6,6,7,8,6,8,8,3,4,5],
 "O4 Energy-per-kg and utility metering (plastics)":                                [7,8,6,7,6,6,6,7,9,6,7,7,5,5,5],
 "O5 Mobile job-ticket, WIP and dispatch tracking":                                 [6,9,4,6,7,7,9,7,6,6,7,7,5,5,8],
 "O6 Production scheduling (corrugator / press)":                                  [7,9,4,6,4,5,8,7,5,5,7,6,5,6,7],
 "O7 Compressed-air pressure/flow monitoring":                                      [6,7,5,7,6,6,6,6,8,6,5,6,6,3,3],
 "O8 Resin-dryer / material-condition monitoring":                                  [7,6,3,6,5,5,6,6,7,5,5,4,6,4,3],
 "O9 IMM process-parameter logger (EUROMAP 63/77, Modbus)":                         [6,8,4,5,4,4,6,5,5,5,6,4,5,6,4],
 "O10 Blown-film giveaway analytics (roll-weight based)":                           [7,8,5,7,5,5,7,6,6,5,6,3,5,6,5],
 "O11 Kraft/resin price intelligence + supplier quote comparison":                  [7,7,5,5,6,7,9,9,6,7,6,7,5,4,8],
 "O12 Document AI: RFQ/PO/spec extraction into quotes":                             [5,7,4,5,6,7,9,9,6,7,5,6,4,3,6],
 "O13 EPR / recycled-content compliance records":                                   [6,4,6,4,6,6,9,9,6,5,5,5,5,4,5],
 "O14 Camera-based print defect inspection":                                        [8,7,6,6,2,3,3,4,5,3,5,5,3,6,3],
 "O15 Mould shot-counter + preventive-maintenance workflow":                        [6,6,4,6,6,6,7,7,7,6,5,5,5,4,4],
}
rows = sorted(((sum(w*s for w, s in zip(WEIGHTS, v)) / 10, k, v) for k, v in SCORES.items()), reverse=True)
print("| Rank | Opportunity | " + " | ".join(CRITERIA) + " | Weighted (0-100) |")
print("|" + "---|" * (len(CRITERIA) + 3))
print("| | **Weight** | " + " | ".join(str(w) for w in WEIGHTS) + " | 100 |")
for i, (tot, k, v) in enumerate(rows, 1):
    print(f"| {i} | {k} | " + " | ".join(map(str, v)) + f" | **{tot:.1f}** |")
