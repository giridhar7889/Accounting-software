import re
import pandas as pd

places = '''New York
Long Is City
Long Island C
Muellheim
Kifisia
San Francisco
Long Island C Astoria
LONG ISALND C ASTORIA
Long Island Long Island C
LONG ISLAND C LONG ISLAND C
Los Angeles
Long Island
Miami Beach
Koebenhavn
Las Vegas
Astoria
London
Seoul
Western Queens
San Luis Obis
South Beach
NEW YORK NEW YORK 
HENDERSON
WOODSIDE WOODSIDE
Toronto
Miami
CALIFON
NEWARK
LONG ISLAN LONG ISLAND C
Denville
ALBUQUERQUE
BROOKLYN
Columbus
Tucson 
Dallas
Washington
Washington DC
JAMAICA
Redmond
Seoul
'''

def delete_places(description):

    global places
    place_list = []
    place_line = places.split('\n')
    for place in place_line:
        place_list.append(place)
    for place in place_list:
        pattern_place = re.compile(re.escape(place) + r' \b[A-Z]{2}\b',flags = re.IGNORECASE)
        match_place = re.search(pattern_place, description)
        if match_place:
            sub = match_place.group()
            description = re.sub(sub, '', description)
            # return description


    pattern_end_two_upper = re.compile(r'\b[A-Z]{2}\b$')
    match_end_two_upper = re.search(pattern_end_two_upper,description)
    if match_end_two_upper:
        description = re.sub(match_end_two_upper,'')
        # return description

    # return description

def process_description(description):
    #phone number
    description = re.sub(r'\b\d{3}-?\d{3}-?\d{4}\b', '', description)
    #long numbers before I replace with space
    #merge receipts 
    description = re.sub(r'(\d{5,})\s?(\d{5,})',r'\1\2',description)

    #dates

    

    pattern_payment_to = r'^.*?Payment.*?To (.*)'
    match = re.search(pattern_payment_to, description, re.IGNORECASE)
    if match:
        part_after_to = match.group(1).strip()
        if re.search('[a-zA-Z]{2,}',part_after_to):
            description = part_after_to
        # print(f'hihi {part_after_to}')
    
    

        # Check if there are any digits in the part after 'Payment To'
        #update need to see what is wrong
        # if any(char.isdigit() for char in part_after_to):
        #     # If there are digits, return the whole part
        #     pass
        # else:
        #     description = part_after_to

    pattern_state_card = re.compile(r'(New York)? ?(([A-Z]){2})? Card \d{4}$')
    description = re.sub(pattern_state_card,'',description)
    # match_pattern_state_card = re.search(pattern_state_card, description)
    # if match_pattern_state_card:
    #     matched_text = match_pattern_state_card.group()
    #     modified_text = re.sub(r'[A-Z]{2}', '', matched_text)
    #     description = description.replace(matched_text, modified_text)
    #     description = ' '.join(description.split())
    # else:
    #     pass

    description = re.sub(r'(\d{1,2}[\/-]\d{1,2})([\/-]\d{2,4})?','',description)
    # description = re.sub(r'(\d{2}(\/|-)\d{2})', '', description)


    #do not delete everything beforehand 
    #description = re.sub(r'(.*)(\d{2}/\d{2})', '', description)

    # pattern_card_transfer = re.compile(r'Ending In \d{4}', flags=re.IGNORECASE)
    # match_card_transfer = re.search(pattern_card_transfer, description)
    # if match_card_transfer:
    #     description = re.sub("Payment To ", "Payment To/From ", description).strip()
    #     return description.strip()

    # description = delete_places(description)
    # pattern_star = re.compile(r'\b\w*\*\w*\b')
    # match_star = re.search(pattern_star, description)
    # if match_star:
    #     match_star = match_star.group()
    #     if re.search(r'[a-zA-Z]',match_star):
    #         if re.search(r'\d', match_star):
    #             pass
    #         description = re.sub(r'\S*\*', '', description)
    #     else:
    #         description = re.sub(r'\S*\*', '', description)

    #chase bank characteristics 
    pattern_orig = r'Orig CO Name:(.*?) Orig ID:'
    match = re.search(pattern_orig, description)
    if match:
        description = match.group(1).strip()
    description = re.sub(r'PPD ID:','', description)
    description = re.sub(r'CCD ID:','', description)
    description = re.sub(r'Web ID:','', description)
    description = re.sub(r'^(Recurring )?Card Purchase (With Pin)? ?(Return)?','',description)
    description = re.sub(r'^Refund of', '', description)
    
    pattern_adj_fee = r'Foreign Exch Rt ADJ Fee.*'
    match = re.search(pattern_adj_fee,description)
    if match: 
        description = 'Foreign Exch Rt ADJ Fee'
        return description
    
    pattern_adj_fee = r'Insufficient Funds Fee.*'
    match = re.search(pattern_adj_fee,description)
    if match: 
        description = 'Insufficient Funds Fee'
        return description
    # description = re.sub(r'CP WEB PYMT P','',description)
    # description = re.sub(r'In [EDI ]?P[A]?YM[E]?NTS','',description)
    # description = re.sub(r'I EDI PYMNTS','',description)
    # description = re.sub(r'RES \d{4}','',description,flags=re.IGNORECASE)
    # description = re.sub(r'Gametime Orders Gametime 0','Gametime',description)

    #payment processors
    description = re.sub(r'SP\s*\*', ' ', description) #ADDED THIS
    description = re.sub(r'Sq\s*\*','', description,flags=re.IGNORECASE) #MOVED TO BEGINNING
    description = re.sub(r'Tst\s*\*', '', description, flags=re.IGNORECASE)  # MOVED TO BEGINNING
    # description = re.sub(r'\.Com\*','.Com ',description, flags=re.IGNORECASE)
    
    description = re.sub(r'\.\.\.', ' ', description)

    
    #space dependent, normalize spacing beforehand
    description = re.sub(r' {2,}',' ',description)
    word_counts = len(description.split())
    if word_counts < 2: 
        pass
    else: 
        #replacing digits first before deleting receipts
        description = re.sub(r'\(.*\)', '', description)
    word_counts = len(description.split())
    print(description)
    if word_counts <= 1:
        pass
    else:
        description = re.sub(r'\*',' ',description)
        #pattern_receipt = re.compile(r'[a-zA-Z\d]{6,}(-[a-zA-Z\d]{1,})*')
        pattern_receipt = re.compile(r'(?=\w*\d)(?=\w*[a-zA-Z\-!"#\$%\'*+,.:;<=>?@[\\\]\^_`{|}~])[a-zA-Z0-9-\-!"#\$%\'*+,.:;<=>?@[\\\]\^_`{|}~]{4,}')
        words = description.split()
        for i in range(1,len(words)):
            if re.search(pattern_receipt,words[i]):
                if re.search(r'[a-zA-Z]', words[i]):
                    if re.search(r'\d', words[i]):
                        words[i] = re.sub(pattern_receipt,'',words[i])
        description = ' '.join(words)

