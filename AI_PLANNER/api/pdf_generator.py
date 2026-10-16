import io
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to compute total page count and draw
    headers/footers with 'Page X of Y' on every page.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            try:
                self.draw_page_decorations(num_pages)
            except Exception:
                pass
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        try:
            # Header line on pages 2+
            if self._pageNumber > 1:
                self.setStrokeColor(colors.HexColor('#e2e8f0'))
                self.setLineWidth(0.75)
                self.line(36, letter[1] - 28, letter[0] - 36, letter[1] - 28)
                self.setFont('Helvetica-Bold', 8)
                self.setFillColor(colors.HexColor('#94a3b8'))
                self.drawString(36, letter[1] - 24, 'SMART TRAVEL PLANNER • PERSONALIZED ITINERARY')

            # Footer
            self.setStrokeColor(colors.HexColor('#e2e8f0'))
            self.setLineWidth(0.75)
            self.line(36, 30, letter[0] - 36, 30)

            self.setFont('Helvetica', 8)
            self.setFillColor(colors.HexColor('#64748b'))
            self.drawString(36, 18, 'Smart Travel Planner • Generated with AI')
            
            page_text = f'Page {self._pageNumber} of {page_count}'
            self.drawRightString(letter[0] - 36, 18, page_text)
        finally:
            self.restoreState()


def format_inline_markdown(text: str) -> str:
    """Escapes XML entities and formats markdown bold and italic tags."""
    # First escape standard XML entities
    s = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    # Replace bold **text** with <b>text</b>
    s = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', s)
    # Replace italic *text* with <i>text</i>
    s = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'<i>\1</i>', s)
    # Replace inline code `text`
    s = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', s)
    return s


def create_safe_paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    """
    Safely creates a ReportLab Paragraph. If XML parsing fails due to unclosed tags
    or malformed markdown, strips tags and falls back to plain escaped text.
    """
    try:
        return Paragraph(text, style)
    except Exception:
        clean = re.sub(r'<[^>]+>', '', text)
        safe = clean.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return Paragraph(safe, style)


def generate_itinerary_pdf(city: str, duration: str, interests: str, itinerary_markdown: str) -> bytes:
    """
    Renders complete AI itinerary into a high-quality multi-page PDF document
    with zero clipping, proper pagebreaks, and crisp vector typography.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=42
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=4
    )
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=14,
        textColor=colors.HexColor('#475569'),
        spaceAfter=8
    )
    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#b45309'),
        spaceBefore=12,
        spaceAfter=5,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=5
    )
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#1e293b'),
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=4
    )
    quote_style = ParagraphStyle(
        'Quote',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#92400e'),
        backColor=colors.HexColor('#fef3c7'),
        borderColor=colors.HexColor('#f59e0b'),
        borderWidth=1,
        borderPadding=6,
        spaceBefore=5,
        spaceAfter=8,
        keepWithNext=True
    )

    story = []

    # Header branding
    story.append(create_safe_paragraph(
        '✈️ <b>SMART TRAVEL PLANNER</b>',
        ParagraphStyle(
            'Logo',
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=colors.HexColor('#d97706'),
            spaceAfter=2
        )
    ))
    safe_city_title = city.strip().upper() if city else "CUSTOM TRIP"
    story.append(create_safe_paragraph(f'{safe_city_title} DAY TRIP ITINERARY', title_style))
    story.append(create_safe_paragraph(
        f'<b>Destination:</b> {city} &nbsp;|&nbsp; '
        f'<b>Duration:</b> {duration} &nbsp;|&nbsp; '
        f'<b>Interests:</b> {interests}',
        meta_style
    ))
    story.append(HRFlowable(
        width='100%',
        thickness=2,
        color=colors.HexColor('#f59e0b'),
        spaceBefore=0,
        spaceAfter=12
    ))

    # Parse and transform markdown content line by line
    raw_lines = itinerary_markdown.split('\n')
    for raw in raw_lines:
        line = raw.strip()
        if not line:
            continue

        if line.startswith('### '):
            content = format_inline_markdown(line[4:].strip())
            story.append(create_safe_paragraph(content, h2_style))
        elif line.startswith('## '):
            content = format_inline_markdown(line[3:].strip())
            story.append(create_safe_paragraph(content, h2_style))
        elif line.startswith('# '):
            content = format_inline_markdown(line[2:].strip())
            story.append(create_safe_paragraph(content, h1_style))
        elif line.startswith('* ') or line.startswith('- ') or line.startswith('+ '):
            content = format_inline_markdown(line[2:].strip())
            story.append(create_safe_paragraph(f'• {content}', bullet_style))
        elif re.match(r'^\d+\.\s+', line):
            num_match = re.match(r'^(\d+\.\s+)(.*)', line)
            if num_match:
                prefix = num_match.group(1)
                content = format_inline_markdown(num_match.group(2).strip())
                story.append(create_safe_paragraph(f'{prefix}{content}', bullet_style))
            else:
                content = format_inline_markdown(line)
                story.append(create_safe_paragraph(content, bullet_style))
        elif line.startswith('> '):
            content = format_inline_markdown(line[2:].strip())
            story.append(create_safe_paragraph(content, quote_style))
        else:
            content = format_inline_markdown(line)
            story.append(create_safe_paragraph(content, body_style))

    try:
        doc.build(story, canvasmaker=NumberedCanvas)
    except Exception:
        # Fallback to standard document builder if NumberedCanvas encounters an edge case
        buffer = io.BytesIO()
        fallback_doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=42
        )
        fallback_doc.build(story)

    return buffer.getvalue()
