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


def pil_image_to_base64(image: Image.Image) -> str:
    image_stream = io.BytesIO()
    image.save(image_stream, format="PNG")
    base64_image = base64.b64encode(image_stream.getvalue()).decode("utf-8")

    return base64_image


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
    "DreamShaper": {
        "num_inference_steps": 30,
        "guidance_scale": 7,
        "ratio": {
            "square": (512, 512),
            "tall": (512, 768),
            "wide": (768, 512),
        },
    },
    "RealitiesEdgeXL": {
        "num_inference_steps": 7,
        "guidance_scale": 2.5,
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
    conditional_image: str,
    controlnet_conditioning_scale: list,
    pipeline_type: str,
    api_token: str,
    generated_images_placeholder,
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
    cols_1 = st.columns(4)
    if submitted:
        if secret_key != api_token and uid != "-1":
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
                            seeds = [random.randint(0, 1e9) for _ in range(num_images)]
                        all_images = []  # List to store all generated images
                        data = {
                            "key": api_token,
                            "prompt": prompt,  # prompt
                            "model_name": model_name,  # See avaialble models in https://github.com/NicheTensor/NicheImage/blob/main/configs/model_config.yaml
                            "seed": seed,  # -1 means random seed
                            "miner_uid": int(
                                uid
                            ),  # specify miner uid, -1 means random miner selected by validator
                            "pipeline_type": pipeline_type,
                            "conditional_image": conditional_image,
                            "pipeline_params": {  # params feed to diffusers pipeline, see all params here https://huggingface.co/docs/diffusers/api/pipelines/stable_diffusion/text2img#diffusers.StableDiffusionPipeline.__call__
                                "width": width,
                                "height": height,
                                "num_inference_steps": num_inference_steps,
                                "guidance_scale": guidance_scale,
                                "negative_prompt": negative_prompt,
                                "controlnet_conditioning_scale": controlnet_conditioning_scale,
                            },
                        }
                        duplicate_data = [data.copy() for _ in range(num_images)]
                        for i, d in enumerate(duplicate_data):
                            d["seed"] = seeds[i]
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
                                output[i] = Image.new("RGB", (width, height), (0, 0, 0))
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
                            for i, image in enumerate(st.session_state.generated_image):
                                cols_1[i].image(
                                    image,
                                    caption=captions[i],
                                    use_column_width=True,
                                    output_format="PNG",
                                )
                                # Add image to the list
                                all_images.append(image)

                        # Save all generated images to session state
                        st.session_state.all_images = all_images
                        zip_io = io.BytesIO()

                        # Download option for each image
                        with zipfile.ZipFile(zip_io, "w") as zipf:
                            for i, image in enumerate(st.session_state.all_images):
                                image_data = io.BytesIO()
                                image.save(image_data, format="PNG")
                                image_data.seek(0)
                                # Write each image to the zip file with a name
                                zipf.writestr(
                                    f"output_file_{i+1}.png", image_data.read()
                                )
                        # Create a download button for the zip file
                        st.download_button(
                            ":red[**Download All Images**]",
                            data=zip_io.getvalue(),
                            file_name="output_files.zip",
                            mime="application/zip",
                            use_container_width=True,
                        )
                status.update(
                    label="✅ Images generated!", state="complete", expanded=False
                )
            except Exception as e:
                print(e)
                st.error(f"Encountered an error: {e}", icon="🚨")

    # If not submitted, chill here 🍹
    else:
        pass
