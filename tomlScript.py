import toml
import json   
import streamlit as st


newDic={}
for key in st.secrets['eecredentials']:
    newDic[key.replace("eecredentials_","")] = st.secrets['eecredentials'][key]
#json_object = json.dumps(newDic, indent = 4)   
with open('credentials.json', 'w') as outfile:
    json.dump(newDic, outfile)
