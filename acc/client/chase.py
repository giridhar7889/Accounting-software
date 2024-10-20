import pandas as pd
import re
import pdfplumber
# from pdf import *
import os
from .config import *
from .process_description import *
from .ai import ai_get_year
from .ai import ai_year_filename

pattern_mdy = re.compile(r'\d{1,2}\/\d{1,2}(\/\d{4})')  # Pattern to match MM/DD format
pattern_md = re.compile(r'\d{1,2}\/\d{1,2}')  # Pattern to match MM/DD format
end_of_section_pattern = [re.compile(r'(.*)total(.*)(-?\$?\b(?:\d{1,3}(?:,\d{3})*|\d*)\.\d{2}\b|(?<=\s)\.\d{2}(?=\s|$)) *?',flags=re.IGNORECASE),
                          re.compile(r' *?Continued.*?',flags = re.IGNORECASE),
                          re.compile(r'.*?Page *?\d{0,2}? *?of',flags = re.IGNORECASE),
                          re.compile(r'^\*end\*')]

check_pattern_in_d = re.compile(r'.*?check[^\d]+(\d{3,6})',flags=re.IGNORECASE)

#input is file_path, output is text
def get_first_page(file_path):
    pdf = pdfplumber.open(file_path)
    page = pdf.pages[0]
    text = page.extract_text(x_tolerance=3, y_tolerance=0.3,layout =False)
    return text

#input is file_path, output is entire text of the pdf
def get_entire_text(file_path):
    pdf = pdfplumber.open(file_path)
    lines = ''
    for page in pdf.pages: 
        text = page.extract_text(x_tolerance=1, y_tolerance=0.5,layout =True)
        lines = lines + '\n' + text
    return lines

#input is entire_text and filename, output is year
#first uses regex pattern to find year, then ai using filename, then ai using entire first page clues
def find_year(entire_text,file_path):
    year = None

    #use regex
    for format in year_formats_config:
        year = re.search(format,entire_text)

        if year is not None: 
            year = year.group(2)
            # print(f'year {year}')
            if len(year)!=4:
                year = str(base_year_config)+year
            return year 
        
    #use filename
    directory, filename = os.path.split(file_path)
    year = ai_year_filename(filename)
    if not year == "X":
        return year

    #use first page
    if year == "X":
        first_page_text = get_first_page(file_path)
        lines = first_page_text.split('\n')
        number_lines = []
        for line in lines: 
            numbers = re.findall(r'\d+',line)
            if len(numbers)>=2:
                number_lines.append(line)
        first_page_text = '\n'.join(number_lines)
        year = ai_get_year(first_page_text)
        return year
    
    print("year is None")
    return year

def format_date(date,year):
    try: 
        pattern_date = re.compile(r'^\d{2}\/\d{2}\/\d{4}$')
        if pattern_date.match(date):
            return date
        else:
            if len(date.split('/'))==2:
                month, day = date.split('/')
            elif len(date.split('/'))==3:
                month, day, year = date.split('/')


            month = month.zfill(2)
            day = day.zfill(2)
            if len(year) == 2:
                year = base_year_config + year
            formatted_date = f'{month}/{day}/{year}'
            return formatted_date
        
    except Exception as e:
            print(f'Unable to continue: format_date error {e}')

def get_deposits(lines):
    for line in lines:
        for pattern in num_deposits_config:
            match_deposits = pattern.match(line)
            if match_deposits: 
                deposits = match_deposits.group(1)
                deposits = deposits.replace(',','')
                deposits = deposits.replace('$','')
                try:
                    deposits = float(deposits)
                    return deposits
                except Exception as e: 
                    print('Unable to continue: cannot convert deposits to float')
    print('No deposits were found')
    return 1000

