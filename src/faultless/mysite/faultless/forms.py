from django import forms

from .models import Document, Rules


class RuleForm(forms.ModelForm):
    class Meta:
        model = Rules
        fields = ["name", "scale", "description"]
        widgets = {
            "description": forms.Textarea(
                attrs={
                    "class": "inputbox",
                    "id": "description",
                    "placeholder": "Description",
                }
            ),
            "name": forms.Textarea(
                attrs={
                    "class": "name",
                    "id": "name",
                    "placeholder": "Name",
                }
            ),
            "scale": forms.NumberInput(
                attrs={
                    "class": "scale",
                    "id": "scale",
                    "placeholder": "Scale",
                    "max": "5",
                    "min": "1",
                }
            ),
        }


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ("file",)

    def clean_file(self):
        file = self.cleaned_data.get("file", False)
        if file:
            if not file.name.endswith((".doc", ".docx")):
                raise forms.ValidationError("Only .doc and .docx files are allowed")
            return file
        else:
            raise forms.ValidationError("Couldn't read uploaded file")
