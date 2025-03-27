import bs4
from langchain import hub
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import START, StateGraph
from typing import List, TypedDict
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play

load_dotenv()

# Get API key - use OPENAI_API_KEY as this is the standard name
openai_api_key = os.getenv("OPENAI_KEY")
if not openai_api_key:
    raise ValueError("Please set OPENAI_API_KEY in your environment variables")


#Initalize ElevenLabs for Voice Responses
client = ElevenLabs(
  api_key=os.getenv("ELEVENLABS_API_KEY"),
)

# Initialize LLM - using the standard ChatOpenAI
llm = ChatOpenAI(model="gpt-4", api_key=openai_api_key)  # Changed from "gpt-4o-mini" which doesn't exist

embeddings = OpenAIEmbeddings(model="text-embedding-3-large", api_key=openai_api_key)

# Load and process documents
loader = WebBaseLoader(
    web_paths=("https://www.morgan.edu/computer-science/faculty-and-staff","https://www.morgan.edu/computer-science/faculty-and-staff/shuangbao-wang","https://www.morgan.edu/computer-science/faculty-and-staff/md-rahman","https://www.morgan.edu/computer-science/faculty-and-staff/amjad-ali","https://www.morgan.edu/computer-science/faculty-and-staff/radhouane-chouchane","https://www.morgan.edu/computer-science/faculty-and-staff/monireh-dabaghchian","https://www.morgan.edu/computer-science/faculty-and-staff/jamell-dacon","https://www.morgan.edu/computer-science/faculty-and-staff/naja-mack","https://www.morgan.edu/computer-science/degrees-and-programs"),
    bs_kwargs=dict(
        parse_only=bs4.SoupStrainer(
            class_=("profile-box","body-copy","copy"),
        )
    ),
)
docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
all_splits = text_splitter.split_documents(docs)

# Set up vector store
connection = "postgresql+psycopg://langchain:langchain@localhost:6024/langchain"
collection_name = "prof_docs"

vector_store = PGVector(
    embeddings=embeddings,
    collection_name=collection_name,
    connection=connection,
    use_jsonb=True,
)

# Index chunks
vector_store.add_documents(documents=all_splits)

# Define proper prompt template
prompt_template = ChatPromptTemplate.from_messages([
    ("system", "You are a friendly and knowledgeable AI Academic assistant. Your job is to help students answer questions they have about morgan state university's computer science department and program."),
    ("human", "Question: {question}\n\nContext: {context}")
])

# Define state for application
class State(TypedDict):
    question: str
    context: List[Document]
    answer: str

# Define application steps
def retrieve(state: State):
    retrieved_docs = vector_store.similarity_search(state["question"])
    return {"context": retrieved_docs}

def generate(state: State):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    # Format the prompt with the question and context
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
graph = workflow.compile()

# Test the application
try:
    response = graph.invoke({"question": input("Enter your queston")})
    print(response["answer"])
    audio = client.text_to_speech.convert_as_stream(
        text=response["answer"],
        voice_id="onwK4e9ZLuTAKqWW03F9",
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    play(audio)
except Exception as e:
    print(f"Error occurred: {str(e)}")