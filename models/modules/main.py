# __import__('pysqlite3')
# import sys
# sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.schema import prompt
from langchain_community.callbacks import get_openai_callback

from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI

# from langchain_community.chat_models import AzureChatOpenAI

from dotenv import load_dotenv
from . import EMBEDDINGS_BGE_BASE
import os

# loading virtual env
load_dotenv()
os.environ["OPENAI_ENDPOINT"] = os.environ.get('AZURE_OPENAI_ENDPOINT')
os.environ["OPENAI_API_VERSION"] = os.environ.get("AZURE_OPENAI_API_VERSION")

from langchain_openai import AzureChatOpenAI

azure_openai_mode = True


# Downloading Embeddings i.e: bge-base-en


class Chatbase:
    def __init__(self, embeddings=EMBEDDINGS_BGE_BASE):
        self.embeddings = embeddings

    def load_text(self, dir):
        loader = TextLoader(dir)
        documents = loader.load()
        return documents

    def split_docs(self, documents, chunk_size=750, chunk_overlap=50):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        splitted_docs = text_splitter.split_documents(documents)
        return splitted_docs

    def embed(self, persist_path, docs):
        try:
            vectordb = Chroma.from_documents(documents=docs, embedding=self.embeddings, persist_directory=persist_path)
            vectordb.persist()
            return True
        except:
            return False

    def ask(self, query, model_name="gpt-3.5-turbo-16k"):
        # using openAI 0.28
        language_model = None
        if azure_openai_mode:

            language_model = AzureChatOpenAI(
                openai_api_version=os.environ['AZURE_OPENAI_API_VERSION'],
                deployment_name=os.environ['AZURE_DEPLOYMENT_NAME'],
            )
        else:
            language_model = ChatOpenAI(model_name=model_name)

        response = language_model.invoke(('human',query))

        # print(response)
        return response

    def doc_chat(self, query, vectordb, model_name="gpt-3.5-turbo-16k"):
        matching_docs = vectordb.similarity_search_with_score(query)

        # using openAI 0.28
        language_model = None
        if azure_openai_mode:

            language_model = AzureChatOpenAI(
                openai_api_version=os.environ['AZURE_OPENAI_API_VERSION'],
                deployment_name=os.environ['AZURE_DEPLOYMENT_NAME'],
            )
        else:
            language_model = ChatOpenAI(model_name=model_name)
        retrieval_chain = RetrievalQA.from_chain_type(language_model,
                                                      chain_type="stuff",
                                                      retriever=vectordb.as_retriever(search_kwargs={'k': 30},
                                                                                      return_source_documents=True))
        response = retrieval_chain.invoke(query)

        # print(response)
        return response, matching_docs


if __name__ == '__main__':
    # docs = chatobj.load_docs('/home/ubuntu/workspace/data')
    # docs_split = chatobj.split_docs(docs)
    # persistDb= chatobj.persist_db('./Database', docs_split)
    chatobj = Chatbase(EMBEDDINGS_BGE_BASE)
    vectordb = Chroma(persist_directory="./Database", embedding_function=EMBEDDINGS_BGE_BASE)
    while (True):
        query = input("Enter the Query: ")
        if query == "exit":
            break
        else:
            with get_openai_callback() as cb:
                resp, sources = chatobj.chat(query, vectordb)
                print(resp, "\n{}".format(cb))
