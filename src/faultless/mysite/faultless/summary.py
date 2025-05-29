from .models import Trace, Rules
from django.core.cache import cache
from faultless.marker.functions.spire.utils import remove_evaluation_warning
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse import Langfuse
from langfuse.callback import CallbackHandler
import spire.doc
import os
from docx import Document
from pathlib import Path
import json

def get_feedback(errors):
    # get keys for your project from https://cloud.langfuse.com
    os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-03837ecb-bae5-4aa2-a319-1afb959284f5"
    os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-b860425a-38b3-4c13-a85c-5b1c0c38605a"
    os.environ["LANGFUSE_HOST"] = "https://cloud.langfuse.com"
    os.environ["GOOGLE_API_KEY"] = "AIzaSyBBYnENqtXiXais7x7t9LANWGEcOQLzA4Q"

    """config_file = Path("./src/faultless/config")
    langfuse_config = get(value="langfuse", file=config_file / "platforms.yml")
    llm_config = get(value="google", file=config_file / "llm.yml")"""

    """langfuse = Langfuse(
        secret_key=langfuse_config["secret_key"],
        public_key=langfuse_config["public_key"],
        host=langfuse_config["host"],
    )"""

    langfuse = Langfuse()

    langfuse.create_prompt(
        name="Summary",
        prompt="You are a given a report and a list of the errors that found in the report. You need to evaluate the quality of the report and give some feedback. A well-crafted summary gives authors a high-level view of issues and guidance on where to start.\n"
        + "Also go through the error list and find out 8 most critical errors in the report."
        + "\n"
        + "\n"
        "return in a json object with following structure:"
        + "\n"
        + "'feedback': <feedback on the report quality and how to improve it>, 'critical_errors': <list of 8 most critical errors(in short description) in the report>"
        + "\n"
        + "\n"
        "Report: " 
        + "\n"
        + "\n"
        "{{report}}"
        + "\n"
        + "\n"
        "Errors: " 
        + "\n"
        + "\n"
        "{{errors}}",
        config={
            "model": "gemini-2.0-flash",
            "temperature": 0,
        },
        labels=["production"],
    )

    langfuse = Langfuse()

    langfuse_callback_handler = CallbackHandler()

    # Get report from the doc
    report = cache.get("selected")
    body = Document(report)
    text = "\n".join([para.text for para in body.paragraphs])

    langfuse_prompt = langfuse.get_prompt("Summary")

    langchain_prompt = ChatPromptTemplate.from_template(
        langfuse_prompt.get_langchain_prompt(),
        metadata={"langfuse_prompt": langfuse_prompt},
    )

    model = langfuse_prompt.config["model"]

    temperature = str(langfuse_prompt.config["temperature"])
    model = ChatGoogleGenerativeAI(model=model, temperature=temperature)
    chain = langchain_prompt | model
    
    error_texts = []
    for error in errors:
        error_texts.append(f"Error Type: {error['error_type']}, Original: {error['original']}, Message: {error['message']}")

    example_input = {
        "report": text,
        "errors": error_texts,
    }
    response = chain.invoke(input=example_input, config={"callbacks": [langfuse_callback_handler]})

    return json.loads(response.content[7:-3])


