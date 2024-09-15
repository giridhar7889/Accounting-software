# import tkinter as tk
# from tkinter import filedialog, messagebox, scrolledtext
import pandas as pd
import re
import pdfplumber
# from pdf import *
import os
import time
import datetime
import sys
from .config import *
from .process_description import *

def process_data(text, year, count):

    pattern_date = re.compile(r'(\d{2})\/(\d{2})')  # Pattern to match MM/DD format
    pattern_price = re.compile(r'(-?\$?\b(\d{1,3}(?:,\d{3})*|\d*)\.\d{2}\b|(?<=\s)\.\d{2}(?=\s|$))')
    # pattern_price = re.compile(r'-?\$?\b\d{1,3}(?:,\d{3})*\.\d{2}\b')
    pattern_check_number = re.compile(r'\d{3,6}')

    # CC
    # def changesign():
    #     if forever:
    #         sign = 'Payment'
    #     else:
    #         sign = 'Deposit'
    #     return sign

    lines = text
    dates = []
    prices = []
    prices1 = []
    descriptions = []
    checks = []
    # signs = []
    memo = []
    cum_sum = 0
    has_jan = False
    has_dec = False

    has_date = False
    has_price = False
    has_check = False

    # year_provided = False
    forever = False
    year = year
    # lines = [line for line in lines if pattern_date.match(line) or pattern_check_number.match(line)]

    for line in lines:
        type = 'description'
        match_date = re.search(pattern_date, line)  # Search for MM/DD format
        match_price = re.search(pattern_price, line)  # Search for price with optional comma and decimal
        match_check = re.match(pattern_check_number, line)

        if match_check:
            type = 'check'
            has_check = True

        if match_price:
            price = match_price.group()
            # print('matched price')
            # print(price)
            price = price.replace('$', "")
            price = price.replace(',', '')
            # price_float = float(price)
            # if price_float < 0:
            #     sign = 'Deposit'
            # else:
            #     sign = 'Payment'
            # price = price.replace('-','')
            price = f"{float(price):.2f}"
            price = float(price)
            has_price = True

        if match_date:
            date = match_date.group()
            # Check if the date includes a year
            if len(date.split('/')) == 2:
                # if not year_provided:
                #     # Ask the user for the year if not already provided
                #     year_provided = True
                date += f'/{year}'
            # dates.append(date)
            has_date = True

            # Extract the description starting after the date
            start = match_date.end()

            if (type == 'description' and has_date and has_price):
                if match_price:
                    end = match_price.start()
                    description = line[start:end].strip()
                else:
                    description = line[start:].strip()
                full_description = description
                memo.append(full_description)
                #update add process_description function
                description = None
                descriptions.append(description)
                if cum_sum:
                    cum_sum += price
                    if cum_sum <= count + 0.001: 
                        sum = cum_sum
                        prices.append(price)
                        prices1.append("")
                    else: 
                        prices.append("")
                        prices1.append(price)
                else: 
                    if float(price)>0:
                        prices.append(price)
                        prices1.append("")
                    else:
                        prices.append("")
                        prices1.append(abs(price))
                # print(f'cumsum!! {cum_sum}')
                dates.append(date)
                checks.append("")
                # CC
                # sign = changesign()
                # signs.append(sign)

        if (type == 'check' and has_check and has_date and has_price):
            match_check = re.match(pattern_check_number, line)
            if match_check:
                check = match_check.group()
                descriptions.append('Check')
                checks.append(check)
                forever = True
                # CC
                # sign = changesign()
            prices.append("")
            prices1.append(price)
            dates.append(date)
            # signs.append(sign)
            memo.append(None)

        has_date = False
        has_check = False
        has_price = False

    # print(len(dates))
    # print(len(prices))
    # print(len(descriptions))
    # print(len(checks))
    # print(len(prices1))
    # print(len(memo))
    # print(len(signs))
    df = pd.DataFrame({all_columns_config[0]: dates, all_columns_config[1]: descriptions, deposit_config: prices, withdrawal_config: prices1,'Checks': checks,
                        all_columns_config[3]: memo})  # ,deleted'Transaction Type': signs
    df[all_columns_config[2]] = None
    account_order = ['Date', 'Description', 'Account', deposit_config, withdrawal_config,'Checks', 'Memo']
    df = df[account_order]
    df['Date']=pd.to_datetime(df['Date'],format='%m/%d/%Y')
    months = df['Date'].dt.month.unique()
    if 1 in months and 12 in months: 
        df.loc[df['Date'].dt.month ==12,'Date'] = df.loc[df['Date'].dt.month == 12, 'Date'].apply(lambda x: x.replace(year= int(year) - 1))
    
    df['Date'] = df['Date'].dt.strftime('%m/%d/%Y')
    # print(df.shape)
    return df
    # df.to_clipboard(index=False)

    # print(df.Date.to_string())
    # print(df.Description.to_string())
    # print(df.Price.to_string())
    # df = df.to_string(index = False)
    # print(df)

    # print(df.Date.to_string())
    # print(df.Description.to_string())
    # print(df.Price.to_string())
    # df = df.to_string(index = False)
    # print(df)

    # return df

