#a.py

import streamlit as st
import re
from PIL import Image
import requests
from io import BytesIO
from streamlit_cropper import st_cropper
import numpy as np
import drive_module.drive_ops as drive_ops
import cv2
import tempfile

def get_video_size_from_drive(file_id: str):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"

    # tải về file tạm
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        r = requests.get(url, stream=True)
        for chunk in r.iter_content(chunk_size=8192):
            tmp.write(chunk)
        tmp_path = tmp.name

    # đọc metadata bằng cv2
    cap = cv2.VideoCapture(tmp_path)
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return width, height, frame_count

def get_image_size_from_drive(file_id: str):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    r = requests.get(url)  # không dùng stream=True
    r.raise_for_status()
    img = Image.open(BytesIO(r.content))
    return img.width, img.height, 1


def get_file_size(file_id: str, is_video: bool):
    if is_video:
        return get_video_size_from_drive(file_id)
    else:
        return get_image_size_from_drive(file_id)

if "file_name_om" not in st.session_state:
    st.session_state.file_name_om = ""

# Hàm để reset input sau khi tải
def reset_filename():
    st.session_state.file_name_om = ""

    
def get_largest_crop_fit(img_width, img_height, aspect_ratio):
    """
    Tìm khung crop lớn nhất với tỉ lệ aspect_ratio (w/h),
    sao cho không vượt ra ngoài ảnh và ít nhất 1 chiều đạt max (rộng hoặc cao).
    Trả về: crop_width, crop_height, (min_cx, max_cx, min_cy, max_cy)
    """
    a, b = aspect_ratio
    crop_width_by_height = int(img_height * a / b)

    if crop_width_by_height <= img_width:
        # Chiều cao chiếm tối đa
        crop_width = crop_width_by_height
        crop_height = img_height
    else:
        # Chiều rộng chiếm tối đa
        crop_width = img_width
        crop_height = int(img_width * b / a)

    # Giới hạn tâm khung để khung không vượt biên
    min_cx = crop_width // 2
    max_cx = img_width - crop_width // 2
    min_cy = crop_height // 2
    max_cy = img_height - crop_height // 2

    center_range = (min_cx, max_cx, min_cy, max_cy)

    return crop_width, crop_height, center_range

def get_crop_center(rect):
    left = rect[0]
    top = rect[1]
    width = rect[2]
    height = rect[3]

    center_x = left + width / 2
    center_y = top + height / 2

    return center_x, center_y