def write_summary(score, quality, feedback, critical_errors, severity_frequency, type_frequency):
    from .models import Rules
    
    file = Path(cache.get("selected"))
    file = file.with_stem(f"{file.stem}_modified")
    
    # Load the document
    doc = spire.doc.Document()
    doc.LoadFromFile(str(file))
    
    # Get the first section and insert content at the beginning
    first_section = doc.Sections[0]
    
    # Insert paragraphs at the beginning of the document (in reverse order)
    # We'll build the content and insert it at position 0
    
    # First, let's add a page break at the end of our summary (this will be inserted first)
    page_break = first_section.Body.AddParagraph()
    page_break.AppendBreak(spire.doc.BreakType.PageBreak)
    first_section.Body.ChildObjects.Insert(0, page_break)
    
    # Add feedback section (inserting in reverse order)
    feedback_lines = feedback.split('\n')
    for i in range(len(feedback_lines) - 1, -1, -1):
        line = feedback_lines[i]
        if line.strip():
            feedback_para = first_section.Body.AddParagraph()
            feedback_para.AppendText(line.strip())
            feedback_para.Format.AfterSpacing = 8
            first_section.Body.ChildObjects.Insert(0, feedback_para)
    
    # Add feedback title
    feedback_title = first_section.Body.AddParagraph()
    feedback_title.AppendText("Detailed Feedback:")
    feedback_title.Format.IsBold = True
    feedback_title.Format.AfterSpacing = 10
    first_section.Body.ChildObjects.Insert(0, feedback_title)
    
    # Add spacing
    spacing_para2 = first_section.Body.AddParagraph()
    spacing_para2.Format.AfterSpacing = 15
    first_section.Body.ChildObjects.Insert(0, spacing_para2)
    
    # Add critical errors in reverse order
    for i in range(len(critical_errors) - 1, -1, -1):
        error = critical_errors[i]
        error_para = first_section.Body.AddParagraph()
        # Remove the number prefix if it already exists in the error text
        error_text = error.strip()
        if error_text and error_text[0].isdigit() and '. ' in error_text[:3]:
            # Error already has numbering, use it as is
            error_para.AppendText(error_text)
        else:
            # Add numbering if not present
            error_para.AppendText(f"{error_text}")
        error_para.Format.AfterSpacing = 5
        error_para.ListFormat.ApplyNumberedStyle()
        first_section.Body.ChildObjects.Insert(0, error_para)
    
    # Add Top Key Issues title
    issues_title = first_section.Body.AddParagraph()
    issues_title.AppendText(f"Top {len(critical_errors)} Key Issues:")
    issues_title.Format.IsBold = True
    issues_title.Format.AfterSpacing = 10
    first_section.Body.ChildObjects.Insert(0, issues_title)
    
    # Add spacing after table
    spacing_para = first_section.Body.AddParagraph()
    spacing_para.Format.AfterSpacing = 15
    first_section.Body.ChildObjects.Insert(0, spacing_para)
    
    # Create and add table for category breakdown
    table = first_section.Body.AddTable()
    # Dynamic row count based on error types + 1 for header
    row_count = len(type_frequency) + 1
    table.ResetCells(row_count, 3)  # Dynamic rows for categories + 1 header row, 3 columns
    
    # Set table header
    header_cell1 = table.Rows[0].Cells[0]
    header_cell1.CellFormat.VerticalAlignment = spire.doc.VerticalAlignment.Middle
    header_para1 = header_cell1.AddParagraph()
    header_para1.AppendText("Error Type")
    
    header_cell2 = table.Rows[0].Cells[1]
    header_cell2.CellFormat.VerticalAlignment = spire.doc.VerticalAlignment.Middle
    header_para2 = header_cell2.AddParagraph()
    header_para2.AppendText("Count")
    
    header_cell3 = table.Rows[0].Cells[2]
    header_cell3.CellFormat.VerticalAlignment = spire.doc.VerticalAlignment.Middle
    header_para3 = header_cell3.AddParagraph()
    header_para3.AppendText("Penalty")
    
    # Populate table with actual error types and their frequencies
    row_index = 1
    for error_type, count in sorted(type_frequency.items(), key=lambda x: x[1], reverse=True):
        # Get penalty for this error type
        try:
            scale = Rules.objects.get(name=error_type).scale
            if scale <= 2:
                penalty = count * 1  # Minor errors: 1 point each
            elif 2 < scale <= 4:
                penalty = count * 2  # Major errors: 2 points each
            else:
                penalty = count * 5  # Critical errors: 5 points each
        except:
            penalty = 0
        
        cell1 = table.Rows[row_index].Cells[0]
        para1 = cell1.AddParagraph()
        para1.AppendText(error_type)
        
        cell2 = table.Rows[row_index].Cells[1]
        para2 = cell2.AddParagraph()
        para2.AppendText(str(count))
        
        cell3 = table.Rows[row_index].Cells[2]
        para3 = cell3.AddParagraph()
        para3.AppendText(str(penalty))
        
        row_index += 1
    
    # Format table
    table.AutoFit(spire.doc.AutoFitBehaviorType.AutoFitToContents)
    
    # Insert table at beginning
    first_section.Body.ChildObjects.Insert(0, table)
    
    # Add category title
    category_title = first_section.Body.AddParagraph()
    category_title.AppendText("Error Type Breakdown:")
    category_title.Format.IsBold = True
    category_title.Format.AfterSpacing = 10
    first_section.Body.ChildObjects.Insert(0, category_title)
    
    # Add severity summary after quality grade
    severity_summary = first_section.Body.AddParagraph()
    severity_text = f"Severity Summary: {severity_frequency['critical']} Critical, {severity_frequency['major']} Major, {severity_frequency['minor']} Minor errors"
    severity_summary.AppendText(severity_text)
    severity_summary.Format.AfterSpacing = 10
    first_section.Body.ChildObjects.Insert(0, severity_summary)
    
    # Add quality paragraph
    quality_para = first_section.Body.AddParagraph()
    quality_para.AppendText(f"Qualitative Grade: {quality}")
    quality_para.Format.AfterSpacing = 15
    first_section.Body.ChildObjects.Insert(0, quality_para)
    
    # Add score paragraph
    score_para = first_section.Body.AddParagraph()
    score_para.AppendText(f"Overall Document Quality Score: {score}/100")
    score_para.Format.AfterSpacing = 5
    first_section.Body.ChildObjects.Insert(0, score_para)
    
    # Add separator
    separator_para = first_section.Body.AddParagraph()
    separator_para.AppendText("-" * 50)
    first_section.Body.ChildObjects.Insert(0, separator_para)
    
    # Add title
    title_para = first_section.Body.AddParagraph()
    title_para.AppendText("Document Quality Summary")
    # Apply heading style
    title_para.Format.HorizontalAlignment = spire.doc.HorizontalAlignment.Center
    title_text = title_para.Items[0]
    title_text.CharacterFormat.FontSize = 16
    title_text.CharacterFormat.Bold = True
    first_section.Body.ChildObjects.Insert(0, title_para)
    
    # Save the modified document
    doc.SaveToFile(str(file), spire.doc.FileFormat.Docx)
    doc.Close()
    remove_evaluation_warning(file)
    
    print(f"Summary has been added to the document and saved as: {file}")


