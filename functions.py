def calculate_total_price(item_obj, design_type, selected_years):
    """
    Calculates the total price of an item based on selected years (total pages) and design type.
    
    Args:
        item_obj (items): The SQLAlchemy items object containing years_available (dict).
        design_type (str): The cover type selected ("normal", "custom", etc.).
        selected_years (list): A list of year strings selected by the user.
        
    Returns:
        float: The calculated total price.
    """
    
    # item_obj.years_available is the dictionary: {'year': page_count, ...}
    available_years_data = item_obj.years_available

    total_pages = 0

    # 1. Calculate total pages
    for year in selected_years:
        # Use .get(year, 0) to safely retrieve page count, defaulting to 0 if the year key is missing
        page_count = available_years_data.get(year)
        
        # Defensive check for None (addresses the previous TypeError)
        if page_count is None:
            # You can raise an error here or skip the year. Skipping is safer.
            print(f"Warning: Page count for year {year} is missing in available data. Skipping.")
            continue
            
        if not isinstance(page_count, int):
            # Ensure page_count is an integer before adding it
            try:
                page_count = int(page_count)
            except ValueError:
                print(f"Error: Page count for year {year} is not a valid number: {page_count}. Skipping.")
                continue

        total_pages += page_count


    # 2. Define base costs
    base_cost = {
        "normal": 200,
        "custom": 500,
        "minimalistic": 80
    }

    # 3. Determine design cost
    # Convert design_type to lowercase to make the lookup case-insensitive
    design_type_lower = design_type.lower()
    
    # If the design type is not recognized, default to "normal" cost
    design_cost = base_cost.get(design_type_lower, base_cost["normal"]) 

    # 4. Calculate final price
    price_per_page = 5.0
    binding_price = 400.0
    
    total_price = (total_pages * price_per_page) + design_cost + binding_price

    # Return the total price as a float
    return total_price

# The following functions were commented out in your original code. 
# They are not needed if you are using Flask-SQLAlchemy for database operations.

# def add_item(id, name, img, design_type,years_available):
#     items.append(
#         {
#             "id": len(cart) + 1,
#             "name": name,
#             "img": img,
#             "design_type": design_type,
#             "selected_years": [],
#             "years_available": years_available
#         }
#     )

# def delete_item(id):
#     pass

# def update_item():
#     pass