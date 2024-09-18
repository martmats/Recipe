import streamlit as st
import requests
import json

# API credentials from secrets.toml
SPOONACULAR_API_KEY = st.secrets["api"]["SPOONACULAR_API_KEY"]
EDAMAM_APP_ID = st.secrets["api"]["EDAMAM_APP_ID"]
EDAMAM_API_KEY = st.secrets["api"]["EDAMAM_API_KEY"]
# Set page configuration
st.set_page_config(page_title="Meal Plan Generator", page_icon="🍽️", layout="wide")

# Caching function for search results using st.cache_data
@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_from_spoonacular(query, diet=None, time=None, calories=None):
    url = f"https://api.spoonacular.com/recipes/complexSearch?apiKey={SPOONACULAR_API_KEY}"
    params = {
        'query': query,
        'number': 80,  # Request 80 results
        'addRecipeInformation': True
    }
    if diet:
        params['diet'] = diet
    if time:
        params['maxReadyTime'] = time
    if calories:
        params['maxCalories'] = calories

    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get('results', [])
    return None
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

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_from_edamam(query, diet=None):
    url = "https://api.edamam.com/search"
# Track selected day for each recipe in session state
if "selected_days" not in st.session_state:
    st.session_state.selected_days = {}

# API endpoint for Edamam Recipes API
BASE_URL = "https://api.edamam.com/api/recipes/v2"

# Sidebar options for search filters
st.sidebar.title("Meal Plan Options")
diet_type = st.sidebar.selectbox("Select Diet", ["Balanced", "Low-Carb", "High-Protein", "None"], index=0)
calorie_limit = st.sidebar.number_input("Max Calories (Optional)", min_value=0, step=50)

# Input field for the search query
query = st.text_input("Search for recipes (e.g., chicken, vegan pasta)", "dinner")

# Helper function to add recipes to the meal plan
def add_recipe_to_day(day, recipe):
    st.session_state.meal_plan[day].append(recipe)

# Search button
if st.button("Search Recipes"):
    # Build the query parameters for the API request
    params = {
        'q': query,
        'app_id': EDAMAM_APP_ID,
        'app_key': EDAMAM_API_KEY,
        'to': 80  # Request 80 results
        "type": "public",
        "q": query,
        "app_id": EDAMAM_APP_ID,
        "app_key": EDAMAM_APP_KEY,
    }
    if diet:
        params['diet'] = diet

    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get('hits', [])
    return None
    # Add optional filters
    if diet_type != "None":
        params["diet"] = diet_type.lower()
    if calorie_limit > 0:
        params["calories"] = f"lte {calorie_limit}"

    # Send API request
    response = requests.get(BASE_URL, params=params)

def fetch_from_mealdb(query):
    url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={query}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('meals', [])
    return None

def search_recipes(query, diet=None, time=None, calories=None):
    # Fetch results from all three APIs
    spoonacular_results = fetch_from_spoonacular(query, diet=diet, time=time, calories=calories) or []
    edamam_results = fetch_from_edamam(query, diet=diet) or []
    mealdb_results = fetch_from_mealdb(query) or []

    # Combine the results from all APIs
    all_results = spoonacular_results + edamam_results + mealdb_results

    return all_results

