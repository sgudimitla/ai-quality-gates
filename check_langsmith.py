from dotenv import load_dotenv
load_dotenv()

import os
from langsmith import Client

print("TRACING :", os.getenv("LANGSMITH_TRACING"))
print("PROJECT :", os.getenv("LANGSMITH_PROJECT"))
print("KEY SET :", bool(os.getenv("LANGSMITH_API_KEY")))
print("PROJECTS:", [p.name for p in Client().list_projects()])