def filter_lines(entire_text,year):

    lines = entire_text.split('\n')

    checks_list = []
    memo_list = []
    dates_list = []
    amounts_list = []

    # Variable to store the current pattern to use for line processing
    current_pattern = None
    heading_pattern = None

    # Iterate over each line
    for i, line in enumerate(lines):
        # print(line)
        # Check if the line matches any of the headings
        for heading, line_pattern in headings_config.items():
            if heading.match(line):
                # If a heading is found, set the current pattern to the corresponding line pattern
                # print(f"Found heading: {line.strip()}")
                current_pattern = line_pattern
                heading_pattern = heading
                break
        for skip_heading in ignore_config:
            if skip_heading.match(line):
                # print(f"Skip heading: {line.strip()}")
                current_pattern = None
                break
        else:
            if current_pattern:  # Ensure current_pattern is set
                match = current_pattern.match(line)


                if match:
                    # If there's a match, extract values based on the current pattern
                    if current_pattern == cdda_pattern_config:
                        check_no, description, date, amount = [x.strip() for x in match.groups()]
                        for j in range(1,3):
                            if i+j < len(lines):
                                next_line = lines[i+j].strip()
                                next_match = current_pattern.match(next_line)
                                end_match = any(pattern.match(next_line) for pattern in end_of_section_pattern)                                
                                
                                if not next_match and next_line !="" and not end_match:
                                    description += ' ' + next_line
                                else: 
                                    break

                    if heading_pattern == pa_config:
                        date, description, amount = [x.strip() for x in match.groups()]
                        j=1
                        if i - j >= 0:  # Make sure we're not out of bounds
                            prev_line = lines[i - j].strip()
                            heading_match = heading_pattern.match(prev_line)

                            if not heading_match and prev_line != "":
                             # Only append if the prev_line is not a heading and not empty
                                description = prev_line + ' ' + description
                            else:
                                pass 
                    
                        if i + j < len(lines):  # Make sure we're not out of bounds
                            next_line = lines[i + j].strip()
                            next_match = current_pattern.match(next_line)
                            end_match = any(pattern.match(next_line) for pattern in end_of_section_pattern)

                            if not next_match and next_line != "" and not end_match:
                                description += ' ' + next_line
                            else:
                                pass 

                    elif current_pattern == dda_pattern_config:  # Check for second pattern
                        date, description, amount = [x.strip() for x in match.groups()]
                        for j in range(1,3):
                            if i+j < len(lines):
                                next_line = lines[i+j].strip()
                                next_match = current_pattern.match(next_line)
                                end_match = any(pattern.match(next_line) for pattern in end_of_section_pattern)                                
                                
                                if not next_match and next_line !="" and not end_match:
                                    description += ' ' + next_line
                                else: 
                                    break
                    
                    elif current_pattern == ddab_pattern_config:
                        date, description, amount = [x.strip() for x in match.groups()]
                        for j in range(1,3):
                            if i+j < len(lines):
                                next_line = lines[i+j].strip()
                                next_match = current_pattern.match(next_line)
                                end_match = any(pattern.match(next_line) for pattern in end_of_section_pattern)                                
                                
                                if not next_match and next_line !="" and not end_match:
                                    description += ' ' + next_line
                                else: 
                                    break
                    
                    elif current_pattern == ddab_pattern_config:
                        date, description, amount = [x.strip() for x in match.groups()]
                        for j in range(1,3):
                            if i+j < len(lines):
                                next_line = lines[i+j].strip()
                                next_match = current_pattern.match(next_line)
                                end_match = any(pattern.match(next_line) for pattern in end_of_section_pattern)                                
                                
                                if not next_match and next_line !="" and not end_match:
                                    description += ' ' + next_line
                                else: 
                                    break

                    date = format_date(date,year)
                    amount = amount.replace('$','')
                    amount = amount.replace(',','')
                    check_in_d = check_pattern_in_d.match(description)
                    
                    if check_in_d:
                        check_no = check_in_d.group(1)
                    else:
                        check_no = ""

                    memo_list.append(description)
                    dates_list.append(date)
                    amounts_list.append(amount)
                    checks_list.append(check_no) 

                else:
                    pass
                    # Line doesn't match the current pattern
                    # if len(line.strip())<1:
                    #     pass
                    # else:
                    #     pass
                        # print("Skipped line:", line.strip())
            else:
                pass
                # Current pattern is not set
                # if len(line.strip())<1:
                #     pass
                # else:
                #     pass
                # print("No current pattern set; skipping line:", line.strip()) 

    df = pd.DataFrame({
        date_config: dates_list, 
        memo_config: memo_list, 
        deposit_config: amounts_list,
        checks_config: checks_list,
        description_config:None,
        account_config:None,
        ai_vendor_payee_config:None,
        withdrawal_config:""})  

    account_order = [date_config, ai_vendor_payee_config, description_config, account_config, deposit_config, withdrawal_config,checks_config, memo_config]
    df = df[account_order]
    # print(df.to_string())

    try: 
        df[deposit_config] = df[deposit_config].astype(float)
        has_positive = (df[deposit_config] > 0).any()
        has_negative = (df[deposit_config] < 0).any()
        if has_positive and has_negative: 
            df[withdrawal_config] = df[deposit_config].apply(lambda x: abs(x) if x < 0 else "")
            df[deposit_config] = df[deposit_config].apply(lambda x: x if x > 0 else "")
        else:
            #deposits type is float
            deposits = get_deposits(lines)
            cum_sum = 0
            for i, row in df.iterrows():
                current_value = row[deposit_config]

                if cum_sum + current_value <= deposits:
                    cum_sum += current_value  # Add to cumulative sum if within deposit limit
                else:
                    # Calculate the remaining deposit that can be added
                    remaining_deposit = deposits - cum_sum
                    if remaining_deposit > 0:
                        df.at[i, deposit_config] = remaining_deposit  # Set the remainder to deposit_config

                        # Move the excess to withdrawal_config
                        df.at[i, withdrawal_config] = ""
                    else:
                        # All deposit capacity is used, move everything to withdrawal_config
                        df.at[i, deposit_config] = ""
                        df.at[i, withdrawal_config] = current_value

                    cum_sum = deposits  # We have reached the deposit limit

                    # For subsequent rows, move everything to withdrawal_config
                    for j in range(i + 1, len(df)):
                        df.at[j, withdrawal_config] = df.at[j, deposit_config]
                        df.at[j, deposit_config] = ""
                    break

    except Exception as e:
        print(f'Unable to continue: Error converting prices to float {e}') 
    
    return df

def chase(file_path):
    has_year = True
    #checks whether or not we need to find year
    entire_text = get_entire_text(file_path)
    num_mdy = pattern_mdy.findall(entire_text)
    num_md = pattern_md.findall(entire_text)

    if len(num_mdy)==len(num_md):
        print("same mm/dd and mm/dd/yyyy formats found.")

    if not len(num_mdy)>len(num_md):
       has_year = False
       year = "2023"
    #    year = find_year(entire_text, file_path)

    #checkpoint passed we have the year
    if has_year == True or year is not None:
        # print(year)
        # print(entire_text)
        df = filter_lines(entire_text,year)
        return df
        #can continue
    else:
        print('Unable to continue: year error')


# df=chase('/Users/jinhe/Documents/M&T Bank/Short Chase.pdf')
# print(df.to_string())