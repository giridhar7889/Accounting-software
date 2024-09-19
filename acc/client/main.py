#first run main
#second run history
#third copy paste and rename payee to description 
#fourth fill in the values and get empty values pycharm

import pandas as pd
import random
import pdfplumber
from .config import *
import os
import datetime
import re
from .process_description import *
from .chase import *
from .ai import edit

def format_date(date):
    pattern_date = re.compile(r'^\d{1,2}\/\d{1,2}\/\d{2,4}$')
    if pattern_date.match(date):
        month, day, year = date.split('/')
        month = month.zfill(2)
        day = day.zfill(2)
        if len(year) == 2:
            year = base_year_config + year
        formatted_date = f'{month}/{day}/{year}'
        return formatted_date
    else: 
        return date

# Function to extract text and other information from a page
def extract_original(page):
    text = page.extract_text()
    # print('text!')
    # print(text)
    count = text.lower().count('page')
    account_activity = text.lower().count('account activity')
    h = page.height
    w = page.width
    return text, count, h, w, account_activity

# Function to get table data from a cropped page
def get_table_data(table_settings, page1): 
    # pageim = page1.to_image()
    table = page1.extract_table(table_settings)
    return table

# Function to convert table to DataFrame
def print_df(table): 
    df = pd.DataFrame(table[1:], columns=table[0]).reset_index(drop=True)
    return df

# Function to process each page and extract the table
def get_rows(page):
    text, count, h, w , account_activity = extract_original(page)
    if count == 0: 
        print('no crop found in the pdf and skips page')
        return None
    else: 
        while True: 
            if count == 0:
                break
            h = h - 9
            crop_box = (0, 0, w, h)
            page1 = page.within_bbox(crop_box)
            text = page1.extract_text()
            count1 = text.lower().count('page')
            if count > count1: 
                break
        # return page1
        table = get_table_data(table_settings, page1)
        return table

# Open the PDF file
def bank_main(file_path):
    pdf = pdfplumber.open(file_path)
    all_pages = []  # List to store all DataFrames

    # Loop through each page and extract the table
    for page in pdf.pages: 
        table = get_rows(page)
        if table is not None:  # Check if table extraction was successful
            try:
                df = print_df(table).reset_index(drop=True)
                common_columns = ['', '', '', '']
                df = df.reindex(columns=common_columns)
                all_pages.append(df)
            except Exception as e: 
                print(f"Error processing page: {e}")

    # Combine all DataFrames into a single DataFrame
    if all_pages:  # Ensure that all_pages is not empty
        combined_df = pd.concat(all_pages, ignore_index=True)
        combined_df = combined_df[~(combined_df == '').all(axis=1)]
        return combined_df
    else:
        print("No tables found in the PDF.")
        return pd.DataFrame()  # Return an empty DataFrame if no tables are found

def is_valid_date(date_str):
    pattern_date = re.compile(r'^\d{1,2}\/\d{1,2}\/\d{2,4}$')
    """Check if the date_str matches MM/DD/YYYY format."""
    if pd.isna(date_str):
        return False
    if bool(pattern_date.match(date_str)) == True:
        return bool(pattern_date.match(date_str))
    else: 
        # print(f'wrong date {date_str}')
        return bool(pattern_date.match(date_str))



# Apply function to filter DataFrame

