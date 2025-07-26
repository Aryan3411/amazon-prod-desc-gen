import streamlit as st
from PIL import Image
import os
import io
import json
import re
import requests
from dotenv import load_dotenv
from openai import OpenAI

# --- Configuration and Setup ---
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
IDEOGRAM_API_KEY = os.getenv("IDEOGRAM_API_KEY")
st.set_page_config(page_title="Product Content Generator", layout="centered")

# --- Helper Functions ---

def generate_amazon_image_suite_prompts(generated_content, client):
    """
    Generates a suite of 5 targeted, professionally-styled Amazon A+ Content prompts using OpenAI.
    """
    # Consolidate product info for the AI prompt
    product_context = f"""
- Product Title: {generated_content.get('product_title', 'N/A')}
- Key Benefits: {generated_content.get('product_benefits', 'N/A').replace('Product Benefits', '').strip()}
- Key Ingredients & Features: {generated_content.get('product_features', 'N/A').replace('Product Features', '').strip()}
- How to Use: {generated_content.get('how_to_use', 'N/A').replace('How to Use', '').strip()}
- Description Keywords: flake removal, dandruff relief, biotin, salicylic acid, rosemary, hydration
    """

    # System prompt to let OpenAI generate the entire prompts
    system_prompt = f"""
You are an expert Art Director and professional product photographer with 15+ years of experience in Amazon A+ Content creation. Your task is to write 5 distinct, highly-detailed, and evocative prompts for an AI image generator. These prompts must create stunning, clean, high-end BACKGROUNDS for a product shot (e.g., a conditioner tube), where the actual product will be overlaid later using a 'replace-background' feature. Use professional photography and design language, specifying lighting, materials, composition, and camera settings (e.g., depth of field, lens type). Include precise overlay text instructions (position and content) to match Amazon A+ layout standards. The overlay text should directly present product information (e.g., benefits, ingredients) without prefixes like 'Powered by' or 'Backed by', using concise, clear phrasing based on the provided product context.

**Product Information:**
{product_context}

**Your Instructions:**
- Generate exactly 5 unique prompts, each representing a different visual concept relevant to the product (e.g., lifestyle, ingredient focus, benefit highlight, scientific trust, before/after comparison).
- Each prompt must end with: "Commercial product photography background, 8K, photorealistic, shot on a 85mm f/1.4 lens with a shallow depth of field."
- Ensure the prompts are diverse in style and setting, leveraging the product keywords (flake removal, dandruff relief, biotin, salicylic acid, rosemary, hydration) to inspire creative backgrounds.
- Specify overlay text for each prompt, placing it at an appropriate position (e.g., top center, bottom left) with content derived from the product benefits, ingredients, or features.

**Format:**
Return a single, valid JSON object with one key, "prompts", containing a list of exactly 5 strings corresponding to the 5 image types.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": system_prompt}],
            temperature=0.8,
            response_format={"type": "json_object"}
        )
        response_content = response.choices[0].message.content
        prompt_data = json.loads(response_content)
        
        if "prompts" in prompt_data and isinstance(prompt_data["prompts"], list):
            return prompt_data["prompts"]
        else:
            st.error("AI returned an unexpected format for prompts.")
            st.json(prompt_data)
            return []

    except Exception as e:
        st.error(f"Error generating AI image prompts: {e}")
        return []

def generate_images(prompts, reference_image_path):
    """Generates images using the Ideogram API."""
    if not IDEOGRAM_API_KEY:
        st.error("IDEOGRAM_API_KEY not found in environment variables.")
        return

    st.subheader("🖼️ Generated Images")
    
    cols = st.columns(2)
    col_index = 0

    for i, prompt in enumerate(prompts, 1):
        with open(reference_image_path, 'rb') as ref_image_file:
            with st.spinner(f"Generating image {i}/{len(prompts)}..."):
                files = {'image': (os.path.basename(reference_image_path), ref_image_file, 'image/png')}
                data = {
                    "prompt": prompt, "style_type": "GENERAL", "rendering_speed": "TURBO",
                    "aspect_ratio": "1x1", "num_images": 1
                }
                headers = {"Api-Key": IDEOGRAM_API_KEY}
                try:
                    response = requests.post("https://api.ideogram.ai/v1/ideogram-v3/replace-background", headers=headers, data=data, files=files)
                    response.raise_for_status()
                    result_json = response.json()
                    if result_json.get('data'):
                        image_url = result_json['data'][0]['url']
                        with cols[col_index]:
                            st.image(image_url, caption=f"Concept {i}", use_container_width=True)
                            col_index = (col_index + 1) % 2
                    else:
                        st.error(f"Image {i}: API did not return image data. Response: {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"API Error on image {i}: {e}")
                    response_text = response.text if 'response' in locals() and hasattr(response, 'text') else 'No response text.'
                    st.error(f"Response Body: {response_text}")

# --- Streamlit UI and Main Logic ---
st.title("🛍️ Amazon A+ Content Generator")
st.markdown("Generate full product copy and a suite of strategic images from just a title and a reference photo.")

with st.form("generate_form"):
    product_input = st.text_area("Enter Product Title", height=100, placeholder="e.g., Bare Anatomy EXPERT Anti-Dandruff Conditioner with Rosemary")
    uploaded_file = st.file_uploader("Upload Reference Image (White Background)", type=["png", "jpg", "jpeg"])
    submitted = st.form_submit_button("✨ Generate Full Content Suite")

if submitted and product_input and uploaded_file:
    with st.spinner("Generating... This is a multi-step AI process and may take a few minutes."):
        try:
            # --- 1. TEXT CONTENT GENERATION ---
            text_prompt = f"""
