from __future__ import annotations

import io
import os
import tempfile
import pandas as pd
import streamlit as st

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, Image

# Import Core Refactored Layer
from core.inputs import LiftBankInput, DEFAULT_BANKS, BUILDING_TYPES, BUILDING_GRADES, DOOR_TYPES, ZONING_OPTIONS
from core.analytical_engine import clean_input_df, build_analysis_rows, build_recommendation_rows, build_benchmark_rows

st.set_page_config(page_title="VT Engineering Review Platform", page_icon="🛗", layout="wide")

def dataframe_to_pdf_table(df: pd.DataFrame, max_rows: int = 45):
    styles = getSampleStyleSheet()
    cell = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=6.5, leading=8)
    head = ParagraphStyle("Header", parent=styles["Normal"], fontSize=6.5, leading=8, textColor=colors.white, fontName="Helvetica-Bold")
    clean = df.head(max_rows).copy().fillna("")
    data = [[Paragraph(str(c), head) for c in clean.columns]] + [[Paragraph(str(v), cell) for v in row] for row in clean.astype(str).values.tolist()]
    tbl = Table(data, colWidths=[780 / max(1, len(clean.columns))] * len(clean.columns))
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
        ("PADDING", (0, 0), (-1, -1), 2),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))
    return tbl

def save_uploaded_image(image_bytes, image_name):
    if not image_bytes or not image_name: return None
    suffix = os.path.splitext(image_name)[1] or ".png"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(image_bytes)
    tmp.flush()
    tmp.close()
    return tmp.name

def create_pdf(project_name, project_address, prepared_by, logo_bytes, logo_name, photo_bytes, photo_name, input_df, analysis_df, rec_df, bm_df) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=25, leftMargin=25, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("Title", parent=styles["Title"], fontSize=18, textColor=colors.HexColor("#0F172A"), alignment=1)
    sub = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=10, textColor=colors.HexColor("#475569"), alignment=1)
    sec = ParagraphStyle("Sec", parent=styles["Heading2"], fontSize=11, textColor=colors.HexColor("#1E3A8A"), spaceBefore=10, spaceAfter=5)
    
    elements = []
    logo = save_uploaded_image(logo_bytes, logo_name)
    photo = save_uploaded_image(photo_bytes, photo_name)
    
    if logo: elements += [Image(logo, width=110, height=55), Spacer(1, 10)]
    elements += [
        Paragraph("Vertical Transportation Engineering Review", title), Spacer(1, 8),
        Paragraph(f"<b>Project:</b> {project_name}", sub),
        Paragraph(f"<b>Address:</b> {project_address or '-'}", sub),
        Paragraph(f"<b>Prepared By:</b> {prepared_by}", sub), Spacer(1, 14)
    ]
    if photo: elements += [Image(photo, width=360, height=190), Spacer(1, 14)]
    
    elements += [
        Paragraph("Benchmark basis: CIBSE Guide D / ISO 8100-32 style target metrics used for preliminary comparison.", sub),
        Paragraph("Note: final traffic analysis must be verified by elevator specialist/manufacturer.", sub), Spacer(1, 18),
        Paragraph("Tower & Lift Inputs", sec), dataframe_to_pdf_table(input_df),
        Paragraph("Benchmark Targets", sec), dataframe_to_pdf_table(bm_df),
        Paragraph("Result Recommendations", sec), dataframe_to_pdf_table(rec_df),
        Paragraph("Detailed Analysis", sec), dataframe_to_pdf_table(analysis_df)
    ]
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def init_state():
    defaults = {"page": 1, "project_name": "Radiant Tower", "project_address": "", "prepared_by": "ATGC Engineering", "logo_bytes": None, "logo_name": None, "project_photo_bytes": None, "project_photo_name": None, "input_df": DEFAULT_BANKS.copy()}
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

def go_to(page: int): 
    st.session_state.page = page
    st.rerun()

def page_header(step: int): 
    st.caption({1: "Step 1 of 3 — Project Information", 2: "Step 2 of 3 — Tower & Lift Engineering Inputs", 3: "Step 3 of 3 — Benchmarks, Results & Recommendations"}[step])

init_state()

if st.session_state.page == 1:
    page_header(1)
    st.title("🏗️ Project Information")
    project_name = st.text_input("Project Name", value=st.session_state.project_name)
    project_address = st.text_area("Project Address", value=st.session_state.project_address)
    prepared_by = st.text_input("Prepared By", value=st.session_state.prepared_by)
    c1, c2 = st.columns(2)
    with c1:
        logo_file = st.file_uploader("Upload Company Logo", type=["png", "jpg", "jpeg"])
        if logo_file: st.image(logo_file, caption="Company Logo Preview", width=180)
    with c2:
        project_photo = st.file_uploader("Upload Project Photo", type=["png", "jpg", "jpeg"])
        if project_photo: st.image(project_photo, caption="Project Photo Preview", width=260)
        
    if st.button("Next →", type="primary"):
        st.session_state.project_name = project_name
        st.session_state.project_address = project_address
        st.session_state.prepared_by = prepared_by
        if logo_file: 
            st.session_state.logo_bytes = logo_file.getvalue()
            st.session_state.logo_name = logo_file.name
        if project_photo: 
            st.session_state.project_photo_bytes = project_photo.getvalue()
            st.session_state.project_photo_name = project_photo.name
        go_to(2)

