import openai
from openai import OpenAI
import os
import pandas as pd
# Step 1: Define your inverted index for efficient lookups
inverted_index = {
    'marketing': ['Advertising and Promotion'],
    'ads': ['Advertising and Promotion'],
    'promotion': ['Advertising and Promotion'],
    'advertising': ['Advertising and Promotion'],
    'car': ['Automobile Expense'],
    'automobile': ['Automobile Expense'],
    'vehicle': ['Automobile Expense'],
    'fuel': ['Automobile Expense:Gas'],
    'gas': ['Automobile Expense:Gas'],
    'petrol': ['Automobile Expense:Gas'],
    'parking': ['Automobile Expense:Parking'],
    'bank': ['Bank Service Charges'],
    'charges': ['Bank Service Charges'],
    'computer': ['Computer and Internet Expenses'],
    'internet': ['Computer and Internet Expenses'],
    'fine': ['Fines and Penalties'],
    'cleaning': ['Janitorial Expense'],
    'cleaner': ['Janitorial Expense'],
    'janitor': ['Janitorial Expense'],
    'supplies': ['Office Supplies'],
    'meals': ['Meals and Entertainment'],
    'entertainment': ['Meals and Entertainment'],
    'dining': ['Meals and Entertainment'],
    'retail': ['Office Supplies'],
    'professional': ['Professional Fees'],
    'lawyer': ['Professional Fees'],
    'repair': ['Repairs and Maintenance'],
    'repairs': ['Repairs and Maintenance'],
    'maintenance': ['Repairs and Maintenance'],
    'software': ['Software'],
    'website': ['Software'],
    'air': ['Travel Expense:Air'],
    'flight': ['Travel Expense:Air'],
    'plane': ['Travel Expense:Air'],
    'transportation': ['Travel Expense:Local'],
    'local': ['Travel Expense:Local'],
    'taxi': ['Travel Expense:Local'],
    'laundry': ['Laundry Expense'],
    'dry cleaning': ['Laundry Expense'],
    'withdrawal': ['Withdrawal'],
    'cash': ['Withdrawal'],
    'transfer': ['Withdrawal', 'Transfer To/From'],
    'hotel': ['Travel Expense:Lodging'],
    'lodging': ['Travel Expense:Lodging'],
    'accommodation': ['Travel Expense:Lodging']
}
# Step 3: Function to find accounts based on description


def ai_year_filename(file_name):
    try: 
        prompt = f'''
        Find the year of the statement ending date. It could be written in many different formats like mmyyyy mmddyyyy mmyy yyyymm or yymm. 
        
        For example:
        "11/01/23 - 11/30/23" should return 2023
        "05312024" should return 2024
        "052024" should return 2024
        "071522" should return 2022
        "20240403" should return 2024

        Output: Return only the year in format YYYY with no additional text.
        If no year was provided in the input, return X.
        
        Input:
        {file_name}
        
        '''

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # or "gpt-3.5-turbo" if you don't have access to GPT-4
            messages=[
                    {"role": "user", "content": prompt}
                ], 

            temperature = 0.01,
            max_tokens = 3,
            top_p=1
            )
        print("Total tokens used:", response.usage.total_tokens)
        print("Prompt tokens:", response.usage.prompt_tokens)
        print("Completion tokens:", response.usage.completion_tokens)
        return response.choices[0].message.content.strip()
    except Exception as e: 
        return f'error occured {e}'
    
def ai_get_year(text):
    try: 
        prompt = f'''
        Find the year of the statement ending date. It could be written in many different formats like month day, year through month day, year or ending balance on month day, year. 
        
        For example:
        "December 30, 2021 through January 30, 2022" should return 2022.
        "11/01/23 - 11/30/23" should return 2023
        "Closing Date 10/13/23" should return 2023
        "Ending Balance as of 05/31/2024" should return 2024
        "December 09, 2023 - January 08, 2024" should return 2024

        Output: Return only the year in format YYYY with no additional text.
        
        Input:
        {text}
        
        '''

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # or "gpt-3.5-turbo" if you don't have access to GPT-4
            messages=[
                    {"role": "user", "content": prompt}
                ], 

            temperature = 0.01,
            max_tokens = 3,
            top_p=1
            )
        print("Total tokens used:", response.usage.total_tokens)
        print("Prompt tokens:", response.usage.prompt_tokens)
        print("Completion tokens:", response.usage.completion_tokens)
        return response.choices[0].message.content.strip()
    except Exception as e: 
        return f'error occured {e}'

