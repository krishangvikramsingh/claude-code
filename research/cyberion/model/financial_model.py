"""Cyberion / PackQuote Margin Control - transparent 36-month scenario model.

All figures in INR, excluding GST. Every input is a stated assumption, not a
forecast. Change the ASSUMPTIONS dict and re-run:  python3 financial_model.py
Outputs: monthly.csv (36 months x 3 scenarios) and summary.md.
"""
import csv, math, os

HERE = os.path.dirname(os.path.abspath(__file__))

# New paying software accounts added per month, months 1..12, then per-quarter for Q5..Q12
NEW_ACCTS = {
    "conservative": [0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3] + [9, 10, 12, 12, 14, 15, 15, 16],
    "base":         [0, 0, 0, 1, 2, 2, 3, 3, 4, 4, 5, 5] + [18, 21, 24, 27, 30, 33, 36, 39],
    "optimistic":   [0, 0, 1, 2, 3, 3, 4, 5, 6, 6, 7, 8] + [27, 33, 39, 45, 51, 57, 63, 69],
}

ASSUMPTIONS = {
    "conservative": dict(arpa0=4500, arpa_growth_m=0.006, onboard_fee=20000, churn_m=0.030,
                         hw_attach=0.10, sales_hire_m=13, eng2_hire_m=16),
    "base":         dict(arpa0=6000, arpa_growth_m=0.010, onboard_fee=30000, churn_m=0.020,
                         hw_attach=0.20, sales_hire_m=10, eng2_hire_m=13),
    "optimistic":   dict(arpa0=7500, arpa_growth_m=0.012, onboard_fee=40000, churn_m=0.015,
                         hw_attach=0.30, sales_hire_m=8,  eng2_hire_m=10),
}

COMMON = dict(
    founder_draw=100000,      # founder living cost, from month 1
    eng1=85000, eng1_m=3,     # full-stack engineer (fully loaded)
    cs1=45000, cs1_m=6,       # implementation / customer-success executive (fully loaded)
    accts_per_cs=60,          # one CS/implementation person per 60 live accounts (Indian SMEs need hand-holding)
    sales=60000,              # field sales executive (fixed part)
    sales_commission=0.10,    # of first-year contract value booked, paid on booking
    eng2=110000,              # second engineer (IoT / data)
    tools_fixed=20000,        # cloud base, SaaS tools, accounting, legal retainer
    infra_per_acct=250,       # hosting + storage + backups per account per month
    ai_per_acct=150,          # LLM / OCR usage per account per month (capped by credits)
    support_per_acct=300,     # variable support cost per account (calls, WhatsApp, visits)
    onboard_cost=12000,       # variable cost of an onboarding (travel, setup time)
    marketing_m=40000,        # from month 4: travel, demos, content, associations
    trade_fair={9: 300000, 21: 350000, 33: 400000},  # e.g. IndiaCorr / PrintPack-type events
    # Second product (monitoring add-on) from month 13: hardware sold at cost+margin + SaaS
    hw_nodes_per_attach=4, hw_price=12000, hw_cost=6500, hw_saas=900, hw_support=200,
    hw_dev_once={10: 250000, 11: 150000, 12: 100000},  # prototyping, EMC pre-scan, pilot units
)


