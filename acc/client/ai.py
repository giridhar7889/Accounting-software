import openai
from openai import OpenAI
import os

API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI()

def edit(description):

    # comapny named from lucie , vs payment from lucie, unable to detect
    try: 
        prompt = f'''
        You are an accountant classifying bank transactions. Your task is to extract and simplify the vendor/payee name from the given transaction description, ensuring it is suitable for accounting software like QuickBooks or Xero.

        Instructions:

        Simplify the Vendor/Payee Name: Remove acronyms, unnecessary characters, and business structures (e.g., INC, LLC, LTD) while retaining the core name. Ensure the name is in title case, with each word starting with an uppercase letter and the rest in lowercase.
        
        Transaction Types:
        1. Bank or Credit Card Transactions: If the transaction is between bank accounts or credit cards, keep the account or credit card number intact.
        2. Company vs. Person: Distinguish between companies and people. For example, if the description is "Payment from John Doe," return "John Doe." If the description is "From Lucie Inc.," return "From Lucie Inc."
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

# to do: Amazon vs Amazon Prime but not Amazon Install etc
# block below to test code    
# description = "Amazon Prime"
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