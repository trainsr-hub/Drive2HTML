# Commander.py
import streamlit as st
from Tab1_Drive import run_tab1
from Tab2_Cloner import run_tab2  # Import thêm Tab 2

def main():
    st.set_page_config(page_title="Commander Dashboard", layout="wide")
    st.title("🎮 Commander Control Center")

    # Cập nhật danh sách Tab
    tab1, tab2, tab3 = st.tabs(["📁 Drive Explorer", "👯 Folder Cloner", "📊 Analytics"])

    with tab1:
        run_tab1()

    with tab2:
        # Gọi script Cloner vào Tab 2
        run_tab2()

    with tab3:
        st.write("Nội dung Analytics...")

if __name__ == "__main__":
    main()
