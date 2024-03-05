import streamlit as st
import base64
import io
import random
import time
from typing import List
from PIL import Image
import aiohttp
import asyncio
import requests
import streamlit as st
import requests
import zipfile
import io
import pandas as pd
from core import *
from utils import icon
from streamlit_image_select import image_select
from PIL import Image
import random
import time
import base64
from typing import List
import aiohttp
import asyncio
import plotly.express as px
from common import set_page_container_style

replicate_text = "NicheImage - Subnet 23 - Bittensor"
replicate_logo = "assets/NicheTensorTransparent.png"
replicate_link = "https://github.com/NicheTensor/NicheImage"

st.set_page_config(
    page_title="NicheImage Generator", page_icon=replicate_logo, layout="wide"
)
set_page_container_style(
    max_width=1100,
    max_width_100_percent=True,
    padding_top=0,
    padding_right=10,
    padding_left=5,
    padding_bottom=10,
)


def get_or_create_eventloop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError as ex:
        if "There is no current event loop in thread" in str(ex):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return asyncio.get_event_loop()


# UI configurations
st.markdown(
    """<style>
    #root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 2rem;}
</style>

""",
    unsafe_allow_html=True,
)
css = """
<style>
section.main > div:has(~ footer ) {
    padding-bottom: 5px;
}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# API Tokens and endpoints from `.streamlit/secrets.toml` file
API_TOKEN = st.secrets["API_TOKEN"]
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
        st.image(replicate_logo, use_column_width=True)
        with st.form("my_form"):
            model_name = st.selectbox(
                ":blue[**Select Model**]",
                options=["DreamShaper"],
            )
            prompt = st.text_area(
                ":blue[**Enter prompt ✍🏾**]",
                value="3d render of cat in the style of Louis Wain, add detail, very colorful",
            )
            aspect_ratio = "Square"
            conditional_image = st.file_uploader(
                ":blue[**Upload your image**]",
                type=["png", "jpg", "jpeg"],
                help="Upload an image to condition the generation",
            )
            if conditional_image:
                st.image(conditional_image)
            with st.container(border=True):
                canny_strength = st.slider(
                    ":blue[**Canny Strength**]",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.5,
                    step=0.01,
                    help="Strength of the Canny ControlNet",
                )
                depth_strength = st.slider(
                    ":blue[**Depth Strength**]",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.5,
                    step=0.01,
                    help="Strength of the Depth ControlNet",
                )
                mlsd_strength = st.slider(
                    ":blue[**MLSD Strength**]",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.5,
                    step=0.01,
                    help="Strength of the MLSD ControlNet",
                )
                controlnet_conditioning_scale = [
                    canny_strength,
                    depth_strength,
                    mlsd_strength,
                ]

            num_images = 4
            negative_prompt = st.text_area(
                ":blue[**Negative Prompt 🙅🏽‍♂️**]",
                value="low quality, blurry, pixelated, noisy, low resolution, defocused, out of focus, overexposed, bad image, nsfw",
                help="This is a negative prompt, basically type what you don't want to see in the generated image",
            )
            with st.expander(
                "📚 Advanced",
                expanded=False,
            ):
                uid = st.text_input("Specify an UID", value="-1")
                secret_key = st.text_input("Enter secret key", value="")
                seed = st.text_input("Seed", value="-1")
            # The Big Red "Submit" Button!
            submitted = st.form_submit_button(
                "Submit", type="primary", use_container_width=True
            )

        return (
            submitted,
            model_name,
            prompt,
            negative_prompt,
            aspect_ratio,
            num_images,
            uid,
            secret_key,
            seed,
            conditional_image,
            controlnet_conditioning_scale,
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
        model_name,
        prompt,
        negative_prompt,
        aspect_ratio,
        num_images,
        uid,
        secret_key,
        seed,
        conditional_image,
        controlnet_conditioning_scale,
    ) = configure_sidebar()
    if conditional_image:
        conditional_image = Image.open(conditional_image)
        conditional_image = pil_image_to_base64(conditional_image)
    main_page(
        submitted,
        model_name,
        prompt,
        negative_prompt,
        aspect_ratio,
        num_images,
        uid,
        secret_key,
        seed,
        conditional_image,
        controlnet_conditioning_scale,
        "controlnet_txt2img",
        API_TOKEN,
        generated_images_placeholder,
    )
    if not submitted:
        with generated_images_placeholder.container():
            st.info("🎨 :blue[**Canny Edge**]")
            cols = st.columns(2)
            with cols[0]:
                st.image(
                    "https://huggingface.co/takuma104/controlnet_dev/resolve/main/gen_compare/control_images/converted/control_bird_canny.png",
                    use_column_width=True,
                )
            with cols[1]:
                st.image(
                    "https://cdn-lfs.huggingface.co/repos/f4/f7/f4f7a7f70b5d098c5f2b46c19c2063eea26d6eba1488e9141804f6402b509cbb/3907d804ef04bcc1dd998ddb8dbd01ad6ffd071d6f13bd2e8a03936f7fe35f13?response-content-disposition=inline%3B+filename*%3DUTF-8%27%27output_bird_canny_1.png%3B+filename%3D%22output_bird_canny_1.png%22%3B&response-content-type=image%2Fpng&Expires=1709913845&Policy=eyJTdGF0ZW1lbnQiOlt7IkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTcwOTkxMzg0NX19LCJSZXNvdXJjZSI6Imh0dHBzOi8vY2RuLWxmcy5odWdnaW5nZmFjZS5jby9yZXBvcy9mNC9mNy9mNGY3YTdmNzBiNWQwOThjNWYyYjQ2YzE5YzIwNjNlZWEyNmQ2ZWJhMTQ4OGU5MTQxODA0ZjY0MDJiNTA5Y2JiLzM5MDdkODA0ZWYwNGJjYzFkZDk5OGRkYjhkYmQwMWFkNmZmZDA3MWQ2ZjEzYmQyZThhMDM5MzZmN2ZlMzVmMTM%7EcmVzcG9uc2UtY29udGVudC1kaXNwb3NpdGlvbj0qJnJlc3BvbnNlLWNvbnRlbnQtdHlwZT0qIn1dfQ__&Signature=JplN20XzO7Y34tz-FkA3-cv4VRfIkzz9Tf8-Re7EdW-7%7EaBEItVnl5SDX44oSk-WeNFPfhcHg-b7RK1zlD6H1n3Zo7Y8JtMR1Z07%7ElZ6S6s80j1vpOrMmnkyB-7DcM9Mvi2ITDPXhOdYGnAK1GER1Zdg-ctVEkf7frNEj%7E5zcqJ1kFyRCJcjPHtgAtIAySOANk6BIZEWLEbZGM3b4swTMnNPUZZw5CYRp2dgGgVEo8i6xalR1l8rqvAxQ3yB4C5nfJURcqQLY1lkk9B58dhR6Afy5ZG-krqilv07R7HqbsS7GWq6w8BCEXA0E9cjQTqzqlpCZG0wH78vNE8GDdF6kQ__&Key-Pair-Id=KVTP0A1DKRTAX",
                    use_column_width=True,
                )
            st.info("🎨 :blue[**Depth Map**]")
            cols2 = st.columns(2)
            with st.container():
                with cols2[0]:
                    st.image(
                        "https://huggingface.co/takuma104/controlnet_dev/resolve/main/gen_compare/control_images/converted/control_vermeer_depth.png",
                        use_column_width=True,
                    )
                with cols2[1]:
                    st.image(
                        "https://cdn-lfs.huggingface.co/repos/f4/f7/f4f7a7f70b5d098c5f2b46c19c2063eea26d6eba1488e9141804f6402b509cbb/25c89f31165aa3c435b28deeb1e542c68b0dab496727403c1f3c7ded3b78fdd1?response-content-disposition=inline%3B+filename*%3DUTF-8%27%27output_vermeer_depth_2.png%3B+filename%3D%22output_vermeer_depth_2.png%22%3B&response-content-type=image%2Fpng&Expires=1709913950&Policy=eyJTdGF0ZW1lbnQiOlt7IkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTcwOTkxMzk1MH19LCJSZXNvdXJjZSI6Imh0dHBzOi8vY2RuLWxmcy5odWdnaW5nZmFjZS5jby9yZXBvcy9mNC9mNy9mNGY3YTdmNzBiNWQwOThjNWYyYjQ2YzE5YzIwNjNlZWEyNmQ2ZWJhMTQ4OGU5MTQxODA0ZjY0MDJiNTA5Y2JiLzI1Yzg5ZjMxMTY1YWEzYzQzNWIyOGRlZWIxZTU0MmM2OGIwZGFiNDk2NzI3NDAzYzFmM2M3ZGVkM2I3OGZkZDE%7EcmVzcG9uc2UtY29udGVudC1kaXNwb3NpdGlvbj0qJnJlc3BvbnNlLWNvbnRlbnQtdHlwZT0qIn1dfQ__&Signature=b%7EhyTb-HRh2shXtGNEfhNrXU%7EsuQdyE0iTXVKpR76CDxlS147%7EYxiU%7E9JJAL1asz-vfUS5u%7ErtqIRfGkKAcU1DP8lqtGhIfDBi6iPNEyWoAWAGj7mF6y50qj7xeq2Iz4yWeHoiZpzotiWbMqCE6V6QKrHsaU2btHlHjlLsw4owh3ELXjHB6%7ENCKwH0uKLfABOBZzrOJOCilJU8VwiCRsk3QryLD3uywZMGDxyzd1vxnaBR4PTIrZ46FEatcXCpGdZ1ZJngtdiepdLRX4tI41gVk0fWYrQ5wOnMSudCQuCfVXvHRnoPwKUVcmF5mCa7smZykizITEmwg3ctW4W80pBA__&Key-Pair-Id=KVTP0A1DKRTAX",
                        use_column_width=True,
                    )
            st.info("🎨 :blue[**MLSD**]")
            cols3 = st.columns(2)
            with st.container():
                with cols3[0]:
                    st.image(
                        "https://huggingface.co/takuma104/controlnet_dev/resolve/main/gen_compare/control_images/converted/control_room_mlsd.png",
                        use_column_width=True,
                    )
                with cols3[1]:
                    st.image(
                        "https://cdn-lfs.huggingface.co/repos/f4/f7/f4f7a7f70b5d098c5f2b46c19c2063eea26d6eba1488e9141804f6402b509cbb/92c95cf788f547ef7ea2da0fb45a0232864899ddd93c8f04d88b04f681216ad3?response-content-disposition=inline%3B+filename*%3DUTF-8%27%27output_room_mlsd_0.png%3B+filename%3D%22output_room_mlsd_0.png%22%3B&response-content-type=image%2Fpng&Expires=1709912870&Policy=eyJTdGF0ZW1lbnQiOlt7IkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTcwOTkxMjg3MH19LCJSZXNvdXJjZSI6Imh0dHBzOi8vY2RuLWxmcy5odWdnaW5nZmFjZS5jby9yZXBvcy9mNC9mNy9mNGY3YTdmNzBiNWQwOThjNWYyYjQ2YzE5YzIwNjNlZWEyNmQ2ZWJhMTQ4OGU5MTQxODA0ZjY0MDJiNTA5Y2JiLzkyYzk1Y2Y3ODhmNTQ3ZWY3ZWEyZGEwZmI0NWEwMjMyODY0ODk5ZGRkOTNjOGYwNGQ4OGIwNGY2ODEyMTZhZDM%7EcmVzcG9uc2UtY29udGVudC1kaXNwb3NpdGlvbj0qJnJlc3BvbnNlLWNvbnRlbnQtdHlwZT0qIn1dfQ__&Signature=A9jKF1jw8YO8OFuB7CzbaeQrEdT8wuPZJnT%7E1gZTxBAot9-HBQypW4IMsP7XPCeWnfdJBH4EKcsfzP2RU2-y2%7ENHrJl6wd9n-Wyi5traDPUgoHlSGIe6BvEKJlkzUI7gf87ThVWNc6wI3kHZM0l3dESE0ID2e2aCKGNxUCfaV%7EBdyt-Myr0HbVQtfYR8SjW7Rdj5WCJy9vOZKS3y2nzfPsUZRNtup4Xw3EW%7Ei0BGomdrB%7EfoOj4A0CvuL-La8SxPz1a3AcakD0ti8P0TPIJ9FrjmWLr49t9gJvn2XMYD3mH8VVsSBsGDn6pjgTLS4FK0KvCu-lIqt14v1bF10wCzBA__&Key-Pair-Id=KVTP0A1DKRTAX",
                        use_column_width=True,
                    )


if __name__ == "__main__":
    main()
