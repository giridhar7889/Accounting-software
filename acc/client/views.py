import os
import shutil
import logging
import pandas as pd
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .forms import PDFUploadForm
from .main import *
import csv
from io import BytesIO
import uuid 
# Set up logging
logger = logging.getLogger(__name__)

# Global dictionaries
df_dict = pd.DataFrame()       # Complete transaction data
df_dict_ai = pd.DataFrame()    # AI-processed and deduplicated data for client review

# Handle the file upload and processing
def home(request):
    global df_dict, df_dict_ai
    if request.method == 'POST':
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist('pdf_file')  # Get list of uploaded files

            # Check if multiple files were uploaded
            if len(files) > 1:
                # Create a directory to hold the multiple files
                upload_dir = handle_directory_upload(files)
                file_path_or_dir = upload_dir  # Pass the directory to main()
            else:
                # Handle single file upload
                pdf_file = files[0]
                file_path = handle_uploaded_file(pdf_file)
                file_path_or_dir = file_path  # Pass the file path to main()

            try:
                # Call the main() function to process either the file or directory
                df_complete = main(file_path_or_dir)
                df_complete['primary_key'] = df_complete.apply(lambda row: uuid.uuid4(), axis=1)
                # Store the pre-processed df_complete in df_dict
                df_dict = df_complete.copy()
               # print(df_dict.to_string())
                # Process AI suggestions and deduplicate
                #filling the description using memo
                df_complete[description_config] = df_complete.apply(
                    lambda row: process_description(row[memo_config]) if pd.isna(row[description_config]) else row[description_config],
                    axis=1
                )
                print(df_complete.to_string())
                df_dict=df_complete.copy()
                # Create the summary DataFrame for Vendors/Payees
                df_dict_ai = df_complete.drop_duplicates(subset=description_config, keep='first', ignore_index=True).copy()

                df_dict_ai['primary_key'] = df_complete['primary_key']
                print("Before applying AI edits:")
                print(df_dict_ai.to_string())

# Ensure the AI function is called properly
                df_dict_ai.loc[:, ai_vendor_payee_config] = df_dict_ai.apply(
    lambda row: edit(row[description_config]) if pd.isna(row[ai_vendor_payee_config]) else row[ai_vendor_payee_config],
    axis=1
)

# Output the modified DataFrame
                print("After applying AI edits:")
                print(df_dict_ai.to_string())
               
                # Update df_dict_ai to ensure uniqueness
                df_dict_ai = df_dict_ai.drop_duplicates(subset=ai_vendor_payee_config, keep='first', ignore_index=True)
                print("this is ai rows below ")
                print(df_dict_ai.to_string())
                # Send df_dict_ai (deduplicated) to the client for review
                if not df_dict_ai.empty:
                    json_data = df_dict_ai.to_dict(orient='records')
                    print('json data')
                    print(json_data)
                    return JsonResponse({'data': json_data})
                else:
                    return JsonResponse({'data': []})

            except Exception as e:
                logger.error(f"Error processing file: {e}")
                return HttpResponse(f"Error processing file: {e}")
    else:
        form = PDFUploadForm()

    return render(request, 'client/home.html', {'form': form})


