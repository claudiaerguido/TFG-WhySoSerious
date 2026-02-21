from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import markdown
import re
import os

def create_pdf(input_md, output_pdf):
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.darkblue
    )
    
    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=18,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.black
    )
    
    h3_style = ParagraphStyle(
        'CustomH3',
        parent=styles['Heading3'],
        fontSize=14,
        spaceBefore=15,
        spaceAfter=5,
        textColor=colors.darkgrey
    )
    
    body_style = styles['BodyText']
    body_style.fontSize = 11
    body_style.leading = 14

    story = []

    try:
        with open(input_md, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: Could not find input file {input_md}")
        return

    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('# '):
            story.append(Paragraph(line[2:], title_style))
            story.append(Spacer(1, 12))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:], h2_style))
        elif line.startswith('### '):
            story.append(Paragraph(line[4:], h3_style))
        elif line.startswith('!['):
            # Image handling: ![Alt](path)
            match = re.search(r'\!\[.*?\]\((.*?)\)', line)
            if match:
                img_path = match.group(1)
                # Resolve relative path
                if not os.path.isabs(img_path):
                     # input_md is 'documentacion/documentacion.md'
                     # img_path might be 'imagenes/foo.png'
                     # so we join dirname(input_md) + img_path
                     base_dir = os.path.dirname(input_md)
                     img_path = os.path.join(base_dir, img_path)
                
                if os.path.exists(img_path):
                    try:
                        im = Image(img_path)
                        # Resize if too wide
                        max_width = 450
                        if im.drawWidth > max_width:
                            ratio = max_width / im.drawWidth
                            im.drawHeight = im.drawHeight * ratio
                            im.drawWidth = max_width
                        story.append(im)
                        story.append(Spacer(1, 12))
                        # Add caption if available in alt text? skipping for now
                    except Exception as e:
                         print(f"Error processing image {img_path}: {e}")
                         story.append(Paragraph(f"[Error: Image not found or valid: {img_path}]", body_style))
                else:
                    story.append(Paragraph(f"[Image not found: {img_path}]", body_style))

        elif line.startswith('* ') or line.startswith('- '):
            # Basic bullet point handling
            story.append(Paragraph(f"• {line[2:]}", body_style))
        else:
            # Simple text
            # Replace bold markdown **text** with HTML <b>text</b> for reportlab
            line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
            story.append(Paragraph(line, body_style))
            story.append(Spacer(1, 6))

    try:
        doc.build(story)
        print(f"PDF generado: {output_pdf}")
    except Exception as e:
        print(f"Error building PDF: {e}")

if __name__ == "__main__":
    create_pdf("documentacion/documentacion.md", "documentacion/documentacion.pdf")