def find_accounts(description):
    def normalize_text(text):
        return text.lower().strip()
    description_normalized = normalize_text(description)
    
    # Extract words from the description
    words = description_normalized.split()

    for word in words:
        if word in inverted_index:
            # Return the first matched account found
            return list(inverted_index[word])[0]  # Get the first account in the set

    return "X"  # Return "X" if no accounts matched


API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI()

def edit(description):

    # comapny named from lucie , vs payment from lucie, unable to detect
    try: 
        prompt = f'''
        You are an accountant. Your task is to extract and simplify the vendor/payee name from the given transaction description, ensuring it is suitable for accounting software like QuickBooks or Xero.

        Instructions:

        Simplify the Vendor/Payee Name: Remove very obvious random unecessary characters like store numbers and locations or reciept numbers for example, Duane Reade 293 woefhx234 should be Duane Reade. If a number is part of the company name, keep it. For example 72 French Cleaners or Tha72. Ensure the name is in title case, with each word starting with an uppercase letter and the rest in lowercase.
        
        Transaction Types:
        If some words are cut short, of if there are abbreviations, write it out. For example, Locksmi is Locksmith, and Mktpl is Marketplace.
        1. Bank or Credit Card Transactions: If the transaction is between bank accounts or credit cards, keep the account or credit card number intact.
        2. Company vs. Person: Distinguish between companies and people. For example, if the description is "Payment from John Doe," return "John Doe." If the description is "From Lucie Inc.," return "From Lucie Inc."
                Usually there might be the location of the company at the end. A location, like New York or Nassau cannot be the name of the vendor/payee.

        3. Company Names:
        Core Name: Remove any suffix indicating business type (e.g., Inc, Ltd). Keep only the core company name.
        Branches and Products: Retain branch or product names, like "Microsoft Azure," but unify variations of the same parent company. For instance, "Microsoft Redmond" and "Nnt Microsoft" should both return "Microsoft," while "Nnt Msft Azure" should return "Microsoft Azure."
        4. Special Characters: Ignore URL fragments like "www" or "com" that may have been converted to text.
        
        Output: Return only the simplified vendor/payee name with no additional text.

        Input:
        {description}
        '''
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # or "gpt-3.5-turbo" if you don't have access to GPT-4
            messages=[
                    {"role": "user", "content": prompt}
                ], 

            temperature = 0.01,
            max_tokens = 20,
            top_p=1
            )
        print("Total tokens used:", response.usage.total_tokens)
        print("Prompt tokens:", response.usage.prompt_tokens)
        print("Completion tokens:", response.usage.completion_tokens)
        return response.choices[0].message.content.strip()
    
    except Exception as e: 
        return f'error occured {e}'
    

# def set_account(description, debit, credit):
    
#     try: 
#         if debit and debit != '':
#             transaction_type = 'income'
#             amount = debit   
#         elif credit and credit != '':
#             transaction_type = 'expense'  
#             amount = credit      
#         if "Chk" in description:
#             # Extracting the bank check number to include in the response
#             check_number = description.split(" ")[-1]  # Assuming check number is the last part
#             return f'Transfer To/From {check_number}'

#         prompt = f'''
#         Use the description of the business to categorize income and expenses which is given by {transaction_type}. Consider the Amount: {amount} .

#         Income Examples: Sales etc.
#         Expense Examples: Advertising and Promotion, Utilities, Automobile Expense:Gas, :Air, Cost of Goods Sold etc.

#         Category Example: "E-commerce company"  should result in "Office Supplies", for "Telecommunications company" should be "Utilities"

#         Input: 
#         - Description: {description}
#         - Transaction Type: {transaction_type}
#         - Amount: {amount}

#         If the description is a transfer from a bank account, you have to set the account to Transfer To/From and add the bank details after this, with no additional text.
#         Output: Only return an income or expense account that was provided. based on the description and transaction type with no additional text.
#         '''

