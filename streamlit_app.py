import streamlit as st
import requests
import zipfile
import io
import pandas as pd
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


model_config = {
    "RealisticVision": {
        "ratio": {
            "square": (512, 512),
            "tall": (512, 768),
            "wide": (768, 512),
        },
        "num_inference_steps": 30,
        "guidance_scale": 7.0,
    },
    "AnimeV3": {
        "num_inference_steps": 25,
        "guidance_scale": 7,
        "ratio": {
            "square": (1024, 1024),
            "tall": (672, 1024),
            "wide": (1024, 672),
        },
    },
    "SDXLTurbo": {
        "num_inference_steps": 4,
        "guidance_scale": 0.5,
        "ratio": {
            "square": (512, 512),
            "tall": (512, 768),
            "wide": (768, 512),
        },
    },
    "RealitiesEdgeXL": {
        "num_inference_steps": 7,
        "guidance_scale": 5.5,
        "ratio": {
            "square": (1024, 1024),
            "tall": (672, 1024),
            "wide": (1024, 672),
        },
    },
}


def base64_to_image(base64_string):
    return Image.open(io.BytesIO(base64.b64decode(base64_string)))


async def call_niche_api(url, data) -> List[Image.Image]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                response = await response.json()
        return base64_to_image(response)
    except Exception as e:
        print(e)
        return None


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
st.markdown("## :black[Image Generation Studio by NicheImage]")

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
                options=["RealisticVision", "AnimeV3", "SDXLTurbo", "RealitiesEdgeXL"],
            )
            prompt = st.text_area(
                ":blue[**Enter prompt ✍🏾**]",
                value="An astronaut riding a rainbow unicorn, cinematic, dramatic",
            )
            aspect_ratio = st.selectbox(
                ":blue[**Aspect Ratio**]", options=["Tall", "Wide", "Square"]
            )
            num_images = st.slider(":blue[**Number of images to generate**]", 1, 4, 1)
            negative_prompt = st.text_area(
                ":blue[**Negative Prompt 🙅🏽‍♂️**]",
                value="the absolute worst quality, distorted features",
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
        )


async def get_output(url, datas):
    tasks = [asyncio.create_task(call_niche_api(url, data)) for data in datas]
    return await asyncio.gather(*tasks)


