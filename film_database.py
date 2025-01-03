import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from google.oauth2 import service_account
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode

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
films_df['Year'] = films_df['Year'].astype(str)
# Title of the app
st.title("Jim's Film Database")

# Tabs for different sections
tab1, tab2 = st.tabs(["Add Film", "Film Database"])

with tab1:
    # Form to input new film
    with st.form(key="film_form"):
        title = st.text_input("Movie Title")
        genre = st.text_input("Genre")
        director = st.text_input("Director")
        year = st.number_input("Year", min_value=1900, max_value=2024, step=1)
        submit_button = st.form_submit_button(label="Add Film")

        # Add film to the database if the submit button is pressed
        if submit_button:
            new_film = pd.DataFrame({"Title": [title], "Genre": [genre], "Director": [director], "Year": [year]})
            films_df = pd.concat([films_df, new_film], ignore_index=True)
            update_gsheet_data(films_df)
            st.success(f"Film '{title}' added to the database!")
            
with tab2:
    # Search functionality
    search_term = st.text_input("Search Films (by title, genre, director, or year):")
    if search_term:
        # Convert the search term to lowercase to make it case-insensitive
        search_term = search_term.lower()
        
        # Filter the DataFrame to only include rows where any column contains the search term
        filtered_df = films_df[films_df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]
    else:
        filtered_df = films_df

    # Configure AG Grid options for the filtered DataFrame
    gb = GridOptionsBuilder.from_dataframe(filtered_df)
    gb.configure_default_column(editable=True)  # Make all columns editable
    gb.configure_selection(selection_mode="single", use_checkbox=True)  # Add row selection with checkbox
    grid_options = gb.build()

    # Display the editable table
    grid_response = AgGrid(
        filtered_df,
        gridOptions=grid_options,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode="MODEL_CHANGED",
        fit_columns_on_grid_load=True,
        theme="streamlit",
        enable_enterprise_modules=False,
        height=250,
    )

    # Get the updated DataFrame
    updated_df = grid_response["data"]
    selected_rows = grid_response["selected_rows"]
    
    if st.button("Delete Selected Row"):
        if len(selected_rows) > 0:
            selected_df = pd.DataFrame(selected_rows)
            films_df = films_df.reset_index(drop=True)
            selected_index = films_df[
                (films_df['Title'] == selected_df.iloc[0]['Title']) & 
                (films_df['Genre'] == selected_df.iloc[0]['Genre']) & 
                (films_df['Director'] == selected_df.iloc[0]['Director']) & 
                (films_df['Year'] == selected_df.iloc[0]['Year'])
            ].index
            films_df = films_df.drop(selected_index)
            update_gsheet_data(films_df)
            st.success("Selected film(s) have been deleted!")
        else:
            st.warning("Please select a row to delete.")

    # Button to save edits
    if st.button("Save Changes"):
        films_df = updated_df  # Update the DataFrame with the new data
        update_gsheet_data(films_df)  # Save changes to Google Sheets
        st.success("Changes saved successfully!")
