import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from database.database import create_tables, seed_data
from controllers.login_controller import LoginWindow


def main():
    app = QApplication(sys.argv)

    create_tables()
    seed_data()

    win = LoginWindow()
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()