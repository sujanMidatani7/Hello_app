import asyncio
import aiopg
import psycopg2.extras
from fastapi import FastAPI

app = FastAPI()

dsn = "dbname=postgres user=postgres password=sujanm@9271 host=172.19.0.2"  # Use the correct IP address



def create_table_if_not_exists():
    with psycopg2.connect(dsn) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'Users')")
            table_exists = cur.fetchone()[0]
            print('Table Users exists?', table_exists)

            if not table_exists:
                cur.execute("CREATE TABLE Users(Id SERIAL PRIMARY KEY, Name VARCHAR(20))")


async def insert_name_to_database(name):
    async with aiopg.create_pool(dsn) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                try:
                    await cur.execute("SELECT Name FROM Users WHERE Name = %s", (name,))
                    existing_name = await cur.fetchone()

                    if not existing_name:
                        await cur.execute("INSERT INTO Users (Name) VALUES (%s)", (name,))
                        print("Successfully inserted:", name)
                    else:
                        print("Name already exists:", name)

                except Exception as e:
                    print(f"Error inserting data: {e}")


@app.on_event("startup")
async def startup_event():
    create_table_if_not_exists()


@app.get("/getRecords")
async def query_names():
    async with aiopg.create_pool(dsn) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                try:
                    await cur.execute("SELECT * FROM Users")
                    rows = await cur.fetchall()
                    return rows

                except Exception as e:
                    return f"Error querying data: {e}"


@app.get("/hello/{name}")
async def read_item(name: str):
    await insert_name_to_database(name)
    
    return {"message": f"Hello, {name}! Successfully updated."}
