import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# Load credentials from Streamlit secrets
credentials_info = {
    "type": st.secrets["google_credentials"]["type"],
    "project_id": st.secrets["google_credentials"]["project_id"],
    "private_key_id": st.secrets["google_credentials"]["private_key_id"],
    "private_key": st.secrets["google_credentials"]["private_key"],
    "client_email": st.secrets["google_credentials"]["client_email"],
    "client_id": st.secrets["google_credentials"]["client_id"],
    "auth_uri": st.secrets["google_credentials"]["auth_uri"],
    "token_uri": st.secrets["google_credentials"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["google_credentials"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["google_credentials"]["client_x509_cert_url"],
    "universe_domain": st.secrets["google_credentials"]["universe_domain"]
}


# Setup the connection to Google Sheets
def get_gsheet_data():
    # Define the scope of the API
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Use the credentials loaded from Streamlit secrets
    credentials = service_account.Credentials.from_service_account_info(credentials_info, scopes=scope)
    client = gspread.authorize(credentials)
    
    # Open the sheet by name
    sheet = client.open("Streamlit Film Database").sheet1
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def update_gsheet_data(films_df):
    # Define the scope of the API
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Use the credentials loaded from Streamlit secrets
    credentials = service_account.Credentials.from_service_account_info(credentials_info, scopes=scope)
    client = gspread.authorize(credentials)
    
    # Open the sheet by name
    sheet = client.open("Streamlit Film Database").sheet1
    
    # Update the sheet with new data
    sheet.clear()  # Clear the current data
    sheet.update([films_df.columns.values.tolist()] + films_df.values.tolist())  # Update with new data

# Load data from Google Sheets
films_df = get_gsheet_data()

# Title of the app
st.title("Streamlit Film Database")

# Form to input new film
with st.form(key="film_form"):
    title = st.text_input("Movie Title")
    genre = st.text_input("Genre")
    director = st.text_input("Director")
    year = st.number_input("Year Released", min_value=1900, max_value=2024, step=1)
    submit_button = st.form_submit_button(label="Add Film")

    # Add film to the database if the submit button is pressed
    if submit_button:
        new_film = pd.DataFrame({"Title": [title], "Genre": [genre], "Director": [director], "Year": [year]})
        films_df = pd.concat([films_df, new_film], ignore_index=True)
        update_gsheet_data(films_df)
        st.success(f"Film '{title}' added to the database!")

# Display the films in the database
st.subheader("Films You Have Seen")

if len(films_df) > 0:
    st.dataframe(films_df)
else:
    st.write("No films added yet.")
