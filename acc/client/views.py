# fileupload/views.py
import os


from django.shortcuts import render
from django.http import HttpResponse
from .forms import PDFUploadForm
from .main import *


# Handle the file upload and processing
def home(request):
    if request.method == 'POST':
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            pdf_file = request.FILES['pdf_file']
            file_path = handle_uploaded_file(pdf_file)
            try:
                # Call your main() function to process the file
                result = main(file_path)
                return HttpResponse("File processed successfully.")
            except Exception as e:
                return HttpResponse(f"Error processing file: {e}")
    else:
        form = PDFUploadForm()
    return render(request, 'client/home.html', {'form': form})

# Helper function to save the uploaded file temporarily
def handle_uploaded_file(f):
    upload_path = 'uploads/'
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
    file_path = os.path.join(upload_path, f.name)
    with open(file_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return file_path