def run(name):
    a, c = ASSUMPTIONS[name], COMMON
    adds = NEW_ACCTS[name]
    monthly_adds = adds[:12] + [q // 3 + (1 if i < q % 3 else 0) for q in adds[12:] for i in range(3)]
    rows, accts, hw_accts, cash, booked_accts = [], 0.0, 0.0, 0.0, 0
    for m in range(1, 37):
        new = monthly_adds[m - 1]
        churned = accts * a["churn_m"]
        accts = accts - churned + new
        arpa = a["arpa0"] * (1 + a["arpa_growth_m"]) ** (m - 1)
        sw_mrr = accts * arpa
        new_hw = new * a["hw_attach"] if m >= 13 else 0
        hw_accts = hw_accts * (1 - a["churn_m"]) + new_hw
        hw_mrr = hw_accts * c["hw_nodes_per_attach"] * c["hw_saas"]
        mrr = sw_mrr + hw_mrr
        hw_rev = new_hw * c["hw_nodes_per_attach"] * c["hw_price"]
        onboard_rev = new * a["onboard_fee"]
        revenue = mrr + hw_rev + onboard_rev
        cogs = (accts * (c["infra_per_acct"] + c["ai_per_acct"] + c["support_per_acct"])
                + new * c["onboard_cost"]
                + new_hw * c["hw_nodes_per_attach"] * c["hw_cost"]
                + hw_accts * c["hw_nodes_per_attach"] * c["hw_support"])
        # customer-success team is a cost of delivering the service, so it sits in COGS
        cs_heads = max(1, math.ceil(accts / c["accts_per_cs"])) if m >= c["cs1_m"] else 0
        cogs += cs_heads * c["cs1"]
        people = c["founder_draw"]
        people += c["eng1"] if m >= c["eng1_m"] else 0
        people += c["sales"] if m >= a["sales_hire_m"] else 0
        people += c["eng2"] if m >= a["eng2_hire_m"] else 0
        commission = c["sales_commission"] * new * arpa * 12 if m >= a["sales_hire_m"] else 0
        mkt = (c["marketing_m"] if m >= 4 else 10000) + c["trade_fair"].get(m, 0)
        dev_once = c["hw_dev_once"].get(m, 0)
        opex = people + commission + mkt + c["tools_fixed"] + dev_once
        net = revenue - cogs - opex
        cash += net
        rows.append(dict(scenario=name, month=m, new_accts=new, accts=round(accts, 1),
                         arpa=round(arpa), mrr=round(mrr), arr=round(mrr * 12),
                         revenue=round(revenue), cogs=round(cogs),
                         gross_margin_pct=round(100 * (revenue - cogs) / revenue, 1) if revenue else 0,
                         opex=round(opex), net=round(net), cum_cash=round(cash)))
    return rows


def summarise(rows):
    min_cash = min(r["cum_cash"] for r in rows)
    be = next((r["month"] for r in rows if r["net"] > 0 and all(x["net"] > 0 for x in rows if x["month"] >= r["month"])), None)
    return min_cash, be


def main():
    all_rows, out = [], ["# Model output (generated by financial_model.py)\n"]
    for s in ("conservative", "base", "optimistic"):
        rows = run(s)
        all_rows += rows
        min_cash, be = summarise(rows)
        out.append(f"\n## {s.title()}\n")
        out.append(f"- Peak cumulative cash requirement: INR {-min_cash/1e5:,.1f} lakh")
        out.append(f"- Sustained operating break-even month: {be if be else 'not within 36 months'}")
        out.append(f"- Month-36 accounts: {rows[-1]['accts']}, MRR INR {rows[-1]['mrr']/1e5:,.2f} lakh, ARR INR {rows[-1]['arr']/1e7:,.2f} crore\n")
        out.append("| Month | New | Accts | MRR (₹L) | Revenue (₹L) | Gross margin % | Opex (₹L) | Net (₹L) | Cum. cash (₹L) |")
        out.append("|---|---|---|---|---|---|---|---|---|")
        for r in rows[:12]:
            out.append(f"| M{r['month']} | {r['new_accts']} | {r['accts']} | {r['mrr']/1e5:.2f} | {r['revenue']/1e5:.2f} | {r['gross_margin_pct']} | {r['opex']/1e5:.2f} | {r['net']/1e5:.2f} | {r['cum_cash']/1e5:.2f} |")
        for q in range(5, 13):
            qr = rows[(q - 1) * 3:(q) * 3]
            rev = sum(x["revenue"] for x in qr); cogs = sum(x["cogs"] for x in qr)
            out.append(f"| Q{q} (M{qr[0]['month']}-{qr[-1]['month']}) | {sum(x['new_accts'] for x in qr)} | {qr[-1]['accts']} | {qr[-1]['mrr']/1e5:.2f} | {rev/1e5:.2f} | {round(100*(rev-cogs)/rev,1)} | {sum(x['opex'] for x in qr)/1e5:.2f} | {sum(x['net'] for x in qr)/1e5:.2f} | {qr[-1]['cum_cash']/1e5:.2f} |")
    with open(os.path.join(HERE, "monthly.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys())); w.writeheader(); w.writerows(all_rows)
    with open(os.path.join(HERE, "summary.md"), "w") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
