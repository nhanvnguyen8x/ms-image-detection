import re
import traceback
from datetime import datetime


question = """what is this receipt about? Return each finding as a {} JSON structured output.
Find these fields especially:
1. receipt_merchant_name
2. receipt_datetime_of_purchase (do your best to obtain in the format of '%Y-%m-%d %H:%M:%S' for python)
3. receipt_unique_id - the most unique identifier of the receipt to indicate it's transaction
4. receipt_total_amount
5. receipt_merchant_address
6. receipt_country (optional) - State the country. This has implications on the currency used, so please check thoroughly for signs it belongs to a certain country especially the address.
7. receipt_ccy (e.g. USD, SGD, VND or other currency)
8. receipt_payment_method - either Cash, Credit Card, PayNow, Zalo etc.
9. category - generalize into either these buckets:["Entertainment", "F&B Expenses", "Fuel/Mileage Expenses", "International Transport Expense", "IT Expenses", "Local Transport Expenses", "Lodging", "Medical", "Office Expense and Supply", "Other Expenses", "Postage & Courier", "Staff Welfare", "Vehicle Expense"].
10. wifi_name - If there are any text relating to SSID or Wifi or network sounding names, state it.
11. wifi_pw - If there are any passwords coming after SSID or Wifi or network names, state it.
"""

def process_total_amount(value_str):
    try:
        if not isinstance(value_str, str):
            # If value_str is not a string, convert it to one
            # This handles cases where value_str might be an integer, float, or other.
            value_str = str(value_str)

        # Remove currency symbols and codes
        number_str = re.sub(r'[^\d.,]', '', value_str)

        # Identify thousands separator (either comma or dot) based on context
        # If there's a dot followed by exactly three digits, assume it's a thousands separator
        if re.search(r'\.\d{3}(?:$|[^0-9])', number_str):
            # Remove thousands separator
            number_str = number_str.replace('.', '')
        else:
            # Remove thousands separator (comma)
            number_str = number_str.replace(',', '')

        # Convert to float
        try:
            return float(number_str)
        except ValueError:
            # Handle the case where the conversion is not possible
            print(f"Could not convert the string '{value_str}' to float.")
            return None
    except:
        traceback.print_exc()
        print("Saw",value_str)
        return None


def process_receipt_datetime(datetime_str):
    try:
        # Define potential date and time formats
        # The following are examples and might need to be adjusted to handle more cases
        date_formats = [
            "%d/%m/%Y %H:%M %p",  # '24/03/2024 11:25 AM'
            "%d-%m-%Y %H:%M:%S",  # '24-03-2024 11:25:00'
            "%Y/%m/%d %H:%M",  # '2024/03/24 11:25'
            "%Y-%m-%d %H:%M:%S",  # '2024-03-01 19:01:33'
            "%Y-%m-%d %I:%M %p",  # '2024-03-22 08:53 AM'
        ]

        # Remove any known non-datetime related text or localization (like 'SA' for AM/PM)
        datetime_str = re.sub(r'\bSA\b', 'AM', datetime_str)
        datetime_str = re.sub(r'\bCH\b', 'PM', datetime_str)

        # Try parsing the string with each format until successful
        for fmt in date_formats:
            try:
                dt = datetime.strptime(datetime_str, fmt)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue

        # If none of the formats work, raise an error or return None
        print(f"Could not parse the datetime string: {datetime_str}")
        return None
    except:
        traceback.print_exc()
        print("Saw",datetime_str)
        return None
