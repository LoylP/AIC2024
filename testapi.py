import requests
import json

# Thông tin API
url = "https://eventretrieval.one/api/v2/submit/e3ed921d-af52-45b8-96fc-f86bcc7a39e4"
params = {
    "session": "Furn-nCpr9FLkzgnLDANO84tyjB0cgVK"
}

# Dữ liệu body
body_data = {
    "answerSets": [
        {
            "answers": [
                {
                    "text": "number-string-number"
                }
            ]
        }
    ]
}

# Hàm để nhập dữ liệu từ người dùng
def get_user_input():
    print("Nhập dữ liệu cho trường 'text' (để trống để sử dụng giá trị mặc định):")
    user_input = input().strip()
    if user_input:
        body_data["answerSets"][0]["answers"][0]["text"] = user_input

# Gọi hàm để nhập dữ liệu
get_user_input()

# Gửi yêu cầu POST
try:
    response = requests.post(url, params=params, json=body_data)
    response.raise_for_status()  # Raise an exception for bad status codes
    
    print("Phản hồi từ server:")
    print(json.dumps(response.json(), indent=2))
except requests.exceptions.RequestException as e:
    print(f"Có lỗi xảy ra: {e}")