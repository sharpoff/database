import os
import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtSql import *
from PyQt6 import QtCore

default_db_name = 'database_new'
default_db_user = 'postgres'
default_db_password = 'secret'
default_db_host = 'localhost'
default_db_port = 5432

default_username = 'bocha'
default_password = '123'

database: QSqlDatabase = None
is_admin = False

class CustomQSqlTableModel(QSqlTableModel):
    def flags(self, index) -> QtCore.Qt.ItemFlag:
        if is_admin:
            return super().flags(index) | QtCore.Qt.ItemFlag.ItemIsEditable
        else:
            return super().flags(index) & ~QtCore.Qt.ItemFlag.ItemIsEditable

class DatabaseTableWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Таблица продуктов")
        self.setGeometry(200, 200, 900, 550)

        self.model: CustomQSqlTableModel = CustomQSqlTableModel(self, database)
        self.model.setTable("product")
        self.model.select()

        self.view = QTableView(self)
        self.view.setModel(self.model)
        self.view.resizeColumnsToContents()

        search_layout = QHBoxLayout()
        search_label = QLabel("Search by product name:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Product name")
        self.search_input.textChanged.connect(self.search_product)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addStretch()

        button_layout = QHBoxLayout()
        
        global is_admin
        if is_admin:
            self.delete_button = QPushButton("Delete selected product")
            self.delete_button.clicked.connect(self.delete_product)
            button_layout.addWidget(self.delete_button)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_table)
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()

        layout: QVBoxLayout = QVBoxLayout()
        layout.addLayout(search_layout)
        layout.addWidget(self.view)
        layout.addLayout(button_layout)

        self.setLayout(layout)
    
    def search_product(self):
        search_text = self.search_input.text().strip()

        if search_text: # case insensitive search
            self.model.setFilter(f"PRODUCT_NAME ILIKE '%{search_text}%'")
        else:
            self.model.setFilter("")

    def delete_product(self):
        if not is_admin:
            QMessageBox.warning(self, "Product deletion error", "Only admin can delete products!")
            return

        selected_indexes = self.view.selectionModel().selectedRows()
        
        if not selected_indexes:
            QMessageBox.warning(self, "Product deletion error", "Please select a product to delete!")
            return

        row = selected_indexes[0].row()
        product_article = self.model.record(row).value('PRODUCT_ARTICLE')
        product_name = self.model.record(row).value('PRODUCT_NAME')

        # approve deletion
        reply = QMessageBox.question(
            self,
            "Product deletion",
            f"Are you sure you want to delete a product:\n\n"
            f"Article: {product_article}\n"
            f"Name: {product_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            query = QSqlQuery(database)
            query.prepare("DELETE FROM product WHERE PRODUCT_ARTICLE = :article")
            query.bindValue(":article", product_article)

            if query.exec():
                QMessageBox.information(self, "Product deletion", "Product deleted successfully!")
                self.refresh_table()
            else:
                QMessageBox.critical(self, "Product deletion error", f"Query error: {query.lastError().text()}")

    def refresh_table(self):
        self.search_input.clear()
        self.model.select()

    def closeEvent(self, event):
        global database
        if database.isOpen():
            database.close()

        event.accept()
    
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        global database
        database = QSqlDatabase.addDatabase('QPSQL')
        self.windows = []

        self.setWindowTitle("Main menu")
        self.setGeometry(100, 100, 400, 200)

        self.user_edit: QLineEdit = QLineEdit(self)
        self.user_edit.setPlaceholderText('Username')
        self.user_edit.setText(default_username)

        self.password_edit: QLineEdit = QLineEdit(self)
        self.password_edit.setPlaceholderText('Password')
        self.password_edit.setText(default_password)

        pass_layout: QHBoxLayout = QHBoxLayout()
        self.show_pass_button: QPushButton = QPushButton("Show password", self)
        self.show_pass_button.clicked.connect(self.show_pass)
        self.show_pass()

        pass_layout.addWidget(self.password_edit)
        pass_layout.addWidget(self.show_pass_button)

        self.open_button: QPushButton = QPushButton("Open", self)
        self.open_button.clicked.connect(self.open_db)

        vboxlayout: QVBoxLayout = QVBoxLayout()
        vboxlayout.addWidget(self.user_edit)
        vboxlayout.addLayout(pass_layout)
        vboxlayout.addWidget(self.open_button)
        self.setLayout(vboxlayout)
    
    def show_pass(self):
        if self.password_edit.echoMode() == QLineEdit.EchoMode.Normal:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_pass_button.setText('Show password')
        else:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_pass_button.setText('Hide password')
    
    def open_db(self):
        global database
        if database and database.isOpen():
            QMessageBox.critical(self, 'Database error', 'Database already opened')
            return
        
        database.setDatabaseName(default_db_name)
        database.setUserName(default_db_user)
        database.setPassword(default_db_password)
        database.setHostName(default_db_host)
        database.setPort(default_db_port)

        if not database.open():
            QMessageBox.critical(self, 'Database error', 'Failed to open db')
            return
        
        if self.user_edit.text() == "":
            QMessageBox.critical(self, 'Database error', 'Failed to open db. Username is empty!')
            database.close()
            return
        elif self.password_edit.text() == "":
            QMessageBox.critical(self, 'Database error', 'Failed to open db. Password is empty!')
            database.close()
            return

        query = QSqlQuery(database)
        query.prepare(f"SELECT login, role, password FROM users WHERE \"login\" = (:user)")
        query.bindValue(":user", self.user_edit.text())

        if not query.exec():
            QMessageBox.critical(self, "Database error", f"Error executing query: {query.lastError().text()}")
            database.close()
            return

        if not query.next(): # value exists
            QMessageBox.critical(self, 'Authentication error', 'Username is empty or doesn\'t exist!')
            database.close()
            return
        
        username = str(query.value('login'))
        role = str(query.value('role'))
        password = str(query.value('password'))

        if password != self.password_edit.text():
            QMessageBox.critical(self, 'Authentication error', 'Password doesn\'t match!')
            database.close()
            return
        
        global is_admin
        if role == 'Администратор' or role == 'Админ' or role == 'Administrator' or role == 'Admin':
            is_admin = True
        
        # if everything is ok
        self.show_table()
    
    def show_table(self):
        table = DatabaseTableWindow()
        self.windows.append(table)
        table.show()
    
    def closeEvent(self, event):
        # close db
        if database.isOpen():
            database.close()

        # close all table windows
        for window in self.windows:
            window.close()

        event.accept()

def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()