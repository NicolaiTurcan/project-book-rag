"""Conversational Book RAG with Chat History and Token Usage Tracking."""

import re
from pathlib import Path
from colorama import Fore, Style, just_fix_windows_console
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

just_fix_windows_console()
load_dotenv()

BOOK_FILE = "adventures_of_pinocchio_collodi.txt"
PERSIST_DIR = "chroma_db"

# init Chroma
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = Chroma(
	collection_name="gutenberg_rag",
	embedding_function=embeddings,
	persist_directory=PERSIST_DIR,
)

if vectorstore._collection.count() == 0:
	print(Fore.YELLOW + f"Vector store is empty. Embedding {BOOK_FILE}..." + Style.RESET_ALL)
	raw_text = (Path("data") / BOOK_FILE).read_text(encoding="utf-8")

	pattern = r"\*\*\* START OF THE PROJECT GUTENBERG EBOOK .*?\*\*\*(.*?)\*\*\* END OF THE PROJECT GUTENBERG EBOOK"
	match = re.search(pattern, raw_text, re.DOTALL)
	body = match.group(1).strip() if match else raw_text
	paragraphs = [re.sub(r"\s*\n\s*", " ", p).strip() for p in body.split("\n\n")]
	cleaned_text = "\n\n".join(p for p in paragraphs if p)

	doc = Document(
		page_content=cleaned_text,
		metadata={"source": BOOK_FILE, "title": "The Adventures of Pinocchio", "author": "Carlo Collodi"},
	)

	splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100, add_start_index=True)
	chunks = splitter.split_documents([doc])

	chunk_ids = [f"{BOOK_FILE}-{i}" for i in range(len(chunks))]
	vectorstore.add_documents(documents=chunks, ids=chunk_ids)
	print(Fore.GREEN + f"Indexed {len(chunks)} chunks successfully." + Style.RESET_ALL)

retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

# initLLM (Groq)
llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)


def rephrase_question(user_question: str, history: list) -> tuple[str, int, int]:
	"""Rephrases the question considering the context of the dialog history."""
	system_instruction = SystemMessage(
		content=(
			"Given a chat history and the latest user question which might reference context in the chat history, "
			"formulate a standalone question that can be understood without the chat history. "
			"Do NOT answer the question, just reformulate it if needed and otherwise return it as is."
		)
	)
	# Assembling: system prompt + history + new question
	prompt_messages = [system_instruction] + history + [HumanMessage(content=user_question)]
	
	response = llm.invoke(prompt_messages)
	standalone_query = response.content.strip()
	
	usage = response.response_metadata.get("token_usage", {})
	return standalone_query, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


def answer_question(user_question: str, context: str, history: list) -> tuple[str, int, int]:
	"""Generates a response based on the passages found."""
	system_prompt = SystemMessage(
		content=(
			"You are a library reading companion. Answer the user question using ONLY the provided book passages below.\n"
			"If the answer cannot be found in the passages, you MUST state: "
			"'I cannot find the answer in the provided passages of the book.'\n"
			"Do not invent facts or use outside knowledge.\n\n"
			f"Passages:\n{context}"
		)
	)
	prompt_messages = [system_prompt] + history + [HumanMessage(content=user_question)]
	
	response = llm.invoke(prompt_messages)
	usage = response.response_metadata.get("token_usage", {})
	return response.content, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


def main():
	print(Fore.CYAN + "=== Conversational Book RAG: The Adventures of Pinocchio ===" + Style.RESET_ALL)
	print("Ask questions about the book (type 'quit' to exit).\n")

	chat_history = []
	session_tokens = 0

	while True:
		try:
			user_input = input(Fore.CYAN + "Question: " + Style.RESET_ALL).strip()

			if not user_input:
				continue

			if user_input.lower() in ("quit", "exit", "q"):
				print(Fore.CYAN + "Goodbye!" + Style.RESET_ALL)
				break

			total_prompt_tokens = 0
			total_completion_tokens = 0

			# If there is a conversation history, we contextualize the question.
			if chat_history:
				query_to_search, p_tok, c_tok = rephrase_question(user_input, chat_history)
				total_prompt_tokens += p_tok
				total_completion_tokens += c_tok
				print(Style.DIM + f"  [Contextualized query: {query_to_search}]" + Style.RESET_ALL)
			else:
				query_to_search = user_input

			# Searching for relevant excerpts from the book
			docs = retriever.invoke(query_to_search)
			context = "\n\n---\n\n".join([d.page_content for d in docs])

			# Generating response
			answer, p_tok, c_tok = answer_question(user_input, context, chat_history)
			total_prompt_tokens += p_tok
			total_completion_tokens += c_tok

			# Outputting the answer
			print("\n" + Fore.GREEN + f"Answer:\n{answer}" + Style.RESET_ALL)

			# Displaying the passages used
			if "I cannot find the answer in the provided passages of the book." not in answer:
				print("\n" + Style.DIM + "Passages used:" + Style.RESET_ALL)
				for i, doc in enumerate(docs, start=1):
					idx = doc.metadata.get("start_index", "N/A")
					snippet = doc.page_content.replace("\n", " ")[:160]
					print(Style.DIM + f"  [{i}] (start_index: {idx}) {snippet}..." + Style.RESET_ALL)

			# Counting and outputting the tokens consumed for the entire request
			total_tokens = total_prompt_tokens + total_completion_tokens
			session_tokens += total_tokens
			print("\n" + Fore.YELLOW + f"[Tokens used: Input: {total_prompt_tokens} | Output: {total_completion_tokens} | Total: {total_tokens}] | Session Tokens: {session_tokens}]" + Style.RESET_ALL)
			print("-" * 90)

			# Preserving history (we keep the last 6 exchanges)
			chat_history.append(HumanMessage(content=user_input))
			chat_history.append(AIMessage(content=answer))
			if len(chat_history) > 6:
				chat_history = chat_history[-6:]

		except Exception as e:
			print(Fore.RED + f"\nError: {e}" + Style.RESET_ALL)


if __name__ == "__main__":
	main()