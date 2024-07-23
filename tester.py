import re
def extract_session_id(session_str:str):
    match=re.search(r"/sessions/(.*?)/contexts/", session_str)
    if match:
        extracted_string=match.group(1)
        return extracted_string
    return ""
def get_str_from_food_dict(food_dict:dict):
    return ", ".join([f"{int(value)} {key}" for key, value in food_dict.items()])
if __name__ == "__main__":
    print(extract_session_id(" projects/ak-chatbot-hvvs/agent/sessions/ee1a0332-ed32-e249-7a16-c23211704531/contexts/ongoing-order"))
