from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY

def generate_pdf():
    doc = SimpleDocTemplate("backend/data/ADA_2025_Clinical_Guidelines.pdf", pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    Story = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))

    title = "2025 American Diabetes Association (ADA) Clinical Guidelines"
    Story.append(Paragraph(title, styles["Title"]))
    Story.append(Spacer(1, 12))

    section1 = "Section 9: Pharmacologic Approaches to Glycemic Treatment"
    Story.append(Paragraph(section1, styles["Heading2"]))
    Story.append(Spacer(1, 6))

    text1 = """Metformin remains the preferred initial pharmacologic agent for the treatment of type 2 diabetes. 
    However, the 2025 guidelines emphasize that early combination therapy should be considered in more patients 
    at treatment initiation to extend the time to treatment failure and preserve beta-cell function."""
    Story.append(Paragraph(text1, styles["Justify"]))
    Story.append(Spacer(1, 12))

    text2 = """For patients with established atherosclerotic cardiovascular disease (ASCVD) or indicators of high 
    ASCVD risk (such as patients >55 years of age with coronary, carotid or lower-extremity artery stenosis >50% 
    or left ventricular hypertrophy), a sodium-glucose cotransporter 2 (SGLT2) inhibitor or glucagon-like peptide 1 
    (GLP-1) receptor agonist with demonstrated cardiovascular disease benefit is highly recommended."""
    Story.append(Paragraph(text2, styles["Justify"]))
    Story.append(Spacer(1, 12))

    section2 = "Section 10: Cardiovascular Disease and Risk Management"
    Story.append(Paragraph(section2, styles["Heading2"]))
    Story.append(Spacer(1, 6))

    text3 = """Blood pressure should be measured at every routine clinical visit. Patients with blood pressure >= 140/90 mmHg 
    should have blood pressure confirmed using multiple readings, including measurements on a separate day, to diagnose hypertension. 
    All hypertensive patients with diabetes should monitor their blood pressure at home. Treatment for hypertension should include 
    lifestyle interventions and pharmacologic therapy."""
    Story.append(Paragraph(text3, styles["Justify"]))
    Story.append(Spacer(1, 12))

    section3 = "Section 11: Chronic Kidney Disease and Risk Management"
    Story.append(Paragraph(section3, styles["Heading2"]))
    Story.append(Spacer(1, 6))

    text4 = """At least once a year, assess urinary albumin (e.g., spot urinary albumin-to-creatinine ratio) and 
    estimated glomerular filtration rate (eGFR) in patients with type 1 diabetes with duration of >= 5 years and in all 
    patients with type 2 diabetes regardless of treatment. Patients with urinary albumin >= 300 mg/g and eGFR >= 20 
    should be treated with an SGLT2 inhibitor to reduce CKD progression and cardiovascular events."""
    Story.append(Paragraph(text4, styles["Justify"]))
    Story.append(Spacer(1, 12))

    doc.build(Story)

if __name__ == "__main__":
    generate_pdf()
    print("Created backend/data/ADA_2025_Clinical_Guidelines.pdf")
