import os
# Function to clean and organize text data
def clean_and_organize(text):
    # Example: Remove extra whitespace, special characters, etc.
    cleaned_text = text.replace('\n', ' ').strip()  # Replace newlines with spaces and remove leading/trailing whitespace
    # You can add more cleaning and organizing steps as needed
    return cleaned_text

# Function to combine text data from a folder
def combine_text_from_folder(folder_path):
    context_text = ""
    
    # Iterate through files in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                file_text = file.read()
                # Append the file's text to the context_text
                context_text += file_text + "\n\n"  # You can adjust the separator as needed
    
    # Clean and organize the combined information if necessary
    # For example, remove extra whitespace, special characters, etc.
    context_text = clean_and_organize(context_text)
    
    return context_text
