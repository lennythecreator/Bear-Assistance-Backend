import os
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph
from typing import List, TypedDict


# Load environment variables
load_dotenv()

# Define state for application
class State(TypedDict):
    question: str
    context: List[Document]
    answer: str

def initialize_graph():
    # Get API keys
    openai_api_key = os.getenv("OPENAI_KEY")
    groq_api_key = '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'

    # Initialize LLM and embeddings
    llm = init_chat_model(model="llama3-8b-8192", api_key=groq_api_key, model_provider='groq', max_tokens = 150, temperature = 0.7)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large", api_key=openai_api_key)

    # Set up vector store
    connection = "postgresql+psycopg://langchain:langchain@localhost:6024/langchain"
    collection_name = "prof_docs"
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=connection,
        use_jsonb=True,
    )

    # Define prompt template
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """You are an AI Academic Assistant for Morgan State University's Computer Science department. Your goal is to help students by answering their questions accurately and in a friendly, conversational tone.

Instructions:

1.  Read the provided context carefully. The context contains the information necessary to answer the student's question.
2.  Answer the student's question directly and factually. Ensure the information you provide is accurate and based solely on the context.
3.  Avoid explicitly stating that the information comes from the provided context. Instead, present the information as if you are directly providing it.
4.  Use a friendly and conversational tone. Imagine you are a helpful peer or advisor assisting the student. Employ natural language and avoid overly formal or robotic phrasing.
5.  If possible, incorporate elements of the student's question into your response to create a more natural flow.
6.  Prioritize clarity and conciseness. Deliver the information in a way that is easy for the student to understand.

Example:

Context: Dr. Shuangbao "Paul" Wang's email address is shuangbao.wang@morgan.edu.

Student Question: How do I contact Dr. Wang?

Good Response: You can reach Dr. Shuangbao "Paul" Wang at shuangbao.wang@morgan.edu.

Bad Response: According to the provided context, Dr. Shuangbao "Paul" Wang's email address is shuangbao.wang@morgan.edu.
"""),
        ("human", "Question: {question}\n\nContext: {context}")
    ])

    # Define application steps
    def retrieve(state: State):
        retrieved_docs = vector_store.similarity_search(state["question"])
        return {"context": retrieved_docs}

    def generate(state: State):
        docs_content = "\n\n".join(doc.page_content for doc in state["context"])
        formatted_prompt = prompt_template.format_messages(
            question=state["question"],
            context=docs_content
        )
        response = llm.invoke(formatted_prompt)
        return {"answer": response.content}

    # Build and compile the graph
    workflow = StateGraph(State)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("generate", generate)
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "generate")
    return workflow.compile()

# Initialize the graph when the module is imported
graph = initialize_graph()