def main_page(
    submitted: bool,
    model_name: str,
    prompt: str,
    negative_prompt: str,
    aspect_ratio: str,
    num_images: int,
    uid: str,
    secret_key: str,
    seed: str,
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
    tab1, tab2 = st.tabs(["✨ Image Generation", "📊 NicheImage Statistics"])
    with tab1:
        cols_1 = st.columns(4)
        if submitted:
            if secret_key != API_TOKEN and uid != "-1":
                st.error("Invalid secret key")
                return
            try:
                uid = int(uid)
            except ValueError:
                uid = -1
            width, height = model_config[model_name]["ratio"][aspect_ratio.lower()]
            width = int(width)
            height = int(height)
            num_inference_steps = model_config[model_name]["num_inference_steps"]
            guidance_scale = model_config[model_name]["guidance_scale"]

            with st.status(
                "👩🏾‍🍳 Whipping up your words into art...", expanded=True
            ) as status:
                try:
                    # Only call the API if the "Submit" button was pressed
                    if submitted:
                        start_time = time.time()
                        # Calling the replicate API to get the image
                        with generated_images_placeholder.container():
                            try:
                                seed = int(seed)
                            except ValueError:
                                seed = -1
                            if seed >= 0:
                                seeds = [int(seed) + i for i in range(num_images)]
                            else:
                                seeds = [
                                    random.randint(0, 1e9) for _ in range(num_images)
                                ]
                            all_images = []  # List to store all generated images
                            data = {
                                "key": API_TOKEN,
                                "prompt": prompt,  # prompt
                                "model_name": model_name,  # See avaialble models in https://github.com/NicheTensor/NicheImage/blob/main/configs/model_config.yaml
                                "seed": seed,  # -1 means random seed
                                "miner_uid": int(
                                    uid
                                ),  # specify miner uid, -1 means random miner selected by validator
                                "pipeline_params": {  # params feed to diffusers pipeline, see all params here https://huggingface.co/docs/diffusers/api/pipelines/stable_diffusion/text2img#diffusers.StableDiffusionPipeline.__call__
                                    "width": width,
                                    "height": height,
                                    "num_inference_steps": num_inference_steps,
                                    "guidance_scale": guidance_scale,
                                    "negative_prompt": negative_prompt,
                                },
                            }
                            duplicate_data = [data.copy() for _ in range(num_images)]
                            for i, d in enumerate(duplicate_data):
                                d["seed"] = seeds[i]

                            print(duplicate_data)
                            # Call the NicheImage API
                            loop = get_or_create_eventloop()
                            asyncio.set_event_loop(loop)
                            output = loop.run_until_complete(
                                get_output(
                                    "http://proxy_client_nicheimage.nichetensor.com:10003/generate",
                                    duplicate_data,
                                )
                            )
                            while len(output) < 4:
                                output.append(None)
                            for i, image in enumerate(output):
                                if not image:
                                    output[i] = Image.new(
                                        "RGB", (width, height), (255, 255, 255)
                                    )
                            print(output)
                            if output:
                                st.toast("Your image has been generated!", icon="😍")
                                end_time = time.time()
                                status.update(
                                    label=f"✅ Images generated in {round(end_time-start_time, 3)} seconds",
                                    state="complete",
                                    expanded=False,
                                )

                                # Save generated image to session state
                                st.session_state.generated_image = output
                                captions = [f"Image {i+1} 🎈" for i in range(4)]
                                all_images = []
                                # Displaying the image
                                for i, image in enumerate(
                                    st.session_state.generated_image
                                ):
                                    cols_1[i].image(
                                        image,
                                        caption=captions[i],
                                        use_column_width=True,
                                    )
                                    # Add image to the list
                                    all_images.append(image)

                            # Save all generated images to session state
                            st.session_state.all_images = all_images
                except Exception as e:
                    print(e)
                    st.error(f"Encountered an error: {e}", icon="🚨")

        # If not submitted, chill here 🍹
        else:
            st.markdown(
                """
                ### 🎨 A beautiful landscape
                """
            )
            cols_1 = st.columns(2)
            cols_1[0].image(
                "assets/rv_1.jpg",
                caption="Realistic Vision 🌠",
                use_column_width=True,
            )
            cols_1[1].image(
                "assets/sdxlturbo_1.jpg",
                caption="SDXL Turbo 🧭",
                use_column_width=True,
            )
            st.image(
                "assets/animev3_1.jpg",
                caption="Anime V3 🗻",
                use_column_width=True,
            )
    with tab2:
        st.markdown(
            """
            **NicheImage is a decentralized network of image generation models, powered by the Bittensor protocol. Below you find information about the current models on the network.**
            """,
            unsafe_allow_html=True,
        )
        response = requests.get(
            "http://proxy_client_nicheimage.nichetensor.com:10003/get_uid_info"
        )
        if response.status_code == 200:
            response = response.json()
            # Plot distribution of models
            model_distribution = {}
            for uid, info in response["all_uid_info"].items():
                model_name = info["model_name"]
                model_distribution[model_name] = (
                    model_distribution.get(model_name, 0) + 1
                )
            fig = px.pie(
                values=list(model_distribution.values()),
                names=list(model_distribution.keys()),
                title="Model Distribution",
            )
            st.plotly_chart(fig)
            transformed_dict = []
            for k, v in response["all_uid_info"].items():
                transformed_dict.append(
                    {
                        "uid": k,
                        "model_name": v["model_name"],
                        "mean_score": sum(v["scores"]) / (len(v["scores"]) + 1),
                    }
                )
            transformed_dict = pd.DataFrame(transformed_dict)
            # plot N bar chart for N models, sorted by mean score
            for model in model_distribution.keys():
                model_data = transformed_dict[transformed_dict["model_name"] == model]
                model_data = model_data.sort_values(by="mean_score", ascending=False)
                if model_data.mean_score.sum() == 0:
                    continue
                st.write(f"Model: {model}")
                st.bar_chart(model_data[["uid", "mean_score"]].set_index("uid"))

        else:
            st.error("Error getting miner info")


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
    )


if __name__ == "__main__":
    main()
