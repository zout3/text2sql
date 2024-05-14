import os
import re
from collections import defaultdict
from llama_index.core.schema import TextNode
from llama_index.core import VectorStoreIndex
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.objects import (
    SQLTableNodeMapping,
    ObjectIndex,
    SQLTableSchema,
)


def get_db_graph(db, degree):
    tables = db.get_usable_table_names()
    graph = defaultdict(set)
    if degree == 0:
        return graph
    for table in tables:
        table_info = db.get_table_info([table])
        neighbors = re.findall("REFERENCES ([a-z]+)", table_info)
        graph[table].update(neighbors)
        for neighbor in neighbors:
            graph[neighbor].add(table)
    if degree > 1:
        for i in range(degree-1):
            graph_new = defaultdict(set)
            for node, nbrs in graph.items():
                graph_new[node].update(nbrs)
                for nbr in nbrs:
                    graph_new[node].update(graph[nbr]) 
            graph = graph_new
    return graph

def get_schema_retriever(path, dbs, top_k=3, degree=1):
    db_lc, db_li = dbs[0], dbs[1]
    nbr = get_db_graph(db_lc, degree)
    mapping = SQLTableNodeMapping(db_li)
    path_storage = path + f"schema_storage_{degree}/"
    if not os.path.exists(path_storage):
        os.mkdir(path_storage)
        table_schema_objs = []
        query = "SELECT DISTINCT {} FROM {} LIMIT 10"
        for table in db_lc.get_usable_table_names():
            schema = db_lc.get_table_info([table])
            unique_column_vals = []
            for column in db_li.get_table_columns(table):
                column_name = column["name"]
                vals = column_name + " : " + db_lc.run(query.format(column_name, table))[1:-1]
                unique_column_vals.append(vals)
            context_str = schema + "\n\nSampled values for each column\n" + "\n".join(unique_column_vals)
            with open(path_storage + table + ".txt", "w", encoding='UTF-8') as file:
                file.write(context_str)
            table_schema_objs.append(SQLTableSchema(table_name=table, context_str=" ".join(nbr[table])))
        
        index = ObjectIndex.from_objects(
            table_schema_objs,
            mapping,
            VectorStoreIndex)
        index.persist(persist_dir=path_storage)
    else:
        index = ObjectIndex.from_persist_dir(
            persist_dir=path_storage,
            object_node_mapping=mapping)
    retriever = index.as_retriever(similarity_top_k=top_k)
    return retriever

def get_document_retriever(path, top_k=5):
    if not os.path.exists(path + "document_storage/"):
        with open(path + "document.txt", "r", encoding='UTF-8') as file:
            lines = file.readlines()
        unique_lines = {l for l in lines if len(l) > 0}
        nodes = [TextNode(text=node) for node in unique_lines]
        index = VectorStoreIndex(nodes)
        index.storage_context.persist(persist_dir=path+"document_storage/")
    else:   
        storage_context = StorageContext.from_defaults(persist_dir=path+"document_storage/")
        index = load_index_from_storage(storage_context)
    retriever = index.as_retriever(similarity_top_k=top_k)
    return retriever

def get_example_index_and_retriever(path, top_k=5):
    if not os.path.exists(path + "example_storage/"):
        examples = []
        example = ""
        with open(path + "example.txt", "r", encoding='UTF-8') as file:
            while True:
                line = file.readline()
                if not line:
                    break
                elif line.find("NL2SQL example begin") > -1:
                    example = ""
                elif line.find("NL2SQL example end") > -1:
                    examples.append(example)
                else:
                    example = example + '\n' + line
        nodes = []
        for example in examples:
            question, _ = example.split("SQL:")
            nodes.append(TextNode(text=question, metadata={"example":example}))
        index = VectorStoreIndex(nodes)
        index.storage_context.persist(persist_dir=path+"example_storage/")
    else:   
        storage_context = StorageContext.from_defaults(persist_dir=path+"example_storage/")
        index = load_index_from_storage(storage_context)
    retriever = index.as_retriever(similarity_top_k=top_k)
    return index, retriever

def generate_prompt_from_document(retriever, query):
    prompt = "\n".join(k.text for k in retriever.retrieve(query))
    return prompt + "\n\n"

def generate_prompt_from_schema(retriever, query, path, degree=1):
    tables = set()
    for node in retriever.retrieve(query):
        tables.add(node.table_name)
        tables.update(node.context_str.split())
    prompts = []
    for table in tables:
        with open(path + f"schema_storage_{degree}/" + table + ".txt", "r", encoding='UTF-8') as file:
            prompts.append(file.read())
    return "\n".join(prompts) + "\n\n"

def generate_prompt_from_example(retriever, query, threshold=0.78):
    prompt = "\n".join(
        k.metadata["example"] for k in retriever.retrieve(query) if k.score > threshold
    )
    return prompt + "\n\n"






