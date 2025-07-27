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
    Generates a suite of 6 targeted, professionally-styled Amazon A+ Content prompts using OpenAI.
    """
    # Consolidate product info for the AI prompt
    product_context = f"""
    - Product Title: {generated_content.get('product_title', 'N/A')}
    - Key Benefits: {generated_content.get('product_benefits', 'N/A').replace('Product Benefits', '').strip()}
    - Key Ingredients & Features: {generated_content.get('product_features', 'N/A').replace('Product Features', '').strip()}
    - How to Use: {generated_content.get('how_to_use', 'N/A').replace('How to Use', '').strip()}
    """

    # System prompt to let OpenAI generate the entire prompts for Amazon
    system_prompt = """
You are a creative director AI specializing in generating prompts for text-to-image models for Amazon A+ Content. Your task is to create a suite of 6 distinct, detailed image prompts based on the product context provided.

**Primary Objective:** Analyze the provided product context to identify its core brand persona ("Bare Anatomy - Natural," "Bare Anatomy - Clinical," or "Chemist at Play - Playful"). Then, generate 6 prompts for the templates below, ensuring the style aligns with the identified persona.

**⚠️ Critical Rule for Product Object Handling:**
**You MUST strictly command the image model to use the product from the provided reference image as an unchangeable asset. The model is forbidden from generating an imaginary product or altering the shape, label, or appearance of the provided product object. The only task is to place this exact product object attractively within a newly generated scene.**

**Brand Personas for Identification:**

* **Persona A: Bare Anatomy - Natural/Soothing:** (Keywords: Elegant, calm, botanical, trusted. Colors: sage green, muted lavender, light beige).
* **Persona B: Bare Anatomy - Clinical/Scientific:** (Keywords: Scientific, effective, serious. Colors: monochromatic black, white, grey).
* **Persona C: Chemist at Play - Playful/Vibrant:** (Keywords: Fun, modern, energetic, bold. Colors: coral red, bright pink, orange, turquoise blue).

**Required Output Format (JSON only):**
{ "prompts": [ "Prompt 1...", "Prompt 2...", "Prompt 3...", "Prompt 4...", "Prompt 5...", "Prompt 6..." ] }

**Image Template Instructions (generate one prompt for each):**

1.  **Image Prompt 1: The "Simple Product Shot"**: Places the uploaded product photo on a clean, single-color studio background that complements the persona. No text.
2.  **Image Prompt 2: The "Key Ingredients Showcase"**: Uses the uploaded product photo as the hero object and arranges visuals of 3-4 key ingredients around it (e.g., in a grid or as callouts).
3.  **Image Prompt 3: The "Product Benefits Feature"**: Places the uploaded product photo on one side. On the other side, create a clean layout listing 3-4 key benefits with text and custom icons.
4.  **Image Prompt 4: The "How to Use" Guide**: An instructional graphic, likely with lifestyle photos of the product in use, showing 2-3 steps.
5.  **Image Prompt 5: The "Brand Promise / Free-From" Graphic**: Places the uploaded product photo and its packaging in a clean setting, with a heading and a grid of 6 icons for claims like "Sulphate-Free."
6.  **Image Prompt 6: The "Proof of Efficacy"**: A side-by-side "Before & After" image or a data-focused graphic. Does not need to include the product shot.
"""
    final_user_prompt = f"{system_prompt}\n\nHere is the product context to use:\n{product_context}"
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": final_user_prompt}],
            temperature=0.8,
            response_format={"type": "json_object"}
        )
        response_content = response.choices[0].message.content
        prompt_data = json.loads(response_content)
        if "prompts" in prompt_data and isinstance(prompt_data["prompts"], list):
            return prompt_data["prompts"]
        else:
            st.error("AI returned an unexpected format for Amazon prompts.")
            return []
    except Exception as e:
        st.error(f"Error generating Amazon AI image prompts: {e}")
        return []

def generate_meta_ads_prompts(generated_content, client):
    """
    Generates a suite of 6 targeted, professionally-styled Meta Ads prompts using OpenAI.
    """
    product_context = f"""
    - Product Title: {generated_content.get('product_title', 'N/A')}
    - Key Benefits: {generated_content.get('product_benefits', 'N/A').replace('Product Benefits', '').strip()}
    - Key Ingredients & Features: {generated_content.get('product_features', 'N/A').replace('Product Features', '').strip()}
    - How to Use: {generated_content.get('how_to_use', 'N/A').replace('How to Use', '').strip()}
    - Customer Review: {generated_content.get('real_results', 'N/A').strip()}
    """

    system_prompt = """
