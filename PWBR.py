import os
import sys
import subprocess
import threading
import time
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QListWidget, QLabel, QPushButton,
    QLineEdit, QFileDialog, QTextEdit, QMessageBox, QHBoxLayout, QListWidgetItem, QSpinBox
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

# --- Пути к ресурсам ---
def resource_path(relative_path):
    """Возвращает правильный путь к файлу, будь то скрипт или exe"""
    try:
        # Если запускается из PyInstaller, файлы лежат во временной папке _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Если запускаем скрипт напрямую
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

RESOURCES_DIR = "resources"

# Директория батников
if getattr(sys, 'frozen', False):
    # Если запускается из exe
    THIS_DIR = os.path.dirname(sys.executable)
else:
    # Если запускается как скрипт
    THIS_DIR = os.path.dirname(os.path.abspath(__file__))

BAT_DIR = os.path.join(THIS_DIR, "bat_files")

class BatRunner(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PWBR")
        # Используем resource_path для иконки
        self.setWindowIcon(QIcon(resource_path(os.path.join(RESOURCES_DIR, "GameIcon.ico"))))
        self.resize(700, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Список батников
        layout.addWidget(QLabel("Список батников:"))
        self.bat_list = QListWidget()
        self.bat_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self.bat_list)

        # --- Рабочая директория ---
        wd_layout = QHBoxLayout()
        wd_layout.addWidget(QLabel("Директория Perfect World:"))
        self.wd_edit = QLineEdit()
        self.wd_edit.setPlaceholderText("Укажите путь к папке, где лежит elementclient.exe")
        wd_layout.addWidget(self.wd_edit)
        browse_btn = QPushButton("Обзор")
        browse_btn.clicked.connect(self.choose_dir)
        wd_layout.addWidget(browse_btn)
        layout.addLayout(wd_layout)

        # --- Задержка между батниками ---
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("Задержка между батниками (сек):"))
        self.delay_spin = QSpinBox()
        self.delay_spin.setMinimum(0)
        self.delay_spin.setMaximum(60)
        self.delay_spin.setValue(5)  # по умолчанию 5 секунд
        delay_layout.addWidget(self.delay_spin)
        layout.addLayout(delay_layout)

        # --- Кнопки ---
        btn_layout = QHBoxLayout()
        run_btn = QPushButton("▶ Запустить выбранные")
        run_btn.clicked.connect(self.run_selected)
        refresh_btn = QPushButton("🔄 Обновить список")
        refresh_btn.clicked.connect(self.refresh_list)
        btn_layout.addWidget(run_btn)
        btn_layout.addWidget(refresh_btn)
        layout.addLayout(btn_layout)

        # --- Лог ---
        layout.addWidget(QLabel("Лог выполнения:"))
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        self.setLayout(layout)

        # Создаём папку bat_files, если её нет
        os.makedirs(BAT_DIR, exist_ok=True)
        self.refresh_list()

    def refresh_list(self):
        """Обновляет список .bat файлов из подпапки"""
        self.bat_list.clear()
        bat_files = [f for f in os.listdir(BAT_DIR) if f.lower().endswith(".bat")]
        if not bat_files:
            return
        for f in bat_files:
            self.bat_list.addItem(QListWidgetItem(f))

    def choose_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Выбрать директорию", THIS_DIR)
        if folder:
            self.wd_edit.setText(folder)

    def run_selected(self):
        """Запускает выбранные .bat файлы"""
        items = self.bat_list.selectedItems()
        if not items:
            QMessageBox.warning(self, "Внимание", "Выберите хотя бы один .bat файл")
            return

        working_dir = self.wd_edit.text().strip()
        if not working_dir:
            QMessageBox.warning(self, "Нет директории", "Укажите рабочую директорию перед запуском.")
            return
        if not os.path.isdir(working_dir):
            QMessageBox.critical(self, "Ошибка", "Указанная директория не существует.")
            return

        delay_sec = self.delay_spin.value()

        bat_files = [os.path.join(BAT_DIR, i.text()) for i in items]
        self.log.append(f"\n=== Запуск {len(bat_files)} файлов (интервал {delay_sec} сек, без ожидания завершения) ===")
        for bf in bat_files:
            self.log.append(f"  • {os.path.basename(bf)}")

        threading.Thread(target=self.run_bats_async,
                         args=(bat_files, working_dir, delay_sec),
                         daemon=True).start()

    def run_bats_async(self, bat_files, working_dir, delay_sec):
        """Запускает .bat файлы последовательно, не дожидаясь завершения"""
        for idx, bat_path in enumerate(bat_files, start=1):
            bat_name = os.path.basename(bat_path)
            self.log.append(f"\n▶ Запуск {idx}/{len(bat_files)}: {bat_name}")
            try:
                subprocess.Popen(
                    ["cmd", "/c", bat_path],
                    cwd=working_dir,
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                self.log.append(f"Запущен {bat_name} ✅")
            except Exception as e:
                self.log.append(f"Ошибка запуска {bat_name}: {e}")
            time.sleep(delay_sec)
        self.log.append("\n=== Все батники запущены ===\n")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = BatRunner()
    win.show()
    sys.exit(app.exec())