# View to handle saving edited rows
@csrf_exempt
def save_edits(request):
    global df_dict, df_dict_ai

    if request.method == 'POST':
        try:
            # Parse the incoming JSON data
            data = json.loads(request.body)
            row_index = data['index']
            updated_row = data['updated_row']

            # Find the corresponding row in df_dict using ai_vendor_payee_config to identify the unique entry
            # Update df_dict and df_dict_ai with the new values
            
            description = df_dict_ai.at[row_index, description_config]
            # Update both df_dict and df_dict_ai with the edited information
            for key, value in updated_row.items():
                     
                     df_dict_ai.at[row_index, key] = value

                
             

            return JsonResponse({'status': 'success'})
        except Exception as e:
            logger.error(f"Error updating row: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


# View for displaying the review page with account info (deduplicated view for client)
def review_account(request):
    global df_dict_ai
    for key in df_dict_ai.keys():
         print(key)
    # Check if df_dict_ai is not empty
    # Update df_dict using description as the key
    
    if not df_dict_ai.empty:
        return render(request, 'client/review_account.html', {'data': df_dict_ai.to_dict(orient='records')})
    else:
        return HttpResponse("No account data to display.")


# Helper function to handle multiple file uploads
def handle_directory_upload(files):
    upload_dir = 'uploads/multiple_files/'
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    # Save each file in the directory
    for file in files:
        file_path = os.path.join(upload_dir, file.name)
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

    return upload_dir  # Return the directory path


# Helper function to save a single file
def handle_uploaded_file(f):
    upload_path = 'uploads/'
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
    file_path = os.path.join(upload_path, f.name)
    with open(file_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return file_path

@csrf_exempt
def update_account(request):
    global df_dict, df_dict_ai

    if request.method == 'POST':
        try:
            # Parse the incoming JSON data from the POST request
            data = json.loads(request.body)
            row_index = data.get('index')  # Use get() to avoid KeyError if 'index' is missing
            
            # Check if row_index is a valid integer
            try:
                row_index = int(row_index)
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Invalid index'}, status=400)

            account_value = data['account']  # Get the new account value

            # Validate the account_value
            if not account_value or not isinstance(account_value, str):
                return JsonResponse({'status': 'error', 'message': 'Invalid account value'}, status=400)
            description = df_dict_ai.iloc[row_index][description_config]
            df_dict_ai.loc[df_dict_ai.index[row_index], 'Account'] = account_value

            logger.info(f"Account updated successfully for row {row_index}: {account_value}")
            return JsonResponse({'status': 'success', 'message': 'Account information updated successfully'})
            # Check if the row index exists in both dataframes
            if row_index in df_dict_ai.index and row_index in df_dict.index:
                # Update the 'Account' field in df_dict_ai
                df_dict_ai.at[row_index, 'Account'] = account_value

                # Update the 'Account' field in df_dict (matching by 'Suggested_Vendor_Payee')
                vendor_payee_key = df_dict_ai.at[row_index, 'Suggested_Vendor_Payee']
                df_dict.loc[df_dict['Suggested_Vendor_Payee'] == vendor_payee_key, 'Account'] = account_value

                logger.info(f"Account updated successfully for row {row_index}: {account_value}")
                return JsonResponse({'status': 'success', 'message': 'Account information updated successfully'})

            else:
                logger.warning(f"Row index '{row_index}' not found in dataframes")
                return JsonResponse({'status': 'error', 'message': 'Row index not found in data'}, status=404)

        except Exception as e:
            logger.error(f"Error updating account: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    # If the request is not POST, return an error response
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)



# Assuming df_dict and df_dict_ai are already defined as global DataFrames

# View to render the download page
def download_page(request):
    global df_dict, df_dict_ai
    print("entered downloads page")
    
    # Update df_dict using description as the key
    print(df_dict.to_string())
    for idx, row in df_dict_ai.iterrows():
        description = row[description_config]
        print(description)
        df_dict.loc[df_dict[description_config] == description, 'Account'] = row['Account']
        df_dict.loc[df_dict[description_config] == description, 'Suggested_Vendor_Payee'] = row['Suggested_Vendor_Payee']

    # Use df_dict_ai if it exists, otherwise fall back to df_dict
    transactions = df_dict
    print('df_dict')
    print(df_dict.to_string())
    # Convert DataFrame to a list of dictionaries to pass to the template
    transactions_list = transactions.to_dict('records')
    # print(transactions_list)
    print('transactionscolumns')

    print(transactions.columns)  # Print column names of df_dict

    return render(request, 'client/download.html', {'transactions': transactions_list})

# View to download as CSV
def download_csv(request):
    global df_dict, df_dict_ai

    # Use df_dict_ai if it exists, otherwise fall back to df_dict
    transactions = df_dict

    # Create a CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'

    writer = csv.writer(response)
    writer.writerow(transactions.columns)  # Write CSV header
    for index, row in transactions.iterrows():
        writer.writerow(row)  # Write data rows

    return response


# View to download as Excel
def download_excel(request):
    global df_dict, df_dict_ai

    # Use df_dict_ai if it exists, otherwise fall back to df_dict
    transactions = df_dict

    # Create an Excel response
    output = BytesIO()
    
    # Use the xlsxwriter engine in Pandas
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        transactions.to_excel(writer, sheet_name='Transactions', index=False)

    # After the writer is closed, we need to seek to the beginning of the BytesIO stream
    output.seek(0)

    # Create the HTTP response for downloading the Excel file
    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="transactions.xlsx"'

    return response

