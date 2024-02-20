# Apartment Management System SQL Query Generator

This script allows you to interactively generate SQL queries for an Apartment Management System using LangChain integrated with open source llms and execute them on a MySQL database.

## Requirements

* **Python:** Make sure you have Python 3.11.6 installed on your system.
* **Dependencies:** The script utilizes various libraries. Install them using the following command:
    ```bash
    pip install -r requirements.txt
* **Ollama Models:** In order to use ollama models make sure you have downloaded it locally(Linux,Mac).
    ```bash
    curl https://ollama.ai/install.sh | sh
    ollama run deepseek-coder:6.7b-instruct-q4_0

    

## Usage

1. **Database Setup:**
    * Ensure you have a MySQL database set up with the appropriate schema for your Apartment Management System. The details provided in the script about tables and columns are crucial for query generation.
2. **Running the Script:**
    * Open a terminal and navigate to the directory containing the script (`open_source_llms.py`).
    * Run the script using the following command:
       ```bash
        python open_source_llms.py
        
3. **Interactive Query Generation:**
    * Follow the prompts displayed on the terminal. The script will ask you natural language questions related to your desired query.
    * Based on your responses, the script will use LangChain to generate an SQL query and then execute it on your MySQL database.
    * The results of the query will be displayed in the terminal.

## Code Structure

The script utilizes several classes to achieve its functionality:

* **Mixtral Class:** Responsible for initializing the MixtralAI model, which uses Deep Learning to understand and respond to complex language queries.
* **DeepSeek Class:** Handles interactions with the DeepSeek model, another AI-powered language understanding tool.
* **ChatQuery Class:** Interacts with LangChain to generate and extract SQL queries based on user input.
* **Database Class:** Establishes connections to the MySQL database and executes generated queries.
* **RagSQL Class:** Combines all aforementioned functionalities, allowing you to interact with your database using natural language through LangChain and AI models.

The `main()` function demonstrates how these classes work together to enable interactive SQL query generation.

## Important Notes

- The script suppresses `LangChainDeprecationWarning` for a smoother experience.
- This script serves as a template and might require adjustments based on your specific database schema and query needs.
- Ensure you have the necessary permissions to access and modify your MySQL database.
- While the script leverages AI models for language understanding, it's still under development and might not always generate perfect SQL queries. Feel free to refine the generated queries as needed.





