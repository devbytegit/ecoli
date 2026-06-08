"""
Build a publication-quality Microsoft Word manuscript from paper_draft markdown.

Fixes vs v1:
  - Backtick code text rendered as italic with no literal backtick characters
  - Flowchart rendered as a proper single-column Word table
  - Bullet lists reformatted as proper academic-style lists
  - Numbered sub-lists use correct Word styles with indentation
  - Search queries rendered in a clean table instead of raw code
  - Better spacing and no empty gaps
  - All 9 figures embedded at correct locations
  - Citation references [N] preserved cleanly
  - Professional heading numbering and formatting
"""

import re
import os
import shutil
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

# ── Paths ──────────────────────────────────────────────────────────────
BASE = Path(r"C:\Users\olufi\Desktop\QUICK FILES\ECOLI")
DRAFT = BASE / "paper_draft"
FIGURES = BASE / "data" / "figures"
OUTPUT = BASE / "manuscript" / "ECOLI_Model_Organism_Manuscript.docx"

SECTIONS = [
    "01_abstract.md",
    "02_introduction.md",
    "03_methodology.md",
    "04_results.md",
    "05_discussion.md",
    "06_conclusion.md",
    "07_references.md",
]

# Figure captions
FIGURE_MAP = {
    "fig1_axiomatic_acceptance_gap.png": "Figure 1. The Axiomatic Acceptance Gap \u2014 Justification rates across E. coli, S. cerevisiae, and B. subtilis.",
    "fig2_ecoli_donut.png": "Figure 2. Corpus-wide justification split (Explicit vs. Null).",
    "fig3_corpus_composition.png": "Figure 3. Corpus composition by organism and publication decade (1990\u20132025).",
    "fig4_ecoli_treemap.png": "Figure 4. Treemap of E. coli explicit justification themes.",
    "fig5_umap_publication.png": "Figure 5. 2D UMAP projection of 2,037 justification claim embeddings, colored by cluster.",
    "fig6_cluster_pathway_network.png": "Figure 6. Cluster-to-pathway network mapping (KEGG and EcoCyc).",
    "fig7_temporal_stacked_area.png": "Figure 7. Temporal trajectories of E. coli justification themes (1990\u20132025).",
    "fig8_radar_organism_profiles.png": "Figure 8. Radar chart \u2014 Comparative organism justification profiles.",
    "fig9_heatmap_redesigned.png": "Figure 9. Cross-organism comparative matrix heatmap of normalized justification themes.",
}

# Which figures go after which subsection
SECTION_FIGURES = {
    "after_4.1": ["fig3_corpus_composition.png"],
    "after_4.2": ["fig1_axiomatic_acceptance_gap.png", "fig2_ecoli_donut.png"],
    "after_4.3": ["fig5_umap_publication.png", "fig4_ecoli_treemap.png"],
    "after_4.4": ["fig6_cluster_pathway_network.png"],
    "after_4.5": ["fig7_temporal_stacked_area.png"],
    "after_4.6": ["fig8_radar_organism_profiles.png", "fig9_heatmap_redesigned.png"],
}

# ── Document setup ─────────────────────────────────────────────────────
doc = Document()

# Page setup
for section in doc.sections:
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.18)  # Slightly wider left for binding
    section.right_margin = Cm(2.54)

# Default font
style = doc.styles['Normal']
font = style.font
font.name = 'Times New Roman'
font.size = Pt(12)
font.color.rgb = RGBColor(0, 0, 0)
style.paragraph_format.space_after = Pt(6)
style.paragraph_format.space_before = Pt(0)
style.paragraph_format.line_spacing = 1.15

# Heading styles
for i in range(1, 4):
    hs = doc.styles[f'Heading {i}']
    hs.font.name = 'Times New Roman'
    hs.font.color.rgb = RGBColor(0, 0, 0)
    hs.font.bold = True
    if i == 1:
        hs.font.size = Pt(14)
        hs.paragraph_format.space_before = Pt(24)
        hs.paragraph_format.space_after = Pt(12)
    elif i == 2:
        hs.font.size = Pt(12)
        hs.paragraph_format.space_before = Pt(18)
        hs.paragraph_format.space_after = Pt(6)
    else:
        hs.font.size = Pt(11)
        hs.font.italic = True
        hs.paragraph_format.space_before = Pt(12)
        hs.paragraph_format.space_after = Pt(4)

