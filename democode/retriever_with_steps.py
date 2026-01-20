import os
from langchain_openai import AzureChatOpenAI
from langchain_openai import AzureOpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import warnings
warnings.filterwarnings("ignore")

from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = os.path.join(os.getcwd(), "chroma_db_new2")

def load_embeddings_chroma(persist_directory=CHROMA_PATH):
    from langchain_chroma import Chroma

    # Instantiate the same embedding model used during creation
    print('Instantiating the embedding model')

    embeddings = AzureOpenAIEmbeddings(
        model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"),
        api_key=os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")
    )

    print('Loading Chroma vector database, passing the embedding model to be used to it...')

    # Load the Chroma vector store from the specified directory, using the provided embedding function
    vector_store = Chroma(persist_directory=persist_directory, embedding_function=embeddings) 

    return vector_store  # Return the loaded vector store

def ask_and_get_answer(vector_store, q, k=3):
    """
    Step-by-step approach without LCEL
    Allows examination of chunks before LLM processing
    """
    
    # Initialize Azure LLM
    llm = AzureChatOpenAI(
        temperature=0,
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        model=os.getenv("AZURE_OPENAI_MODEL_NAME")
    )
    
    print('Fetching the retriever for the vector DB')
    retriever = vector_store.as_retriever(search_type='similarity', search_kwargs={'k': k})
    
    # Step 1: Retrieve relevant documents/chunks
    print('Step 1: Retrieving relevant documents from vector store...')
    source_docs = retriever.invoke(q)
    
    # Step 2: Examine the retrieved chunks
    print(f'\nStep 2: Retrieved {len(source_docs)} documents')
    print('=' * 80)
    for i, doc in enumerate(source_docs, 1):
        print(f'\n--- Document {i} ---')
        print(f'Content: {doc.page_content[:200]}...')  # Show first 200 chars
        print(f'Metadata: {doc.metadata}')
        print(f'Full length: {len(doc.page_content)} characters')
    print('=' * 80)
    
    # Step 3: Format the documents into context
    print('\nStep 3: Formatting documents into context...')
    context = "\n\n".join(doc.page_content for doc in source_docs)
    print(f'Context length: {len(context)} characters')
    
    # Step 4: Create the prompt
    print('\nStep 4: Creating the prompt...')
    template = """You are an assistant for question-answering tasks. 
Use the following pieces of retrieved context to answer the question. 
If you don't know the answer, say that you don't know. 
Use three sentences maximum and keep the answer concise.

Context: {context}

Question: {question}

Answer:"""
    
    prompt = ChatPromptTemplate.from_template(template)
    
    # Format the prompt with actual values
    formatted_prompt = prompt.format_messages(context=context, question=q)
    
    # Optional: Print the formatted prompt to examine
    print('\n--- Formatted Prompt Preview ---')
    print(formatted_prompt[0].content[:500] + '...')  # Show first 500 chars
    print('=' * 80)
    
    # Step 5: Send to LLM
    print('\nStep 5: Sending to LLM for answer generation...')
    response = llm.invoke(formatted_prompt)
    
    # Step 6: Extract the answer
    print('\nStep 6: Extracting answer from LLM response...')
    answer = response.content
    
    print(f'\nFinal Answer: {answer}')
    
    # Return in same format as before
    return {
        'answer': answer,
        'context': source_docs,
        'input': q
    }
## MAIN PROCESSING ##

# Load the chroma vector store using the same embedding model as the one used during indexing
vector_store = load_embeddings_chroma()

# Question/Prompt to ask
q = 'What technical skills does Pankaj have?'

# Get the answer from the RAG system (vector store + LLM)
answer = ask_and_get_answer(vector_store, q)

# The response is now a dictionary with 'answer' and 'context' keys
print("\n--- Answer ---")
print(answer['answer'])

print("\n--- Source Documents ---")
for i, doc in enumerate(answer['context'], 1):
    print(f"\nDocument {i}:")
    print(doc.page_content[:200] + "...")  # Print first 200 chars 