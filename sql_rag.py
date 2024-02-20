"""
This script defines a pipeline to interactively generate SQL queries for an Apartment Management System using LangChain and execute them on a MySQL database.

Requirements:
- langchain_mistralai (for ChatMistralAI)
- langchain (for other LangChain components)
- mysql-connector-python (for MySQL database connectivity)

pip isntall -r requirements.txt

Make sure to install these dependencies before running the script.

"""

import re
import os
import warnings
import mysql.connector
from langchain_mistralai.chat_models import ChatMistralAI
from langchain.chains import LLMChain
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain

from mysql.connector import errors
from langchain_core._api.deprecation import LangChainDeprecationWarning
from langchain.memory import ConversationBufferMemory



from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_community.chat_models import ChatOllama


warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)

class Mixtral:
    """
    MixtralAI model initializer.

    Args:
        model_name (str): Name of the MixtralAI model.
        api_key (str): API key for accessing the MixtralAI service.
    """
    def __init__(self, model_name, api_key):
        """Initialize MixtralAI with model name and API key."""
        self.model_name = model_name
        self.api_key = api_key
    
    def __call__(self):
        """Return initialized ChatMistralAI instance."""
        return ChatMistralAI(model_name=self.model_name, mistral_api_key=self.api_key)
    
class DeepSeek:
    """
    DeepSeek model initializer.

    Args:
        model_name (str): Name of the DeepSeek model.
        
    """
    def __init__(self, model_name , temperature=0):
        """Initialize DeepSeek with model name and API key."""
        self.model_name = model_name
        self.temprature = temperature

    def __call__(self):
        """Return initialized DeepSeek instance."""
        return ChatOllama(
            model=self.model_name,
            temperature=self.temprature
        )
        
        

class ChatQuery:

    """
    Represents a class for interacting with LangChain to generate and extract SQL queries.

    Attributes:
        model_name (str): The name of the language model for ChatMistralAI.
        api_key (str): The API key for ChatMistralAI.

    Methods:
        generate_sql_query(user_input: str) -> str:
            Generates an SQL query interactively based on user input using LangChain.

        extract_query(cleaned_query_result: str) -> str or None:
            Extracts the SQL query from the cleaned output obtained from LangChain.

    """

    def __init__(self, model):
        """
        Initilizing the model 
        """
        self.llm = model

    def generate_sql_query(self, user_input , db_schema):

        """
        Generates an SQL query interactively based on user input using LangChain.

        Args:
            user_input (str): User input representing the query.

        Returns:
            str: The SQL query bt removing '\' from llm response.

        """
        prompt = f"""
                        **Role:**
                        - Embrace the persona of "QueryWhiz," a knowledgeable companion specializing in MySQL queries.
                        - Interact seamlessly with users, responding to query needs with clarity and efficiency.
                        - Uphold a professional and informative tone, serving as a virtual guide in the realm of database queries.

                        **Generate MySQL Queries for Apartment Management System**

                        You are tasked with managing an Apartment Management System database. The schema includes the following tables:

                        {db_schema}

                        Using the given schema, generate MySQL queries for the question asked by user:

                        **Output**
                        You will only output the mysql query with proper code formatting and its brief explanation with proper format.

                        """

        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        prompt_rough = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessagePromptTemplate.from_template("{question}")
            ]
        )
        conversation = LLMChain(
            llm=self.llm,
            prompt=prompt_rough,
            verbose=False,
            memory=memory
        )

        conversation({"question": user_input})
        cleaned_query_result = memory.buffer[-1].content.replace('\\', '')
        return cleaned_query_result

    def extract_query(self, cleaned_query_result):
        """
        Extracts the SQL query from the  output obtained from llm.

        Args:
            cleaned_query_result (str): The cleaned output from llm.

        Returns:
            str or None: The extracted SQL query or None if not found.

        """
        pattern = r'```sql(.*?)```'
        match = re.search(pattern, cleaned_query_result, re.DOTALL)
        if match:
            sql_query = match.group(1).strip()
            return sql_query
        else:
            return None

