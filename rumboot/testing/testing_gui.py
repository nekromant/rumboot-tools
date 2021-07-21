import sys
import os
from PyQt5 import QtWidgets
from PyQt5.QtCore import QPoint, QSize, QSettings, Qt, QTimer, QObject, QThread, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QTextCursor
from rumboot.testing.test_desc import *
from rumboot.testing.core import *
from rumboot.testing.executor import TestExecutor
from rumboot.testing.user_interaction import UserInteraction
from rumboot.testing.testing_gui_main_window import Ui_MainWindow
from rumboot.testing.testing_gui_testing_dialog import Ui_TestingDialog


USER_INTERACTION_TYPE_MESSAGE = 0
USER_INTERACTION_TYPE_YES_NO = 1
USER_INTERACTION_TYPE_OPTION = 2

class UserInteractionRequest:

    def __init__(self, test, type, text, options=None):
        self.test = test
        self.type = type
        self.text = text
        self.options = options
        self.result = None


class TestExecutorWrapper(QObject, UserInteraction):

    finished = pyqtSignal()
    progress = pyqtSignal(int)
    log_str = pyqtSignal(str)
    user_interaction = pyqtSignal(object)

    def __init__(self, test_desc_list, test_context, board_number):
        super().__init__()
        self._test_desc_list = test_desc_list
        self._board_number = board_number
        self._executor = TestExecutor(test_context, self, log_func=self._log_func)
        self._stop_request = False
        self._thread = QThread()
        self.moveToThread(self._thread)
        self._thread.started.connect(self._thread_proc)

        if self._board_number:
            self._test_and_mkdir("logs")
            self._board_log_path = os.path.join("logs", f"board_{self._board_number}")
            self._test_and_mkdir(self._board_log_path)


    # UserInteraction
    def request_message(self, test, text):
        request = UserInteractionRequest(test, USER_INTERACTION_TYPE_MESSAGE, text)
        self.user_interaction.emit(request)

    # UserInteraction
    def request_yes_no(self, test, text):
        request = UserInteractionRequest(test, USER_INTERACTION_TYPE_YES_NO, text)
        request.result = False
        self.user_interaction.emit(request)
        return request.result

    # UserInteraction
    def request_option(self, test, text, options):
        request = UserInteractionRequest(test, USER_INTERACTION_TYPE_OPTION, text, options)
        request.result = 0
        self.user_interaction.emit(request)
        return request.result

    def start_testing_nonblocking(self):
        self._stop_request = False
        self._thread.start()

    def terminate_testing_nonblocking(self):
        prev_stop_request = self._stop_request
        self._stop_request = True
        return prev_stop_request

    @pyqtSlot()
    def _thread_proc(self):
        test_index = 0
        for test_desc in self._test_desc_list:
            if self._stop_request:
                break
            self.progress.emit(test_index)
            test_index += 1
            self._executor.exec_test(test_desc)
            self._save_log(test_desc)
        self._thread.quit() # quit from default message loop
        self.finished.emit()

    def _log_func(self, text):
        self.log_str.emit(text)

    def _save_log(self, test_desc):
        if self._board_number == 0:
            return
        with open(os.path.join(self._board_log_path, f"{test_desc.full_name}.log"), "w") as file:
            file.write(test_desc.log_text)

    def _test_and_mkdir(self, path):
        if not os.path.exists(path):
            os.mkdir(path)
        elif not os.path.isdir(path):
            raise Exception(f"{path} is not a directory")


class UserOptionDialog(QtWidgets.QDialog):

    def __init__(self, parent, request):
        super().__init__(parent)
        self._request = request
        self.setWindowTitle("Запрос к пользователю")

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(QtWidgets.QLabel(f"Тест: {self._request.test.full_name}\n\n{self._request.text}:\n"))
        index = 0
        for option in self._request.options:
            button = QtWidgets.QPushButton(option)
            self.layout.addWidget(button)
            button.clicked.connect(self._make_func_accept_option(index))
            index += 1
        self.setLayout(self.layout)

    def _make_func_accept_option(self, index):
        def func_template():
            self._request.result = index
            self.accept()
        return func_template