#         response = client.chat.completions.create(
#             model="gpt-4o-mini",  # or "gpt-3.5-turbo" if you don't have access to GPT-4
#             messages=[
#                     {"role": "user", "content": prompt}
#                 ], 

#             temperature = 0.01,
#             max_tokens = 10,
#             top_p=1
#             )
#         print("Total tokens used:", response.usage.total_tokens)
#         print("Prompt tokens:", response.usage.prompt_tokens)
#         print("Completion tokens:", response.usage.completion_tokens)
#         print(f'the transaction type is {transaction_type} and the amount is {amount}')
#         return response.choices[0].message.content.strip()
#     except Exception as e: 
#         return f'error occured: {e}'
def set_account(description, debit, credit):
    inverted_index = {
    'marketing': ['Advertising and Promotion'],
    'ads': ['Advertising and Promotion'],
    'promotion': ['Advertising and Promotion'],
    'advertising': ['Advertising and Promotion'],
    'car': ['Automobile Expense'],
    'automobile': ['Automobile Expense'],
    'vehicle': ['Automobile Expense'],
    'fuel': ['Automobile Expense:Gas'],
    'gas': ['Automobile Expense:Gas'],
    'petrol': ['Automobile Expense:Gas'],
    'parking': ['Automobile Expense:Parking'],
    'bank': ['Bank Service Charges'],
    'charges': ['Bank Service Charges'],
    'computer': ['Computer and Internet Expenses'],
    'internet': ['Computer and Internet Expenses'],
    'fine': ['Fines and Penalties'],
    'cleaning': ['Janitorial Expense'],
    'cleaner': ['Janitorial Expense'],
    'janitor': ['Janitorial Expense'],
    'supplies': ['Office Supplies'],
    'meals': ['Meals and Entertainment'],
    'entertainment': ['Meals and Entertainment'],
    'dining': ['Meals and Entertainment'],
    'retail': ['Office Supplies'],
    'professional': ['Professional Fees'],
    'lawyer': ['Professional Fees'],
    'repair': ['Repairs and Maintenance'],
    'repairs': ['Repairs and Maintenance'],
    'maintenance': ['Repairs and Maintenance'],
    'software': ['Software'],
    'website': ['Software'],
    'air': ['Travel Expense:Air'],
    'flight': ['Travel Expense:Air'],
    'plane': ['Travel Expense:Air'],
    'transportation': ['Travel Expense:Local'],
    'local': ['Travel Expense:Local'],
    'taxi': ['Travel Expense:Local'],
    'laundry': ['Laundry Expense'],
    'dry cleaning': ['Laundry Expense'],
    'withdrawal': ['Withdrawal'],
    'cash': ['Withdrawal'],
    'transfer': ['Withdrawal', 'Transfer To/From'],
    'hotel': ['Travel Expense:Lodging'],
    'lodging': ['Travel Expense:Lodging'],
    'accommodation': ['Travel Expense:Lodging']
}
# Step 3: Function to find accounts based on description

    def normalize_text(text):
        return text.lower().strip()
    description_normalized = normalize_text(description)
    
    # Extract words from the description
    words = description_normalized.split()

    for word in words:
        if word in inverted_index:
            # Return the first matched account found
            return list(inverted_index[word])[0]  # Get the first account in the set
        
    accounts_expense = [
        'Advertising and Promotion',
        'Automobile Expense',
        'Automobile Expense:Gas',
        'Automobile Expense:Parking',
        'Bank Service Charges',
        'Computer and Internet Expenses',
        'Cost of Goods Sold',
        'Fines and Penalties',
        'Furniture and Equipment',
        'Insurance Expense',
        'IRS Tax',
        'Janitorial Expense',
        'Meals and Entertainment',
        'NYS Tax',
        'Office Expense',
        'Office Supplies',
        'Professional Fees',
        'Repairs and Maintenance',
        'Software',
        'Travel Expense:Air',
        'Travel Expense:Local',
        'Laundry Expense',
        'Utilities',
        'Withdrawal',
        'Transfer To/From',
        'Shareholder Distributions',
        'Travel Expense:Lodging'
    ]

    accounts_income = [
        'Sales',
        'Ticket Sales'
    ]

    try:
        if debit and debit != '':
            transaction_type = 'deposit'
            amount = debit   
        elif credit and credit != '':
            transaction_type = 'withdrawal'  
            amount = credit

        if "Chk" in description:
            check_number = description.split(" ")[-1]  # Assuming check number is the last part
            return f'Transfer To/From {check_number}'

        # Enhanced prompt
        prompt = f'''
        Your task is to suggest the appropriate account for the transaction, considering both the description of the business and whether it is a deposit or withdrawal. 

        Instructions:
        1. Accounts to choose from:
            List A: {', '.join(accounts_income)}
            List B: {', '.join(accounts_expense)}
            Examples: 
            Yelp is 'Advertising and Promotion'
            Car Repairs is 'Automobile Expense'
            Shell is 'Automobile Expense:Gas',
            Nice 11 Parking is 'Automobile Expense:Parking',
            Service Fee is 'Bank Service Charges',
            AT&T, Spectrum is 'Computer and Internet Expenses',
            Chair, Home Depot is 'Furniture and Equipment',
            State Farm Insurance is 'Insurance Expense',
            Restaurant, Starbucks is 'Meals and Entertainment',
            Uline Supplies is 'Office Expense',
            Amazon, CVS is 'Office Supplies',
            Squarespace is 'Software',
            Airline is 'Travel Expense:Air',
            Taxi, Train is 'Travel Expense:Local',
            Internet is 'Utilities',
            Hotel is 'Travel Expense:Lodging'
        2. **Transaction Type**:
            - if 'transaction type' is 'deposit', choose from List A.
            - If the 'transaction type' is a 'withdrawal', choose from List B. 
            If none of them seem likely, return "X".
            
        **Note**: Pay special attention to keywords in the description. For instance, if the description mentions "hotel," it should align with "Travel Expense: Lodging." 

        Input: 
        - Description: {description}
        - Transaction Type: {transaction_type}
        - Amount: {amount}

        If the description is a transfer from a bank account, you have to set the account to Transfer To/From and add the bank details after this, with no additional text.
        Output: Only return an income or expense account that was provided based on the description and transaction type with no additional text.
        '''

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # or "gpt-3.5-turbo" if you don't have access to GPT-4
            messages=[
                {"role": "user", "content": prompt}
            ], 
            temperature=0.01,
            max_tokens=10,
            top_p=1
        )
        print("Total tokens used:", response.usage.total_tokens)
        print("Prompt tokens:", response.usage.prompt_tokens)
        print("Completion tokens:", response.usage.completion_tokens)
        print(f'The transaction type is {transaction_type} and the amount is {amount}')
        
        # Return just the account name without the description
        account_response = response.choices[0].message.content.strip()
        return account_response if account_response in accounts_expense or account_response in accounts_income else "X"

    except Exception as e: 
        return f'Error occurred: {e}'