def extract_file_id(link):
    """
    Trích xuất file_id từ URL Google Drive
    """
    patterns = [
        r'drive\.google\.com\/file\/d\/([a-zA-Z0-9_-]+)',
        r'id=([a-zA-Z0-9_-]+)',
        r'drive\.google\.com\/open\?id=([a-zA-Z0-9_-]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, link)
        if match:
            return match.group(1)
    return None

with st.sidebar:
    folder_id = drive_ops.select_working_folder()

    selected_image_id = None
    image_list = []
    video_list = []
    if folder_id:
        image_list_unsort, video_list_unsort = drive_ops.get_images_in_folder(folder_id)  # List of tuples: (name, file_id)
        image_list_none= sorted(image_list_unsort, key=lambda x: x[0])
        image_list = st.multiselect("Các ảnh:", options=image_list_none, default= image_list_none, key= "linksheeh")
        video_list_none = sorted(video_list_unsort, key=lambda x: x[0])
        video_list = st.multiselect("Các video:", options=video_list_none, default= video_list_none, key= "linkshevideo") 
# Tabs
tab1, tab2 = st.tabs(["Drive Link", "Crop Image"])
with tab1:
    st.title("Google Drive Image Link Formatter")
    video_mode = st.sidebar.checkbox("Video Mode?", key="Video_modeLL")
    # Load selected file_id from sidebar (if any)
    mul_link = []
    if image_list or video_list: 
        st.markdown("### ✅ Ảnh xem trước:")
        cols = st.columns(3)

        for i, image in enumerate(image_list):
            file_id = image[1]
            original_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            img_width_, img_height_, Blue = get_file_size(file_id, video_mode)
            thumbnail_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=s{max(img_width_, img_height_)}"
            html_code = f"<img src='{thumbnail_url}' alt='{image[0]}' style='width:100%; border-radius:6px;'>"
            markdown_code = f'![Preview]({thumbnail_url})'
            if Blue == 1 or Blue < 0:
                with cols[i % 3]:
                    st.markdown(html_code, unsafe_allow_html=True)
                    st.code(thumbnail_url)
                mul_link.append(f"- {thumbnail_url}")

        for i, video in enumerate(video_list):
            file_id = video[1]
            video_link = f"<iframe src='https://drive.google.com/file/d/{file_id}/preview' width='1024' height='576' allow='autoplay' allowfullscreen webkitallowfullscreen mozallowfullscreen></iframe>"
            st.markdown('### 📋 Video:')
            st.markdown(video_link, unsafe_allow_html=True)
            st.code(video_link)
            st.sidebar.markdown("Bìa Video:")
            mul_link.append(f"{video_link}")



        st.sidebar.code("\n".join(mul_link))
    else:
        default_link = ""
        drive_link = st.sidebar.text_input("Nhập link ảnh từ Google Drive:", value=default_link)

        if drive_link:
            file_id = extract_file_id(drive_link)
            if file_id:
                original_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                img_width_, img_height_, Blue = get_file_size(file_id, video_mode)
                thumbnail_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=s{max(img_width_, img_height_)}"
                html_code = f"<img src='{thumbnail_url}' alt='Preview'>"
                markdown_code = f'![Preview]({thumbnail_url})'
                if Blue == 1 or Blue < 0:
                    st.markdown("### ✅ Ảnh xem trước:")
                    st.markdown(html_code, unsafe_allow_html=True)

                    st.markdown("### URL Ảnh:")
                    st.code(thumbnail_url)
                    st.markdown("### 📋 HTML:")
                    st.code(html_code, language="html")
                    st.markdown("### 📋 Markdown:")
                    st.code(markdown_code, language="markdown")
                else:
                    video_link = f"""
                        <style>
                        .embed-container {{ position: relative; width: 100%; padding-bottom: 56.25%; height: 0; overflow: hidden; }}
                        .embed-container iframe, .embed-container video {{ position: absolute; top:0; left:0; width:100%; height:100%; }}
                        </style>

                        <div class="embed-container">
                        <iframe src="https://drive.google.com/file/d/{file_id}/preview" frameborder="0" allowfullscreen></iframe>
                        </div>
                    """
                    st.markdown('### 📋 Video:')
                    st.markdown(video_link, unsafe_allow_html=True)
                    st.code(video_link)
                    st.sidebar.markdown("Bìa Video:")
                st.sidebar.code(thumbnail_url)
            else:
                st.error("❌ Không thể trích xuất file_id từ link đã nhập.")




with tab2:
    demo_url = st.text_input("Dán URL ảnh vào đây:", value="")

    return_type = st.checkbox("Chế Độ Auto?", value=True)
    ratio_choice = st.selectbox("Chọn tỉ lệ crop:", ["3:2", "2:3", "1:1", "4:3", "16:9", "3:4", "9:16", "1:1.4"])
    aspect_dict = {
        "1:1": (1, 1),
        "16:9": (16, 9),
        "4:3": (4, 3),
        "3:4": (3, 4),
        "2:3": (2, 3),
        "9:16": (9, 16),
        "3:2": (3,2),
        "1:1.4": (10,14)
    }
    aspect_ratio = aspect_dict[ratio_choice]
    if demo_url and not drive_link:
        response = requests.get(demo_url)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            
        img_width, img_height = img.size
        raw_image = np.asarray(img).astype('uint8')
        rect = st_cropper(
            img,
            realtime_update=True,
            box_color="#0000FF",
            aspect_ratio=aspect_ratio,
            return_type="box",
            stroke_width=1
        )
        left, top, width, height = tuple(map(int, rect.values()))

        if return_type:
            crop_width, crop_height, center_range = get_largest_crop_fit(img_width, img_height, aspect_ratio)
            center = get_crop_center(tuple(map(int, rect.values())))

            clamped_x = max(center_range[0], min(center[0], center_range[1]))
            clamped_y = max(center_range[2], min(center[1], center_range[3]))
            crop_left = int(clamped_x - crop_width / 2)
            crop_top = int(clamped_y - crop_height / 2)

            # Cắt ảnh theo đúng rect đã chọn
            cropped_np = raw_image[crop_top:crop_top + crop_height, crop_left:crop_left + crop_width]
        else:
            cropped_np = raw_image[top:top + height, left:left + width]

        cropped_img = Image.fromarray(cropped_np)
        st.write("Preview")
        st.image(cropped_img)
        # Save the cropped image to a BytesIO buffer in PNG format
        buf = BytesIO()
        cropped_img.save(buf, format="PNG")
        buf.seek(0)

        st.text_input("Tên ảnh khi tải xuống:", key="file_name_om")

        if st.session_state.file_name_om:
            file_name = f"{st.session_state.file_name_om}.png"
            st.download_button(
                label="Download Cropped Image",
                data=buf,
                file_name=file_name,
                mime="image/png",
                on_click=reset_filename  # Reset sau khi tải
            )
