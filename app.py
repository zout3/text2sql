import os
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain

from utils import (
    init_database,
    llm_generator,
    update_example_index
)

from retrievers import (
    get_schema_retriever,
    get_document_retriever,
    get_example_index_and_retriever,
    generate_prompt_from_document,
    generate_prompt_from_schema,
    generate_prompt_from_example
)

from prompts import (
    CLASSIFICATION_PROMPT,
    SQL_GENERATION_PROMPT,
    CORRECTION_PROMPT,
    SQL_EXTRACTION_PROMPT,
    PREVIEW_PROMPT,
    SQL_RESULT_OUTPUT_PROMPT
)

os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
kg_path = './knowledge/'
openai_model = "gpt-3.5-turbo"

def positive_feedback(schema, document, question, sql):
    # update example.txt
    example = f"question:\n{question}\nSQL:\n{sql}"
    with open(kg_path + "example.txt", "a", encoding='UTF-8') as file:
        file.write("NL2SQL example begin\n")
        file.write(example)
        file.write("\nNL2SQL example end\n\n\n")
    # update vector store                
    st.session_state.ex_idx = update_example_index(kg_path,
                                                   question,
                                                   example,
                                                   st.session_state.ex_idx)                                
    top_k = st.session_state.ex_rtr.similarity_top_k
    st.session_state.ex_rtr = st.session_state.ex_idx.as_retriever(similarity_top_k=top_k)
    # answer the question
    sql_output = st.session_state.dbs[0].run_no_throw(sql)
    
    if len(sql_output) > 2000:
        sql_output = sql_output[:2000]

    answer = llm_generator(
        model = openai_model,
        prompt = SQL_RESULT_OUTPUT_PROMPT,
        schema = schema,
        document = document,
        question = question,
        sql = sql,
        output = sql_output  
    )
    st.session_state.chat_history.append(AIMessage(content=answer))
    st.session_state.chat_status = "clarify"


def negative_feedback():
    message_negative = AIMessage(
        content="Sorry for not being able to help you. Please try to ask again."
    )
    st.session_state.chat_history.append(message_negative)
    st.session_state.chat_status = "clarify"


def self_correct(model, schema, document, question, sql_plain, guide="None", ntime=1):
    for _ in range(ntime):  
        sql_corrected = llm_generator(
            model = openai_model,
            prompt = CORRECTION_PROMPT,
            question = question,
            schema = schema,
            document = document,
            sql_query = sql_plain,
            guide=guide)
        sql_plain = llm_generator(
            model = openai_model,
            prompt = SQL_EXTRACTION_PROMPT,
            text = sql_corrected)           
    preview = llm_generator(
        model = openai_model,
        prompt = PREVIEW_PROMPT,
        schema = schema,
        sql = sql_plain
    )           
    response = f"""
    SQL query:  
    {sql_plain}  
    Output table header preview:  
    {preview}  
    Please tell me if you are satisfied with the preview result.
    You can also provide suggestions on how to improve the SQL query.
    """
    placeholder = st.empty()
    with placeholder.chat_message("AI"):
        st.markdown(response)
        col1,col2,col3,col4 = st.columns([3,3,0.5,0.5])
        with col3:
            st.button(":thumbsup:",
                      on_click=positive_feedback,
                      kwargs={
                          "schema":schema,
                          "document":document,
                          "question":question,
                          "sql":sql_plain,
                          })
        with col4:
            st.button(":thumbsdown:", on_click=negative_feedback)          
    st.session_state.chat_history.append(AIMessage(content=response))
    return sql_plain
    

############################################################################################################## 


st.set_page_config(page_title="TEXT2SQL",
                   page_icon=":speech_ballon:")
st.title("Chat to MySQL Database")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
      AIMessage(content="Hello! I'm a SQL assistant. Ask me anything about your database."),
    ]

