import os
import pandas as pd
from transformers import AutoModel, AutoTokenizer
from bertopic import BERTopic
import streamlit as st
from umap import UMAP
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer

# Download NLTK data if not already downloaded
nltk.download('stopwords')

# Set up the model and tokenizer
model_name = "sentence-transformers/all-MiniLM-L6-v2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

# Function to extract text from files
def extract_text(file_path):
    try:
        if file_path.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        elif file_path.endswith(".docx"):
            import docx
            doc = docx.Document(file_path)
            return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
        elif file_path.endswith(".pdf"):
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(file_path)
            return "\n".join(page.extract_text() for page in pdf_reader.pages if page.extract_text())
    except Exception as e:
        print(f"Error extracting text from {file_path}: {e}")
    return ""

# Function to process the texts and store them in a Pandas dataframe
def process_texts(folder_path):
    texts = []
    file_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    for file_path in file_paths:
        text = extract_text(file_path)
        if text and isinstance(text, str):  # Ensure non-empty and valid strings
            texts.append(text)
    df = pd.DataFrame({"text": texts})
    return df

# Function to preprocess texts with CountVectorizer
def preprocess_texts_with_vectorizer(df):
    # Combine English and German stopwords into a single list
    english_stopwords = set(stopwords.words('english'))
    german_stopwords = set(stopwords.words('german'))
    all_stopwords = sorted(english_stopwords.union(german_stopwords))  # Sorted for consistency
    all_stopwords = [word.strip() for word in all_stopwords if word.isalpha()]

    # Debugging: Print first few stopwords
    print("Sample stopwords:", all_stopwords[:20])

    # Define the CountVectorizer
    vectorizer = CountVectorizer(
        min_df=2,
        ngram_range=(1, 3),
        max_features=10000,
        max_df=0.5,
        stop_words=all_stopwords
    )

    df["cleaned_text"] = df["text"].str.lower()

    # Fit and transform the text data
    vectorized_data = vectorizer.fit_transform(df["cleaned_text"])

    # Debugging: Check if stopwords are in the vocabulary
    print("Stopwords in vocabulary (should not exist):")
    stopwords_in_vocab = [word for word in all_stopwords if word in vectorizer.vocabulary_]
    print(stopwords_in_vocab)  # This should ideally be empty

    # Debugging: Vocabulary and feature names
    print("Vocabulary size:", len(vectorizer.vocabulary_))
    print("Sample vocabulary:", list(vectorizer.vocabulary_.keys())[:20])

    # Return cleaned text for BERTopic
    df["cleaned_text"] = [" ".join([word for word in doc.split() if word not in all_stopwords])
                          for doc in df["cleaned_text"]]
    return df, vectorizer

# # Function to visualize the documents using BERTopic
# def visualize_documents(df, topic_model):
#     fig = topic_model.visualize_documents(df['text'])
#     return fig

# Function to visualize the documents using BERTopic
def visualize_documents(cleaned_text, topic_model):
    fig = topic_model.visualize_documents(cleaned_text, hide_annotations=True)
    return fig

# Main function
def main():
    st.title("Text Topic Modeling App")

    # Get the folder path from the user
    folder_path = st.text_input("Enter the folder path where your files are located:", value=r"C:\Users\User\Documents\Folder")

    if st.button("Process Files"):
        try:
            # Process texts from the specified folder
            df = process_texts(folder_path)

            # Debugging: Print the first few rows of the text column
            st.write("First few texts:")
            st.write(df.head())

            # Preprocess texts with CountVectorizer
            df, vectorizer = preprocess_texts_with_vectorizer(df)

            # # Debugging: Show sample feature names from CountVectorizer
            # st.write("Sample feature names from CountVectorizer:")
            # st.write(vectorizer.get_feature_names_out()[:20])

            # # Debugging: Check the first few rows of cleaned_text
            # print("Cleaned text samples with potential umlauts:")
            # print(df["cleaned_text"].head(10))

            # Save cleaned_text to a file to inspect manually (optional)
            df.to_csv("cleaned_text_debug.csv", index=False, encoding="utf-8")

            from umap import UMAP
            # Define UMAP with a fixed random state
            umap_model = UMAP(n_neighbors=10, n_components=2, min_dist=0.0, metric="cosine", random_state=42)

            # Initialize BERTopic with the custom UMAP model
            topic_model = BERTopic(umap_model=umap_model, language="german")

            # Fit and transform the cleaned data with BERTopic
            topics, probs = topic_model.fit_transform(df["cleaned_text"])

            # Visualize the documents
            doc_vis = visualize_documents(df["cleaned_text"], topic_model)

            # Display the Plotly figure directly in Streamlit
            st.plotly_chart(doc_vis)
        except Exception as e:
            st.error(f"Error processing files: {e}")

if __name__ == "__main__":
    main()