# Streamlit App UI
def main():
    st.title("🍲 Recipe Search Dashboard")

    # Sidebar filters
    st.sidebar.header("Find your Recipe Here")

    # Move search input to sidebar
    query = st.sidebar.text_input("Search here...", "", key="search", label_visibility="visible", placeholder="e.g., vegan casserole")

    diet = st.sidebar.selectbox("Dietary Restrictions", [None, "vegetarian", "vegan", "gluten free", "paleo", "ketogenic"], key="diet")
    time = st.sidebar.number_input("Max Preparation Time (minutes)", min_value=30, max_value=120, step=10, key="time")
    calories = st.sidebar.number_input("Max Calories", min_value=300, max_value=1500, step=100, key="calories")

    # Fetch recipes and display results
    if st.sidebar.button("Search"):
        recipes = search_recipes(query, diet=diet, time=time, calories=calories)

        recipes = response.json().get("hits", [])

        if recipes:
            st.write(f"Top results for '{query}':")
            cols = st.columns(3)  # Display 3 columns per row

            for i, recipe in enumerate(recipes):
                with cols[i % 3]:
                    # Try to handle different structures from the APIs
                    image = recipe.get('image') if 'image' in recipe else recipe.get('recipe', {}).get('image', None)
                    title = recipe.get('title') if 'title' in recipe else recipe.get('recipe', {}).get('label', None)
                    source_url = recipe.get('sourceUrl') if 'sourceUrl' in recipe else recipe.get('recipe', {}).get('url', None)

                    if image and title and source_url:
                        st.markdown(f"""
                        <div class="recipe-container">
                            <img src="{image}" width="100%" height="150px" style="object-fit:cover; border-radius:8px;">
                            <p class="recipe-title">{title}</p>
                            <a href="{source_url}" target="_blank" class="recipe-button">View Recipe</a>
                        </div>
                        """, unsafe_allow_html=True)
            st.write(f"## Showing {len(recipes)} recipes for **{query}**")

            # Display recipes in card format with 3 columns
            cols = st.columns(3)
            for idx, recipe_data in enumerate(recipes):
                recipe = recipe_data["recipe"]

                # Track selection in session_state
                recipe_key = f"recipe_{idx}"
                if recipe_key not in st.session_state.selected_days:
                    st.session_state.selected_days[recipe_key] = "Day 1"  # Default to Day 1

                with cols[idx % 3]:
                    st.markdown(f"""
                    <div class="recipe-container">
                        <img src="{recipe['image']}" alt="Recipe Image"/>
                        <h4>{recipe['label']}</h4>
                        <p>Calories: {recipe['calories']:.0f}</p>
                        <a href="{recipe['url']}" target="_blank"><button>View Recipe</button></a>
                    </div>
                    """, unsafe_allow_html=True)

                    # Select box for choosing the day (saved in session_state)
                    st.session_state.selected_days[recipe_key] = st.selectbox(
                        f"Choose day for {recipe['label']}", 
                        list(st.session_state.meal_plan.keys()), 
                        key=recipe_key
                    )
                    if st.button(f"Add {recipe['label']} to {st.session_state.selected_days[recipe_key]}", key=f"btn_{idx}"):
                        add_recipe_to_day(st.session_state.selected_days[recipe_key], recipe)

        else:
            st.write(f"No recipes found for '{query}' with the selected filters.")
            st.warning("No recipes found. Try adjusting your search.")
    else:
        st.error(f"API request failed with status code {response.status_code}")
        st.write(response.text)

# Add custom CSS for styling with the new colour palette
st.markdown(f"""
    <style>
    /* Style the sidebar */
    [data-testid="stSidebar"] {{
        background-color: #93B6F2;
    }}
    
    /* Style the search input box */
    .search-input input {{
        border: 2px solid #93B6F2;
        padding: 10px;
        font-size: 16px;
        border-radius: 5px;
        background-color: #F0F4FC;
    }}
    
    /* Style the recipe display */
    .recipe-container {{
        border: 1px solid #e0e0e0;
        padding: 10px;
        border-radius: 8px;
        background-color: white;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
    }}
    
    /* Style the recipe titles */
    .recipe-title {{
        font-size: 16px;
        font-weight: normal;
        color: #333;
        margin-top: 10px;
    }}
    
    /* Style the buttons */
    .recipe-button {{
        display: inline-block;
        border: 1px solid #93B6F2;
        color: white;
        background-color: #93B6F2;
        padding: 5px 10px;
        border-radius: 5px;
        text-decoration: none;
        font-weight: normal;
        font-size: 14px;
    }}
    
    .recipe-button:hover {{
        background-color: #7594D3;
        color: white;
        border: 1px solid #7594D3;
    }}
    </style>
""", unsafe_allow_html=True)
# Display the meal plan in a calendar-like format
st.write("## Your Meal Plan")

cols = st.columns(7)  # Display days in a 7-column format (calendar style)
for idx, (day, meals) in enumerate(st.session_state.meal_plan.items()):
    with cols[idx % 7]:
        st.write(f"### {day}")
        if meals:
            for meal in meals:
                st.write(f"- {meal['label']} ({meal['calories']:.0f} calories)")
        else:
            st.write("No meals added yet.")

# Generate shopping list button
if st.button("Generate Shopping List"):
    shopping_list = {}
    for meals in st.session_state.meal_plan.values():
        for recipe in meals:
            for ingredient in recipe["ingredients"]:
                if ingredient["food"] in shopping_list:
                    shopping_list[ingredient["food"]] += ingredient["quantity"]
                else:
                    shopping_list[ingredient["food"]] = ingredient["quantity"]

    # Display the shopping list
    st.write("## Shopping List")
    for food, quantity in shopping_list.items():
        st.write(f"{food}: {quantity}")

if __name__ == "__main__":
    main()