class Database:
    """
    Represents a class for database connectivity and query execution.

    Attributes:
        host (str): The database host.
        db_user (str): The database user.
        db_password (str): The database password.
        db_name (str): The database name.
        max_retries (int): The maximum number of retries for database connection.

    Methods:
        _connect() -> mysql.connector.connection:
            Establishes a connection to the MySQL database.

        is_connected() -> bool:
            Checks if the database connection is currently active.

        execute_query(query: str) -> list:
            Executes an SQL query on the connected database.

    """
    def __init__(self, host="localhost", db_user="root", db_name="Apartments_Data", db_password="admin", max_retries=3):
        self.host = host
        self.db_user = db_user
        self.db_password = db_password
        self.db_name = db_name
        self.max_retries = max_retries
        self.connection = self._connect()

    def _connect(self):
        """
        Establishes a connection to the MySQL database.

        Returns:
            mysql.connector.connection: The database connection object.

        """
        return mysql.connector.connect(
            host=self.host,
            user=self.db_user,
            password=self.db_password,
            database=self.db_name
        )
    def _connect_with_pymsql(self):
        """
        Establishes a connection to the MySQL database.

        Returns:
            mysql.connector.connection: The database connection object.

        """
        return SQLDatabase.from_uri(f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.host}/{self.db_name}")

    def is_connected(self):
        """
        Checks if the database connection is currently active.

        Returns:
            bool: True if the connection is active, False otherwise.

        """
        try:
            self.connection.ping(reconnect=True)
            return True
        except errors.Error:
            return False

    def execute_query(self, query):
        """
        Executes an SQL query on the connected database.

        Args:
            query (str): The SQL query to be executed.

        Returns:
            list: The result set obtained from the query execution.

        Raises:
            Exception: If the query execution fails after the maximum number of retries.

        """

        if not self.is_connected():
            self.connection = self._connect()

        retries = 0
        while retries < self.max_retries:
            try:
                cursor = self.connection.cursor()
                cursor.execute(query)
                results = cursor.fetchall()
                
                column_names = [desc[0] for desc in cursor.description]
                return results, column_names
            except errors.OperationalError as e:
                if "Lost connection" in str(e):
                    print(f"Lost connection. Reconnecting (attempt {retries + 1}/{self.max_retries})...")
                    self.connection = self._connect()
                    retries += 1
                else:
                    return None  # Print the exception
        else:
            print(f"Failed to execute query after {self.max_retries} attempts.")
    
class RagSQL(Database):
    """
    Represents a class for interacting with a MySQL database using LangChain and MistralAI.

    Inherits from the Database class for basic database connectivity and query execution.

    Attributes:
        host (str): The database host.
        db_user (str): The database user.
        db_password (str): The database password.
        db_name (str): The database name.
        max_retries (int): The maximum number of retries for database connection.

    Methods:
        __init__(self, host="localhost", db_user="root", db_name="Apartments_Data", db_password="", max_retries=3):
            Initializes the Rag_SQL instance with database connection details and MistralAI configuration.

        query_with_rag(self, user_input):
            Executes an SQL query using the provided user input and the LangChain/MistralAI infrastructure.

    """

    def __init__(self, host="localhost", db_user="root", db_name="Apartments_Data", db_password="", max_retries=3, model=None):
        """
        Initializes the Rag_SQL instance with database connection details and MistralAI configuration.

        Args:
            host (str): The database host.
            db_user (str): The database user.
            db_password (str): The database password.
            db_name (str): The database name.
            max_retries (int): The maximum number of retries for database connection.

        """

        super().__init__(host, db_user, db_name, db_password, max_retries)
        # self.api_key = api_key
        self.llm = model
        self.db = self._connect_with_pymsql()

    def query_with_rag(self, user_input):
        """
        Executes an SQL query using the provided user input and the LangChain/MistralAI infrastructure.

        Args:
            user_input (str): The user input containing the SQL query.

        Returns:
            list: The result set obtained from the query execution.

        """
        db_chain = SQLDatabaseChain.from_llm(self.llm, self.db, verbose=False)
        return db_chain.run(user_input)

    

