import json
import importlib.resources
from spire.doc import Comment, CommentMark, CommentMarkType, Document
from faultless.marker.functions.spire.utils import remove_evaluation_warning
from pathlib import Path

def rules(ai_output, input_file):
  # Load output Word document
  input_file = Path(input_file)
  output_file = input_file.with_stem(f"{input_file.stem}_modified")

  doc = Document()
  if output_file.exists():
     doc.LoadFromFile(str(output_file))
  else:
     doc.LoadFromFile(str(input_file))

  # Get full plain text of the document
  full_text = doc.GetText()

  # Add comments for each AI match
  for match in ai_output["matches"]:
      
      section = match["section"]

      # Use FindAllString to get all matches of the word/phrase
      all_matches = doc.FindAllString(section, False, True)

      for i in range(len(all_matches)):
          # Get the specific occurrence based on the occurrence index
          text_selection = all_matches[i]

          # Create the comment
          comment = Comment(doc)
          comment.Body.AddParagraph().Text = match["message"]
          comment.Format.Author = match["error_type"]
          comment.Format.Initial = "AI"

          text_range = text_selection.GetAsOneRange()
          paragraph = text_range.OwnerParagraph

          # Insert comment into the paragraph
          paragraph.ChildObjects.Insert(paragraph.ChildObjects.IndexOf(text_range) + 1, comment)

          # Insert comment marks
          comment_start = CommentMark(doc, CommentMarkType.CommentStart)
          comment_end = CommentMark(doc, CommentMarkType.CommentEnd)
          comment_start.CommentId = comment.Format.CommentId
          comment_end.CommentId = comment.Format.CommentId
          paragraph.ChildObjects.Insert(paragraph.ChildObjects.IndexOf(text_range), comment_start)
          paragraph.ChildObjects.Insert(paragraph.ChildObjects.IndexOf(text_range) + 2, comment_end)

  # Save and clean up
  doc.SaveToFile(str(output_file))
  doc.Close()
  remove_evaluation_warning(output_file)
  print("Processing completed.")




  