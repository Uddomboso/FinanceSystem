import sqlite3

from PyQt5.QtWidgets import (QDialog,QVBoxLayout,QLabel,QLineEdit,QPushButton,
                             QColorDialog,QMessageBox,QListWidget,QListWidgetItem,QHBoxLayout,QWidget,QInputDialog)


class CategoryManager(QDialog):
    def __init__(self, user_id):
        super().__init__()
        self.setWindowTitle("Manage Categories")
        self.user_id = user_id

        self.layout = QVBoxLayout()

        self.name_label = QLabel("Category Name:")
        self.name_input = QLineEdit()

        self.color_btn = QPushButton("Choose Color")
        self.color_btn.clicked.connect(self.choose_color)
        self.selected_color = "#FFFFFF"

        self.add_btn = QPushButton("Add Category")
        self.add_btn.clicked.connect(self.add_category)

        self.category_list = QListWidget()

        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.name_input)
        self.layout.addWidget(self.color_btn)
        self.layout.addWidget(self.add_btn)
        self.layout.addWidget(QLabel("Existing Categories:"))
        self.layout.addWidget(self.category_list)

        self.setLayout(self.layout)
        self.load_categories()

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.selected_color = color.name()
            self.color_btn.setStyleSheet(f"background-color: {self.selected_color}")

    def add_category(self):
        name = self.name_input.text().strip()
        color = self.selected_color

        if not name:
            QMessageBox.warning(self, "Error", "Please enter a category name.")
            return

        conn = sqlite3.connect("pennywise.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM categories WHERE category_name=? AND user_id=?", (name, self.user_id))
        if cursor.fetchone():
            QMessageBox.warning(self, "Error", "Category already exists.")
            conn.close()
            return
        cursor.execute("INSERT INTO categories (category_name, color, user_id) VALUES (?, ?, ?)",
                       (name,color,self.user_id))

        conn.commit()
        conn.close()

        self.name_input.clear()
        self.load_categories()
        QMessageBox.information(self, "Success", f"Category '{name}' added.")

    def load_categories(self):
        self.category_list.clear()
        conn = sqlite3.connect("pennywise.db")
        cursor = conn.cursor()
        cursor.execute("SELECT category_id, category_name, color FROM categories WHERE user_id=?",(self.user_id,))
        for category_id,name,color in cursor.fetchall():
            row = QWidget()
            hbox = QHBoxLayout()

            label = QLabel(name)
            label.setStyleSheet(f"background:{color}; padding:5px; border-radius:5px;")

            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda _,cid=category_id: self.edit_category(cid))

            del_btn = QPushButton("Delete")
            del_btn.clicked.connect(lambda _,cid=category_id: self.delete_category(cid))

            hbox.addWidget(label)
            hbox.addWidget(edit_btn)
            hbox.addWidget(del_btn)
            row.setLayout(hbox)

            item = QListWidgetItem()
            item.setSizeHint(row.sizeHint())
            self.category_list.addItem(item)
            self.category_list.setItemWidget(item,row)
        conn.close()

    def edit_category(self,category_id):
        new_name,ok = QInputDialog.getText(self,"Edit Category","Enter new name:")
        if ok and new_name.strip():
            conn = sqlite3.connect("pennywise.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE categories SET category_name=? WHERE category_id=? AND user_id=?",
                           (new_name.strip(),category_id,self.user_id))
            conn.commit()
            conn.close()
            self.load_categories()

    def delete_category(self,category_id):
        reply = QMessageBox.question(self,"Delete","Are you sure?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            conn = sqlite3.connect("pennywise.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM categories WHERE category_id=? AND user_id=?",
                           (category_id,self.user_id))
            conn.commit()
            conn.close()
            self.load_categories()