def document_quality_score(severity_frequency):
    error_score = severity_frequency["minor"] * 1 + severity_frequency["major"] * 2 + severity_frequency["critical"] * 5
    score = max(0, 100 - 0.7 * error_score)

    if score < 50:
        quality = "Poor"
    elif 50 <= score < 75:
        quality = "Average"
    elif 75 <= score < 90:
        quality = "Good"
    elif 90 <= score <= 100:
        quality = "Excellent"

    return score, quality

def summary():
    trace_id = cache.get("trace_id")
    errors = Trace.objects.get(id=trace_id).review_output["matches"]
    unique_errors = []
    severity_frequency = {"minor": 0, "major": 0, "critical": 0}
    type_frequency = {}

    original_words = []
    for error in errors:
        if error["original"] not in original_words:

            # Count frequency of error types and severity
            if error["error_type"] not in type_frequency:
                type_frequency[error["error_type"]] = 1
            else:
                type_frequency[error["error_type"]] += 1
            scales = Rules.objects.get(name=error["error_type"]).scale
            if scales <= 2:
                severity_frequency["minor"] += 1
            elif 2 < scales <= 4:
                severity_frequency["major"] += 1
            else:
                severity_frequency["critical"] += 1
            original_words.append(error["original"])
            unique_errors.append(error)

    score, quality = document_quality_score(severity_frequency)
    feedback_output = get_feedback(unique_errors)
    feedback = feedback_output["feedback"]
    critical_errors = feedback_output["critical_errors"]
    write_summary(score, quality, feedback, critical_errors, severity_frequency, type_frequency)

    
