import streamlit as st
import requests
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="NicheImage Studio", layout="wide")
st.markdown("## :black[Image Generation Studio by NicheImage]")
replicate_logo = "assets/NicheTensorTransparent.png"

with st.sidebar:
    st.image(replicate_logo, use_column_width=True)
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
        model_distribution[model_name] = model_distribution.get(model_name, 0) + 1
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
