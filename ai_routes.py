from flask import Blueprint, render_template, request, jsonify, g
import google.generativeai as genai
import os
from models import db, items, cart 
from functions import calculate_total_price 

ai_bp = Blueprint('ai', __name__)

GENAI_API_KEY = 'AIzaSyDZ0BGY6OMHsU9T1bXxz4h2cl_m9-54zJc'

if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')
else:
    print("WARNING: GENAI_API_KEY not set.")
    model = None

def resolve_year_key(input_val, valid_keys):
    if not input_val:
        return None
    
    clean_input = input_val.strip().lower()
    
    month_map = {
        "january": "jan", "february": "feb", "march": "mar", "april": "apr",
        "may": "may", "june": "jun", "july": "jul", "august": "aug",
        "september": "sep", "october": "oct", "november": "nov", "december": "dec"
    }

    for key in valid_keys:
        clean_key = key.lower()
        
        if clean_input == clean_key:
            return key
            
        for full_month, short_month in month_map.items():
            if full_month in clean_input:
                normalized_input = clean_input.replace(full_month, short_month)
                if normalized_input == clean_key:
                    return key
                    
        parts = clean_key.split() 
        if len(parts) > 1:
            db_year = parts[0]
            db_month = parts[1] 
            if db_year in clean_input and db_month in clean_input:
                return key

    return None

@ai_bp.route("/AI")
def ai_interface():
    return render_template("ai.html")

@ai_bp.route("/api/chat", methods=["POST"])
def chat_api():
    try:
        if not model:
            return jsonify({'error': 'AI API Key missing on server.'}), 500

        data = request.json
        user_message = data.get('message')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        user_context_name = "Guest"
        is_logged_in = False
        if g.user:
            user_context_name = g.user.name
            is_logged_in = True

        item_map = {} 
        inventory_context = "CURRENT SHOP INVENTORY:\n"
        
        try:
            all_items = db.session.execute(db.select(items)).scalars().all()
            
            for item in all_items:
                item_map[item.name.lower()] = item.id
                
                if item.years_available:
                    exact_years = list(item.years_available.keys())
                    exact_years.sort()
                    
                    inventory_context += (
                        f"- Item: '{item.name}'\n"
                        f"  * Years: {exact_years}\n"
                    )
                else:
                    inventory_context += f"- Item: '{item.name}' (Out of Stock)\n"

        except Exception as db_e:
            print(f"DB Error in AI: {db_e}")
            inventory_context = "Inventory database is offline."

        system_instruction = (
            f"You are 'Genius AI', speaking to: {user_context_name}.\n"
            "SCOPE: Selling Edexcel papers. You cannot checkout, only add to cart.\n\n"
            
            f"{inventory_context}\n\n"
            
            "--- PRICING ---\n"
            "Formula: (Total Pages * 5) + 400 + CoverCost\n"
            "Cover Costs: Normal(200), Custom(500), Minimalistic(80)\n\n"

            "--- ADD TO CART PROTOCOL ---\n"
            f"User Logged In: {is_logged_in}\n"
            "1. IF NOT LOGGED IN: Refuse to add to cart.\n"
            "2. IF LOGGED IN: If user confirms to buy, output a HIDDEN COMMAND.\n"
            "   Format: ||ADD_CART:ItemName|StartYear|EndYear|CoverType||\n\n"
            "   Example: ||ADD_CART:Pure Maths 1|2019 Jan|2020 Oct|Normal||\n"
        )
        
        full_prompt = f"{system_instruction}\n\nUser Question: {user_message}"
        
        response = model.generate_content(full_prompt)
        ai_text = response.text

        if "||ADD_CART:" in ai_text and is_logged_in:
            try:
                start_tag = "||ADD_CART:"
                end_tag = "||"
                command_str = ai_text.split(start_tag)[1].split(end_tag)[0]
                
                parts = command_str.split('|')
                if len(parts) >= 4:
                    raw_name = parts[0].strip()
                    raw_start = parts[1].strip()
                    raw_end = parts[2].strip()
                    design = parts[3].strip()

                    print(f"AI RAW: Name: {raw_name}, Start: {raw_start}, End: {raw_end}")

                    target_id = item_map.get(raw_name.lower())

                    if target_id:
                        item_obj = db.session.get(items, target_id)
                        years_list = sorted(list(item_obj.years_available.keys()))
                        
                        start_year = resolve_year_key(raw_start, years_list)
                        end_year = resolve_year_key(raw_end, years_list)

                        if start_year and end_year:
                            s_idx = years_list.index(start_year)
                            e_idx = years_list.index(end_year)
                            
                            if s_idx > e_idx: s_idx, e_idx = e_idx, s_idx
                            
                            selected_years = years_list[s_idx : e_idx+1]
                            final_price = calculate_total_price(item_obj, design, selected_years)

                            new_cart_item = cart(
                                user_id=g.user.id,
                                original_item_id=item_obj.id,
                                name=item_obj.name,
                                img=item_obj.img,
                                years_available=item_obj.years_available,
                                selected_years=selected_years,
                                design_type=design,
                                price=final_price
                            )
                            db.session.add(new_cart_item)
                            db.session.commit()

                            ai_text = ai_text.split("||ADD_CART")[0] 
                            ai_text += f"\n\n[SYSTEM]: ✅ Added **{item_obj.name}** ({start_year} - {end_year}) to cart."
                        else:
                            print(f"MATCH FAILED. DB: {years_list}, AI Sent: {raw_start}, {raw_end}")
                            ai_text = ai_text.split("||ADD_CART")[0]
                            ai_text += f"\n\n[SYSTEM ERROR]: Could not match years '{raw_start}' or '{raw_end}' to database."
                    else:
                        ai_text = ai_text.split("||ADD_CART")[0]
                        ai_text += "\n\n[SYSTEM ERROR]: Item not found."

            except Exception as e:
                print(f"Cart Add Error: {e}")
                ai_text = ai_text.split("||ADD_CART")[0]
                ai_text += "\n\n[SYSTEM ERROR]: Processing failed."

        return jsonify({'response': ai_text})

    except Exception as e:
        print(f"AI CRITICAL ERROR: {e}")
        return jsonify({'error': f'System Error: {e}'}), 500