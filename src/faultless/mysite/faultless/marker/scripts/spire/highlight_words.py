# Add Comments to a Paragraph in Word Documents using Python
#
# Reference: https://www.e-iceblue.com/Tutorials/Python/Spire.Doc-for-Python/Program-Guide/Text/Python-Find-and-Highlight-Text-in-Word.html
#
# You can use the Document.FindAllString() method provided by Spire.Doc for Python to find all
# instances of a specified text in a Word document. Then you can loop through these instances and
# highlight each of them with a bright color using TextRange.CharacterFormat.HighlightColor
# property. The detailed steps are as follows:
#
# 1. Create an object of the Document class.
# 2. Load a Word document using Document.LoadFromFile() method.
# 3. Find all instances of a specific text in the document using Document.FindAllString() method.
# 4. Loop through each found instance, and get it as a single text range using TextSelection.GetAsOneRange() method, then highlight the text range with color using TextRange.CharacterFormat.HighlightColor property.
# 5. Save the resulting document using Document.SaveToFile() method.
#
import importlib.resources

# Import CommentMark directly from spire.doc instead of spire.doc.common
from spire.doc import Color, Document

# Import our utility function
from faultless.marker.functions.spire.utils import remove_evaluation_warning

# Define package path as a module-level constant
PACKAGE_PATH = importlib.resources.files("marker.scripts")
input_file = PACKAGE_PATH / "dummy.docx"
output_file = input_file.with_stem(f"{input_file.stem}_modified")

# Create an object of Document class and load a Word document
doc = Document()
doc.LoadFromFile(str(input_file))

# Find the text to comment on
text_selections = doc.FindAllString("advise", False, True)  # noqa: FBT003 Using positional args as required by Spire.Doc

# Loop through all the instances

for selection in text_selections:
    # Get the current instance as a single text range
    text_range = selection.GetAsOneRange()
    # Highlight the text range with a color
    text_range.CharacterFormat.HighlightColor = Color.get_Yellow()

# Save the document
doc.SaveToFile(str(output_file))
doc.Close()

# Remove the "Evaluation Warning" that appears in documents created with the free version of Spire.Doc
remove_evaluation_warning(output_file)
