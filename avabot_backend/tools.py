from langchain_core.tools import tool
import requests
from typing import Annotated, List

import time

retrieved_products = {}


def get_retrieved_products(id):
    for user_id in retrieved_products.keys():
        if user_id == id:
            return retrieved_products[user_id]
    
    return []


def _search(endpoint: str, params: dict = None):
    base_url = "https://dummyjson.com/products/"

    url = base_url + endpoint

    try:
        response = requests.get(url, params=params)
        time.sleep(5)
        return response
    except:
        pass


@tool
def get_products_for_display(
    products: Annotated[List[int], "List of product id's to retrieve."]
) -> str:
    """Use this tool to retrieve a product or list of products by their product id's, for display to user in the app. Always use this after you have used the 'search_products' tool.

    To make use of this tool, specify an action as follows:
    Action:
    ```json
    {
    "action": "get_products_for_display",
    "action_input": {
        "products": []
    }
    }
    ```
    Make sure to fill the products list with the list of products id's to retrieve.
    """

    if len(products) == 0:
        return "You didn't provide any product to retrieve."

    successful_retrievals = []

    for product_id in products:
        response = _search(
            str(product_id),
            params={
                "select": "id,title,description,price,discountPercentage,thumbnail"
            },
        )

        if response:
            if response.status_code == 200:
                from flask import session
                
                id = session["agent-id"]
                successful_retrievals.append(response.text)
                
                if id in retrieved_products.keys():
                    retrieved_products[id].append(response.json())
                else:
                    retrieved_products[id] = [response.json()]

    return f"Products retrieval was successful. And will be displayed to user in the app programatically, dont't try to mimick the products display in your final response to the user, as that will be handled in the best way possible by the app. Now go ahead and reply user in the best way possible, bearing in mind that these set of products were sucessfully retrieved: {successful_retrievals}"


def _augument_products_list(products: List[str]) -> List:
    new_search_keywords = []

    for product in products:
        splitted_keywords = product.split(" ")
        if len(splitted_keywords) > 1:
            new_search_keywords += splitted_keywords

    new_search_keywords = set(new_search_keywords)
    return list(new_search_keywords)


@tool
def search_products(
    products: Annotated[List[str], "list of product names to search."]
) -> str:
    """Use this tool to search for a product or a list of products by their names. After using this tool make sure to display to user the products, that align with user's interest using the 'get_products_for_display' tool.

    To make use of this tool, specify an action as follows:
    Action:
    ```json
    {
    "action": "search_products",
    "action_input": {
        "products": []
    }
    }
    ```
    Make sure to fill the products list with the list of products names to search for.
    """

    if len(products) == 0:
        return "You didn't provide any product to look up, please provide a whitespace separated list of products to search."

    products += _augument_products_list(products)
    total_products_retrieved = 0
    results = ""

    for product in products:
        response = _search("search", params={"q": product, "limit": 20})

        if response:
            if response.status_code == 200:
                if response.json()["total"] == 0:
                    continue

                if total_products_retrieved > 50:
                    break

                total_products_retrieved += response.json()["total"]
                results += f" {response.text}"

    if results == "":
        return "We couldn't find any product matching your search request. Maybe you can find similar keywords, to what you provided me with and then call me again with those similar keywords, so i can make another search. Or if not, reply user the best way possible."

    return results
