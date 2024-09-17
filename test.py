import os

keyframe_base_path = "/home/nguyenhoangphuc-22521129/AIC2024/static/keyframes_preprocess"

def serve_images_around(filename: str):
    folder_path = os.path.join(keyframe_base_path, os.path.dirname(filename))  
    if not os.path.isdir(folder_path):
        print("Folder not found")
        return None

    all_files = sorted(os.listdir(folder_path))
    
    try:
        index = all_files.index(os.path.basename(filename)) 
    except ValueError:
        print("Image not found")
        return None

    start_index = max(0, index - 5)
    end_index = min(len(all_files), index + 6)  
    surrounding_files = all_files[start_index:end_index]

    for img in surrounding_files:
        file_path = os.path.join(folder_path, img)
        if os.path.isfile(file_path):
            print(f"Image: {file_path}")  

# Ví dụ sử dụng
filename = "Videos_L09/L09_V015/17371.jpg"
serve_images_around(filename)