You are a world-class social media creative director AI. Your task is to generate 6 high-impact, scroll-stopping image prompts for Meta Ads (Facebook/Instagram), based on the provided product context.

**Primary Objective:** Identify the brand's Meta Ads persona ("Bare Anatomy - Clinical" or "Chemist at Play - Vibrant/Educational"). Then, generate 6 prompts for the ad angles below, using dynamic layouts, bold typography, and attention-grabbing visuals suitable for a social media feed.

**⚠️ Critical Rule for Product Object Handling:**
**You MUST strictly command the image model to use the product from the provided reference image as an unchangeable asset. The model is forbidden from generating an imaginary product. The only task is to place this exact product object attractively within a newly generated scene.**

**Meta Ad Personas for Identification:**
* **Bare Anatomy - Clinical/Scientific:** (Keywords: Premium, minimalist, authoritative, data-driven. Colors: Monochromatic, deep browns, clean whites).
* **Chemist at Play - Vibrant/Educational:** (Keywords: Bold, direct, energetic, problem-solving. Colors: High-contrast palettes like purple/yellow, orange/white, or pink/red).

**Required Output Format (JSON only):**
{ "prompts": [ "Prompt 1...", "Prompt 2...", "Prompt 3...", "Prompt 4...", "Prompt 5...", "Prompt 6..." ] }

**Meta Ad Template Instructions (generate one prompt for each angle):**

1.  **Image Prompt 1: The "Big Hook" Ad**: A bold, text-focused ad. Places the uploaded product photo against a vibrant background. The main focus is a huge, attention-grabbing claim like "1 SOLD EVERY 30 SECONDS" or "INDIA'S 1st..." in massive, bold font.
2.  **Image Prompt 2: The "Social Proof (Statistic)" Ad**: Focuses on a single, powerful statistic. Places the product on a clean pedestal or surface. The largest element on the screen should be a number, e.g., "92%", with smaller text next to it saying "users agreed..."
3.  **Image Prompt 3: The "Benefit/Lifestyle" Ad**: A visually appealing lifestyle image. It could feature a happy model using the product, or the product itself styled with its core ingredients (like flowers or lab glassware). The prompt should describe a feeling, like "Freshness that lasts."
4.  **Image Prompt 4: The "Reason Why (Ingredient)" Ad**: Explains how the product works. Places the uploaded product photo on one side, and on the other, highlights a key ingredient and its function in clear, concise text.
5.  **Image Prompt 5: The "Testimonial" Ad**: Creates a social proof ad featuring a customer review. Places the product attractively. The prompt should describe creating a graphic that looks like a real customer testimonial, with a 5-star rating, a customer name, and a quote from the product context.
6.  **Image Prompt 6: The "Proof (Before & After)" Ad**: A clear problem/solution visual. This prompt should describe creating a side-by-side Before & After comparison, using either clinical photos or user-generated style images.
"""
    final_user_prompt = f"{system_prompt}\n\nHere is the product context to use:\n{product_context}"
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": final_user_prompt}],
            temperature=0.8,
            response_format={"type": "json_object"}
        )
        response_content = response.choices[0].message.content
        prompt_data = json.loads(response_content)
        if "prompts" in prompt_data and isinstance(prompt_data["prompts"], list):
            return prompt_data["prompts"]
        else:
            st.error("AI returned an unexpected format for Meta Ads prompts.")
            return []
    except Exception as e:
        st.error(f"Error generating Meta Ads AI image prompts: {e}")
        return []

def generate_images(prompts, reference_image_path):
    """Generates images using the Ideogram API."""
    if not IDEOGRAM_API_KEY:
        st.error("IDEOGRAM_API_KEY not found in environment variables.")
        return

    st.write("Debug: Generated Prompts:", prompts)
    
    num_columns = 3 if len(prompts) >= 6 else 2
    cols = st.columns(num_columns)
    col_index = 0

    for i, prompt in enumerate(prompts, 1):
        with open(reference_image_path, 'rb') as ref_image_file:
            with st.spinner(f"Generating image {i}/{len(prompts)}..."):
                files = {'image': (os.path.basename(reference_image_path), ref_image_file, 'image/png')}
                data = {
                    "prompt": prompt, "style_type": "GENERAL", "rendering_speed": "QUALITY",
                    "aspect_ratio": "1x1", "num_images": 1
                }
                headers = {"Api-Key": IDEOGRAM_API_KEY}
                try:
                    response = requests.post("https://api.ideogram.ai/v1/ideogram-v3/replace-background", headers=headers, data=data, files=files)
                    response.raise_for_status()
                    result_json = response.json()
                    if result_json.get('data'):
                        image_url = result_json['data'][0]['url']
                        with cols[col_index % num_columns]:
                            st.image(image_url, caption=f"Concept {i}", use_container_width=True)
                            col_index += 1
                    else:
                        st.error(f"Image {i}: API did not return image data. Response: {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"API Error on image {i}: {e}")
                    response_text = response.text if 'response' in locals() and hasattr(response, 'text') else 'No response text.'
                    st.error(f"Response Body: {response_text}")

# --- Streamlit UI and Main Logic ---
st.title("🛍️ Product Content & Ad Generator")
st.markdown("Generate full product copy and a suite of strategic images for Amazon A+ and Meta Ads.")

with st.form("generate_form"):
    product_input = st.text_area("Enter Product Title", height=100, placeholder="e.g., Bare Anatomy EXPERT Anti-Dandruff Conditioner with Rosemary")
    uploaded_file = st.file_uploader("Upload Reference Image (White Background)", type=["png", "jpg", "jpeg"])
    
    generation_choice = st.selectbox(
        "Select Content Type",
        ("Amazon A+ Content", "Meta Ads", "Both")
    )

    submitted = st.form_submit_button("✨ Generate Full Content Suite")

if submitted and product_input and uploaded_file:
    with st.spinner("Generating... This is a multi-step AI process and may take a few minutes."):
        try:
            # --- 1. TEXT CONTENT GENERATION (Done once for all flows) ---
            # UPDATED: The JSON structure in the prompt now includes all the fields you requested.
            text_prompt = f"""
