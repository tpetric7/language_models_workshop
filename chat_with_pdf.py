# conda activate lmstudio
import streamlit as st
import os
import base64
import fitz  # PyMuPDF, ensure it's installed in your environment

# Assume these imports are your custom modules or setup
from langchain.vectorstores.chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms.ollama import Ollama
from get_embedding_function import get_embedding_function

CHROMA_PATH = "chroma"
PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""

@st.cache_data
def extract_text_from_pdf(pdf_path, page_num):
    """
    Extracts text from a specified page of a PDF.
    """
    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_num - 1)  # Page numbers are zero-indexed in fitz
        text = page.get_text()
        doc.close()
        return text
    except Exception as e:
        return f"Error accessing page {page_num} of {pdf_path}: {str(e)}"

@st.cache_data
def display_pdf(file_path, page_num=None):
    """
    Displays PDF file in Streamlit app, optionally at a specific page.
    """
    try:
        normalized_path = os.path.normpath(file_path)
        absolute_path = os.path.abspath(normalized_path)
        st.write(f"Debug: Attempting to open file at path - {absolute_path} at page {page_num}")  # Debug print

        if not os.path.exists(absolute_path):
            st.error(f"File does not exist: {absolute_path}")
            return

        with open(absolute_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}#page={page_num}" width="100%" height="600" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

    except IOError as e:
        st.error(f"Error opening file '{absolute_path}': {e}")

def query_rag(query_text: str):
    """
    Queries the database and returns the response and sources.
    """
    # Prepare the DB.
    embedding_function = get_embedding_function()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Search the DB.
    results = db.similarity_search_with_score(query_text, k=5)

    context_texts = []
    for result in results:
        doc, _score = result  # Unpack the tuple correctly
        id_parts = doc.metadata['id'].split(':')
        pdf_path = os.path.normpath(id_parts[0].strip())
        page_num = int(id_parts[1]) if len(id_parts) > 1 else None
        text = extract_text_from_pdf(pdf_path, page_num)
        context_texts.append(text)

    context_text = "\n\n---\n\n".join(context_texts)
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)

    # Invoke the model.
    model = Ollama(model="mistral")
    response_text = model.invoke(prompt)

    # Ensure to access 'doc' object's metadata correctly after unpacking
    sources = [f"Document: {doc.metadata['id']}, Text Extracted: {text}" for doc, text in zip((doc for doc, _ in results), context_texts)]
    return response_text, sources

def main():
    """
    Main function to run the Streamlit app.
    """
    st.title("Query Response Generator")
    query_text = st.text_input("Enter your query:", "")
    if st.button("Generate Response"):
        response, sources = query_rag(query_text)
        st.session_state['response'] = response
        st.session_state['sources'] = sources

    if 'response' in st.session_state:
        st.write("Response:", st.session_state['response'])
        for source in st.session_state['sources']:
            st.text(source)  # Display source IDs with an explanation and extracted text for debugging
            try:
                # Here, split and parse the source string carefully
                parts = source.split(', Text Extracted: ')[0].replace('Document: ', '').split(':')
                file_path = parts[0].strip()
                page_num = int(parts[1]) if len(parts) > 1 else None
                display_pdf(file_path, page_num)
            except ValueError as e:
                st.error(f"Error parsing source data: {e}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