#space creating
#special characters, not & not () not / not *(usually separating text and receipt), replace after check receipt after first word
    description = re.sub(r'[!"#\$%\'*+,.:;<=>?@[\\\]\^_`{|}~]',' ',description)

        # match_receipt = re.search(pattern_receipt,description)
    #     match_receipt_iter = re.finditer(pattern_receipt, description)
    #     # description = re.sub(pattern_receipt,'',description)
    #     for match in match_receipt_iter:
    #         match = match.group()
    #         # print(match)
    #         if re.search(r'[a-zA-Z]', match):
    #             if re.search(r'\d', match):
    #                 description = re.sub(match, '', description)
    description = re.sub(r'-',' ',description)
    description = re.sub(r' {2,}',' ',description)
    description = re.sub(r'\d{7,}','',description)

    # word_counts = len(description.split())
    # if word_counts <=1:
    #     pass
    # else:
    #     #might not anchor at the end, 
        #receipt pattern with special charactersw: (?=.*?\d)(?=.*?[a-zA-Z])[a-zA-Z\d]{4,}
        # description = re.sub(r'\b(?=\w*\d)(?=\w*[a-zA-Z\-!"#\$%\'*+,.:;<=>?@[\\\]\^_`{|}~])[a-zA-Z0-9-\-!"#\$%\'*+,.:;<=>?@[\\\]\^_`{|}~]{4,}\b$','',description)
        # description = re.sub(r'\d{5,9}', '', description)
        # description = re.sub(r'Transfer To Chk | Transfer From Chk', ' Transfer To/From', description)
        # description = re.sub(r'\S*#\S*', '', description)
    description = description.strip()
    description = re.sub(r'(\bAssoc\b|\bCorp\b.*|\bInc\b.*|\bLtd\b|\bMfg\b|\bMfrs\b|\bLLC\b.*)$','',description,flags=re.IGNORECASE)
    description = re.sub(r' {2,}',' ',description)
    return description.strip()


# de = process_description('Monthly Service Fee Charged On 05-29-2020')
# print(de)

# # Load the Excel file and specify the sheet and column(s)
# df = pd.read_excel('/Users/jinhe/Documents/Event 365 LLC.xlsx', sheet_name='2023')

# # Initialize an empty list to store processed descriptions
# description = []

# # Iterate over each value in the "Description" column
# for value in df['Description']:
#     if pd.isna(value) or value == '':  # Check if the value is NaN or an empty string
#         description.append('')  # Append an empty string for NaN or empty values
#     else:
#         new = process_description(value)  # Apply your processing function to non-empty values
#         description.append(new)  # Append the processed value to the list

# # Convert the 'description' list into a DataFrame with a column named "Description"
# # description_df = pd.DataFrame(description, columns=['Description'])
# # description_df.to_clipboard(index=False)
# # Print the resulting DataFrame
# # print(description_df)