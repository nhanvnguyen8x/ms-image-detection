from langchain_community.embeddings import SentenceTransformerEmbeddings

EMBEDDINGS_BGE_BASE = SentenceTransformerEmbeddings(model_name="BAAI/bge-base-en")