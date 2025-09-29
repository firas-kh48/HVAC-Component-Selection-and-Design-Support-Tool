from reportlab.lib.pagesizes import inch
from reportlab.pdfgen import canvas
import subprocess

def create_sticker_pdf(number, filename):
    width = 2.2 * inch
    height = 5.75 * inch
    c = canvas.Canvas(filename, pagesize=(width, height))
    c.setFont("Helvetica-Bold", 60)
    c.drawCentredString(width / 2, height / 2, str(number))
    c.save()

def print_pdf(filename):
    subprocess.run(['lp', filename])  # uses default printer

if __name__ == "__main__":
    number = input("Enter the number to print: ")
    pdf_file = "sticker.pdf"
    create_sticker_pdf(number, pdf_file)
    print_pdf(pdf_file)