You are an expert Amazon A+ content writer with a focus on beauty products. Generate a comprehensive product content package from the input: "{product_input}". The tone should be professional, trustworthy, and customer-centric, optimized for Amazon search. Include specific sections for Amazon A+ layout.

**Output Format (JSON only):**
{{
  "product_title": "Styled title (150–200 characters) with brand emphasis and key benefits",
  "product_benefits": "Product Benefits\\n\\t• A list of at least 4-5 key benefits, each with a detailed explanation...",
  "product_features": "Product Features\\n\\t• A list of at least 4-5 product features, focusing on ingredients and technology...",
  "how_to_use": "Direction of Use\\n\\t1. A numbered list of at least 4-5 clear steps for application...",
  "real_results": "Real Results, Real Relief:\\n\\t• Before condition...\\n\\t• After improvement...",
  "product_description": "Product Description\\n\\nFull marketing-friendly description (3–4 paragraphs) with SEO keywords and customer pain points addressed."
}}
"""
            text_response = client.chat.completions.create(
                model="gpt-4-turbo", messages=[{"role": "user", "content": text_prompt}], temperature=0.7,
                response_format={"type": "json_object"}
            )
            text_content = text_response.choices[0].message.content.strip()
            result = json.loads(text_content)

            # --- Save reference image ---
            reference_img = Image.open(uploaded_file)
            reference_image_path = "reference_image.png"
            reference_img.save(reference_image_path, "PNG")

            st.subheader("Uploaded Reference")
            st.image(reference_img, caption="Reference Product Image", width=350)
            
            # --- 2. CONDITIONAL IMAGE GENERATION ---

            if generation_choice in ["Amazon A+ Content", "Both"]:
                st.header("🚀 Amazon A+ Content Images")
                prompts_to_generate = generate_amazon_image_suite_prompts(result, client)
                if prompts_to_generate:
                    generate_images(prompts_to_generate, reference_image_path)
                else:
                    st.warning("Could not generate Amazon A+ prompts.")

            if generation_choice in ["Meta Ads", "Both"]:
                st.header("📱 Meta Ads Images")
                prompts_to_generate = generate_meta_ads_prompts(result, client)
                if prompts_to_generate:
                    generate_images(prompts_to_generate, reference_image_path)
                else:
                    st.warning("Could not generate Meta Ads prompts.")
            
            st.markdown("---")

            # --- 3. DISPLAY TEXT CONTENT ---
            st.subheader("✍️ Generated Product Copy")
            with st.expander("Click to view/copy the generated text content"):
                for key, value in result.items():
                    st.markdown(f"#### {key.replace('_', ' ').title()}")
                    st.text(value)

        except json.JSONDecodeError as e:
            st.error(f"JSON Parsing Error: {str(e)}")
            with st.expander("Debug: Raw API Response"):
                st.text(text_content if 'text_content' in locals() else "No response to display")
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")

elif submitted:
    st.error("Please provide both a product title and a reference image.")