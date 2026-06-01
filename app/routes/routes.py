from pydantic import ValidationError
import json
import re
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from app.schemas.claim_schema import ClaimRequest, ClaimAssessmentResponse
from app.agents.manager_agent import manager_agent
import os
import shutil
from app.ingestion.ingestion import ingest_pdf

app = FastAPI()

DATA_DIR = r".\Instructions_pdf"
os.makedirs(DATA_DIR, exist_ok=True)

@app.post("/upload-pdf")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
): 
    try:
        file_path = os.path.join(DATA_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        background_tasks.add_task(ingest_pdf, file_path)

        return {"message": "Upload received. Ingestion started in background."}
    except Exception as e:
        return {"error": str(e)}

@app.post("/query")
async def query_claim(data: ClaimRequest):
    try:
        # --- Structured message: question and claim separately ---
        response = manager_agent.invoke({
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"QUESTION:\n{data.question}"
                                    },
                                    {
                                        "type": "text",
                                        "text": "CLAIM_DETAILS:"
                                    },
                                    {
                                        "type": "text",
                                        "text": json.dumps(
                                            data.claim_details.model_dump(),
                                            indent=2
                                        )
                                    }
                                ]
                            }
                        ]
                    })

        raw = response["messages"][-1].content
        # print("raw response",raw)
        if isinstance(raw, list):
            raw = raw[0]
        if isinstance(raw, dict):
            raw = raw.get("text", str(raw))

        raw = raw.replace("```json", "").replace("```", "")
        raw = re.sub(r"^\s*json\s*", "", raw)

        # Handle out-of-scope phrases
        irrelevant_phrases = [
            "I can only assist with insurance",
            "not related to insurance",
            "out of scope"
        ]
        if any(p.lower() in raw.lower() for p in irrelevant_phrases):
            return JSONResponse(
                status_code=200,
                content={
                    "message": "Sorry, I can only assist with insurance claim and policy related queries.",
                    "status": "out_of_scope"
                }
            )

        # Extract JSON safely
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise ValueError(f"Invalid JSON from LLM: {raw}")

        output_dict = json.loads(match.group())

        # Validate response
        validated_output = ClaimAssessmentResponse(
            claim_id=data.claim_details.claim_id,
            **output_dict
        )

        return validated_output.dict()

    except ValidationError as ve:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "Claim response is invalid or missing required fields.",
                "error": ve.errors(),
                "raw_response": raw
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        )
