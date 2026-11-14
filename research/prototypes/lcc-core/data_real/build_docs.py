"""Wrap pdftotext output of data_real/raw/* in the front matter extract.py expects. Run with python -I."""
import os, json
ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS = [
 ("ADIENT-SSM-Q-R10", "adient_manual/manual.txt", "customer_requirement", "Adient Global Supplier Standards Manual, Quality chapter, Rev 10.0", "2023-04-01", "Adient", ["CUST-ADIENT"]),
 ("ADIENT-LTR-UC", "adient_letter/letter.txt", "customer_requirement", "Adient letter to suppliers: Unauthorized changes", "2023-04-28", "Adient US LLC", ["CUST-ADIENT"]),
 ("ASTEMO-SCM-R4", "astemo/guidebook.txt", "customer_requirement", "Astemo Supplier Change Management Guidebook, Rev 4.0", "2025-12-01", "Astemo", ["CUST-ASTEMO"]),
 ("FORD-573-18V806", "ford_573/18V806.txt", "recall_report", "Ford Part 573 Safety Recall Report 18V-806", "2018-11-14", "Ford Motor Company", ["CUST-FORD"]),
]
for doc_id, rel, typ, title, date, author, mentions in DOCS:
    text = open(os.path.join(ROOT, "raw", rel), encoding="utf-8").read().replace("\f", "\n\n")
    head = ["---", f"id: {doc_id}", f"type: {typ}", f"title: {json.dumps(title)}", f"date: '{date}'",
            f"author: {json.dumps(author)}", f"valid_from: '{date}'", "valid_to: null", "supersedes: null", "mentions:"]
    head += [f"- {m}" for m in mentions] + ["---", ""]
    open(os.path.join(ROOT, "docs", doc_id + ".md"), "w", encoding="utf-8").write("\n".join(head) + text)
    print(doc_id, len(text))
