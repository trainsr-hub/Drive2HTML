import streamlit as st
import drive_module.drive_ops as drive_ops
import yaml
from collections import deque
import time

st.set_page_config(page_title="Visual Drive Renamer Pro", layout="wide")

st.title("🖼️ Drive Graph-based Renamer")

# --- TABS CHO 2 TASK ---
tab1, tab2 = st.tabs(["📤 Task 1: Export Metadata", "🔗 Task 2: Graph-based Rename"])

# --- TASK 1: EXPORT (Yêu cầu có Folder ID) ---
with tab1:
    folder_id = drive_ops.select_working_folder()
    if folder_id:
        images, _ = drive_ops.get_or_cache_data(
            key=f"media_list_{folder_id}",
            loader_func=lambda: drive_ops.get_images_in_folder(folder_id),
            dependencies=folder_id
        )

        if images:
            # Sắp xếp và đếm file
            sorted_images = sorted(images, key=lambda x: x[0].lower())
            total_files = len(sorted_images)
            
            # Hiển thị số lượng file bằng metric cho đẹp
            st.metric(label="Tổng số file ảnh tìm thấy", value=total_files)
            
            # Tạo cấu trúc Linkage_DB
            linkage_db = {"Linkage_DB": {}}
            
            # 1. Bổ sung node mẫu Rank 2 (mặc định)
            default_node_id = "node_1776343517737"
            linkage_db["Linkage_DB"][default_node_id] = {
                "name": "FFF-01-",
                "color": "B",
                "rank": 2,
                "links_to": []
            }
            
            # 2. Thêm các file ảnh Rank 1
            for name, f_id in sorted_images:
                linkage_db["Linkage_DB"][f_id] = {
                    "name": name,
                    "image": f"https://drive.google.com/thumbnail?id={f_id}&sz=s800",
                    "color": "B",
                    "rank": 1,
                    "links_to": []
                }
            
            st.subheader("📋 Linkage_DB Metadata")
            yaml_output = yaml.dump(linkage_db, sort_keys=False, allow_unicode=True)
            full_content = f"---\n{yaml_output}---"
            # Tùy chọn tải file .md xuống
            st.download_button(
                label="📥 Tải file .md về máy",
                data=full_content,
                file_name=f"Linkage_DB_{int(time.time())}.md",
                mime="text/markdown",
                use_container_width=True
            )
            st.divider()
            st.code(full_content, language="yaml")
        else:
            st.warning("Không tìm thấy ảnh nào trong thư mục này.")
    else:
        st.info("Vui lòng nhập link folder ở Sidebar để thực hiện Task 1.")

# --- TASK 2: GRAPH RENAME (Hoạt động độc lập hoàn toàn) ---
with tab2:
    st.subheader("🔗 Tính toán Prefix dựa trên đồ thị")
    
    input_method = st.radio("Phương thức nhập:", ["Tải file .md", "Dán YAML"], horizontal=True)
    yaml_content = ""
    
    if input_method == "Tải file .md":
        uploaded_file = st.file_uploader("Upload file .md để xử lý đổi tên", type=["md", "yaml"])
        if uploaded_file:
            yaml_content = uploaded_file.getvalue().decode("utf-8")
    else:
        yaml_content = st.text_area("Dán YAML tại đây:", height=300)

    if st.button("🔍 Kiểm tra cấu trúc đổi tên", use_container_width=True):
        if yaml_content:
            try:
                clean_yaml = yaml_content.strip()
                if "---" in clean_yaml:
                    parts = clean_yaml.split("---")
                    clean_yaml = parts[1] if len(parts) > 1 else parts[0]
                
                data = yaml.safe_load(clean_yaml)
                db = data.get("Linkage_DB", {})
                
                roots = {k: v for k, v in db.items() if v.get("rank") == 2}
                rename_tasks = []
                
                for root_id, root_info in roots.items():
                    prefix_name = root_info.get("name")
                    queue = deque()
                    for link_id in root_info.get("links_to", []):
                        queue.append((link_id, 1))
                    
                    visited = set()
                    while queue:
                        curr_id, dist = queue.popleft()
                        if curr_id in visited or curr_id not in db:
                            continue
                        
                        visited.add(curr_id)
                        node = db[curr_id]
                        if node.get("rank") == 1:
                            old_name = node.get("name")
                            new_name = f"{prefix_name}{dist:02d}_{old_name}"
                            rename_tasks.append((curr_id, old_name, new_name))
                        
                        for next_id in node.get("links_to", []):
                            if next_id not in visited:
                                queue.append((next_id, dist + 1))
                
                if rename_tasks:
                    st.success(f"Tìm thấy {len(rename_tasks)} file nằm trong chuỗi liên kết.")
                    st.session_state['tasks_task2'] = rename_tasks
                    with st.expander("Xem chi tiết danh sách đổi tên", expanded=True):
                        for fid, old, new in rename_tasks:
                            st.text(f"🔹 {old} ➔ {new}")
                else:
                    st.warning("Không tìm thấy chuỗi liên kết nào từ các node Rank 2.")
            except Exception as e:
                st.error(f"Lỗi: {e}")

    if 'tasks_task2' in st.session_state:
        if st.button("🔥 XÁC NHẬN ĐỔI TÊN HÀNG LOẠT TRÊN DRIVE", type="primary", use_container_width=True):
            success = 0
            progress_bar = st.progress(0)
            for i, (fid, _, new) in enumerate(st.session_state['tasks_task2']):
                if drive_ops.rename_file(fid, new):
                    success += 1
                progress_bar.progress((i + 1) / len(st.session_state['tasks_task2']))
            
            st.success(f"Đã cập nhật thành công {success} file!")
            del st.session_state['tasks_task2']