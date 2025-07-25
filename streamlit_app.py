import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
import json
import re

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="Amazon Product Content Generator", layout="centered")

st.title("🛍️ Amazon Product Content Generator")
st.markdown("Generate full Amazon-style content from a one-line product title.")

with st.form("generate_form"):
    product_input = st.text_area("Enter Product Title", height=100, placeholder="e.g. Glow Essence Vitamin C Face Serum | Brightening & Hydrating | With Hyaluronic Acid & Niacinamide | ...")
    submitted = st.form_submit_button("Generate")

if submitted and product_input:
    with st.spinner("Generating product content..."):
        prompt = f"""
You are an expert Amazon content writer. Generate product content from the following one-line input:

Input:
"{product_input}"

Output format (as JSON with emojis and formatted strings):

{{
  "product_title": "Styled title (150–200 characters)",

  "product_benefits": "💎 Product Benefits\\n\\t• ...\\n\\t• ...",

  "product_features": "⚙️ Product Features\\n\\t• ...\\n\\t• ...",

  "how_to_use": "📋 How to Use\\n\\t1. ...\\n\\t2. ...",

  "product_description": "📝 Product Description\\n\\nFull marketing-friendly description (3–4 paragraphs)."
}}

Ensure each section is clear, well-written, and formatted exactly like above. Return only the JSON object, without any markdown code blocks or extra text.
"""

        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            response_content = response.choices[0].message.content.strip()

            # Clean response: remove markdown code blocks if present
            cleaned_content = re.sub(r'^\`\`\`json\n|\`\`\`$', '', response_content).strip()

            # Debug: Display raw response for troubleshooting
            with st.expander("Debug: Raw API Response"):
                st.text(response_content)

            # Parse JSON
            result = json.loads(cleaned_content)

            st.subheader("✅ Product Title")
            st.markdown(f"`{result['product_title']}`")

            st.markdown("---")
            st.markdown("### 💎 Product Benefits")
            benefits = result['product_benefits'].split("\n")[1:]  # Skip the header line
            for benefit in benefits:
                if benefit.strip():  # Only display non-empty lines
                    st.markdown(f"{benefit.strip()}")

            st.markdown("---")
            st.markdown("### ⚙️ Product Features")
            features = result['product_features'].split("\n")[1:]  # Skip the header line
            for feature in features:
                if feature.strip():  # Only display non-empty lines
                    st.markdown(f"{feature.strip()}")

            st.markdown("---")
            st.markdown("### 📋 How to Use")
            steps = result['how_to_use'].split("\n")[1:]  # Skip the header line
            for step in steps:
                if step.strip():  # Only display non-empty lines
                    st.markdown(f"{step.strip()}")

            st.markdown("---")
            st.markdown("### 📝 Product Description")
            st.markdown(result['product_description'])

        except json.JSONDecodeError as e:
            st.error(f"JSON Parsing Error: {str(e)}")
            st.error("The API response may not be valid JSON. Check the raw response below for details.")
        except Exception as e:
            st.error(f"Something went wrong: {str(e)}")