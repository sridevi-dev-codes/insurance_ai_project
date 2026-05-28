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
    file: UploadFile = File(...)
): 
 try:
    file_path = os.path.join(DATA_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(ingest_pdf, file_path)

    return {
        "message": "Upload received. Ingestion started in background."
    }
 except Exception as e:
         return {"error": str(e)}

@app.post("/query")
async def query_claim(data: ClaimRequest):
    try:
        claim_context = f"""
Insurance Claim Assessment Request

Question:
{data.question}

Claim Details:
Claim ID: {data.claim_details.claim_id}
Policy ID: {data.claim_details.policy_id}
Claim Type: {data.claim_details.claim_type}
Incident Type: {data.claim_details.incident_type}
Incident Date: {data.claim_details.incident_date}
Reported Delay Days: {data.claim_details.reported_delay_days}
Estimated Damage: ₹{data.claim_details.estimated_damage}
IDV: ₹{data.claim_details.idv}
Deductible: ₹{data.claim_details.deductible}
Previous Claims in 90 Days: {data.claim_details.previous_claims_90_days}
Documents Submitted: {", ".join(data.claim_details.documents_submitted)}
Policy Status: {data.claim_details.policy_status}
"""

        # Call LLM agent
        response = manager_agent.invoke({
            "messages": [{"role": "user", "content": claim_context}]
        })

        raw = response["messages"][-1].content
        if isinstance(raw, list):
            raw = raw[0]
        if isinstance(raw, dict):
            raw = raw.get("text", str(raw))

        # Clean markdown / prefix
        raw = raw.replace("```json", "").replace("```", "")
        raw = re.sub(r"^\s*json\s*", "", raw)

        # --- Handle irrelevant response ---
        irrelevant_phrases = [
            "I can only assist with insurance",
            "not related to insurance",
            "out of scope"
        ]
        if any(phrase.lower() in raw.lower() for phrase in irrelevant_phrases):
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

        # --- Validate against Pydantic model ---
        try:
            validated_output = ClaimAssessmentResponse(
                claim_id=data.claim_details.claim_id,
                **output_dict
            )
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

        # ✅ Everything valid, return dict
        return validated_output.dict()

    except HTTPException as http_error:
        raise http_error

    except ValueError as ve:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "We couldn’t process the claim response. Please try again.",
                "error": str(ve)
            }
        )

    except Exception:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Something went wrong while processing your claim. Please try again in a few moments."
            }
        )


# import json
# import re
# from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
# from fastapi.responses import JSONResponse
# from app.schemas.claim_schema import ClaimRequest, ClaimAssessmentResponse
# from app.agents.manager_agent import manager_agent
# import os
# import shutil
# from app.ingestion.ingestion import ingest_pdf

# app = FastAPI()

# DATA_DIR = r".\Instructions_pdf"
# os.makedirs(DATA_DIR, exist_ok=True)
# @app.post("/upload-pdf")
# async def upload_pdf(
#     background_tasks: BackgroundTasks,
#     file: UploadFile = File(...)
# ): 
#  try:
#     file_path = os.path.join(DATA_DIR, file.filename)

#     with open(file_path, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)

#     background_tasks.add_task(ingest_pdf, file_path)

#     return {
#         "message": "Upload received. Ingestion started in background."
#     }
#  except Exception as e:
#          return {"error": str(e)}

# @app.post("/query")
# async def query_claim(data: ClaimRequest):

#     try:
#         claim_context = f"""
# Insurance Claim Assessment Request

# Question:
# {data.question}

# Claim Details:
# Claim ID: {data.claim_details.claim_id}
# Policy ID: {data.claim_details.policy_id}
# Claim Type: {data.claim_details.claim_type}
# Incident Type: {data.claim_details.incident_type}
# Incident Date: {data.claim_details.incident_date}
# Reported Delay Days: {data.claim_details.reported_delay_days}
# Estimated Damage: ₹{data.claim_details.estimated_damage}
# IDV: ₹{data.claim_details.idv}
# Deductible: ₹{data.claim_details.deductible}
# Previous Claims in 90 Days: {data.claim_details.previous_claims_90_days}
# Documents Submitted: {", ".join(data.claim_details.documents_submitted)}
# Policy Status: {data.claim_details.policy_status}
# """
#         # -------------------------
#         response = manager_agent.invoke({
#             "messages": [
#                 {
#                     "role": "user",
#                     "content": claim_context
#                 }
#             ]
#         })
#         raw = response["messages"][-1].content
#         if isinstance(raw, list):
#             raw = raw[0]
#         if isinstance(raw, dict):
#             raw = raw.get("text", str(raw))
#         # remove markdown + prefix noise
#         raw = raw.replace("```json", "").replace("```", "")
#         raw = re.sub(r"^\s*json\s*", "", raw)
#         # extract JSON block safely
#         match = re.search(r"\{.*\}", raw, re.DOTALL)
#         if not match:
#             raise ValueError(f"Invalid JSON from LLM: {raw}")
#         try:
#             output = json.loads(match.group())
#         except json.JSONDecodeError:
#             raise ValueError(f"JSON parsing failed: {raw}")
#         if not isinstance(output, dict):
#             raise ValueError(f"Unexpected output type: {type(output)}")
#         return output
#         # return ClaimAssessmentResponse(
#         #     claim_id=data.claim_details.claim_id,
#         #     eligibility=output.get("eligibility", "Pending"),
#         #     fraud_risk=output.get("fraud_risk", "Unknown"),
#         #     recommended_payout=output.get("recommended_payout", 0),
#         #     reasoning=output.get("reasoning", []),
#         #     citations=output.get("citations", []),
#         #     retrieved_documents=output.get("retrieved_documents", [])
#         # )

# except HTTPException as http_error:
#     raise http_error

# except ValueError as e:
#     return JSONResponse(
#         status_code=400,
#         content={
#             "status": "error",
#             "message": "We couldn’t process the claim response. Please try again.",
#             "error": str(e)
#         }
#     )

# except Exception:
#     return JSONResponse(
#         status_code=500,
#         content={
#             "status": "error",
#             "message": "Something went wrong while processing your claim. Please try again in a few moments."
#         }
#     )
