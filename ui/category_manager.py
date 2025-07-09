from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
                             QColorDialog, QMessageBox, QListWidget, QListWidgetItem, QHBoxLayout)
import sqlite3

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

        cursor.execute("SELECT * FROM Category WHERE categoryName=? AND userID=?", (name, self.user_id))
        if cursor.fetchone():
            QMessageBox.warning(self, "Error", "Category already exists.")
            conn.close()
            return

        cursor.execute("INSERT INTO Category (categoryName, color, userID) VALUES (?, ?, ?)",
                       (name, color, self.user_id))
        conn.commit()
        conn.close()

        self.name_input.clear()
        self.load_categories()
        QMessageBox.information(self, "Success", f"Category '{name}' added.")

    def load_categories(self):
        self.category_list.clear()
        conn = sqlite3.connect("pennywise.db")
        cursor = conn.cursor()
        cursor.execute("SELECT categoryName, color FROM Category WHERE userID=?", (self.user_id,))
        for name, color in cursor.fetchall():
            item = QListWidgetItem(name)
            item.setBackgroundColor(color)
            self.category_list.addItem(item)
        conn.close()