#return df
def driver(file_path, bank):
    print('driver running')
    if os.path.isdir(file_path):
        all_df = []  # Flat list to store all DataFrames from all files
        for filename in os.listdir(file_path):
            # print('inside driver loop')
            full_path = os.path.join(file_path, filename)
            if full_path.startswith('.') or not full_path.lower().endswith('.pdf'):
                continue
            if os.path.isfile(full_path):  # Check if it's a file')
                if bank == bank_config[0]:
                    try: 
                        # print('equals to first bank_config')
                        combined_df = bank_main(full_path)
                        # print(combined_df)
                        all_df.append(combined_df)
                    except Exception as e: 
                        print(f'Problem with bank_main {full_path}: {e}')
                elif bank == bank_config[1] or bank== bank_config[2]:
                    try: 
                        combined_df = chase(full_path)
                        all_df.append(combined_df)
                    except Exception as e: 
                        print(f'ID 2 Problem with {full_path}: {e}')
        # Concatenate all DataFrames from all files
        if bank == bank_config[0]:
            print('driver out of loop running')
            if all_df:  # Ensure that all_df is not empty
                print('all_df exists')
                final_combined_df = pd.concat(all_df, ignore_index=True)
                final_combined_df = final_combined_df[~(final_combined_df == '').all(axis=1)]
                # print(final_combined_df.shape)
                columns = columns_config
                if len(final_combined_df.columns) == len(columns):
                    final_combined_df.columns = columns
                else:
                    print("The number of columns does not match the length of the column names list.")

                final_combined_df = final_combined_df[final_combined_df['Date'].apply(is_valid_date)]
                final_combined_df['Date'] = final_combined_df['Date'].apply(format_date).astype(str)
                final_combined_df = final_combined_df[final_combined_df[memo_config].str.strip() != 'BEGINNING BALANCE']
                final_combined_df[description_config] = None
                final_combined_df['Account']=None
                final_combined_df[description_config] = final_combined_df[memo_config].apply(process_description)
                final_combined_df = final_combined_df[all_columns_config]
                
                # print(final_combined_df.to_string())
                final_combined_df.reset_index(drop=True, inplace=True)
                return final_combined_df
                #update entire df instead of Memo column
                # copy = final_combined_df[memo_config]
                # copy.to_clipboard(index = True)
            else:
                print("No tables found in any of the files.")
                
        elif bank == bank_config[1] or bank== bank_config[2]:
            print('second option combine')
            final_combined_df = pd.concat(all_df, ignore_index=True)
            return final_combined_df
            #all_df['Memo'].to_clipboard(index = True)

    #add extra section for individual files
    else:
        if os.path.isfile(file_path):  # Check if it's a file
            if bank == bank_config[0]:
                m_and_t_file(file_path)
            if bank == bank_config[1] or bank== bank_config[2]:
                print('is file chase bank')
                df = chase(file_path) #returns df
                return df
            

def m_and_t_file(file_path):
    try: 
        combined_df = bank_main(file_path) #instead of full_path
        all_df = combined_df #instead of append
        if not all_df.empty:  # Ensure that all_df is not empty
            final_combined_df = all_df #instead of concat
            final_combined_df = final_combined_df[~(final_combined_df == '').all(axis=1)]
            # print(final_combined_df.shape)
            columns = columns_config
            if len(final_combined_df.columns) == len(columns):
                final_combined_df.columns = columns
            else:
                print("The number of columns does not match the length of the column names list.")

            final_combined_df = final_combined_df[final_combined_df['Date'].apply(is_valid_date)]
            final_combined_df['Date'] = final_combined_df['Date'].apply(format_date).astype(str)
            final_combined_df = final_combined_df[final_combined_df[memo_config].str.strip() != 'BEGINNING BALANCE']
            final_combined_df[description_config] = None
            final_combined_df['Account']=None
            final_combined_df[description_config] = final_combined_df[memo_config].apply(process_description)
            final_combined_df = final_combined_df[all_columns_config]
            
            # print(final_combined_df.to_string())
            final_combined_df.reset_index(drop=True, inplace=True)
            # final_combined_df.to_clipboard(index = True)
        else:
            print("No tables found in any of the files.")
    except Exception as e: 
        print(f'M_and_T with {file_path}: {e}') #instead of full_path

        

def get_bank(file_path, bank): 
    pdf = pdfplumber.open(file_path)
    for page in pdf.pages:
        text = page.extract_text()
        print(text)
        bank_count = text.upper().count(bank)
        if bank_count > 0: 
            return bank
        else:
            return False

