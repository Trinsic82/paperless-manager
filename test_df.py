import streamlit as st
import pandas as pd

df = pd.DataFrame({
    "Typ": ["http://google.com", "http://bing.com"],
    "Markdown": ["[Google](http://google.com)", "[Bing](http://bing.com)"]
})
st.dataframe(df, use_container_width=True)
