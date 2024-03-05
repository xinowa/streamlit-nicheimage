import streamlit as st
import base64
import io
import random
import time
from typing import List
from PIL import Image
import aiohttp
import asyncio
from diffusers.utils import load_image
from streamlit_image_select import image_select
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
                options=["RealisticVision", "AnimeV3", "DreamShaper", "RealitiesEdgeXL"],
            )
            prompt = st.text_area(
                ":blue[**Enter prompt ✍🏾**]",
                value="3d render of cat in the style of Louis Wain, add detail, very colorful",
            )
            aspect_ratio = "Square"
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
            "",
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
    ) = configure_sidebar()
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
        [],
        "txt2img",
        API_TOKEN,
        generated_images_placeholder,
    )
    if not submitted:
        with gallery_placeholder.container():
            with st.container():
                st.info(
                    "👩🏾‍🍳 :blue[**Realistic Vision Style - [CivitAI](https://civitai.com/models/4201/realistic-vision-v60-b1)**]"
                )
                st.balloons()
            with st.container(border=True):
                _ = image_select(
                    label="",
                    images=[
                        "https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/401d2674-e1f8-4976-a615-36110d0b76b3/original=true/ref-res-1.jpeg",
                        "https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/d2050c06-e916-4091-857a-66bdafcaf6d9/original=true/00029-913302605.jpeg",
                        "https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/0012d0e9-6d77-4981-b16e-13ac9f3eeb53/original=true/00011-836818560.jpeg",
                        "https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/088542b8-00dc-4135-8115-f2086ebb4ffb/original=true/06772-2405195618-HDR,UHD,8K,Highly%20detailed,best%20quality,masterpiece,_lora_catman_0.8_,maomi,blurry%20background,blurry,sunglasses,hat,hands%20in%20poc.jpeg",
                        "https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/3b23b565-9b7b-4e5b-9a40-ff9b5e80565d/original=true/00076-329187343.jpeg",
                    ],
                    use_container_width=False,
                )
            with st.container():
                st.info(
                    "👩🏾‍🍳 :blue[**DreamShaper Style - [CivitAI](https://civitai.com/models/4384/dreamshaper)**]"
                )
            with st.container(border=True):
                _ = image_select(
                    label="",
                    images=[
                        "https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/af837eea-2ccc-4801-b916-75ecb270c382/original=true/71584-4007479174-masterpiece,%20a%20dinosaur%20(in%20the%20museum_1.2),%20background%20is%20museum%20exhibition,%20(art%20by%20YRAX_1.1),%20saturated%20colors,%20concept%20art,.jpeg",
                        "https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/77940ee3-062a-4d2b-95c4-52c69b79fffd/original=true/00524-2430470379.jpeg",
                        "https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/1649bcd9-4417-4c83-97f8-674373b67d61/original=true/42445-1548916933-wabstyle,%20monochrome,%20_lora_wabstyle_1_%20a%20dog.jpeg",
                        "https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/09264ecb-38c6-42ed-a2f7-a7ab5ab662fb/original=true/00262-5775713%20-%20Kopie.jpeg",
                        "https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/a25faadc-7370-426d-9e95-1e102a10e508/original=true/00613-787076454-(a%20Glass%20ring_1.3),%20masterpiece,%20best%20quality,%20_lora_RingArt_Sora_0.8_,%20(style%20of%20Ellen%20Gallagher_1.3)__(masterpiece,%20best%20quali%20(1).jpeg",
                    ],
                    use_container_width=False,
                )
            with st.container():
                st.info(
                    "👩🏾‍🍳 :blue[**AnimeV3 Style - [CivitAI](https://civitai.com/models/146113/newdream-sdxl)**]"
                )
            with st.container(border=True):
                _ = image_select(
                    label="",
                    images=[
                        "https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/c788e346-7af1-4135-928a-c944634a4a51/original=true/Soldier.jpeg",
                        "https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/dc86e78e-7587-45b8-b709-b6f611af68fa/original=true/pirate%20(3).jpeg",
                        "https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/cb6aa6c4-6cd6-4efd-84a8-4b3917ca4d24/original=true/00000-1761366536.jpeg",
                        "https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/61cad059-f9d8-446f-b33d-b22e078ac5fb/original=true/Scream.jpeg",
                        "https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/58d55973-12c9-4854-afbc-4fbd8f5434ef/original=true/CarSakura.jpeg",
                    ],
                    use_container_width=False,
                )
            with st.container():
                st.info(
                    "👩🏾‍🍳 :blue[**RealitiesEdgeXL Style - [CivitAI](https://civitai.com/models/129666?modelVersionId=356472)**]"
                )
            with st.container(border=True):
                _ = image_select(
                    label="",
                    images=[
                        "https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/7ae8de93-3634-4fb2-acb6-7ba66a630670/original=true/00044-3526680654.jpeg",
                        "https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/d7a3e977-5433-46d0-82ba-4946386bd28e/original=true/00135-1518921975.jpeg",
                        "https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/c3852385-4c73-4821-ac6f-b9f0323c7d6f/original=true/08323--3358745561.jpeg",
                        "https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/7f6be0cf-4b58-4c16-aa8f-4c396fb135b2/original=true/ComfyUI-1-_01583_.jpeg",
                        "https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/e9ecf8ad-8f3b-4fc3-9eca-c59389e84a3f/original=true/08314--1054985950.jpeg",
                    ],
                    use_container_width=False,
                )


if __name__ == "__main__":
    main()
