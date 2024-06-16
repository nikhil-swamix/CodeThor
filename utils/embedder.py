from chromadb import EmbeddingFunction, Documents, Embeddings
from typing import List, Optional, cast
from enum import Enum
import os


def st_embedder(sentences, model_name="nomic-ai/nomic-embed-text-v1", cache_folder="D:\\Models\\"):
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name, trust_remote_code=True, cache_folder=cache_folder)
    embeddings = model.encode(sentences)
    return embeddings


# def ol_embedder(sentences,):
def normalize(data):
    def top_percentile(lst, p):
        sortedl = sorted(lst)
        return sortedl[int(len(sortedl) * p / 100)]

    def fn(lst):
        top_p = top_percentile(lst, 40)
        mn, mx, mean = min(lst), max(lst), sum(lst) / len(lst)

        lst = [(x) / (mx - mn) for x in lst]
        # print(min_val, max_val)
        norm = []
        for x in lst:
            # x = x**2

            if x >= top_p:
                x = x
            else:
                x = x**2
            norm.append(x)
        return norm

    if isinstance(data[0], list):
        return [fn(sublist) for sublist in data]
    else:
        return fn(data)


class OllamaEmbedder(EmbeddingFunction):

    def __init__(
        self,
        model_name=[
            "znbang/bge:large-zh-v1.5-f16",
            "mixbai",
            "nomic-embed-text:latest",
            "milkey/gte:large-zh-f16",
        ][1],
    ) -> None:
        # mxbai-embed-large:335m | nomic-embed-text:latest
        self.model = model_name
        print(f"Using Embedding model: {self.model}")

    def __call__(self, sentences):
        import ollama

        c = ollama.Client(host="http://localhost:11433")

        def fetch_embedding(sentence):

            response = c.embeddings(model=self.model, prompt=sentence)
            return response['embedding']

        embeddings = []
        for sentence in sentences:
            try:
                embedding = fetch_embedding(sentence)
                embeddings.append(embedding)
            except Exception as e:
                # Handle exceptions (you can log it or raise)
                embeddings.append(None)

        return normalize(embeddings)


class VoyageAIEmbeddingFunction(EmbeddingFunction[Documents]):
    """Embedding function for Voyageai.com. API docs - https://docs.voyageai.com/reference/embeddings-api"""

    class InputType(str, Enum):
        DOCUMENT = "document"
        QUERY = "query"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "voyage-code-2",
        max_batch_size: int = 128,
        truncation: Optional[bool] = True,
        input_type: Optional[InputType] = None,
    ):

        if not api_key and "VOYAGE_API_KEY" not in os.environ:
            raise ValueError("Please provide a VoyageAI API key.")

        try:
            import voyageai

            if max_batch_size > voyageai.VOYAGE_EMBED_BATCH_SIZE:
                raise ValueError(f"The maximum batch size supported is {voyageai.VOYAGE_EMBED_BATCH_SIZE}.")
            self._batch_size = max_batch_size
            self._model = model_name
            self._truncation = truncation
            self._client = voyageai.Client(api_key=api_key)
            self._input_type = input_type
        except ImportError:
            raise ValueError(
                "The VoyageAI python package is not installed. Please install it with `pip install voyageai`"
            )

    def __call__(self, input: Documents) -> Embeddings:
        if len(input) > self._batch_size:
            raise ValueError(f"The maximum batch size supported is {self._batch_size}.")
        results = self._client.embed(
            texts=input,
            model=self._model,
            truncation=self._truncation,
            input_type=self._input_type,
        )
        return cast(Embeddings, results.embeddings)


class MixedbreadAIEmbeddingFunction:
    """Embedding function for MixedbreadAI. API docs - https://docs.mixedbread.ai/reference/embeddings-api"""

    class InputType(str, Enum):
        DOCUMENT = "document"
        QUERY = "query"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "mixedbread-ai/mxbai-embed-large-v1",
        max_batch_size: int = 128,
        truncation: Optional[bool] = True,
        input_type: Optional[InputType] = None,
    ):
        from mixedbread_ai.client import MixedbreadAI

        if not api_key and "MIXEDBREAD_API_KEY" not in os.environ:
            raise ValueError("Please provide a MixedbreadAI API key.")

        self._batch_size = max_batch_size
        self._model = model_name
        self._truncation = truncation
        self._client = MixedbreadAI(api_key=os.environ["MIXEDBREAD_API_KEY"])
        self._input_type = input_type

    def __call__(self, input: list) -> list:

        if len(input) > self._batch_size:
            raise ValueError(f"The maximum batch size supported is {self._batch_size}.")
        results = self._client.embeddings(
            model=self._model,
            input=input,
        )
        return [x.embedding for x in results.data]


if __name__ == "__main__":
    sentences = ['search_query: What is TSNE?', 'search_query: Who is Laurens van der Maaten?']

    # print("ST Embeddings:")
    # st_embeddings = st_embedder(sentences)
    # print(st_embeddings)

    # ol_embeddings = VoyageAIEmbeddingFunction()(sentences)
    ol_embeddings = OllamaEmbedder()(sentences)
    print((ol_embeddings))
