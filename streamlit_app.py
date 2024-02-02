import streamlit as st
import requests
import zipfile
import io
from utils import icon
from streamlit_image_select import image_select
from PIL import Image
import base64
from typing import List


def base64_to_image(base64_string):
    return Image.open(io.BytesIO(base64.b64decode(base64_string)))


def call_niche_api(url, data) -> List[Image.Image]:
    try:
        response = requests.post(url, json=data)
        if response.status_code != 200:
            print(f"API call failed with status code {response.status_code}")
            return None
        response = response.json()

        return [base64_to_image(response)]
    except Exception as e:
        print(e)
        return None


# UI configurations
st.set_page_config(
    page_title="NicheImage Generator", page_icon=":bridge_at_night:", layout="wide"
)
icon.show_icon(":foggy:")
st.markdown("# :rainbow[Text-to-Image Studio by NicheImage]")

# API Tokens and endpoints from `.streamlit/secrets.toml` file
API_TOKEN = st.secrets["API_TOKEN"]
replicate_text = "NicheImage - Subnet 23 - Bittensor"
replicate_logo = "https://nichetensor.com/wp-content/uploads/2023/09/cropped-NicheTensorTextLogo-300x51.png"
replicate_link = "https://github.com/NicheTensor/NicheImage"
# Placeholders for images and gallery
generated_images_placeholder = st.empty()
gallery_placeholder = st.empty()


def configure_sidebar() -> None:
    """
    Setup and display the sidebar elements.

    This function configures the sidebar of the Streamlit application,
    including the form for user inputs and the resources section.
    """
    with st.sidebar:
        with st.form("my_form"):
            st.info("**Start here ↓**", icon="👋🏾")
            with st.expander(":rainbow[**Refine your output here**]"):
                # Advanced Settings (for the curious minds!)
                width = st.number_input("Width of output image", value=768)
                height = st.number_input("Height of output image", value=1024)
                num_inference_steps = st.slider(
                    "Number of denoising steps", value=30, min_value=1, max_value=50
                )
                guidance_scale = st.slider(
                    "Scale for classifier-free guidance",
                    value=7.5,
                    min_value=1.0,
                    max_value=20.0,
                    step=0.1,
                )
            model_name = st.selectbox(
                "Select Model", options=["RealisticVision", "AnimeV3", "SDXLTurbo"]
            )
            prompt = st.text_area(
                ":orange[**Enter prompt: start typing, Shakespeare ✍🏾**]",
                value="An astronaut riding a rainbow unicorn, cinematic, dramatic",
            )
            negative_prompt = st.text_area(
                ":orange[**Party poopers you don't want in image? 🙅🏽‍♂️**]",
                value="the absolute worst quality, distorted features",
                help="This is a negative prompt, basically type what you don't want to see in the generated image",
            )

            # The Big Red "Submit" Button!
            submitted = st.form_submit_button(
                "Submit", type="primary", use_container_width=True
            )

        # Credits and resources
        st.divider()
        st.markdown(
            ":orange[**Resources:**]  \n"
            f"<img src='{replicate_logo}' style='height: 1em'> [{replicate_text}]({replicate_link})",
            unsafe_allow_html=True,
        )

        return (
            submitted,
            width,
            height,
            num_inference_steps,
            guidance_scale,
            model_name,
            prompt,
            negative_prompt,
        )


