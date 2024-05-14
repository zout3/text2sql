from llama_index.core.schema import TextNode

from llama_index.core import SQLDatabase as sqldb_li
from langchain_community.utilities import SQLDatabase as sqldb_lc

from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain


def init_database(user, password, host, port, database):
    db_uri = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
    db_lc = sqldb_lc.from_uri(db_uri)
    db_li = sqldb_li.from_uri(db_uri)
    return [db_lc, db_li]

def llm_generator(model, prompt, **kwargs):
    llm = ChatOpenAI(model=model, temperature=0.0)
    chain = LLMChain(llm=llm, prompt=prompt)
    answer = chain.invoke(kwargs)["text"]
    return answer

def update_example_index(path, question, example, index):
    node = [TextNode(text=question, metadata={"example":example})]
    index.insert_nodes(node)
    index.storage_context.persist(persist_dir=path+"example_storage/")
    return index