class TestingDialog(QtWidgets.QDialog, Ui_TestingDialog):

    def __init__(self, parent, test_desc_list, test_context, board_number):
        super().__init__(parent)
        self._test_desc_list = test_desc_list
        self._executor_wrapper = TestExecutorWrapper(test_desc_list, test_context, board_number)
        self._executor_wrapper.finished.connect(self.accept, type=Qt.BlockingQueuedConnection)
        self._executor_wrapper.progress.connect(self._executor_wrapper_progress, type=Qt.BlockingQueuedConnection)
        self._executor_wrapper.log_str.connect(self._executor_wrapper_log_str, type=Qt.BlockingQueuedConnection)
        self._executor_wrapper.user_interaction.connect(self._executor_wrapper_user_interaction, type=Qt.BlockingQueuedConnection)

        self.setupUi(self)
        self.test_progress_bar.setRange(0, len(self._test_desc_list))

        QTimer.singleShot(0, self._start_testing)

    def done(self, code):
        if code == QtWidgets.QDialog.Accepted:
            super().done(code)
        else:
            if not self._executor_wrapper.terminate_testing_nonblocking():
                self._executor_wrapper_log_str("\n*** Stop request has been send. Wait for the end of the current test...\n")
                self.dialog_button_box.setEnabled(False)

    @pyqtSlot()
    def _start_testing(self):
        self._executor_wrapper.start_testing_nonblocking()

    @pyqtSlot(int)
    def _executor_wrapper_progress(self, test_index):
        self.test_progress_bar.setValue(test_index + 1)
        self.test_name_line_edit.setText(self._test_desc_list[test_index].full_name)

    @pyqtSlot(str)
    def _executor_wrapper_log_str(self, text):
        self.log_plain_text_edit.moveCursor(QTextCursor.End)
        self.log_plain_text_edit.insertPlainText(text)

    @pyqtSlot(object)
    def _executor_wrapper_user_interaction(self, request):
        if request.type == USER_INTERACTION_TYPE_MESSAGE:
            QtWidgets.QMessageBox.information(self, "Запрос к пользователю", f"Тест: {request.test.full_name}\n\n{request.text}")
        elif request.type == USER_INTERACTION_TYPE_YES_NO:
            answer = QtWidgets.QMessageBox.question(self, "Запрос к пользователю", f"Тест: {request.test.full_name}\n\n{request.text}", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            request.result = answer == QtWidgets.QMessageBox.Yes
        elif  request.type == USER_INTERACTION_TYPE_OPTION:
            dialog = UserOptionDialog(self, request)
            dialog.exec_()
        else:
            raise Exception("Unknown user interaction request type")


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self, test_registry, test_context):
        super().__init__()
        self._test_registry = test_registry
        self._test_context = test_context
        self._test_items = []

        self.setupUi(self)
        self._setup_test_tree()
        self.test_selected_button.clicked.connect(self._test_selected_button_clicked)
        self.test_failed_button.clicked.connect(self._test_failed_button_clicked)
        self.exit_action.triggered.connect(self.close)
        self.reset_status_log_action.triggered.connect(self._reset_status_log_action_triggered)
        self.about_qt_action.triggered.connect(lambda : QtWidgets.QMessageBox.aboutQt(self))

        self._settings = QSettings("gui.ini", QSettings.IniFormat)
        self._settings_resore()

        self._update_chip()
        self._reload_test_tree()
        self._update_current_test_info()
        self.current_test_tab_widget.setCurrentIndex(0)

    def closeEvent(self, event):
        self._settings_save()

    def _setup_test_tree(self):
        self.test_tree.setColumnCount(2)
        self.test_tree.setHeaderLabels(["Тест", "Статус"])
        self.test_tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.test_tree.itemChanged.connect(self._test_tree_update_item)
        self.test_tree.itemSelectionChanged.connect(self._update_current_test_info)

    def _settings_resore(self):
        self._settings.beginGroup("Main")
        self.board_number_auto_inc_action.setChecked(self._settings.value("board_number_auto_inc", 0, int) != 0)
        self.board_number_spin_box.setValue(self._settings.value("board_number", 0, int))
        self._settings.endGroup()

        self._settings.beginGroup("MainWindow")
        self.resize(self._settings.value("size", self.size(), QSize))
        self.move(self._settings.value("pos", self.pos(), QPoint))
        self._settings.endGroup()

    def _settings_save(self):
        self._settings.beginGroup("Main")
        self._settings.setValue("board_number_auto_inc", 1 if self.board_number_auto_inc_action.isChecked() else 0)
        self._settings.setValue("board_number", self.board_number_spin_box.value())
        self._settings.endGroup()

        self._settings.beginGroup("MainWindow")
        self._settings.setValue("size", self.size())
        self._settings.setValue("pos", self.pos())
        self._settings.endGroup()

    def _update_chip(self):
        self.chip_name_line_edit.setText(f"{self._test_context.chip.name} ({self._test_context.chip.part})")

    def _reload_test_tree(self):
        update_suitable(self._test_registry, self._test_context)
        self.test_tree.clear()
        self._test_items = []
        self._reload_test_tree_recursive(self._test_registry.all_tests, None)
        self._update_tests_status()
        self.test_tree.expandAll()

    def _reload_test_tree_recursive(self, tests, parent):
        for key, value in tests.items():
            item = QtWidgets.QTreeWidgetItem(self.test_tree if parent == None else parent)
            if isinstance(value, TestDesc):
                item.test_desc = value
                self._test_items.append(item)
                item.setText(0, value.name)
                item.setCheckState(0, Qt.Unchecked)
                if value.suitable:
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable)
                    item.setForeground(0, Qt.gray)
            else:
                item.test_desc = None
                item.setText(0, key)
                item.setCheckState(0, Qt.Unchecked)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                self._reload_test_tree_recursive(value, item)

    def _update_current_test_info(self):
        self.current_test_log_plain_text_edit.setPlainText(None)
        self.current_test_log_plain_text_edit.hide()
        self.current_test_description_label.setText(None)
        self.current_test_description_label.hide()

        test_desc = None
        if self.test_tree.selectedItems():
            item = self.test_tree.selectedItems()[0]
            test_desc = item.test_desc

        if test_desc:
            if test_desc.log_text:
                self.current_test_log_plain_text_edit.setPlainText(test_desc.log_text)
                self.current_test_log_plain_text_edit.show()
            if "description" in test_desc.params:
                self.current_test_description_label.setText(test_desc.params["description"])
            else:
                self.current_test_description_label.setText("<Нет описания теста>")
            self.current_test_description_label.show()

    @pyqtSlot()
    def _update_tests_status(self):
        for item in self._test_items:
            item.setForeground(1, Qt.black if item.test_desc.suitable else Qt.gray)
            if item.test_desc.status == TEST_STATUS_NOT_EXECUTED:
                item.setText(1, "Не запускался")
                item.setBackground(1, Qt.gray if item.test_desc.suitable else Qt.white)
            elif item.test_desc.status == TEST_STATUS_PASSED:
                item.setText(1, "Пройден")
                item.setBackground(1, Qt.green)
            elif item.test_desc.status == TEST_STATUS_FAULT:
                item.setText(1, "Ошибка")
                item.setBackground(1, Qt.red)
            else:
                raise Exception("Unknown test status")

    @pyqtSlot(QtWidgets.QTreeWidgetItem, int)
    def _test_tree_update_item(self, item, column):
        if not item.test_desc:
            for i in range(item.childCount()):
                child = item.child(i)
                if not child.test_desc or child.test_desc.suitable:
                    child.setCheckState(0, item.checkState(0))

    @pyqtSlot()
    def _test_selected_button_clicked(self):
        test_desc_list = []
        for item in self._test_items:
            if item.checkState(0) == Qt.Checked:
                test_desc = item.test_desc
                test_desc.status = TEST_STATUS_NOT_EXECUTED
                test_desc.log_text = None
                test_desc_list.append(test_desc)
        self._test_list(test_desc_list)

    @pyqtSlot()
    def _test_failed_button_clicked(self):
        test_desc_list = []
        for item in self._test_items:
            test_desc = item.test_desc
            if test_desc.status == TEST_STATUS_FAULT:
                test_desc_list.append(test_desc)
        self._test_list(test_desc_list)

    def _test_list(self, test_desc_list):
        if not test_desc_list:
            QtWidgets.QMessageBox.critical(self, "Ошибка", "Нет выбранных тестов")
            return
        self._update_tests_status()
        self._update_current_test_info()
        testing_dialog = TestingDialog(self, test_desc_list, self._test_context, self.board_number_spin_box.value())
        testing_dialog.exec_()
        self._update_tests_status()
        self._update_current_test_info()
        if self.board_number_auto_inc_action.isChecked():
            if all([x.test_desc.status == TEST_STATUS_PASSED for x in self._test_items if x.test_desc.suitable]):
                self.board_number_spin_box.setValue(self.board_number_spin_box.value() + 1)
                self._settings_save()
                QtWidgets.QMessageBox.information(self, "Информация", "Все тесты пройдены, номер платы увеличен на 1")

    @pyqtSlot()
    def _reset_status_log_action_triggered(self):
        for item in self._test_items:
            test_desc = item.test_desc
            test_desc.status = TEST_STATUS_NOT_EXECUTED
            test_desc.log_text = None
        self._update_tests_status()
        self._update_current_test_info()


def start_testing_gui(test_registry, test_context):
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(test_registry, test_context)
    window.show()
    app.exec_()
