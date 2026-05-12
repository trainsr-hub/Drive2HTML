# Tab1_Drive.py
import streamlit as st
import yaml
import re
# Import theo đúng yêu cầu đã ghi chú ở đầu file drive_ops.py
import drive_module.drive_ops as drive_ops

def slugify_name(name):
    """Thay thế kí tự đặc biệt thành '_'"""
    return re.sub(r'[^a-zA-Z0-9]', '_', name)

def transform_to_custom_structure(node):
    """
    Chuyển đổi sang cấu trúc custom với các logic mới:
    - Sort alphabet cho children.
    - Bỏ qua Folder nếu không có children.
    """
    # Trường hợp là Folder (có children)
    if node.get("children") is not None:
        # Đệ quy xử lý các con trước
        formatted_children = []
        for child in node["children"]:
            transformed = transform_to_custom_structure(child)
            # Chỉ add nếu transformed không phải None (loại bỏ folder rỗng)
            if transformed is not None:
                formatted_children.append(transformed)
        
        # --- LOGIC: Bỏ qua Folder không có children ---
        if not formatted_children:
            return None
            
        # --- LOGIC: Sort alphabet ASC ---
        # Vì folder trả về dict {key: list}, file trả về str, ta cần logic sort cẩn thận
        def get_sort_key(item):
            if isinstance(item, dict):
                return list(item.keys())[0].lower()
            return str(item).lower()

        formatted_children.sort(key=get_sort_key)
        
        folder_key = slugify_name(node["name"])
        return {folder_key: formatted_children}
    
    # Trường hợp là File
    else:
        file_id = node.get("id")
        return f"https://drive.google.com/thumbnail?id={file_id}&sz=s1648"

def build_nested_tree(items, root_id):
    """Xây dựng cây thư mục từ list phẳng"""
    nodes = {root_id: {"name": "Root Folder", "children": []}}
    for item in items:
        nodes[item['id']] = {
            "name": item['name'],
            "id": item['id'],
            "mimeType": item['mimeType'],
            "children": [] if item['mimeType'] == "application/vnd.google-apps.folder" else None
        }
    for item in items:
        parent_id = item.get('parents', [None])[0]
        if parent_id in nodes:
            node_data = nodes[item['id']]
            if nodes[parent_id]["children"] is not None:
                nodes[parent_id]["children"].append(node_data)
    return nodes[root_id]

def run_tab1():
    """Hàm chính để gọi từ Commander.py"""
    st.subheader("📂 Drive Thumbnail Link to YAML (Tab 1)")
    
    # Input link folder nằm ở sidebar chung hoặc tại Tab này
    folder_url = st.text_input("🔗 Nhập link thư mục Google Drive", key="tab1_url")

    if folder_url:
        folder_id = drive_ops.extract_folder_id_from_url(folder_url)
        if folder_id:
            try:
                with st.spinner("Đang truy xuất cấu trúc..."):
                    flat_items = drive_ops.list_folder_contents_recursive(folder_id)
                
                base_tree = build_nested_tree(flat_items, folder_id)
                
                # --- Xử lý danh sách con của Root ---
                root_children = []
                for child in base_tree["children"]:
                    transformed = transform_to_custom_structure(child)
                    if transformed is not None:
                        root_children.append(transformed)
                
                # Sort alphabet cho cấp cao nhất (Root)
                def get_sort_key(item):
                    if isinstance(item, dict):
                        return list(item.keys())[0].lower()
                    return str(item).lower()
                
                root_children.sort(key=get_sort_key)

                custom_data = {
                    "Eva_Display_Ecstasy": root_children
                }

                yaml_output = yaml.dump(custom_data, indent=2, allow_unicode=True, sort_keys=False)
                st.code(yaml_output, language='yaml')
            except Exception as e:
                st.error(f"Lỗi: {e}")
        else:
            st.error("Link Drive không hợp lệ.")
