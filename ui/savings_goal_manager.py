from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QProgressBar)
import sqlite3

class SavingsGoalManager(QDialog):
    def __init__(self, user_id):
        super().__init__()
        self.setWindowTitle("Savings Goal Manager")
        self.user_id = user_id

        self.layout = QVBoxLayout()

        self.goal_label = QLabel("Set Annual Savings Goal:")
        self.goal_input = QLineEdit()
        self.goal_input.setPlaceholderText("e.g. 5000")

        self.commit_label = QLabel("Set Monthly Commitment:")
        self.commit_input = QLineEdit()
        self.commit_input.setPlaceholderText("e.g. 300")

        self.set_goal_btn = QPushButton("Save Goal and Commitment")
        self.set_goal_btn.clicked.connect(self.save_goal)

        self.progress_label = QLabel("Progress:")
        self.progress_bar = QProgressBar()

        self.transfer_btn = QPushButton("Transfer Monthly Commitment")
        self.transfer_btn.clicked.connect(self.transfer_commitment)

        self.layout.addWidget(self.goal_label)
        self.layout.addWidget(self.goal_input)
        self.layout.addWidget(self.commit_label)
        self.layout.addWidget(self.commit_input)
        self.layout.addWidget(self.set_goal_btn)
        self.layout.addWidget(self.progress_label)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.transfer_btn)

        self.setLayout(self.layout)
        self.load_progress()

    def save_goal(self):
        goal = self.goal_input.text().strip()
        commit = self.commit_input.text().strip()

        if not goal.isdigit() or not commit.isdigit():
            QMessageBox.warning(self, "Invalid Input", "Goal and Commitment must be numbers.")
            return

        conn = sqlite3.connect("pennywise.db")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS SavingsGoal (
                userID INTEGER PRIMARY KEY,
                annualGoal INTEGER,
                monthlyCommit INTEGER,
                totalSaved INTEGER DEFAULT 0
            )
        """)

        cursor.execute("REPLACE INTO SavingsGoal (userID, annualGoal, monthlyCommit) VALUES (?, ?, ?)",
                       (self.user_id, int(goal), int(commit)))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Saved", "Savings goal and commitment saved.")
        self.load_progress()

    def transfer_commitment(self):
        conn = sqlite3.connect("pennywise.db")
        cursor = conn.cursor()

        cursor.execute("SELECT monthlyCommit, totalSaved FROM SavingsGoal WHERE userID=?", (self.user_id,))
        row = cursor.fetchone()

        if row:
            commit, saved = row
            new_total = saved + commit
            cursor.execute("UPDATE SavingsGoal SET totalSaved=? WHERE userID=?", (new_total, self.user_id))
            conn.commit()
            QMessageBox.information(self, "Transferred", f"{commit} added to savings. Total: {new_total}")
        else:
            QMessageBox.warning(self, "Missing Goal", "Please set a goal and commitment first.")

        conn.close()
        self.load_progress()

    def load_progress(self):
        conn = sqlite3.connect("pennywise.db")
        cursor = conn.cursor()
        cursor.execute("SELECT annualGoal, totalSaved FROM SavingsGoal WHERE userID=?", (self.user_id,))
        row = cursor.fetchone()
        if row:
            goal, saved = row
            progress = int((saved / goal) * 100) if goal > 0 else 0
            self.progress_bar.setValue(progress)
            self.progress_bar.setFormat(f"{saved} / {goal} ({progress}%)")
        conn.close()