# List Bullet style
lb = doc.styles['List Bullet']
lb.font.name = 'Times New Roman'
lb.font.size = Pt(11)
lb.paragraph_format.space_after = Pt(3)
lb.paragraph_format.space_before = Pt(1)

# List Number style
ln = doc.styles['List Number']
ln.font.name = 'Times New Roman'
ln.font.size = Pt(11)
ln.paragraph_format.space_after = Pt(3)
ln.paragraph_format.space_before = Pt(1)


# ── Helper functions ───────────────────────────────────────────────────

def clean_fig_paths(text):
    """Remove raw data/figures/ paths from text, keeping Figure N references."""
    # (visualized in Figure X, path)
    text = re.sub(
        r'\((?:visualized (?:in|as) )?(?:a )?(?:\w+ )?(?:in )?(Figure \d+),?\s*data/figures/\w+\.png\)',
        r'(\1)',
        text
    )
    # ; visualized in Figure X, path
    text = re.sub(
        r';\s*visualized in (Figure \d+),?\s*data/figures/\w+\.png',
        r'; \1',
        text
    )
    # standalone path
    text = re.sub(r',?\s*data/figures/\w+\.png', '', text)
    # showing that: (Figure X) at end
    text = re.sub(r'\(visualized (?:in|as a) (Figure \d+)\)', r'(\1)', text)
    return text


def clean_inline_backticks(text):
    """Convert `code` to just the text (no backticks). We apply formatting via runs."""
    # Already handled by add_formatted_runs, but for safety in places
    # where we do plain text operations:
    return text


def add_formatted_runs(paragraph, text):
    """
    Parse inline markdown and add properly formatted Word runs.
    Handles: **bold**, *italic*, $LaTeX$, `code`, and nested combinations.
    No raw markdown syntax remains in the output.
    """
    # Pattern order matters: **bold** before *italic*
    pattern = re.compile(
        r'(\*\*(.+?)\*\*)'          # group 1,2: bold
        r'|(\*([^*]+?)\*)'          # group 3,4: italic (non-greedy, no nested *)
        r'|(\$([^$]+?)\$)'          # group 5,6: LaTeX math
        r'|(`([^`]+?)`)'            # group 7,8: inline code
    )

    pos = 0
    for m in pattern.finditer(text):
        # Plain text before this match
        if m.start() > pos:
            plain = text[pos:m.start()]
            if plain:
                run = paragraph.add_run(plain)
                run.font.name = 'Times New Roman'
                run.font.size = Pt(12)

        if m.group(2):  # Bold
            run = paragraph.add_run(m.group(2))
            run.bold = True
            run.font.name = 'Times New Roman'
            run.font.size = Pt(12)
        elif m.group(4):  # Italic
            run = paragraph.add_run(m.group(4))
            run.italic = True
            run.font.name = 'Times New Roman'
            run.font.size = Pt(12)
        elif m.group(6):  # LaTeX math \u2014 italic
            run = paragraph.add_run(m.group(6))
            run.italic = True
            run.font.name = 'Times New Roman'
            run.font.size = Pt(12)
        elif m.group(8):  # Inline code \u2014 italic, no backticks
            run = paragraph.add_run(m.group(8))
            run.italic = True
            run.font.name = 'Times New Roman'
            run.font.size = Pt(11)

        pos = m.end()

    # Remaining text
    if pos < len(text):
        remaining = text[pos:]
        if remaining:
            run = paragraph.add_run(remaining)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(12)


