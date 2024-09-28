import json

file_paths = [
    '/home/phuc/Dev/AIC2024/static/ocr_filter_part1.json',
    '/home/phuc/Dev/AIC2024/static/ocr_filter_part2.json',
    '/home/phuc/Dev/AIC2024/static/ocr_filter.json'
]

# Danh sách để lưu trữ dữ liệu từ các file
combined_data = []

# Đọc và gộp dữ liệu từ các file
for file_path in file_paths:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        combined_data.extend(data)  # Giả sử mỗi file chứa một danh sách

# Ghi dữ liệu gộp vào file mới
with open('/home/phuc/Dev/AIC2024/static/ocr_filter_new.json', 'w', encoding='utf-8') as f:
    json.dump(combined_data, f, ensure_ascii=False, indent=4)