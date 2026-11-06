"""Ask questions about your book in the terminal.

Copy the code of your RAG system from the notebook into this file, then add a
loop so that librarians can ask questions in the terminal.

Run it from the project root with:

    uv run python rag_cli.py
"""

import re
from pathlib import Path
from colorama import Fore, Style, just_fix_windows_console
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

just_fix_windows_console()  # so that the colours also work in the Windows terminal

load_dotenv(".env")  # load environment variables from .env file

BOOK_FILE = "adventures_of_pinocchio_collodi.txt"
PERSIST_DIR = "chroma_db"

# init the embedding model and the Chroma vector store
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = Chroma(
    collection_name="gutenberg_rag",
    embedding_function=embeddings,
    persist_directory=PERSIST_DIR,
)

# create the vector store only if it is empty
if vectorstore._collection.count() == 0:
    print(Fore.YELLOW + f"Vector store is empty. Embedding {BOOK_FILE}..." + Style.RESET_ALL)
    book_path = Path("data") / BOOK_FILE
    raw_text = book_path.read_text(encoding="utf-8")

    # removing the Gutenberg license from the text
    pattern = r"\*\*\* START OF THE PROJECT GUTENBERG EBOOK .*?\*\*\*(.*?)\*\*\* END OF THE PROJECT GUTENBERG EBOOK"
    match = re.search(pattern, raw_text, re.DOTALL)
    body = match.group(1).strip() if match else raw_text
    paragraphs = [re.sub(r"\s*\n\s*", " ", p).strip() for p in body.split("\n\n")]
    cleaned_text = "\n\n".join(p for p in paragraphs if p)

    doc = Document(
        page_content=cleaned_text,
        metadata={
            "source": BOOK_FILE,
            "title": "The Adventures of Pinocchio",
            "author": "Carlo Collodi",
        },
    )

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150, add_start_index=True)
    chunks = splitter.split_documents([doc])

    chunk_ids = [f"{BOOK_FILE}-{i}" for i in range(len(chunks))]
    vectorstore.add_documents(documents=chunks, ids=chunk_ids)
    print(Fore.GREEN + f"Indexed {len(chunks)} chunks successfully." + Style.RESET_ALL)

# 3. Configu Retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

# Config RAG Chain (Groq + ChatPromptTemplate + StrOutputParser)
prompt_template = ChatPromptTemplate.from_template("""
You are a library reading companion. Answer the user's question relying ONLY on the provided book passages below.
If the answer cannot be found in the passages, you MUST state clearly: "I cannot find the answer in the provided passages of the book."
Do not make up facts or use outside knowledge.

Passages from the book:
{context}

Question:
{question}

Answer:
""")

llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)
parser = StrOutputParser()
chain = prompt_template | llm | parser

# Welcome message
print(Fore.CYAN + "Ask a question about the book (type quit to exit)." + Style.RESET_ALL)

# "Question-and-answer" cycle in the terminal
while True:
    try:
        question = input("\n" + Fore.CYAN + "Question: " + Style.RESET_ALL).strip()

        if not question:
            continue

        if question.lower() in ("quit", "exit", "q"):
            print(Fore.CYAN + "Goodbye!" + Style.RESET_ALL)
            break

        # receive relevant passages
        docs = retriever.invoke(question)
        context = "\n\n---\n\n".join([d.page_content for d in docs])

        # generate response
        answer = chain.invoke({"context": context, "question": question})

        # display the answer in green (Fore.GREEN)
        print("\n" + Fore.GREEN + f"Answer:\n{answer}" + Style.RESET_ALL)

        # display the used passages in grey (Style.DIM)
        print("\n" + Style.DIM + "Passages used:" + Style.RESET_ALL)
        for i, doc in enumerate(docs, start=1):
            idx = doc.metadata.get("start_index", "N/A")
            snippet = doc.page_content.replace("\n", " ")[:200]
            print(Style.DIM + f"  [{i}] (start_index: {idx}) {snippet}..." + Style.RESET_ALL)

    except Exception as e:
        print(Fore.RED + f"\nError: {e}" + Style.RESET_ALL)
        print(Style.DIM + "If this is a rate limit error, wait a minute and try again." + Style.RESET_ALL)