You are an expert Amazon A+ content writer with a focus on beauty products. Generate a comprehensive product content package from the input: "{product_input}". The tone should be professional, trustworthy, and customer-centric, optimized for Amazon search with keywords like 'anti-dandruff', 'flake removal', 'biotin', 'rosemary', and 'hydrating conditioner'. Include specific sections for Amazon A+ layout.

**Output Format (JSON only):**
{{
  "product_title": "Styled title (150–200 characters) with brand emphasis and key benefits",
  "product_benefits": "Product Benefits\\n\\t• Benefit 1 with detail...\\n\\t• Benefit 2 with detail...",
  "product_features": "Product Features\\n\\t• Feature 1 with ingredient focus...\\n\\t• Feature 2 with technology highlight...",
  "how_to_use": "Direction of Use\\n\\t1. Step 1 with clear instruction...\\n\\t2. Step 2 with detail...",
  "why_youll_love_it": "Why You'll Love It:\\n\\t• Unique selling point 1...\\n\\t• Unique selling point 2...",
  "real_results": "Real Results, Real Relief:\\n\\t• Before condition...\\n\\t• After improvement...",
  "key_ingredients": "Our Key Ingredients:\\n\\t• Ingredient 1: Benefit...\\n\\t• Ingredient 2: Benefit...",
  "product_description": "Product Description\\n\\nFull marketing-friendly description (3–4 paragraphs) with SEO keywords and customer pain points addressed."
}}
"""
            text_response = client.chat.completions.create(
                model="gpt-4-turbo", messages=[{"role": "user", "content": text_prompt}], temperature=0.7,
                response_format={"type": "json_object"}
            )
            text_content = text_response.choices[0].message.content.strip()
            result = json.loads(text_content)

            # --- 2. IMAGE CONTENT GENERATION ---
            reference_img = Image.open(uploaded_file)
            reference_image_path = "reference_image.png"
            reference_img.save(reference_image_path, "PNG")

            st.subheader("Uploaded Reference")
            st.image(reference_img, caption="Reference Product Image", width=350)
            st.markdown("---")
            
            prompts_to_generate = generate_amazon_image_suite_prompts(result, client)

            if prompts_to_generate:
                generate_images(prompts_to_generate, reference_image_path)
            else:
                st.warning("Could not generate image prompts. Skipping image generation.")

            st.markdown("---")

            # --- 3. DISPLAY TEXT CONTENT ---
            st.subheader("✍️ Generated Product Copy")
            with st.expander("Click to view/copy the generated text content"):
                st.markdown("#### Product Title")
                st.code(result['product_title'], language=None)
                st.markdown("#### Product Benefits")
                st.text(result['product_benefits'].replace('Product Benefits\n', ''))
                st.markdown("#### Product Features")
                st.text(result['product_features'].replace('Product Features\n', ''))
                st.markdown("#### Direction of Use")
                st.text(result['how_to_use'].replace('Direction of Use\n', ''))
                st.markdown("#### Why You'll Love It")
                st.text(result['why_youll_love_it'].replace('Why You\'ll Love It:\n', ''))
                st.markdown("#### Real Results, Real Relief")
                st.text(result['real_results'].replace('Real Results, Real Relief:\n', ''))
                st.markdown("#### Our Key Ingredients")
                st.text(result['key_ingredients'].replace('Our Key Ingredients:\n', ''))
                st.markdown("#### Product Description")
                st.markdown(result['product_description'].replace("Product Description\n\n", ""))

        except json.JSONDecodeError as e:
            st.error(f"JSON Parsing Error: {str(e)}")
            st.error("Check the raw response below for details.")
            with st.expander("Debug: Raw API Response"):
                st.text(text_content if 'text_content' in locals() else "No response to display")
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")

elif submitted:
    st.error("Please provide both a product title and a reference image.")