from fastapi import FastAPI,HTTPException
from pydantic import BaseModel, Field
from backend import run_workflow 
import uvicorn 

app = FastAPI(title="Self_Corective RAG Workflow API", version="1.0")

class WorkflowRequest(BaseModel):
    topic: str = Field(min_length=2,max_length=100, description="The topic for which the answer needs to be generated.")

@app.post("/workflow")
async def run_workflow_endpoint(request: WorkflowRequest):
    try:
        result = run_workflow(request.topic)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)