import PyPDF2
import sys

def extract_text(pdf_path, txt_path):
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ''
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += f"--- PAGE {page_num + 1} ---\n"
                text += page.extract_text() + "\n\n"
            
        with open(txt_path, 'w', encoding='utf-8') as out_file:
            out_file.write(text)
        print("Extraction successful.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    pdf_path = r"c:\Users\mezya\OneDrive\Desktop\python project\docs\Rapport_SondagePro_Django (1).pdf"
    txt_path = r"c:\Users\mezya\OneDrive\Desktop\python project\docs\extracted_text.txt"
    extract_text(pdf_path, txt_path)
