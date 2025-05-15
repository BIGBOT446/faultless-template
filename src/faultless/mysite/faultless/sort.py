from docx import Document
from .para import Paragraph
from .errors import Error


def sort_para(report):
    report = Document(report)
    output = []
    for para in report.paragraphs:
        output.append(para)
    return output


def sort_error(output):
    all_errors = []
    errors = output["matches"]
    for e in errors:
        new_error = Error(
            e["message"], 
            e["original"],
            e["corrected"],
            e["p_location"],
            e["s_location"],
        )
        all_errors.append(new_error)
    return all_errors

def main(report, output):
    p = sort_para(report)
    errors = sort_error(output)
    all_para = []
    for i in range(len(p)):
        para = Paragraph()
        para.add_body(p[i].text)
        for e in errors:
            if e.p_location == i:
                para.add_error(e)
        all_para.append(para)
    return all_para
