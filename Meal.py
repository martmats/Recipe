import streamlit as st
import requests

# Load secrets for API keys
APP_ID = st.secrets["app_id"]
APP_KEY = st.secrets["app_key"]


# Function to fetch meal plans
def get_meal_plan(meal_type, diet_label, meals_per_day):
    url = f"https://api.edamam.com/api/meal-planner/v1/{APP_ID}/select"
    
    # Define a meal plan structure based on meals per day
    plan = {
        "sections": {
            "Breakfast": {},  # Breakfast section
            "Lunch": {  # Lunch section
                "sections": {
                    "Starter": {},
                    "Main": {},
                    "Dessert": {}
                }
            },
            "Dinner": {  # Dinner section
                "sections": {
                    "Main": {},
                    "Dessert": {}
                }
            }
        }
    }

    # Prepare the payload with number of days and meal plan
    payload = {
        "size": meals_per_day,  # Number of days to plan for
        "plan": plan
    }

    # Only include diet label if it's not "No diet"
    if diet_label != "No diet":
        payload["plan"]["accept"] = {"all": [{"diet": [diet_label]}]}  # Add dietary filter

    # Make the API request
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error: {response.status_code} - {response.text}")
        return None

# Sidebar filters
st.sidebar.header("Filter Meals")
meal_type = st.sidebar.selectbox("Select Meal Type", ["Breakfast", "Lunch", "Dinner"])
diet_label = st.sidebar.selectbox("Diet Type", ["No diet", "Vegan", "Vegetarian", "Keto", "Paleo"])
meals_per_day = st.sidebar.number_input("Meals per Day", min_value=1, max_value=7, value=3)

# Button to generate meal plan
if st.sidebar.button("Generate Meal Plan"):
    meal_plan = get_meal_plan(meal_type, diet_label, meals_per_day)
    
    if meal_plan:  # Check if meal plan exists
        st.write(f"### {meal_type} Recipes")
        
        # Check if 'selection' key is in the response
        if 'selection' in meal_plan:
            for day, selection in enumerate(meal_plan['selection']):
                st.write(f"#### Day {day + 1}")
                cols = st.columns(3)  # Display 3 recipes per row
                for meal_section, section in selection['sections'].items():
                    if 'assigned' in section:  # Check if a meal is assigned
                        meal = section['assigned']
                        with cols[day % 3]:
                            st.write(f"**{meal_section}**")
                            st.image(f"https://via.placeholder.com/150?text={meal_section}", use_column_width=True)
                            st.write(f"Calories: {section['fit']['ENERC_KCAL']['min']} kcal")
                            st.write(f"[View Recipe]({meal})")
        else:
            st.warning("No meals found in the response.")
    else:
        st.error("Failed to generate meal plan. Please check your inputs and try again.")

# Shopping list generation
def generate_shopping_list(selected_meals):
    url = f"https://api.edamam.com/api/meal-planner/v1/{APP_ID}/shopping-list"
    payload = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "entries": selected_meals  # Add the selected meal URIs here
    }
    response = requests.post(url, json=payload)
    return response.json()

# Add functionality to generate shopping list (optional)
if st.button("Generate Shopping List"):
    if meal_plan and 'selection' in meal_plan:
        selected_meals = []  # Collect the meal URIs for the shopping list
        for day, selection in enumerate(meal_plan['selection']):
            for meal_section, section in selection['sections'].items():
                if 'assigned' in section:
                    selected_meals.append(section['assigned'])

        shopping_list = generate_shopping_list(selected_meals)
        st.write("### Shopping List")
        for item in shopping_list['entries']:
            st.write(f"- {item['food']}: {item['quantities'][0]['quantity']} {item['quantities'][0]['measure']}")
    else:
        st.error("Please generate a meal plan first.")
