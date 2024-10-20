from django import forms

class PDFUploadForm(forms.Form):
    pdf_file = forms.ClearableFileInput(attrs={'allow_multiple_selected': True})
