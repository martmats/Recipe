import streamlit as st
import requests

# Set page configuration
st.set_page_config(page_title="Meal Plan Generator", page_icon="🍽️", layout="wide")

# CSS Styling: Blue Sidebar, White Background, and Recipe Card Styling
st.markdown("""
    <style>
        .stApp {{
            background-color: white;
        }}
        /* Blue background for the sidebar */
        section[data-testid="stSidebar"] {{
            background-color: #007bff;
        }}
        /* Style the recipe display */
        .recipe-container {{
            border: 1px solid #e0e0e0;
            padding: 10px;
            border-radius: 8px;
            background-color: white;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
            text-align: center;
            margin-bottom: 20px;
        }}
        .recipe-container img {{
            border-radius: 8px;
            width: 100%;
        }}
        .recipe-container button {{
            background-color: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            margin-top: 10px;
        }}
    </style>
    """, unsafe_allow_html=True)

# API credentials from Streamlit Secrets (stored in Streamlit Cloud)
EDAMAM_APP_ID = st.secrets["app_id"]
EDAMAM_APP_KEY = st.secrets["app_key"]

# Initialize the meal plan to persist data using session state
if "meal_plan" not in st.session_state:
    st.session_state.meal_plan = {f"Day {i+1}": [] for i in range(7)}

# Cache API response to avoid multiple calls for the same query
@st.cache_data
def fetch_recipes(query, diet_type, calorie_limit):
    # API endpoint for Edamam Recipes API
    BASE_URL = "https://api.edamam.com/api/recipes/v2"
    
    # Build the query parameters for the API request
    params = {
        "type": "public",
        "q": query,
        "app_id": EDAMAM_APP_ID,
        "app_key": EDAMAM_APP_KEY,
    }
    
    # Add optional filters
    if diet_type != "None":
        params["diet"] = diet_type.lower()
    if calorie_limit > 0:
        params["calories"] = f"lte {calorie_limit}"
    
    # Send API request
    response = requests.get(BASE_URL, params=params)
    
    if response.status_code == 200:
        return response.json().get("hits", [])
    else:
        st.error(f"API request failed with status code {response.status_code}")
        st.write(response.text)
        return []

# Sidebar options for search filters and search query
st.sidebar.title("Meal Plan Options")
diet_type = st.sidebar.selectbox("Select Diet", ["Balanced", "Low-Carb", "High-Protein", "None"], index=0)
calorie_limit = st.sidebar.number_input("Max Calories (Optional)", min_value=0, step=50)
query = st.sidebar.text_input("Search for recipes (e.g., chicken, vegan pasta)", "dinner")
if st.sidebar.button("Search Recipes"):
    st.session_state.recipes = fetch_recipes(query, diet_type, calorie_limit)

# Track selected day for each recipe in session state
if "selected_days" not in st.session_state:
    st.session_state.selected_days = {}

# Helper function to add recipes to the meal plan
def add_recipe_to_day(day, recipe):
    st.session_state.meal_plan[day].append(recipe)

# Show recipes if search has been performed
if "recipes" in st.session_state:
    recipes = st.session_state.recipes
    if recipes:
        st.write(f"## Showing {len(recipes)} recipes for **{query}**")
        cols = st.columns(3)
        for idx, recipe_data in enumerate(recipes):
            recipe = recipe_data["recipe"]
            recipe_key = f"recipe_{idx}"
            if recipe_key not in st.session_state.selected_days:
                st.session_state.selected_days[recipe_key] = "Day 1"

            with cols[idx % 3]:
                st.markdown(f"""
                <div class="recipe-container">
                    <img src="{recipe['image']}" alt="Recipe Image"/>
                    <h4>{recipe['label']}</h4>
                    <p>Calories: {recipe['calories']:.0f}</p>
                    <a href="{recipe['url']}" target="_blank"><button>View Recipe</button></a>
                </div>
                """, unsafe_allow_html=True)

                selected_day = st.selectbox(
                    f"Choose day for {recipe['label']}",
                    list(st.session_state.meal_plan.keys()), 
                    key=f"day_{recipe_key}"
                )
                if st.button(f"Add {recipe['label']} to {selected_day}", key=f"btn_{idx}"):
                    add_recipe_to_day(selected_day, recipe)

# Display the meal plan in a calendar-like format
st.write("## Your Meal Plan")
cols = st.columns(7)
for idx, (day, meals) in enumerate(st.session_state.meal_plan.items()):
    with cols[idx % 7]:
        st.write(f"### {day}")
        if meals:
            for meal in meals:
                st.write(f"- {meal['label']} ({meal['calories']:.0f} calories)")
        else:
            st.write("No meals added yet.")

# Input for number of people before generating the shopping list
people = st.sidebar.number_input("How many people?", min_value=1, value=1)

# Generate shopping list button
if st.sidebar.button("Generate Shopping List"):
    shopping_list = {}
    for meals in st.session_state.meal_plan.values():
        for recipe in meals:
            for ingredient in recipe["ingredients"]:
                food_item = ingredient["food"]
                quantity = ingredient["quantity"] * people  # Adjusting for number of people
                if food_item in shopping_list:
                    shopping_list[food_item] += quantity
                else:
                    shopping_list[food_item] = quantity

    # Display the shopping list
    st.write("## Shopping List")
    for food, quantity in shopping_list.items():
        st.write(f"{food}: {quantity}")