with st.sidebar:
    st.subheader("Settings")
    st.write("This is a chat application using MySQL. Connect to the database and start chatting")
    st.text_input("Host", value=st.secrets["DB_HOST"], key="Host")
    st.text_input("User", value=st.secrets["DB_USER"], key="User")
    st.text_input("Password", type=st.secrets["DB_PASSOWRD"], value="940719", key="Password")
    st.text_input("Database", value=st.secrets["DB_NAME"], key="Database")

    if st.button("Start"):
        with st.spinner("Connecting to database..."):
            databases = init_database(
                st.session_state["User"],
                st.session_state["Password"],
                st.session_state["Host"],
                st.session_state["Database"]
            )
            st.session_state.dbs = databases
            st.success("Connected to database!")
            
        with st.spinner("Initializing knowledge base..."):
            st.session_state.sc_rtr = get_schema_retriever(kg_path, databases)
            st.session_state.dc_rtr = get_document_retriever(kg_path)
            st.session_state.ex_idx, st.session_state.ex_rtr = \
                get_example_index_and_retriever(kg_path)
            st.success("Knowledge base initialized!")


for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("AI"):
            st.markdown(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("Human"):
            st.markdown(message.content)


if "chat_status" not in st.session_state:
    st.session_state.chat_status = "clarify"



user_input = st.chat_input("Type a message...")


if user_input is not None and user_input.strip() != "":
    if st.session_state.chat_status == "clarify":
        print("question:\n", user_input, "\n")
        question = user_input
        with st.chat_message("Human"):
            st.markdown(question)
        st.session_state.chat_history.append(HumanMessage(content=question))
        
        schema = generate_prompt_from_schema(st.session_state.sc_rtr, question, kg_path)
        document = generate_prompt_from_document(st.session_state.dc_rtr, question)
        
        print("schema:\n", schema, "\n")
        print("document:\n", document, "\n")
        
        classification = llm_generator(
            model = openai_model,
            prompt = CLASSIFICATION_PROMPT,
            schema = schema,
            document = document,
            question = question
        )
               
        if "INSUFFICIENT" in classification:
            clarification = classification.split("INSUFFICIENT")[-1].strip()
            if not clarification:
                clarification = "The question is irrelevant of the database. Please ask question about the database."   
            else:
                clarification = clarification + " And please ask a complete question instead of additions to the previous question."
            
            with st.chat_message("AI"):
                st.markdown(clarification)
            st.session_state.chat_history.append(AIMessage(content=clarification))

                
        elif "INFORMATIVE" in classification: 
            example = generate_prompt_from_example(st.session_state.ex_rtr, question)
            print("example:\n", example, "\n")
            sql_unrefined = llm_generator(
                model = openai_model,
                prompt = SQL_GENERATION_PROMPT,
                schema = schema,
                document = document,
                example = example,
                question = question
            )
            # self-correction
            sql_plain = llm_generator(
                model = openai_model,
                prompt = SQL_EXTRACTION_PROMPT,
                text = sql_unrefined)
            
            sql_sc = self_correct(
                model = openai_model,
                schema = schema,
                document = document,
                question = question,
                sql_plain = sql_plain,
                ntime = 2
            )
            st.session_state.chat_status = "review"
            st.session_state.sql = sql_sc
            st.session_state.schema = schema
            st.session_state.document = document
            st.session_state.question = question
            st.session_state.guide = ""
            
    elif st.session_state.chat_status == "review":
        guide = user_input
        with st.chat_message("Human"):
            st.markdown(guide)
        st.session_state.chat_history.append(HumanMessage(content=guide))
        st.session_state.guide += guide + "\n"
        sql_sc = self_correct(
            model = openai_model,
            schema = st.session_state.schema,
            document = st.session_state.document,
            question = st.session_state.question,
            sql_plain = st.session_state.sql,
            guide = st.session_state.guide
        )

    
    
    
    
    
    
    
    
    
            

    


