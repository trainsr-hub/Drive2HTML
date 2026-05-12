# Tab2_Cloner.py
import streamlit as st
# Import theo đúng yêu cầu đã ghi chú ở đầu file drive_ops.py
import drive_module.drive_ops as drive_ops

def clone_folder_logic(service, source_id, target_parent_id, new_name):
    """
    Hàm đệ quy sử dụng drive_ops để sao chép cấu trúc thư mục.
    """
    # 1. Tạo folder mới
    file_metadata = {
        'name': new_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [target_parent_id]
    }
    new_folder = service.files().create(body=file_metadata, fields='id').execute()
    new_id = new_folder.get('id')

    # 2. Lấy danh sách con của folder nguồn bằng hàm có sẵn trong module
    items = drive_ops.list_folder_contents(source_id)
    
    for item in items:
        # Chỉ clone nếu là folder
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            clone_folder_logic(service, item['id'], new_id, item['name'])
            
    return new_id

def run_tab2():
    """Hàm chính để gọi từ Commander.py"""
    st.subheader("📂 Character Folder Cloner (Tab 2)")

    # Truy cập service đã khởi tạo trong drive_ops
    service = drive_ops.drive_service

    # 1. Nhập Working Folder bằng hàm có sẵn trong module
    working_id = drive_ops.select_working_folder()

    if working_id:
        # 2. Lấy danh sách folder con để làm template (Sort ASC theo name)
        try:
            children = drive_ops.list_folder_contents(working_id)
            # Lọc chỉ lấy folder và sắp xếp theo tên
            templates = sorted(
                [f for f in children if f['mimeType'] == 'application/vnd.google-apps.folder'],
                key=lambda x: x['name']
            )
            
            if not templates:
                st.warning("Thư mục này không chứa folder con nào để làm template.")
            else:
                template_names = [f['name'] for f in templates]
                template_map = {f['name']: f['id'] for f in templates}

                # Sidebar Selector
                selected_tpl = st.sidebar.selectbox("🎯 Chọn Folder Template:", template_names, key="tpl_select")
                source_id = template_map[selected_tpl]

                # 3. Cấu hình số lượng và nút bấm
                st.divider()
                col1, col2 = st.columns([1, 2])
                with col1:
                    num_to_create = st.number_input("Số lượng folder clone:", min_value=1, max_value=5, value=1, key="num_clone")
                
                if st.button(f"🚀 Xác nhận tạo {num_to_create} bản sao cho '{selected_tpl}'"):
                    existing_names = set(template_names)
                    
                    with st.status("Đang thực hiện sao chép...", expanded=True) as status:
                        for i in range(num_to_create):
                            # Logic chống trùng tên
                            count = 1
                            new_name = f"{selected_tpl}_Clone_{count}"
                            while new_name in existing_names:
                                count += 1
                                new_name = f"{selected_tpl}_Clone_{count}"
                            
                            st.write(f"Đang tạo: `{new_name}`...")
                            clone_folder_logic(service, source_id, working_id, new_name)
                            
                            # Cập nhật danh sách để lần loop sau không trùng
                            existing_names.add(new_name)
                        
                        status.update(label="Hoàn tất sao chép!", state="complete", expanded=False)
                    
                    st.balloons()
                    st.success(f"Đã tạo xong {num_to_create} folder mới trong Working Folder.")
                    st.info("Hãy refresh (F5) hoặc đợi vài giây để Drive cập nhật danh sách mới.")

        except Exception as e:
            st.error(f"Lỗi truy xuất dữ liệu: {e}")
    else:
        st.info("Vui lòng dán link Google Drive Folder vào Sidebar để bắt đầu.")