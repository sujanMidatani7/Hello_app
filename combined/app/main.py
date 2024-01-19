import asyncio
import psycopg2
from psycopg2 import sql
import aiopg
import psycopg2.extras
from fastapi import FastAPI
import openai
from openai import OpenAI
import os
import weaviate
import numpy as np
# import weaviate.classes as wvc
import json
from openai import AzureOpenAI
# gets the API Key from environment variable AZURE_OPENAI_API_KEY
client2 = AzureOpenAI(
    # https://learn.microsoft.com/en-us/azure/ai-services/openai/reference#rest-api-versioning
    api_version="2023-07-01-preview",
    # https://learn.microsoft.com/en-us/azure/cognitive-services/openai/how-to/create-resource?pivots=web-portal#create-a-resource
    azure_endpoint="https://virtualinterview.openai.azure.com",
)
dsn = "dbname=testDB user=postgres password=Postgres05 host=172.18.0.2"
client = weaviate.Client(
    url="http://localhost:5435/"
)
# Define a schema with a class representing your data
schema = {
            "class": "Product",
            "description": "Supplement products",
            "properties": [
                {
                    "dataType": ["text"],
                    "description": "Text",
                    "name": "name",
                },
                {
                    "dataType": ["number"],
                    "description": "Embeedding of the particular text",
                    "name": "embedding",
                },
            ]
        }
async def get_embedding(text, model="text-embedding-ada-002"):
   text = text.replace("\n", " ")
   print(client2.embeddings.create(input = [text], model=model).data[0].embedding)
   return (client2.embeddings.create(input = [text], model=model).data[0].embedding)
async def insert_data_to_weaviate(name,vector):
    class_obj = {"class": "DocumentSearch", "vectorizer": "none"}
    # client1.schema.create_schema(schema)
    if not client.schema.exists("DocumentSearch"):
        client.schema.create_class(class_obj)
        print(f"Product class was created because it didn't exist.")
    else:
        # client.schema.delete_class("DocumentSearch")
        print(f"Product class already exists")
        # client.schema.create_class(class_obj)
    documents = [name]
    client.batch.configure(batch_size=len(documents))
    with client.batch as batch:
        for i, doc in enumerate(documents):
            properties = {"source_text": doc}
            batch.add_data_object(properties, "DocumentSearch", vector=vector)
async def review_data(vector_array):
    result = client.query.get("DocumentSearch", ["source_text"]).with_near_vector({
        "vector": vector_array,
        "certainty": 0.7
    }).with_limit(2).with_additional(['certainty', 'distance']).do()
    print(json.dumps(result,indent=4))
def create_table_if_not_exists():
    with psycopg2.connect(dsn) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Check if the table exists
            cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'Users')")
            table_exists = cur.fetchone()[0]
            print('Table Users exists?', table_exists)
            if not table_exists:
                # Create the table if it doesn't exist
                cur.execute("CREATE TABLE Users(Id SERIAL PRIMARY KEY, Name VARCHAR(20))")
async def insert_name_to_database(name):
    async with aiopg.create_pool(dsn) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                try:
                    # create_table_if_not_exists()  # Ensure the table exists
                    # Check if the name already exists in the Users table
                    await cur.execute("SELECT Name FROM Users WHERE Name = %s", (name,))
                    existing_name = await cur.fetchone()
                    if not existing_name:
                        # If the name doesn't exist, insert it
                        await cur.execute("INSERT INTO Users (Name) VALUES (%s)", (name,))
                        print("Successfully inserted:", name)
                    else:
                        print("Name already exists:", name)
                except Exception as e:
                    print(f"Error inserting data: {e}")
async def query_names():
    async with aiopg.create_pool(dsn) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                try:
                    # create_table_if_not_exists()  # Ensure the table exists
                    await cur.execute("SELECT * FROM Users")
                    rows = await cur.fetchall()
                    # Print all the values
                    for row in rows:
                        print(row)
                    print("Successful")
                except Exception as e:
                    print(f"Error querying data: {e}")
def generate_openai_embedding(name):
    # Call the OpenAI embeddings API
    response = openai.Embed.create(
        model="text-davinci-002",
        objects=[{"text": name}],
    )
    # Extract and return the embedding
    print(response['choices'][0]['embedding'])
@app.get("/hello/{name}")
async def read_item(name: str):
    create_table_if_not_exists
    await (insert_name_to_database(name))  # Start database operation asynchronously
    embedding_result = np.array(await get_embedding(name))
    # print(embedding_result)
    await query_names()
    await insert_data_to_weaviate(name, embedding_result)
    await review_data(embedding_result)
    return {"message": f"Hello, {name}! Successfully updated."}
