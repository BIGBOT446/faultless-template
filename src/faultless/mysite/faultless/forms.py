from django import forms
from .models import Document, Rules
import json


class RuleForm(forms.ModelForm):
    class Meta:
        model = Rules
        fields = ["name", "scale", "description", "output_format"]
        widgets = {
            "description": forms.Textarea(
                attrs={
                    "class": "inputbox",
                    "id": "description",
                    "placeholder": "Description",
                    "style": "width: 100%; height: 200px;",
                }
            ),
            "name": forms.Textarea(
                attrs={
                    "class": "name",
                    "id": "name",
                    "placeholder": "Name",
                    "style": "width: 100%; height: 50px;",
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
            "output_format": forms.Textarea(
                attrs={
                    "rows": 10,
                    "cols": 60,
                    "placeholder": '{"matches": [{"error_type": "", "message": "", "original": "", "occurrence_index": ""}]}',
                    "style": "width: 100%; height: 200px;",
                }
            ),
        }
    

    def clean_output_format(self):
        raw_data = self.cleaned_data.get('output_format')

        # Structure validation
        if not isinstance(raw_data, dict) or 'matches' not in raw_data:
            raise forms.ValidationError("JSON must be an object with a 'matches' key.")

        if not isinstance(raw_data['matches'], list):
            raise forms.ValidationError("'matches' must be a list.")

        for match in raw_data['matches']:
            if not isinstance(match, dict):
                raise forms.ValidationError("Each item in 'matches' must be a dictionary.")

            required_keys = {"error_type", "message", "original", "occurrence_index"}
            if set(match.keys()) != required_keys:
                raise forms.ValidationError(f"Each match must have exactly these keys: {required_keys}")

            for key in required_keys:
                if not isinstance(match[key], str):
                    raise forms.ValidationError(f"'{key}' must be a string.")

        return raw_data


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