def crop_page(file_path):
    pdf = pdfplumber.open(file_path)
    lines = ''
    for page in pdf.pages: 
        # text, count, h, w , account_activity = extract_original(page)
        # if count == 0: 
        #     print('no page detected')
        #     continue
        # else: 
        #     while True: 
        #         if count == 0:
        #             break
        #         h = h - 9
        #         crop_box = (0, 0, w, h)
        #         page1 = page.within_bbox(crop_box)
        #         text = page1.extract_text()
        #         count1 = text.lower().count('page')
        #         if count > count1: 
        #             break
        #     # return page1
        #change from page1 to page
        text = page.extract_text(x_tolerance=2, y_tolerance=0.3)
        lines = lines + '\n' + text
    print(lines)
    year, lines, count = filter_lines(lines)
    return year, lines, count
    # return lines.strip()

def filter_lines(text):
    table_headers = 0
    year = None
    deposits = None
    filtered_lines = []
    pattern_date = re.compile(r'^\d{2}/\d{2}')  # Pattern to match MM/DD format at the start of the line
    pattern_date_middle = re.compile(r'.*\d{2}/\d{2}.*')  # Pattern to match MM/DD format at the start of the line
    pattern_check_number = re.compile(r'^\d{3,8}\b')  
    pattern_ending_balance = re.compile(r'.*start.*ending.*balance.*', flags=re.IGNORECASE)
    lines = text.split('\n')
    pattern_year = re.compile(r'.*,.*through.*, (.*)')
    pattern_year_cc = re.compile(r'Opening\/Closing Date \d{2}\/\d{2}\/\d{2} - \d{2}\/\d{2}\/(\d{2})')
    num_deposits = re.compile(r'Total Deposits and Additions (\$)?(.*)', flags=re.IGNORECASE)
    balance = re.compile(r'DATE DESCRIPTION AMOUNT BALANCE', flags=re.IGNORECASE)
    table_headers = re.compile(r'DATE DESCRIPTION AMOUNT', flags=re.IGNORECASE)
    for line in lines:
        if balance.search(line):
            has_balance = True
            break
        else: 
            has_balance = False

    for line in lines: 
        if year == None: 
            if pattern_year.search(line): 
                year = pattern_year.search(line).group(1)
            if pattern_year_cc.search(line):
                # year = '20'
                year = pattern_year_cc.search(line).group(1)
                if len(year)!=4:
                    # print('hi')
                    year = str(base_year_config)+year
        if num_deposits.search(line):
            print('num deposits')
            deposits = num_deposits.search(line).group(2)
            deposits = re.sub(r',','',deposits)
            deposits = float(str(deposits))
        if pattern_check_number.match(line) and pattern_date_middle.search(line):
            print('check number')
            filtered_lines.append(line)
        if pattern_date.match(line):
            print('date')
            filtered_lines.append(line)
        if pattern_ending_balance.match(line):
            print(line)
            print('ending balance')
            break
    return year, filtered_lines, deposits

def chase(file_path):

    #returns the text of the pdf file
    year, transaction_list, count = crop_page(file_path)
    print('year!!')
    print(year)
    print(count)
    print(len(transaction_list))
    for item in transaction_list: 
        print(item)
    df = process_data(transaction_list,year, count)
    return df
    # count = get_count()+1
    # print(f'this is count type {type(count)}')
    # df = process_data(QB_file_1, self.start_date, count)
    # all_df.append(df)
    # print(df.shape)
    # combined_df = pd.concat(all_df, ignore_index=True)
    # return combined_df

def save_dataframe_to_excel(df, file_path):
    directory, filename_with_ext = os.path.split(self.file_path_statement)
    filename, ext = os.path.splitext(filename_with_ext)
    with pd.ExcelWriter(file_path, if_sheet_exists="replace",
                        mode='a') as writer:
        df.to_excel(writer, sheet_name=filename, index=False)
    print(f"DataFrame has been written to the '{filename}' sheet in '{file_path}'.")


#to delete afterwards

# chase('/Users/jinhe/Documents/M&T Bank/Other Files/Chase Platinum Select Checking.pdf')

# file_path = file_path_config
# if os.path.isdir(file_path):
#     all_df = []  # Flat list to store all DataFrames from all files
#     for filename in os.listdir(file_path):
#         # print('inside driver loop')
#         full_path = os.path.join(file_path, filename)
#         if full_path.startswith('.') or not full_path.lower().endswith('.pdf'):
#             continue
#         if os.path.isfile(full_path):  # Check if it's a file')
#             try: 
#                 combined_df = chase(full_path)
#                 print('combined!')
#                 all_df.append(combined_df)
#                 final_combined_df = pd.concat(all_df, ignore_index=True)
#                 print(final_combined_df.to_string())
#             except Exception as e: 
#                 print(f'ID 2 Problem with {full_path}: {e}')
    # Concatenate all DataFrames from all files

    # print('second option combine')
    # final_combined_df = pd.concat(all_df, ignore_index=True)
    # print(final_combined_df.to_string())
    # keyboard = final_combined_df['Memo'].dropna()
    # keyboard.to_clipboard(index=True)

# main_get_df(file_path_config)