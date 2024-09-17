import streamlit as st
import requests
import json

# API credentials from secrets.toml
SPOONACULAR_API_KEY = st.secrets["api"]["SPOONACULAR_API_KEY"]
EDAMAM_APP_ID = st.secrets["api"]["EDAMAM_APP_ID"]
EDAMAM_API_KEY = st.secrets["api"]["EDAMAM_API_KEY"]

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

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_from_edamam(query, diet=None):
    url = "https://api.edamam.com/search"
    params = {
        'q': query,
        'app_id': EDAMAM_APP_ID,
        'app_key': EDAMAM_API_KEY,
        'to': 80  # Request 80 results
    }
    if diet:
        params['diet'] = diet

    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get('hits', [])
    return None

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
    st.sidebar.header("Filters")
    
    # Move search input to sidebar
    query = st.sidebar.text_input("Search here...", "", key="search", label_visibility="visible", placeholder="e.g., vegan casserole")
    
    diet = st.sidebar.selectbox("Dietary Restrictions", [None, "vegetarian", "vegan", "gluten free", "paleo", "ketogenic"], key="diet")
    time = st.sidebar.number_input("Max Preparation Time (minutes)", min_value=30, max_value=120, step=10, key="time")
    calories = st.sidebar.number_input("Max Calories", min_value=300, max_value=1500, step=100, key="calories")

    # Fetch recipes and display results
    if st.sidebar.button("Search"):
        recipes = search_recipes(query, diet=diet, time=time, calories=calories)
        
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

        else:
            st.write(f"No recipes found for '{query}' with the selected filters.")

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

if __name__ == "__main__":
    main()

