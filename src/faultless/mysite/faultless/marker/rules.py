import json
from spire.doc import Comment, CommentMark, CommentMarkType, Document, Color
from .utils import remove_evaluation_warning
from pathlib import Path
from spire.doc import FileFormat
from faultless.models import Rules

def rules(ai_output, input_file):
    input_file = Path(input_file)
    # Load or create the output Word document
    output_file = input_file.with_stem(f"{input_file.stem}_modified")
    doc = Document()
    if output_file.exists():
        doc.LoadFromFile(str(output_file))
    else:
        doc.LoadFromFile(str(input_file))

    # (Optional) Clean evaluation warning text from full text if present
    full_text = doc.GetText()
    cleaned_text = full_text.replace(
        "Evaluation Warning: The document was created with Spire.Doc for Python.", ""
    ).strip()

    # Loop through each match from the AI output
    for match in ai_output["matches"]:
        original = match["original"]
        occurrence_index = int(match.get("occurrence_index", 1))
        message = match["message"]
        error_type = match["error_type"]

        # Check the scale level
        scale = Rules.objects.get(name=error_type).scale
        if scale <= 2:
            level = "minor"
        elif 2 < scale <= 4:
            level = "major"
        else:
            level = "critical"
        error_type = f" [{level.upper()}]" + " " + error_type
    
        # Find all occurrences of the original text in the document
        all_matches = doc.FindAllString(original, False, True)

        if not all_matches or len(all_matches) < int(occurrence_index):
            print(f"Text '{original}' (occurrence {occurrence_index}) not found in document.")
            continue

        # Get the specific occurrence to comment (1-based index in the text)
        text_selection = all_matches[occurrence_index - 1]

        # Create a new comment with the AI's message
        comment = Comment(doc)
        comment.Body.AddParagraph().Text = message
        comment.Format.Author = error_type
        comment.Format.Initial = "AI"

        # Identify the range of text to attach the comment to
        text_range = text_selection.GetAsOneRange()
        paragraph = text_range.OwnerParagraph

        if not isinstance(paragraph.OwnerTextBody.Owner, Comment):
            if level == "critical":
                text_range.CharacterFormat.HighlightColor = Color.get_Red()
            elif level == "major":
                text_range.CharacterFormat.HighlightColor = Color.get_Yellow()
            else:  # minor
                text_range.CharacterFormat.HighlightColor = Color.get_Green()

        # Insert the comment and comment marks around the text range
        paragraph.ChildObjects.Insert(paragraph.ChildObjects.IndexOf(text_range) + 1, comment)
        comment_start = CommentMark(doc, CommentMarkType.CommentStart)
        comment_end = CommentMark(doc, CommentMarkType.CommentEnd)
        comment_start.CommentId = comment.Format.CommentId
        comment_end.CommentId = comment.Format.CommentId
        idx = paragraph.ChildObjects.IndexOf(text_range)
        paragraph.ChildObjects.Insert(idx, comment_start)
        paragraph.ChildObjects.Insert(idx + 2, comment_end)
        """paragraph.ChildObjects.Insert(paragraph.ChildObjects.IndexOf(text_range), comment_start)
        paragraph.ChildObjects.Insert(paragraph.ChildObjects.IndexOf(text_range) + 2, comment_end)"""

    # Save changes to a new file and remove any evaluation warning text
    doc.SaveToFile(str(output_file), FileFormat.Docx)
    doc.Close()
    remove_evaluation_warning(output_file)
    print("Grammar/spelling check comments inserted successfully.")
