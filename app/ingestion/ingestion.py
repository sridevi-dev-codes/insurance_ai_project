from dotenv import load_dotenv
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.db import get_vector_store
import time

# C:\Users\t91-labuser061568\Documents\agentic-ai-course-may2026\insurance_ai_project\Instructions_pdf
load_dotenv()
PG_CONNECTION = os.getenv("PG_CONNECTION_STRING")


def ingest_pdf(file_path):
   print("Ingestion Started")
   #1. Load PDF
   loader = PyPDFLoader(file_path)
   docs = loader.load()
   for i, doc in enumerate(docs):
    text = doc.page_content or ""
    print(f"Page {i+1}: chars={len(text)}")
   
   
   print("Pages : ", len(docs))

   # 2. Metadata enrichment
   for doc in docs:
       doc.metadata.update({
           "source": file_path,
           "document_extension": "pdf",
           "page": doc.metadata.get("page"),
           "last_updated": os.path.getmtime(file_path)
       })

   # 3. Chunking
   splitter = RecursiveCharacterTextSplitter(
       chunk_size=1000, # characters
       chunk_overlap=200 # characters
   )

   chunks = splitter.split_documents(docs)
   print("Total Chunks", len(chunks))

   # 4 and 5
   # generate the embeddings store in vector db
   vector_store = get_vector_store(collection_name="insurance_support_desk", pre_delete_collection=True)
   # FIXME: I am running a  for loop to add documents with ids. but it should ideally work with batch add_documents.
   for i, chunk in enumerate(chunks):
       vector_store.add_documents([chunk], ids=[f"{chunk.metadata['source']}_{chunk.metadata['page']}_{i}"])

   print("======Ingestion Completed Successfully!=======")


# if __name__ == "__main__":
#    ingest_pdf("data/HR_Support_Desk_KnowledgeBase.pdf")