def main(file_path):
    print("welcome to main")
    print(file_path)
    if os.path.isdir(file_path):
        files_same_bank = []
        for filename in os.listdir(file_path):
            full_path = os.path.join(file_path, filename)
            if full_path.startswith('.') or not full_path.lower().endswith('.pdf'):
                continue
            if os.path.isfile(full_path):  # Check if it's a file
                print('checks passed')
                is_bank = check_bank(full_path, file_path)
                files_same_bank.append(is_bank)

        if is_bank and all(x==files_same_bank[0] for x in files_same_bank) if files_same_bank else False:
            df = driver(file_path, is_bank)
            return df
    else:
        if file_path.startswith('.') or not file_path.lower().endswith('.pdf'):
            pass
        if os.path.isfile(file_path):
            # print('this is it 1')
            is_bank = check_bank(file_path, file_path)  # Check if it's a file
        if is_bank:
            df = driver(file_path,is_bank)
            return df

def check_bank(file_full_path, file_path):
    try: 
        for bank in bank_config: 
            if file_full_path.startswith('.') or not file_full_path.lower().endswith('.pdf'):
                # print('filepath name')
                # print(file_full_path)
                continue
            is_bank = get_bank(file_full_path, bank)
            # print('i am here')
            # print('this is bank')
            print(is_bank)
            if is_bank: 
                return is_bank
        if not is_bank: 
            print("We cannot process your bank yet.")
    except Exception as e: 
        print(f'Problem with check_bank {file_full_path}: {e}')

    # try: 
    #     is_bank_1 = get_bank(file_full_path, bank_config)
    #     if is_bank_1: 
    #         print('i am chase')
    #     else: 
    #         print('we cannot process your bank')
    #         # chase(file_full_path)
    # except Exception as e: 
    #     print(f'1 Problem with {file_full_path}: {e}')

#1st block
# update uncomment   
df_complete = main(file_path_config)
# df_complete.to_clipboard()
# print(df_complete.to_string())

# print(df.to_string())
# print(df[memo_config].to_string())
df_complete[description_config] = df_complete.apply(
    lambda row: process_description(row[memo_config]) if pd.isna(row[description_config]) else row[description_config],
    axis=1
) 

# print(df_complete.to_string())

# print(df.to_string())
df_summary = df_complete.drop_duplicates(subset=description_config,keep='first',ignore_index=True)
# print('df summar')
# print(df_summary.to_string())
# df_summary.to_clipboard()

dfcopy = df_summary[[description_config,memo_config,deposit_config,withdrawal_config]]
# dfcopy.to_clipboard()
# print(dfcopy.to_string())

# df_description = pd.Series(df[description_config].unique())
# df_description.to_clipboard()
# print(df_description.to_string())


#uncomment block for AI 

# def edit(text):
#     count = random.randint(1,10000)
#     text=count
#     return text

# df_ai = dfcopy.copy()
df_ai = dfcopy.head(10).copy()
# print(df_ai.to_string()
df_ai['AI Suggested'] = None
# print(df_ai.to_string())
df_ai['AI Suggested'] = df_ai[description_config].apply(edit)

df_ai_copy = df_ai.copy()
df_ai_copy[account_config]='Sales'

df_ai = df_ai.drop_duplicates(subset='AI Suggested',keep='first',ignore_index=True)
df_ai = df_ai[['AI Suggested',description_config,memo_config,deposit_config,withdrawal_config]]
print(df_ai.to_string())
df_ai.to_clipboard()


def fill(df_ai,df_complete):
    dict_fill_acct = df_ai.set_index('AI Suggested')[account_config].to_dict()
    dict_fill_des = df_ai.set_index(description_config)['AI Suggested'].to_dict()
    df_complete[description_config]=df_complete[description_config].replace(dict_fill_des)
    df_complete[account_config] = df_complete[description_config].map(dict_fill_acct)
    df_complete = df_complete[[description_config,account_config,memo_config,deposit_config,withdrawal_config]]
    return df_complete

# print(dict_fill_acct)


df_fill = fill(df_ai_copy,df_complete)
# df_fill.to_clipboard()
# print(df_fill.to_string())