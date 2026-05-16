import streamlit as st
import pandas as pd

df = pd.DataFrame({"Typ": ["http://test.com/documents?id=1#-disp-Mein Typ"]})
st.dataframe(df, use_container_width=True, column_config={"Typ": st.column_config.LinkColumn(display_text=r"#-disp-(.*)$")})