# to do: Amazon vs Amazon Prime but not Amazon Install etc
# block below to test code    
# description = " DD/BR"
# simplified_vendor = edit(description)
# print('simplified vendor')
# print(simplified_vendor)

# Tsys/Transfirst
# Tsys/Transfirst Discount


# client = OpenAI()
# completion = client.chat.completions.create(
#     model="gpt-4o",
#     messages=[
#         {"role": "user", "content": "write a haiku about ai"}
#     ]
# )

# print(completion)


# Example usage

# data = {
#     'Description': ["A family of independent boutique hotels bound by their Indie spirit and heart for connecting people and places."],
#     'Debit': [""],
#     'Withdrawal': [21.7]
# }

# data = {
#     'Description': ["Pret A Manger", "Classpass Inc.", "Fast Signs","New York State Dmv","Nagle Fuel Corp","Claimid","Ideal Products Inc"],
#     'Debit': ["", 17790.00, "", "","","",""],
#     'Withdrawal': [11.75, '', 68.60, 103.45, 50.34, 204.50,34.2]
# }

# df_ai = pd.DataFrame(data)

# Apply the AI-based account classification function
# df_ai['AI Suggested Account'] = df_ai.apply(
#     lambda row: set_account(row['Description'], row['Debit'], row['Withdrawal']),
#     axis=1
# )

# View the updated dataframe
# print(df_ai)