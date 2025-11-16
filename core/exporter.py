# core/exporter.py

import csv
from fpdf import FPDF
from core.transactions import get_all_txns
from PyQt5.QtWidgets import QFileDialog

def export_csv(user_id, parent=None):
    txns = get_all_txns(user_id)
    if not txns:
        return False, "no data to export"

    path, _ = QFileDialog.getSaveFileName(parent, "save as", "transactions.csv", "CSV files (*.csv)")
    if not path:
        return False, "cancelled"

    try:
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "type", "amount", "category", "account", "desc"])
            for t in txns:
                writer.writerow([
                    t["date"], t["transaction_type"], t["amount"],
                    t["category_name"], t["bank_name"], t["description"] or ""
                ])
        return True, "csv saved"
    except Exception as e:
        return False, str(e)

def export_pdf(user_id, parent=None):
    txns = get_all_txns(user_id)
    if not txns:
        return False, "no data to export"

    path, _ = QFileDialog.getSaveFileName(parent, "save as", "transactions.pdf", "PDF files (*.pdf)")
    if not path:
        return False, "cancelled"

    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Transaction History", ln=True, align="C")
        pdf.ln(10)

        for t in txns:
            line = f"{t['date']} | {t['transaction_type']} | {t['amount']} | {t['category_name']} | {t['bank_name']} | {t['description'] or ''}"
            pdf.cell(200, 8, txt=line, ln=True)

        pdf.output(path)
        return True, "pdf saved"
    except Exception as e:
        return False, str(e)
