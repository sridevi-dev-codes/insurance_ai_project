import streamlit as st
import requests
import json

st.title("AI Insurance Claims System")

# Input for question
question_input = st.text_area(
    "Enter your Question",
    placeholder="Enter your question here",
    height=100
)

# Input for claim details in JSON format
sample_claim = {}
claim_input = st.text_area(
    "Enter Claim Details (JSON format)",
    placeholder=json.dumps(sample_claim, indent=2),
    height=300
)

# Submit button
if st.button("Submit Claim", key="submit_claim"):
    try:
        # Parse the claim details JSON
        claim_details = json.loads(claim_input)

        # Construct the payload
        payload = {
            "question": question_input,
            "claim_details": claim_details
        }

        # Call FastAPI endpoint
        response = requests.post(
            "http://localhost:8000/query",
            json=payload
        )

        # Debugging info (optional)
        st.write("Status Code:", response.status_code)

        # Parse JSON response
        result = response.json()

        if response.ok:
            # Handle out-of-scope responses
            if result.get("status") == "out_of_scope":
                st.warning(result["message"])

            # Handle error responses from API
            elif result.get("status") == "error":
                st.error(result["message"])

            # Valid response
            else:
                st.json(result)

        else:
            st.error("API returned an error")

    except json.JSONDecodeError:
        st.error("Invalid JSON format in input box")

    except Exception as e:
        st.error(f"Error: {e}")

