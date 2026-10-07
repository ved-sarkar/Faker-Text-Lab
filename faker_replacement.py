import pandas as pd
from faker import Faker
import re

# Initialize Faker
fake = Faker()

def replace_tags(value):
    # Convert value to string and handle NaN values
    if pd.isna(value):
        return '', 0, 0, '', ''
    
    value = str(value)
    original = value
    person_count = 0
    phone_count = 0
    person_replacements = []
    phone_replacements = []

    # Replace <PERSON> tags
    while '<PERSON>' in value:
        fake_name = fake.name()
        value = value.replace('<PERSON>', fake_name, 1)
        person_count += 1
        person_replacements.append(fake_name)

    # Replace <PHONE_NUMBER> tags
    while '<PHONE_NUMBER>' in value:
        fake_phone = fake.phone_number()
        value = value.replace('<PHONE_NUMBER>', fake_phone, 1)
        phone_count += 1
        phone_replacements.append(fake_phone)

    return value, person_count, phone_count, ', '.join(person_replacements), ', '.join(phone_replacements)

# Load your Excel file
df = pd.read_excel('output156.xlsx')

# Create new columns for replaced data and tracking information
for column in df.columns:
    df[f'{column}_replaced'], df[f'{column}_person_count'], df[f'{column}_phone_count'], df[f'{column}_person_replacements'], df[f'{column}_phone_replacements'] = zip(*df[column].apply(replace_tags))

# Save the modified DataFrame to a new Excel file
df.to_excel('faker_replaced_output.xlsx', index=False)

print("Replacement complete. Check 'faker_replaced_output.xlsx' for the result.")
