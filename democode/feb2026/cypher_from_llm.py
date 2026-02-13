import os
from neo4j import GraphDatabase
from langchain_community.chat_models import AzureChatOpenAI
from dotenv import load_dotenv

load_dotenv()

#####
# This app demonstrates: 
# 1) Connect to a neo4j instance
# 2) create a knowledge graph (KG) in neo4j programmatically using cypher queries
# 3) Use Azure Open AI to create cypher queries based on our schema and requirement
# 4) execute those queries in neo4j and get the data/results
# 5) Pass the results to LLM for natural language response to our question
#####

# Retrieve Azure OpenAI credentials from environment variables.
azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
azure_api_key = os.environ.get("AZURE_OPENAI_API_KEY")
azure_api_version = os.environ.get("AZURE_OPENAI_API_VERSION")  
azure_deployment_name = os.environ.get("AZURE_OPENAI_MODEL_DEPLOYMENT_NAME")

# 1. Connect to your Neo4j instance.
neo4j_uri = os.environ.get("NEO4J_URI")  # e.g., "bolt://localhost:7687"
neo4j_user = os.environ.get("NEO4J_USER")  # e.g., "neo4j"
neo4j_password = os.environ.get("NEO4J_PASSWORD")  # e.g., "your_password"
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

def run_cypher_query(query: str):
    """Execute a Cypher query and return the results."""
    with driver.session() as session:
        result = session.run(query)
        return [record.data() for record in result]

def clear_graph():
    """Delete all nodes and relationships to avoid duplication errors."""
    clear_query = "MATCH (n) DETACH DELETE n"
    run_cypher_query(clear_query)

def create_sample_data():
    """Create sample nodes and relationships for a healthcare knowledge graph."""
    create_query = """
    CREATE (p:Patient {name: "John Doe", age: 45, gender: "Male"})
    CREATE (d:Doctor {name: "Dr. Smith", specialty: "Cardiology"})
    CREATE (c:Condition {name: "Hypertension", severity: "High"})
    CREATE (m:Medication {name: "Lisinopril", dosage: "10mg", frequency:"Once daily"})
    
    CREATE (p)-[:DIAGNOSED_WITH {diagnosis_date: "2022-05-01"}]->(c)
    CREATE (d)-[:TREATS {since: "2022-06-01"}]->(c)
    CREATE (m)-[:TREATMENT_FOR]->(c)
    """
    run_cypher_query(create_query)

# 2. Initialize the Azure Chat OpenAI LLM using LangChain.
llm = AzureChatOpenAI(
    azure_endpoint=azure_endpoint,      # e.g., "https://ey-openai.openai.azure.com/"
    openai_api_version=azure_api_version,
    deployment_name=azure_deployment_name,
    openai_api_key=azure_api_key,
    temperature=0
)

def generate_cypher_from_question(question: str) -> str:
    """
    Convert a natural language question into a Cypher query for a healthcare knowledge graph.
    Assumes the graph includes:
      - Patient nodes (e.g., 'John Doe')
      - Doctor nodes (e.g., 'Dr. Smith') with property 'name'
      - Condition nodes (e.g., 'Hypertension')
      - Medication nodes (e.g., 'Lisinopril')
    With relationships:
      - Patients DIAGNOSED_WITH Conditions
      - Doctors TREATS Conditions
      - Medications TREATMENT_FOR Conditions
    """
    prompt = (
        "Convert the following natural language question into a Cypher query "
        "to query a healthcare knowledge graph with nodes for Patient, Doctor, Condition, and Medication. "
        "Note: Doctor nodes have a 'name' property (not 'fullName').\n"
        "Relationships: Patients DIAGNOSED_WITH Conditions, Doctors TREATS Conditions, Medications TREATMENT_FOR Conditions.\n\n"
        f"Question: {question}\n\n"
        "Cypher Query:"
    )
    messages = [{"role": "user", "content": prompt}]
    response = llm.invoke(input=messages)
    print("Raw LLM Response:", response)  # Debug print to view the raw LLM response
    try:
        return response.content.strip()
    except AttributeError:
        return response.strip()

# 3. Main execution: Clear graph, create sample data, then generate and execute the query.
if __name__ == "__main__":
    try:
        clear_graph()
        create_sample_data()
        
        question = "Who treats Hypertension?"
        print(f"Natural Language Question: {question}\n")
        
        cypher_query = generate_cypher_from_question(question)
        print("Generated Cypher Query:")
        print(cypher_query, "\n")
        
        results = run_cypher_query(cypher_query)
        print("Query Results:")
        print(results)
    except Exception as e:
        print("An error occurred:", e)