elif st.session_state.page == 2:
    page_header(2)
    st.title("🛗 Tower & Lift Engineering Inputs")
    st.write("Include architectural, population, hardware, door, control/zoning, and pit/overhead data.")
    column_config = {
        "building_type": st.column_config.SelectboxColumn("building_type", options=BUILDING_TYPES, required=True),
        "building_grade": st.column_config.SelectboxColumn("building_grade", options=BUILDING_GRADES, required=True),
        "door_type": st.column_config.SelectboxColumn("door_type", options=DOOR_TYPES, required=True),
        "zoning_strategy": st.column_config.SelectboxColumn("zoning_strategy", options=ZONING_OPTIONS, required=True)
    }
    edited_df = st.data_editor(st.session_state.input_df, num_rows="dynamic", use_container_width=True, hide_index=True, column_config=column_config)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Back"): 
            st.session_state.input_df = edited_df
            go_to(1)
    with c2:
        if st.button("Generate Results →", type="primary"): 
            st.session_state.input_df = clean_input_df(edited_df)
            go_to(3)

elif st.session_state.page == 3:
    page_header(3)
    st.title("📊 Benchmarks, Results & Recommendations")
    input_df = clean_input_df(st.session_state.input_df)
    banks = [LiftBankInput(**row) for row in input_df.to_dict(orient="records")]
    
    with st.spinner("Processing traffic profiles and optimizing iterations..."):
        analysis_df = build_analysis_rows(banks)
        rec_df = build_recommendation_rows(banks)
        bm_df = build_benchmark_rows(banks)
        
    st.subheader("Project")
    st.write(f"**Project Name:** {st.session_state.project_name}")
    st.write(f"**Address:** {st.session_state.project_address or '-'}")
    st.write(f"**Prepared By:** {st.session_state.prepared_by}")
    
    if st.session_state.logo_bytes: st.image(st.session_state.logo_bytes, caption="Company Logo", width=150)
    if st.session_state.project_photo_bytes: st.image(st.session_state.project_photo_bytes, caption="Project Photo", width=300)
    
    st.subheader("Benchmark Targets")
    st.dataframe(bm_df, use_container_width=True, hide_index=True)
    st.subheader("Result Recommendations")
    st.dataframe(rec_df, use_container_width=True, hide_index=True)
    st.subheader("Detailed Benchmark Analysis")
    st.dataframe(analysis_df, use_container_width=True, hide_index=True)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Checks", len(analysis_df))
    m2.metric("PASS", int((analysis_df["Result"] == "PASS").sum()) if not analysis_df.empty else 0)
    m3.metric("FAIL", int((analysis_df["Result"] == "FAIL").sum()) if not analysis_df.empty else 0)
    
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        pd.DataFrame([{"Project Name": st.session_state.project_name, "Address": st.session_state.project_address, "Prepared By": st.session_state.prepared_by}]).to_excel(writer, sheet_name="Project Info", index=False)
        input_df.to_excel(writer, sheet_name="Inputs", index=False)
        bm_df.to_excel(writer, sheet_name="Benchmark Targets", index=False)
        rec_df.to_excel(writer, sheet_name="Recommendations", index=False)
        analysis_df.to_excel(writer, sheet_name="Detailed Analysis", index=False)
    excel_buffer.seek(0)
    
    pdf_bytes = create_pdf(st.session_state.project_name, st.session_state.project_address, st.session_state.prepared_by, st.session_state.logo_bytes, st.session_state.logo_name, st.session_state.project_photo_bytes, st.session_state.project_photo_name, input_df, analysis_df, rec_df, bm_df)
    
    st.subheader("Downloads")
    d1, d2, d3 = st.columns(3)
    with d1: st.download_button("Download Excel", data=excel_buffer.getvalue(), file_name="vt_engineering_review.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    with d2: st.download_button("Download PDF", data=pdf_bytes, file_name="vt_engineering_review.pdf", mime="application/pdf", use_container_width=True)
    with d3: st.download_button("Download CSV", data=analysis_df.to_csv(index=False).encode("utf-8-sig"), file_name="vt_detailed_analysis.csv", mime="text/csv", use_container_width=True)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Back to Tower Inputs"): go_to(2)
    with c2:
        if st.button("Start New Project"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()
            
    st.warning("Preliminary benchmark comparison only. Final VT traffic analysis, fire/life-safety compliance and shaft dimensions must be confirmed by the elevator specialist/manufacturer.")