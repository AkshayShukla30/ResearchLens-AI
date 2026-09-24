from langchain_huggingface import HuggingFaceEmbeddings

MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"

def create_embeddings():
    return HuggingFaceEmbeddings(model_name=MODEL_NAME)