def add_formatted_runs_small(paragraph, text, size=Pt(10)):
    """Like add_formatted_runs but at a smaller font size (for captions, lists)."""
    pattern = re.compile(
        r'(\*\*(.+?)\*\*)'
        r'|(\*([^*]+?)\*)'
        r'|(\$([^$]+?)\$)'
        r'|(`([^`]+?)`)'
    )
    pos = 0
    for m in pattern.finditer(text):
        if m.start() > pos:
            plain = text[pos:m.start()]
            if plain:
                run = paragraph.add_run(plain)
                run.font.name = 'Times New Roman'
                run.font.size = size
        if m.group(2):
            run = paragraph.add_run(m.group(2))
            run.bold = True
            run.font.name = 'Times New Roman'
            run.font.size = size
        elif m.group(4):
            run = paragraph.add_run(m.group(4))
            run.italic = True
            run.font.name = 'Times New Roman'
            run.font.size = size
        elif m.group(6):
            run = paragraph.add_run(m.group(6))
            run.italic = True
            run.font.name = 'Times New Roman'
            run.font.size = size
        elif m.group(8):
            run = paragraph.add_run(m.group(8))
            run.italic = True
            run.font.name = 'Times New Roman'
            run.font.size = size
        pos = m.end()
    if pos < len(text):
        remaining = text[pos:]
        if remaining:
            run = paragraph.add_run(remaining)
            run.font.name = 'Times New Roman'
            run.font.size = size


def insert_figure(doc, fig_filename, width_inches=5.0):
    """Insert a figure with a centered caption below it."""
    fig_path = FIGURES / fig_filename
    if not fig_path.exists():
        print(f"  WARNING: Figure not found: {fig_path}")
        return
    caption_text = FIGURE_MAP.get(fig_filename, fig_filename)

    # Image paragraph
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run()
    run.add_picture(str(fig_path), width=Inches(width_inches))

    # Caption
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(14)
    cap.paragraph_format.space_before = Pt(2)

    # "Figure N." in bold, rest in normal italic
    fig_num_match = re.match(r'^(Figure \d+\.)\s*(.*)$', caption_text)
    if fig_num_match:
        r1 = cap.add_run(fig_num_match.group(1) + " ")
        r1.bold = True
        r1.italic = True
        r1.font.size = Pt(10)
        r1.font.name = 'Times New Roman'
        r2 = cap.add_run(fig_num_match.group(2))
        r2.italic = True
        r2.font.size = Pt(10)
        r2.font.name = 'Times New Roman'
    else:
        r = cap.add_run(caption_text)
        r.italic = True
        r.font.size = Pt(10)
        r.font.name = 'Times New Roman'


def maybe_insert_figures(section_file, subsection_id):
    """Insert figures queued for after this subsection."""
    if section_file != "04_results.md":
        return
    key = f"after_{subsection_id}"
    if key in SECTION_FIGURES:
        for fig_file in SECTION_FIGURES[key]:
            insert_figure(doc, fig_file)


def parse_table(lines):
    """Parse markdown table lines into list of rows."""
    rows = []
    for line in lines:
        line = line.strip()
        if line.startswith('|') and line.endswith('|'):
            if re.match(r'^\|[\s:\-|]+\|$', line):
                continue
            cells = [c.strip() for c in line.split('|')[1:-1]]
            rows.append(cells)
    return rows


