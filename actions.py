from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, List, Dict, Text
import mysql.connector

from dotenv import load_dotenv
from langchain.llms import GooglePalm

# Load environment variables
load_dotenv()

# Initialize the LLM with your API key
llm = GooglePalm(
    google_api_key="YOUR API KEY",
    temperature=0.1,
    max_output_tokens=500
)

# Function to generate SQL query from user input
def generate_sql_query(user_input):
    # Detailed Prompt for SQL Query Generation
    detailed_prompt = f"""
        You are an expert in converting English questions into SQL queries. The SQL database contains a table named tbl_product with the following columns: id, cat_id, subcat_id, pro_qty, theme, style, type, movement, technic, color, gemstone, for_jwll, persnolised, nosering, noseringmegnetic, guage, meterial, length, weight, cmwidth, heightcm, medium, sellingoption, year_of_art, deliver, comission, shipping, terms, cate, spacification, product_highlights, return_policy, deal_summary, location, brand, slug, pro_name, actual_price, offer_price, coupon, vendor, service, organization, user_type, image, discription, status, active, bottom_status, created_date, created_by, updated_date, updated_by, meta_title, meta_keywords, meta_description, dimension_type, length_inch, width_inch, height_inch.

    User's input: "{user_input}"

    Please generate an SQL query that:

    Searches the organization column for the artist's name if mentioned.
    Searches the theme column if a theme is specified.
    Searches the style column if a style is mentioned.
    Searches the material, technic, or color if the user refers to the type of material, technic, or color used.
    Searches the actual_price, offer_price, pro_qty, length, weight, cmwidth, heightcm, length_inch, width_inch, height_inch columns for size or price-related queries.
    Searches the location column if a location is mentioned.
    Adjusts for possible spelling mistakes or variations in case.
    Example Queries:

    For input "Show me the paintings by Ajay Singh", the query should be: SELECT * FROM tbl_product WHERE organization LIKE "Ajay Singh";
    For input "Find artworks related to the 'Modern' theme", the query should be: SELECT * FROM tbl_product WHERE theme LIKE "Modern";
    For input "What are the prices of Ajay Singh's artworks?", the query should be: SELECT actual_price, offer_price FROM tbl_product WHERE organization LIKE "Ajay Singh";
    For input "Show me artworks that are 10 inches in width", the query should be: SELECT * FROM tbl_product WHERE width_inch = 10;
    For input "Find all oil paintings", the query should be: SELECT * FROM tbl_product WHERE technic LIKE "oil".
    Make sure the SQL code does not include ``` at the beginning or end, and avoid using the word 'sql' in the output.
    """
    
    # Generate the SQL query using the LLM
    response = llm(detailed_prompt)
    
    # Extract the SQL query from the response
    sql_query = response.strip()
    
    return sql_query



# # Example usage
# user_input = "Show me all paintings by Ajay Singh"
# sql_query = generate_sql_query(user_input)
# print(f"Generated SQL Query: {sql_query}")


class SearchArtworkByArtist(Action):

    def name(self) -> Text:
        return "action_search_artworks"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get user input
        user_input = tracker.latest_message.get('text')
        print(f"Debug: User input - {user_input}")

        if not user_input:
            dispatcher.utter_message(text="Please provide more details about the artwork.")
            return []

        # Generate the SQL query using LangChain
        sql_query = generate_sql_query(user_input)
        print(f"Generated SQL Query: {sql_query}")

        # Execute the SQL query
        conn = None
        cur = None
        try:
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password='root@175',
                database='ziggu'
            )
            cur = conn.cursor(dictionary=True)
            cur.execute(sql_query)
            artworks = cur.fetchall()

        except mysql.connector.Error as e:
            dispatcher.utter_message(text=f"Database error: {e}")
            return []
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

        # Process and format the results
        if artworks:
            total_artworks = len(artworks)
            response = ""
            for row in artworks:
                response += f"- Artwork name: {row['pro_name']}, Theme: {row['theme']}, Material: {row['meterial']}, Actual Price: {row['actual_price']}, Offer Price: {row['offer_price']}\n"
                response += f"![]({row['image']})\n"

            dispatcher.utter_message(text=f"Found {total_artworks} artworks:\n{response}")
        else:
            dispatcher.utter_message(text=f"Sorry, no artworks matched your criteria.")

        return []


