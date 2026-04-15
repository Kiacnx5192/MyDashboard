st.markdown("<hr style='border:1px dashed #ef4444; margin: 30px 0;'>", unsafe_allow_html=True)
        
        # 🚨 โซนอันตราย: ระบบ Reset ล้างข้อมูลทั้งหมด 🚨
        with st.expander("🚨 โซนอันตราย: ล้างข้อมูลไม้เทรดทั้งหมด (Reset All Data)"):
            st.warning("⚠️ คำเตือน: การกระทำนี้จะลบข้อมูลไม้เทรด 'ทั้งหมด' ตั้งแต่ไม้แรกจนถึงไม้ปัจจุบัน (เหลือไว้แค่หัวตาราง) โปรดตรวจสอบให้แน่ใจก่อนกดนะคะ!")
            
            confirm_text = st.text_input("พิมพ์คำว่า RESET (ตัวพิมพ์ใหญ่) ลงในช่องนี้เพื่อยืนยันการล้างข้อมูล:")
            
            if st.button("🧨 ยืนยันการล้างข้อมูลทั้งหมด", type="primary", disabled=(confirm_text != "RESET")):
                try:
                    gc = get_gspread_client()
                    wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Data8")
                    
                    # สั่งลบข้อมูลตั้งแต่บรรทัดที่ 4 ลงไปจนถึงบรรทัดที่ 1000 (เก็บหัวตาราง 3 บรรทัดแรกไว้)
                    wks.batch_clear(["A4:Q1000"]) 
                    
                    st.success("ล้างข้อมูลทั้งหมดเรียบร้อยแล้วค่ะ! ระบบพร้อมนับ 1 ใหม่แล้ว ✨")
                    st.cache_data.clear()
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")