def main():
    """
    Main function to demonstrate the use of ChatQuery and Database classes.

    """
   
    # Create an instance of Mixtral with the desired model name and API key
    mixtral_llm = Mixtral(model_name="mistral-medium", api_key=os.environ.get('MIXTRAL_API_KEY'))()

    # Create an instance of DeekSeek with the downloaded quantized model name
    deepseek_llm = DeepSeek(model_name="deepseek-coder:6.7b-instruct-q4_0")()

    llm = deepseek_llm


    db_schema = """

            1. TABLE Apartment_Buildings (
                building_id INTEGER NOT NULL,
                building_short_name CHAR(15),
                building_full_name VARCHAR(80),
                building_description VARCHAR(255),
                building_address VARCHAR(255),
                building_manager VARCHAR(50),
                building_phone VARCHAR(80),
                PRIMARY KEY (building_id),
                UNIQUE (building_id)
                );

            2. *TABLE Apartments (
                apt_id INTEGER NOT NULL ,
                building_id INTEGER NOT NULL,
                apt_type_code CHAR(15),
                apt_number CHAR(10),
                bathroom_count INTEGER,
                bedroom_count INTEGER,
                room_count CHAR(5),
                PRIMARY KEY (apt_id),
                UNIQUE (apt_id),
                FOREIGN KEY (building_id) REFERENCES Apartment_Buildings (building_id)
                );

            3. TABLE Apartment_Facilities (
                apt_id INTEGER NOT NULL,
                facility_code CHAR(15) NOT NULL,
                PRIMARY KEY (apt_id, facility_code),
                FOREIGN KEY (apt_id) REFERENCES Apartments (apt_id)
                ); 

            4. TABLE Guests (
                guest_id INTEGER NOT NULL ,
                gender_code CHAR(1),
                guest_first_name VARCHAR(80),
                guest_last_name VARCHAR(80),
                date_of_birth DATETIME,
                PRIMARY KEY (guest_id),
                UNIQUE (guest_id)
                );
                
            5. TABLE Apartment_Bookings (
                apt_booking_id INTEGER NOT NULL,
                apt_id INTEGER,
                guest_id INTEGER NOT NULL,
                booking_status_code CHAR(15) NOT NULL,
                booking_start_date DATETIME,
                booking_end_date DATETIME,
                PRIMARY KEY (apt_booking_id),
                UNIQUE (apt_booking_id),
                FOREIGN KEY (apt_id) REFERENCES Apartments (apt_id),
                FOREIGN KEY (guest_id) REFERENCES Guests (guest_id)
                );

            6. CREATE TABLE View_Unit_Status (
                apt_id INTEGER,
                apt_booking_id INTEGER,
                status_date DATETIME NOT NULL,
                available_yn BIT,
                PRIMARY KEY (status_date),
                FOREIGN KEY (apt_id) REFERENCES Apartments (apt_id),
                FOREIGN KEY (apt_booking_id) REFERENCES Apartment_Bookings (apt_booking_id)
                );

            """
    

    question = "Show each apartment type code, and the maximum and minimum number of rooms for each type."

    print("-----------------------------------------------")
    print("----------------LLM RESPONSE-------------------")
    print("-----------------------------------------------")
    
    chat_query_instance = ChatQuery(model = llm)
    cleaned_query_result = chat_query_instance.generate_sql_query(question,db_schema)
    print(cleaned_query_result)

    # print("-----------------------------------------------")
    # print("----------------PARSED LLM RESPONSE------------")
    # print("-----------------------------------------------")

    # extracted_query = chat_query_instance.extract_query(cleaned_query_result)
    # print(extracted_query)

    # if extracted_query:
        
    #     database_instance = Database()
    #     query_result = database_instance.execute_query(extracted_query)
    #     print("-----------------------------------------------")
    #     print("--------------DB OUTPUT------------------------")
    #     print("-----------------------------------------------")
    #     for row in query_result:
    #         print(row)
    # else:
    #     print("No SQL query found in the output.")

    # print("-----------------------------------------------")
    # print("--------------WITH SQL RAG---------------------")
    # print("-----------------------------------------------")

    # x = RagSQL(model=deepseek_llm)
    # x.query_with_rag("Show each apartment type code, and the maximum and minimum number of rooms for each type.")


if __name__ == "__main__":
    
    main()
    