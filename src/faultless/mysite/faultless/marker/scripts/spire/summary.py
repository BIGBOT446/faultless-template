import json
import importlib.resources
from spire.doc import Comment, CommentMark, CommentMarkType, Document, Section
from faultless.marker.functions.spire.utils import remove_evaluation_warning
from pathlib import Path

def insert_text_new_page(input_file, tidy_response):
    input_file = Path(input_file)
    output_file = input_file.with_stem(f"{input_file.stem}_modified")

    doc = Document()
    if output_file.exists():
      doc.LoadFromFile(str(output_file))
    else:
      doc.LoadFromFile(str(input_file))

    section = doc.AddSection()
    section.AddParagraph().AppendText(tidy_response)
    doc.SaveToFile(str(output_file))
    doc.Close()
    remove_evaluation_warning(output_file)
    print("Processing completed.")