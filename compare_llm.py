
import os 
from sql_rag import ChatQuery , Database 
from langchain_community.llms import VLLMOpenAI
from typing import Optional, Dict
import pandas as pd
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

import mysql.connector

from langchain.output_parsers import StructuredOutputParser, ResponseSchema

import io


def get_report(session_id: str) -> Optional[str]:
    reports_dir = "Reports"
    filename = f'output{session_id}.csv'
    file_path = os.path.join(reports_dir, filename)
    
    if os.path.exists(file_path):
        return file_path
    else:
        return None

def write_excel(question, gpt_query, deepseek_query, gpt_query_result, deepseek_query_result, session_id , explanation):
    try:
        data = {
            'Question': [question],
            'GPT Query': [gpt_query],
            'GPT Query Result': [gpt_query_result.to_string(index=False)],
            'Deepseek Query': [deepseek_query],
            'Deepseek Query Result': [deepseek_query_result.to_string(index=False)],
            'DeepSeek Explanation' : [explanation]
        }

        # Create a DataFrame from the dictionary
        df = pd.DataFrame(data)

        directory = "Reports"
        if not os.path.exists(directory):
            os.makedirs(directory)

        file_path = os.path.join(directory, f'output{session_id}.csv')

        # Check if the file exists
        file_exists = os.path.isfile(file_path)

        # Write DataFrame to CSV
        if not file_exists:
            # If the file doesn't exist, create a new one with header
            df.to_csv(file_path, index=False)
        else:
            # Append to existing CSV file without header
            df.to_csv(file_path, index=False, mode='a', header=False)
    except Exception as e:
        print(f"An error occurred while writing to CSV: {e}")


def execute_db_query(db ,query1 , query2):

    
    
    try:
        query1_result,column_names1 = db.execute_query(query1)
        print("query 1 ", query1_result)
        df1 = pd.DataFrame(query1_result, columns=column_names1)
       
    except:
        df1 = pd.DataFrame()
    try:
        query2_result, column_names2 = db.execute_query(query2)
        df2 = pd.DataFrame(query2_result, columns=column_names2)
      
    except Exception as e:
        print(f"An error occurred: {e}")
        df2 = pd.DataFrame()
       
        
    return df1 , df2


def post_process(question , response , results , llm):
    

    response_schemas = [
        ResponseSchema(name="explanation", description="explanation of executed query results ")
    ]

    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()
   
    
    prompt2 = ChatPromptTemplate(
        messages=[
            HumanMessagePromptTemplate.from_template(
                """
                        
                        You job is to Explain the query executions results for the simplicity of the human.

                        Question asked by human = {question}
                        Mysql Query and Explanation Generated by AI = {response}
                        Query Execution results = {results}

                        Output:
                        Only explain the results of query execution in a descriptive way and with markdown formatting but nothing else.
                        

                 \n{format_instructions}\n{question}

                """
            )
        ],
        input_variables=["conversation" , "response" , "results"],
        partial_variables={"format_instructions": format_instructions}
    )

    _input = prompt2.format_prompt(question=question , response = response , results = results)
    result = llm(_input.to_messages())
    zz = output_parser.parse(result.content)

    return zz

def get_db_schema_as_string(db_connection):
    try:
      
        # Query to retrieve the schema information
        query = """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = DATABASE();
        """
        query_result,column_names = db_connection.execute_query(query)
        # print("query 1 ", query1_result)
        df1 = pd.DataFrame(query_result, columns=column_names)
       

        return df1
    except mysql.connector.Error as err:
        print("Error:", err)
        return None

def compare_llm_results(db ,gpt_query , question ,db_schema , session_id):
    

    llm = VLLMOpenAI(
    openai_api_key="EMPTY",
    openai_api_base="http://localhost:8000/v1",
    model_name="deepseek-ai/deepseek-coder-6.7b-instruct",
    model_kwargs={"stop": ["."]},
)
    chat_query_instance = ChatQuery(model = llm) 

    llm_response = chat_query_instance.generate_sql_query(question , db_schema)
    query1 = chat_query_instance.extract_query(llm_response)
 
    result1,result2 = execute_db_query(db ,query1, gpt_query)
    
    
    post_process_results = post_process(question , llm_response ,result1 , llm)


    if result1.empty:
        post_process_results = "None"
    
    write_excel(question, gpt_query, query1  , result2,result1  , session_id , post_process_results.get("explanation"))

    return llm_response , post_process_results , result1

    


# compare_llm_results("find out total number of apartments in the database")
# compare_llm_results("count average number of apartments")

