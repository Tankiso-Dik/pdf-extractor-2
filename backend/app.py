from flask import Flask, request, send_file
from flask_cors import CORS
import os
import zipfile
import tempfile
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path

app = Flask(__name__)
CORS(app)

@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'pdf_file' not in request.files:
        return "No pdf_file part in the request", 400
    
    pdf_file = request.files['pdf_file']
    
    if pdf_file.filename == '':
        return "No selected file", 400
    
    if pdf_file:
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, pdf_file.filename)
            pdf_file.save(pdf_path)

            output_zip_path = os.path.join(tmpdir, "pages.zip")
            
            with zipfile.ZipFile(output_zip_path, 'w') as zf:
                try:
                    # Try converting to images first
                    images = convert_from_path(pdf_path)
                    for i, image in enumerate(images):
                        image_filename = f"page_{i+1}.png"
                        image_path = os.path.join(tmpdir, image_filename)
                        image.save(image_path, 'PNG')
                        zf.write(image_path, image_filename)
                except Exception as e:
                    # Fallback to PyPDF2 if pdf2image fails (e.g., missing Poppler)
                    print(f"pdf2image failed: {e}. Falling back to PyPDF2.")
                    reader = PdfReader(pdf_path)
                    for i, page in enumerate(reader.pages):
                        writer = PdfWriter()
                        writer.add_page(page)
                        page_filename = f"page_{i+1}.pdf"
                        page_path = os.path.join(tmpdir, page_filename)
                        with open(page_path, "wb") as output_pdf:
                            writer.write(output_pdf)
                        zf.write(page_path, page_filename)

            return send_file(output_zip_path, as_attachment=True, download_name="pages.zip", mimetype="application/zip")