def main_page(
    submitted: bool,
    width: int,
    height: int,
    num_inference_steps: int,
    guidance_scale: float,
    model_name: str,
    prompt: str,
    negative_prompt: str,
) -> None:
    """Main page layout and logic for generating images.

    Args:
        submitted (bool): Flag indicating whether the form has been submitted.
        width (int): Width of the output image.
        height (int): Height of the output image.
        num_inference_steps (int): Number of denoising steps.
        guidance_scale (float): Scale for classifier-free guidance.
        prompt_strength (float): Prompt strength when using img2img/inpaint.
        prompt (str): Text prompt for the image generation.
        negative_prompt (str): Text prompt for elements to avoid in the image.
    """
    if submitted:
        with st.status(
            "👩🏾‍🍳 Whipping up your words into art...", expanded=True
        ) as status:
            st.write("⚙️ Model initiated")
            st.write("🙆‍♀️ Stand up and strecth in the meantime")
            try:
                # Only call the API if the "Submit" button was pressed
                if submitted:
                    # Calling the replicate API to get the image
                    with generated_images_placeholder.container():
                        all_images = []  # List to store all generated images
                        data = {
                            "key": API_TOKEN,
                            "prompt": prompt,  # prompt
                            "model_name": model_name,  # See avaialble models in https://github.com/NicheTensor/NicheImage/blob/main/configs/model_config.yaml
                            "seed": -1,  # -1 means random seed
                            "miner_uid": -1,  # specify miner uid, -1 means random miner selected by validator
                            "pipeline_params": {  # params feed to diffusers pipeline, see all params here https://huggingface.co/docs/diffusers/api/pipelines/stable_diffusion/text2img#diffusers.StableDiffusionPipeline.__call__
                                "width": width,
                                "height": height,
                                "num_inference_steps": num_inference_steps,
                                "guidance_scale": guidance_scale,
                                "negative_prompt": negative_prompt,
                            },
                        }
                        output = call_niche_api(
                            "http://proxy_client_nicheimage.nichetensor.com:10003/generate",
                            data,
                        )
                        print(output)
                        if output:
                            st.toast("Your image has been generated!", icon="😍")
                            # Save generated image to session state
                            st.session_state.generated_image = output

                            # Displaying the image
                            for image in st.session_state.generated_image:
                                with st.container():
                                    st.image(
                                        image,
                                        caption="Generated Image 🎈",
                                        use_column_width=True,
                                    )
                                    # Add image to the list
                                    all_images.append(image)

                        # Save all generated images to session state
                        st.session_state.all_images = all_images
                status.update(
                    label="✅ Images generated!", state="complete", expanded=False
                )
            except Exception as e:
                print(e)
                st.error(f"Encountered an error: {e}", icon="🚨")

    # If not submitted, chill here 🍹
    else:
        pass

    # Gallery display for inspo
    with gallery_placeholder.container():
        img = image_select(
            label="Like what you see? Right-click and save! It's not stealing if we're sharing! 😉",
            images=[
                "gallery/farmer_sunset.png",
                "gallery/astro_on_unicorn.png",
                "gallery/friends.png",
                "gallery/wizard.png",
                "gallery/puppy.png",
                "gallery/cheetah.png",
                "gallery/viking.png",
            ],
            captions=[
                "A farmer tilling a farm with a tractor during sunset, cinematic, dramatic",
                "An astronaut riding a rainbow unicorn, cinematic, dramatic",
                "A group of friends laughing and dancing at a music festival, joyful atmosphere, 35mm film photography",
                "A wizard casting a spell, intense magical energy glowing from his hands, extremely detailed fantasy illustration",
                "A cute puppy playing in a field of flowers, shallow depth of field, Canon photography",
                "A cheetah mother nurses her cubs in the tall grass of the Serengeti. The early morning sun beams down through the grass. National Geographic photography by Frans Lanting",
                "A close-up portrait of a bearded viking warrior in a horned helmet. He stares intensely into the distance while holding a battle axe. Dramatic mood lighting, digital oil painting",
            ],
            use_container_width=True,
        )


def main():
    """
    Main function to run the Streamlit application.

    This function initializes the sidebar configuration and the main page layout.
    It retrieves the user inputs from the sidebar, and passes them to the main page function.
    The main page function then generates images based on these inputs.
    """
    (
        submitted,
        width,
        height,
        num_inference_steps,
        guidance_scale,
        model_name,
        prompt,
        negative_prompt,
    ) = configure_sidebar()
    main_page(
        submitted,
        width,
        height,
        num_inference_steps,
        guidance_scale,
        model_name,
        prompt,
        negative_prompt,
    )


if __name__ == "__main__":
    main()