def clean_cell(text):
    """Strip markdown from table cell text."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+?)\*', r'\1', text)
    text = text.replace('`', '')
    return text


def add_table_to_doc(doc, rows):
    """Add a professionally formatted Word table."""
    if not rows:
        return
    num_cols = len(rows[0])
    table = doc.add_table(rows=len(rows), cols=num_cols)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Set preferred widths for the cluster table (6 columns)
    col_widths_cm = None
    if num_cols == 6:
        col_widths_cm = [1.5, 4.0, 1.2, 2.5, 2.0, 5.5]

    for i, row_data in enumerate(rows):
        row = table.rows[i]
        for j, cell_text in enumerate(row_data):
            cell = row.cells[j]
            cell.text = ""
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.space_before = Pt(2)

            clean = clean_cell(cell_text)

            if col_widths_cm and j < len(col_widths_cm):
                cell.width = Cm(col_widths_cm[j])

            if i == 0:
                run = p.add_run(clean)
                run.bold = True
                run.font.size = Pt(8)
                run.font.name = 'Times New Roman'
                shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="2E4057"/>')
                cell._tc.get_or_add_tcPr().append(shading)
                run.font.color.rgb = RGBColor(255, 255, 255)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                run = p.add_run(clean)
                run.font.size = Pt(8)
                run.font.name = 'Times New Roman'
                # Alternate row shading
                if i % 2 == 0:
                    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F2F6FA"/>')
                    cell._tc.get_or_add_tcPr().append(shading)

    doc.add_paragraph()


def add_flowchart_table(doc, phases):
    """Render the methodology pipeline as a clean single-column Word table."""
    if not phases:
        return

    # Add a small label before the table
    label_p = doc.add_paragraph()
    label_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    label_p.paragraph_format.space_before = Pt(8)
    label_p.paragraph_format.space_after = Pt(4)

    num_rows = len(phases) * 2 - 1  # phases + arrows between
    table = doc.add_table(rows=num_rows, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Remove all borders first, then add only for phase cells
    for row_idx in range(num_rows):
        cell = table.rows[row_idx].cells[0]
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()

        # Set width
        cell.width = Cm(12)

        if row_idx % 2 == 0:
            # Phase cell
            phase_idx = row_idx // 2
            phase_text = phases[phase_idx]
            run = p.add_run(phase_text)
            run.bold = True
            run.font.size = Pt(10)
            run.font.name = 'Times New Roman'
            run.font.color.rgb = RGBColor(255, 255, 255)
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)

            # Dark background
            shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="2E4057"/>')
            tcPr.append(shading)

            # Add borders
            borders = parse_xml(
                f'<w:tcBorders {nsdecls("w")}>'
                '  <w:top w:val="single" w:sz="4" w:space="0" w:color="2E4057"/>'
                '  <w:left w:val="single" w:sz="4" w:space="0" w:color="2E4057"/>'
                '  <w:bottom w:val="single" w:sz="4" w:space="0" w:color="2E4057"/>'
                '  <w:right w:val="single" w:sz="4" w:space="0" w:color="2E4057"/>'
                '</w:tcBorders>'
            )
            tcPr.append(borders)
        else:
            # Arrow cell \u2014 no borders, just a down arrow
            run = p.add_run("\u2193")
            run.font.size = Pt(16)
            run.font.name = 'Times New Roman'
            run.font.color.rgb = RGBColor(46, 64, 87)
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)

            # Remove borders
            borders = parse_xml(
                f'<w:tcBorders {nsdecls("w")}>'
                '  <w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                '  <w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                '  <w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                '  <w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                '</w:tcBorders>'
            )
            tcPr.append(borders)

    # Spacing after flowchart
    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(6)


# ── Title Page ─────────────────────────────────────────────────────────
for _ in range(6):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)

title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run(
    "Quantifying the Premier Model Microorganism:\n"
    "A Computational Literature-Mining and Clustering Analysis\n"
    "of Escherichia coli\u2019s Dominance in Molecular Biology"
)
run.bold = True
run.font.size = Pt(16)
run.font.name = 'Times New Roman'
run.font.color.rgb = RGBColor(0, 0, 0)
title.paragraph_format.space_after = Pt(36)
title.paragraph_format.line_spacing = 1.3

# Year
yr = doc.add_paragraph()
yr.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = yr.add_run("2025")
run.font.size = Pt(13)
run.font.name = 'Times New Roman'
yr.paragraph_format.space_after = Pt(6)

doc.add_page_break()


# ── Main Processing ────────────────────────────────────────────────────

def get_subsection_id(heading_text):
    """Extract subsection number like '4.2' from heading text."""
    m = re.match(r'^(\d+\.\d+)', heading_text)
    return m.group(1) if m else None


for section_file in SECTIONS:
    filepath = DRAFT / section_file
    if not filepath.exists():
        print(f"WARNING: Section not found: {filepath}")
        continue

    with open(filepath, 'r', encoding='utf-8') as f:
        raw_lines = f.readlines()

    print(f"Processing: {section_file} ({len(raw_lines)} lines)")

    i = 0
    in_code_block = False
    code_block_lines = []
    in_table = False
    table_lines = []
    current_subsection = None

    while i < len(raw_lines):
        line = raw_lines[i].rstrip('\n')

        # ── Horizontal rules: skip ──
        if line.strip() == '---':
            if current_subsection and section_file == "04_results.md":
                maybe_insert_figures(section_file, current_subsection)
            i += 1
            continue

        # ── Code blocks ──
        if line.strip().startswith('```'):
            if not in_code_block:
                in_code_block = True
                code_block_lines = []
                i += 1
                continue
            else:
                in_code_block = False
                if code_block_lines:
                    # Check if this is the methodology flowchart
                    is_flowchart = any(
                        cl.strip().startswith('[Phase') or cl.strip().startswith('[phase')
                        for cl in code_block_lines
                    )
                    if is_flowchart:
                        phases = []
                        for cl in code_block_lines:
                            cl = cl.strip()
                            if cl.startswith('[') and cl.endswith(']'):
                                phases.append(cl[1:-1])
                        add_flowchart_table(doc, phases)
                    else:
                        # Regular code block \u2014 skip (shouldn't appear in paper)
                        pass
                i += 1
                continue

        if in_code_block:
            code_block_lines.append(line)
            i += 1
            continue

        # ── Tables ──
        if line.strip().startswith('|'):
            if not in_table:
                in_table = True
                table_lines = []
            table_lines.append(line)
            i += 1
            if i >= len(raw_lines) or not raw_lines[i].strip().startswith('|'):
                in_table = False
                rows = parse_table(table_lines)
                add_table_to_doc(doc, rows)
            continue

        # ── Empty lines: skip ──
        if line.strip() == '':
            i += 1
            continue

        # ── Headings ──
        heading_match = re.match(r'^(#{1,4})\s+(.+)$', line)
        if heading_match:
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()

            # Figure insertion for previous subsection
            sub_id = get_subsection_id(heading_text)
            if sub_id:
                if current_subsection and section_file == "04_results.md":
                    maybe_insert_figures(section_file, current_subsection)
                current_subsection = sub_id

            # Clean markdown from heading
            heading_text = re.sub(r'\*\*(.+?)\*\*', r'\1', heading_text)
            heading_text = re.sub(r'\*([^*]+?)\*', r'\1', heading_text)
            heading_text = heading_text.replace('`', '')

            # Handle "Table 4.1: ..." as a special bold centered label
            if heading_text.startswith('Table '):
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_before = Pt(12)
                p.paragraph_format.space_after = Pt(6)
                run = p.add_run(heading_text)
                run.bold = True
                run.font.size = Pt(10)
                run.font.name = 'Times New Roman'
                i += 1
                continue

            doc_level = min(level, 3)
            doc.add_heading(heading_text, level=doc_level)
            i += 1
            continue

        # ── Numbered lists (1. 2. 3.) ──
        num_match = re.match(r'^(\d+)\.\s+(.+)$', line.strip())
        if num_match and not line.strip().startswith('|'):
            text = clean_fig_paths(num_match.group(2))

            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(1.27)
            p.paragraph_format.first_line_indent = Cm(-0.63)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.space_before = Pt(2)

            # Add the number prefix as a run
            num_run = p.add_run(f"{num_match.group(1)}.  ")
            num_run.font.name = 'Times New Roman'
            num_run.font.size = Pt(11)

            add_formatted_runs_small(p, text, Pt(11))
            i += 1
            continue

        # ── Bullet lists ──
        bullet_match = re.match(r'^(\s*)\*\s+(.+)$', line)
        if bullet_match:
            indent_spaces = len(bullet_match.group(1))
            text = clean_fig_paths(bullet_match.group(2))

            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.space_before = Pt(1)

            if indent_spaces >= 4:
                # Sub-bullet: deeper indent, smaller bullet
                p.paragraph_format.left_indent = Cm(2.54)
                p.paragraph_format.first_line_indent = Cm(-0.5)
                bullet_char = "\u2013  "  # en-dash as sub-bullet
            else:
                # Main bullet
                p.paragraph_format.left_indent = Cm(1.27)
                p.paragraph_format.first_line_indent = Cm(-0.5)
                bullet_char = "\u2022  "  # bullet character

            run = p.add_run(bullet_char)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(11)

            add_formatted_runs_small(p, text, Pt(11))
            i += 1
            continue

        # ── Regular paragraphs ──
        para_text = line.strip()
        para_text = clean_fig_paths(para_text)

        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.space_after = Pt(6)

        add_formatted_runs(p, para_text)
        i += 1

    # Insert figures for the LAST subsection in results
    if section_file == "04_results.md" and current_subsection:
        maybe_insert_figures(section_file, current_subsection)

    # Page break between major sections (except after last)
    if section_file != SECTIONS[-1]:
        doc.add_page_break()


# ── Save ───────────────────────────────────────────────────────────────
doc.save(str(OUTPUT))
print(f"\nDocument saved to: {OUTPUT}")
print("Done!")
