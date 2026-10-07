import os
import re
import logging
from typing import List, Dict

import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# Path to the uploaded Excel file
data_path = '/mnt/data/faker_replaced_output.xlsx'

# Output directory for logs and results
output_dir = './output'
os.makedirs(output_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    filename=os.path.join(output_dir, 'anonymization.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

# Regular expressions for detecting names and phone numbers
name_regex = r'\b[A-Z][a-z]*\b'  # Simplistic name regex
phone_regex = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'  # Simplistic phone number regex

# Placeholder tags
person_tag = '<PERSON>'
phone_tag = '<PHONE_NUMBER>'

def load_data(path: str) -> pd.DataFrame:
    """
    Load data from an Excel file and return a DataFrame.
    """
    df = pd.read_excel(path, engine='openpyxl')
    # Ensure the notes are in a column named 'Original_Text_replaced'; adjust if necessary
    df = df.rename(columns={'Original_Text_replaced': 'text'})
    df['id'] = df.index  # Assign unique identifiers
    return df[['id', 'text']]

data_df = load_data(data_path)

def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract names and phone numbers from the text using regex.
    """
    names = re.findall(name_regex, text)
    phones = re.findall(phone_regex, text)
    return {'names': names, 'phones': phones}

def replace_entities(text: str) -> Dict:
    """
    Replace names and phone numbers with tags and keep track of changes.
    """
    entities = extract_entities(text)
    replaced_text = text
    changes = []

    # Replace names
    for name in set(entities['names']):
        replaced_text = re.sub(r'\b' + re.escape(name) + r'\b', person_tag, replaced_text)
        changes.append({'entity': name, 'tag': person_tag})

    # Replace phone numbers
    for phone in set(entities['phones']):
        replaced_text = re.sub(re.escape(phone), phone_tag, replaced_text)
        changes.append({'entity': phone, 'tag': phone_tag})

    return {
        'replaced_text': replaced_text,
        'changes': changes
    }

def log_changes(note_id: int, original_text: str, anonymized_text: str, changes: List[Dict], model_name: str):
    """
    Log the changes made during anonymization.
    """
    logging.info(f"Note ID: {note_id}, Model: {model_name}")
    logging.info(f"Original Text: {original_text}")
    logging.info(f"Anonymized Text: {anonymized_text}")
    logging.info(f"Changes: {changes}")

def anonymize_with_local_model(text: str, tokenizer, model, device: str = 'cpu') -> str:
    """
    Use a local model to anonymize the text.
    """
    prompt = f"Anonymize the following text by replacing all names with {person_tag} and all phone numbers with {phone_tag}:\n\n{text}"

    inputs = tokenizer.encode(prompt, return_tensors='pt').to(device)
    max_length = inputs.shape[1] + 200  # Adjust as needed

    with torch.no_grad():
        outputs = model.generate(
            inputs,
            max_length=max_length,
            temperature=0.0,
            num_return_sequences=1,
            eos_token_id=tokenizer.eos_token_id,
        )
    anonymized_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    anonymized_text = anonymized_text[len(prompt):].strip()
    return anonymized_text

def process_notes_with_model(data_df: pd.DataFrame, model_name: str, model_type: str, device: str = 'cpu') -> pd.DataFrame:
    """
    Process all notes with the specified model.
    """
    results = []
    if model_type == 'local':
        # Load the local model
        tokenizer, model = load_local_model(model_name, device)
    elif model_type == 'api':
        pass  # API models are initialized in their respective functions

    for idx, row in tqdm(data_df.iterrows(), total=data_df.shape[0], desc=f"Processing with {model_name}"):
        note_id = row['id']
        original_text = row['text']

        # Start timing
        start_time = pd.Timestamp.now()

        # Anonymize the text
        if model_type == 'local':
            anonymized_text = anonymize_with_local_model(original_text, tokenizer, model, device)
        else:
            continue  # Skip if the model type is not recognized

        # End timing
        end_time = pd.Timestamp.now()
        processing_time = (end_time - start_time).total_seconds()

        # Replace entities to track changes
        replaced_result = replace_entities(original_text)
        anonymized_text = replaced_result['replaced_text']
        changes = replaced_result['changes']

        # Log changes
        log_changes(note_id, original_text, anonymized_text, changes, model_name)

        # Save the result
        results.append({
            'id': note_id,
            'model': model_name,
            'original_text': original_text,
            'anonymized_text': anonymized_text,
            'processing_time': processing_time,
        })

    # Convert results to DataFrame
    results_df = pd.DataFrame(results)
    # Save results to CSV
    results_df.to_csv(os.path.join(output_dir, f'results_{model_name}.csv'), index=False)
    return results_df

def load_local_model(model_name: str, device: str = 'cpu'):
    """
    Load a local model and tokenizer.
    """
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    model.to(device)
    model.eval()
    return tokenizer, model

def plot_comparison_graphs(results: List[pd.DataFrame]):
    """
    Plot comparison graphs for model processing times and performance.
    """
    combined_results = pd.concat(results, ignore_index=True)

    # Plot processing times
    plt.figure(figsize=(10, 6))
    sns.boxplot(x='model', y='processing_time', data=combined_results)
    plt.title('Processing Time Comparison Across Models')
    plt.xlabel('Model')
    plt.ylabel('Processing Time (seconds)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'processing_time_comparison.png'))
    plt.show()

    # Plot number of changes made (entity replacements)
    combined_results['num_changes'] = combined_results['anonymized_text'].apply(lambda x: x.count(person_tag) + x.count(phone_tag))
    plt.figure(figsize=(10, 6))
    sns.barplot(x='model', y='num_changes', data=combined_results, estimator=sum)
    plt.title('Total Number of Entity Replacements Across Models')
    plt.xlabel('Model')
    plt.ylabel('Number of Replacements')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'entity_replacements_comparison.png'))
    plt.show()

if __name__ == '__main__':
    # List of models to process
    models_to_process = [
        {'name': 'EleutherAI/gpt-neo-1.3B', 'type': 'local'},
        {'name': 'EleutherAI/gpt-neo-2.7B', 'type': 'local'},
    ]

    # Specify the device ('cpu' or 'cuda')
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    all_results = []
    for model_info in models_to_process:
        model_name = model_info['name']
        model_type = model_info['type']

        # Process notes with the model
        model_results = process_notes_with_model(data_df, model_name, model_type, device)
        all_results.append(model_results)

    # Plot comparison graphs
    plot_comparison_graphs(all_results)