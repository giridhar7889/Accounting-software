import openai
from openai import OpenAI
import os

#API_KEY = "os.getenv("OPENAI_API_KEY")


def edit(description):

    # comapny named from lucie , vs payment from lucie, unable to detect
    try: 
        prompt = f'''
        You are an accountant inputting and classifying bank transactions. Extract and simplify the vendor/payee name from the following bank transaction description. 
        Ensure that the vendor/payee name is clear, without any acronyms or unnecessary characters, The output should be in title case, with each word starting with an uppercase letter and the rest in lowercase.
        and suitable for accounting software like QuickBooks or Xero. 

        Your output should be only the simplified vendor/payee name, with no additional text.

        You are able to distinguish different types of input: 
        1. Transactions between bank, credit card accounts, or withdrawals. If the inputs are transactions between bank or credit card accounts, make sure to keep the account or cc number.
        2. Companies vs. People. Sometimes the intput is "payment from [person]" in which case you should return person. "From Lucie Inc.", the whole comany name is "From Lucie" and NOT Lucie as a person. 
        3. Companies / Entities. Remove business structures such as 'INC', 'LLC', 'LIMITED', or abbreviations from company names. Keep only the core name without any suffixes indicating the business type or legal structure. For example, if the name is 'Qbs Software Limited', return only 'Qbs Software'. 
        4. Withdrawals
        5. All inputs were preprocessed by removing and replacing special characters by spaces. Therefore, some text such as "www" and "com" from an URL may show up. Remove any part from the text. 

        Input:
        {description}
        '''
        response = client.chat.completions.create(
            model="gpt-4o",  # or "gpt-3.5-turbo" if you don't have access to GPT-4
            messages=[
                    {"role": "user", "content": prompt}
                ], 

            temperature = 0.01,
            max_tokens = 70,
            top_p=1
            )
        print("Total tokens used:", response.usage.total_tokens)
        print("Prompt tokens:", response.usage.prompt_tokens)
        print("Completion tokens:", response.usage.completion_tokens)
        return response.choices[0].message.content.strip()
    
    except Exception as e: 
        return f'error occured {e}'

#to do: Amazon vs Amazon Prime but not Amazon Install etc
# block below to test code    
# description = "AMEX EPAYMENT ACH PMT W7684"
# simplified_vendor = edit(description)
# print('simplified vendor')
# print(simplified_vendor)