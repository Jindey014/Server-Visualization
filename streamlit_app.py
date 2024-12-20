import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import json

with open("data/main_cleaned.csv", "r", encoding="utf-8", errors="replace") as f:
    df = pd.read_csv(f)

with open("data/boundaries.csv", "r", encoding="utf-8", errors="replace") as f:
    df_boundaries = pd.read_csv(f)


# now we need to merge the main_cleaned data with the boundaries data to get the actual csv file that we will use
# merged_df = pd.merge(df, df_boundaries, on='District', how='right')
# merged_df.to_csv('data/merged_data.csv', index=False)
with open("data/merged_data.csv", "r", encoding="utf-8", errors="replace") as f:
    df_merged = pd.read_csv(f)
merged_df_sorted = df_merged.sort_values(by='S.N.', ascending=True)

merged_df_sorted.to_csv('data/merged_data.csv', index=False)
merged_df_sorted




