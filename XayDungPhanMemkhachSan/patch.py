import io

with io.open('views/Staff.ui', 'r', encoding='utf-8') as f:
    text = f.read()

# We look for the closing of lbl_current_user
target_unix = """           <item>
            <widget class="QLabel" name="lbl_current_user">
             <property name="styleSheet">
              <string notr="true">color: #6B7896; font-size: 13px; border: none; padding-right: 6px;</string>
             </property>
             <property name="text">
              <string>👤  Staff</string>
             </property>
            </widget>
           </item>
          </layout>"""

target_win = target_unix.replace('\n', '\r\n')

replacement_unix = """           <item>
            <widget class="QLabel" name="lbl_current_user">
             <property name="styleSheet">
              <string notr="true">color: #6B7896; font-size: 13px; border: none; padding-right: 6px;</string>
             </property>
             <property name="text">
              <string>👤  Staff</string>
             </property>
            </widget>
           </item>
           <item>
            <widget class="QPushButton" name="btn_logout">
             <property name="styleSheet">
              <string notr="true">QPushButton {
    background-color: #1A2A4A;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 7px 18px;
    font-size: 13px;
}
QPushButton:hover { background-color: #C9A84C; color: #1A2A4A; }</string>
             </property>
             <property name="text">
              <string>Đăng Xuất</string>
             </property>
            </widget>
           </item>
          </layout>"""

replacement_win = replacement_unix.replace('\n', '\r\n')

if target_win in text:
    text = text.replace(target_win, replacement_win)
    with io.open('views/Staff.ui', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Patched utilizing Windows style newlines.")
elif target_unix in text:
    text = text.replace(target_unix, replacement_unix)
    with io.open('views/Staff.ui', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Patched utilizing Unix style newlines.")
else:
    print("Failed to find target in file.")
