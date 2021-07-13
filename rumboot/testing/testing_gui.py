from rumboot.testing.user_interaction import UserInteraction
import sys
# import gc
# import os
# import traceback
# from collections import OrderedDict
# from queue import Queue
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QTimer, QObject, QThread, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QTextCursor


# from PyQt5.QtCore import QObject, QFileInfo, QSettings, QThread, pyqtSignal, Qt, pyqtSlot, QEventLoop
# from PyQt5.QtWidgets import QAction, QFileDialog, QInputDialog

# from htmlViewer import htmlViewer
# from testing import intialize_testing, RumbootTestFacility, find_tests

from rumboot.testing.test_desc import *
from rumboot.testing.core import *
from rumboot.testing.executor import TestExecutor
from rumboot.testing.testing_gui_main_window import Ui_MainWindow
from rumboot.testing.testing_gui_testing_dialog import Ui_TestingDialog


class TestExecutorWrapper(QObject, UserInteraction):

    finished = pyqtSignal()
    progress = pyqtSignal(int)
    log_str = pyqtSignal(str)

    def __init__(self, test_desc_list, test_context):
        super().__init__()
        self._test_desc_list = test_desc_list
        self._executor = TestExecutor(test_context, self, self._log_func)
        self._stop_request = False
        self._thread = QThread()
        self.moveToThread(self._thread)
        self._thread.started.connect(self._thread_proc)

    # UserInteraction
    def request_message(self, text):
        raise Exception("Method UserInteraction.request_message is not implemented")

    # UserInteraction
    def request_yes_no(self, text):
        raise Exception("Method UserInteraction.request_yes_no is not implemented")

    # UserInteraction
    def request_option(self, text, options):
        raise Exception("Method UserInteraction.request_option is not implemented")

    def start_testing_nonblocking(self):
        self._stop_request = False
        self._thread.start()

    def terminate_testing_nonblocking(self):
        if not self._stop_request:
            self._log_func("\n*** Stop request has been send. Wait for the end of the current test...\n")
            self._stop_request = True

    @pyqtSlot()
    def _thread_proc(self):
        test_index = 0
        for test_desc in self._test_desc_list:
            if self._stop_request:
                break
            self._log_func(f"=== Processing {test_desc.full_name} ===\n") # ???
            self.progress.emit(test_index)
            test_index += 1
            self._executor.exec_test(test_desc)
        self._thread.quit() # quit from default message loop
        self.finished.emit()

    def _log_func(self, text):
        self.log_str.emit(text)


class TestingDialog(QtWidgets.QDialog, Ui_TestingDialog, UserInteraction): # ??? no UserInteraction

    def __init__(self, parent, test_desc_list, test_context):
        super().__init__(parent)
        self._test_desc_list = test_desc_list
        self._executor_wrapper = TestExecutorWrapper(test_desc_list, test_context)
        self._executor_wrapper.finished.connect(self.accept)
        self._executor_wrapper.progress.connect(self._executor_wrapper_progress)
        self._executor_wrapper.log_str.connect(self._executor_wrapper_log_str)

        self.setupUi(self)
        self.test_progress_bar.setRange(0, len(self._test_desc_list))

        QTimer.singleShot(0, self._start_testing)

    def done(self, code):
        if code == QtWidgets.QDialog.Accepted:
            super().done(code)
        else:
            self._executor_wrapper.terminate_testing_nonblocking()
            self.dialog_button_box.setEnabled(False)

    # UserInteraction
    def request_message(self, text):
        raise Exception("Method UserInteraction.request_message is not implemented")

    # UserInteraction
    def request_yes_no(self, text):
        raise Exception("Method UserInteraction.request_yes_no is not implemented")

    # UserInteraction
    def request_option(self, text, options):
        raise Exception("Method UserInteraction.request_option is not implemented")

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


# class TestStruct():
#     def __init__(self, test, enable=True):
#         self.test = test
#         self.enable = enable

#     def set_enable(self, enable):
#         self.enable = enable


# class SignalsManager(QObject):
#     update_progress_bar_signal = pyqtSignal(int)
#     update_test_status_signal = pyqtSignal(str, int)
#     ask_user_continue_signal = pyqtSignal(str)
#     ask_user_signal = pyqtSignal(str)
#     close_ask_dialog_signal = pyqtSignal()

#     update_terminal_progress_bar_signal = pyqtSignal(int, int, int)
#     set_value_terminal_label_signal = pyqtSignal(str)

#     def __init__(self, user_answer_signal, user_answer_continue_signal):
#         super().__init__()

#         self.user_answer_signal = user_answer_signal
#         self.user_answer_continue_signal = user_answer_continue_signal

#     def __del__(self):
#         if hasattr(self, 'loop') and self.loop:
#             self.loop.quit()

#     def update_progress_bar_terminal(self, value, minimum=None, maximum=None):
#         self.update_terminal_progress_bar_signal.emit(value, minimum, maximum)

#     def set_value_terminal_label(self, text):
#         self.set_value_terminal_label_signal.emit(text)

#     def update_progress_bar(self, value: int):
#         self.update_progress_bar_signal.emit(value)

#     def update_test_status(self, test_name: str, test_status: int):
#         self.update_test_status_signal.emit(test_name, test_status)

#     def ask_user(self, text):
#         self.ask_user_signal.emit(text)  # PP: Send signal to the main thread
#         return self.start_loop(self.user_answer_signal, self.get_user_answer)

#     def ask_user_continue(self, path_to_html):
#         self.ask_user_continue_signal.emit(path_to_html)  # PP: Send signal to the main thread
#         return self.start_loop(self.user_answer_continue_signal, self.get_user_answer_continue)

#     def start_loop(self, signal, slot):
#         # Create a loop where we will wait user answer
#         self.loop = QEventLoop()
#         signal.connect(slot)

#         # Enter into loop
#         self.loop.exec()

#         # We have exited from loop so check why
#         return self.user_answer

#     @pyqtSlot(str, int)
#     def get_user_answer(self, result_text, result_button):
#         self.loop.quit()
#         self.user_answer = {'text': result_text,
#                             'button': result_button}

#     @pyqtSlot(int)
#     def get_user_answer_continue(self, result_button):
#         self.loop.quit()
#         self.user_answer = result_button

#     def close_ask_dialog(self):
#         self.close_ask_dialog_signal.emit()


# class TestRunner(QObject):
#     # update_board_num_signal = pyqtSignal()

#     def __init__(self, test_list: list, signal_manager, __g_facility):
#         super().__init__()

#         self.test_list = test_list
#         self.signal_manager = signal_manager
#         self.__g_facility = __g_facility

#     @pyqtSlot()
#     def run(self):
#         try:
#             self.__g_facility.reset_test_list()  # PP: Need to reset because we don't want run tests from previous click
#             self.__g_facility.register_tests(self.test_list)
#             self.__g_facility.run(self.signal_manager)

#             # self.update_board_num_signal.emit()
#         except:
#             print(traceback.format_exc())

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
#     current_profile = None
#     user_answer_signal = pyqtSignal(str, int)
#     user_answer_continue_signal = pyqtSignal(int)

    def __init__(self, test_registry, test_context):
        super().__init__()
        self._test_registry = test_registry
        self._test_context = test_context
        self._test_items = []

        self.setupUi(self)
        self._setup_test_tree()
        self.test_selected_button.clicked.connect(self._test_selected_button_clicked)
#         self.button_run_failed_tests.clicked.connect(self.run_failed_tests)

        self._update_chip()
        self._reload_test_tree()
        self._update_current_test_info()
        self.current_test_tab_widget.setCurrentIndex(0)
#         self.tosaveload = [self.boardnum]
#         for tmpl in self.platfom_templates_group.actions():
#             self.tosaveload.append(tmpl)
#         self.initProgressBar(0, 300, 0)
#         self.selectProfile("settings")

#         self.setupPlatform()

#         self.__g_facility = None

#         exit_button = self.findChild(QAction, "exit")
#         exit_button.triggered.connect(self.close) #exitEventHandler
#         self.action_clear_log.triggered.connect(self.clear_log)
#         self.action_save_log.triggered.connect(self.save_log_in_file)

#         self.button_test.clicked.connect(self.start_testing)
#         self.button_run_failed_tests.clicked.connect(self.run_failed_tests)

#         for qact in self.platfom_templates_group.actions():
#             qact.changed.connect(self.setupPlatform)

    def _setup_test_tree(self):
        self.test_tree.setColumnCount(2)
        self.test_tree.setHeaderLabels(["Тест", "Статус"])
        self.test_tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.test_tree.itemChanged.connect(self._test_tree_update_item)
        self.test_tree.itemSelectionChanged.connect(self._update_current_test_info) # ???

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

        test_desc = None
        if self.test_tree.selectedItems():
            item = self.test_tree.selectedItems()[0]
            test_desc = item.test_desc

        if test_desc:
            if test_desc.log_text:
                self.current_test_log_plain_text_edit.setPlainText(test_desc.log_text)
                self.current_test_log_plain_text_edit.show()

    # ??? mark or not #???
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

    # ??? mark
    def _test_tree_update_item(self, item, column):
        if not item.test_desc:
            for i in range(item.childCount()):
                child = item.child(i)
                if not child.test_desc or child.test_desc.suitable:
                    child.setCheckState(0, item.checkState(0))

    # ??? mark
    def _test_selected_button_clicked(self):
        test_desc_list = []
        for item in self._test_items:
            if item.checkState(0) == Qt.Checked:
                test_desc = item.test_desc
                test_desc.status = TEST_STATUS_NOT_EXECUTED
                test_desc.log_text = None
                test_desc_list.append(test_desc)
        if not test_desc_list:
            QtWidgets.QMessageBox.critical(self, "Ошибка", "Нет выбранных тестов")
            return
        self._update_tests_status()
        self._update_current_test_info()
        testing_dialog = TestingDialog(self, test_desc_list, self._test_context)
        testing_dialog.exec_()
        self._update_tests_status()
        self._update_current_test_info()

#     def getPlatformName(self):
#         ret = False
#         for qact in self.platfom_templates_group.actions():
#             if qact.isChecked():
#                 ret = True
#                 break
#         if ret == False:
#             qact = self.platfom_templates_group.actions()[0]
#         return qact.text().split(",")

#     def setupPlatform(self):
#         self.platform_name, self.chip_name = self.getPlatformName()
#         if self.platform_name != None:
#             self.labelPlatName.setText(self.labelPlatName.text().split()[0] + " " + self.platform_name + "(" + self.chip_name + ")")
#         self.treeWidget.clear()
#         self.setTreeWidget()

#     @pyqtSlot()
#     def start_testing(self, status: str = None):
#         print("start_testing")
#         selected_tests = self.getSelectedTests(status)
#         if not selected_tests:
#             print("Ошибка. Тесты для запуска не выбраны")
#             return
#         self.initProgressBar(0, len(selected_tests), 0)

#         # Init run_test wrapper and signal manager (which will send and receive signals to/from main thread)
#         self.signal_manager = SignalsManager(self.user_answer_signal, self.user_answer_continue_signal)
#         if not self.__g_facility:
#             self.init_g_facility()
#         self.test_runner = TestRunner(selected_tests, self.signal_manager, self.__g_facility)

#         # TODO: check, why increment_board_num doesn't increment QSpin...
#         # self.test_runner.update_board_num_signal.connect(self.increment_board_num)

#         # Connect possible signals signal manager with main thread functions
#         self.signal_manager.update_progress_bar_signal.connect(self.setValueProgressBar)
#         self.signal_manager.ask_user_signal.connect(self.ask_user)
#         self.signal_manager.ask_user_continue_signal.connect(self.ask_user_continue)
#         self.signal_manager.close_ask_dialog_signal.connect(self.close_ask_dialog)
#         self.signal_manager.update_test_status_signal.connect(self.set_test_status)

#         self.signal_manager.update_terminal_progress_bar_signal.connect(self.update_terminal_progress_bar)
#         self.signal_manager.set_value_terminal_label_signal.connect(self.set_value_terminal_label)

#         # Run run_test wrapper and signal manager in separated thread
#         self.test_run_thread = QThread(parent=self)
#         self.signal_manager_thread = QThread(parent=self)

#         self.test_runner.moveToThread(self.test_run_thread)
#         self.signal_manager.moveToThread(self.signal_manager_thread)

#         self.test_run_thread.started.connect(self.test_runner.run)

#         self.signal_manager_thread.start()
#         self.test_run_thread.start()

#     def run_failed_tests(self):
#         self.start_testing("Ошибка")

#     def init_g_facility(self):
#         term, reset = intialize_testing(self.chip_name)
#         self.__g_facility = RumbootTestFacility(self.platform_name, term, reset)

#     def restore(self, settings):
#         print("Restoring window states")
#         finfo = QFileInfo(settings.fileName())
#         if finfo.exists() and finfo.isFile():
#             for w in self.tosaveload:
#                 mo = w.metaObject()
#                 if w.objectName() != "":
#                     for i in range(mo.propertyCount()):
#                         name = mo.property(i).name()
#                         val = settings.value("{}/{}".format(w.objectName(), name), w.property(name))
#                         w.setProperty(name, val)

#     def save(self, settings):
#         print("Saving window states")
#         for w in self.tosaveload:
#             mo = w.metaObject()
#             if w.objectName() != "":
#                 for i in range(mo.propertyCount()):
#                     name = mo.property(i).name()
#                     settings.setValue("{}/{}".format(w.objectName(), name), w.property(name))

#     def initProgressBar(self, mininum, maximum, value):
#         self.progress.setMinimum(mininum)
#         self.progress.setMaximum(maximum)
#         self.progress.setValue(value)

#     @pyqtSlot(int)
#     def setValueProgressBar(self, value):
#         self.progress.setValue(value)

#     @pyqtSlot(int, int, int)
#     def update_terminal_progress_bar(self, value, mininum=None, maximum=None):
#         if mininum:
#             self.progressBarTerminal.setMinimum(mininum)
#         if maximum:
#             self.progressBarTerminal.setMaximum(maximum)
#         self.progressBarTerminal.setValue(value)

#     @pyqtSlot(str)
#     def set_value_terminal_label(self, text):
#         self.labelTerminal.setText(text)

#     def setBoardNum(self, value):
#         self.boardnum.setValue(value)

#     def selectProfile(self, profile):
#         if self.current_profile != None:
#             self.save(self.app_settings)
#         self.app_settings = QSettings(profile + ".ini", QSettings.IniFormat)
#         self.restore(self.app_settings)

#     def closeEvent(self, event):
#         self.save(self.app_settings)

#     def exitEventHandler(self):
#         self.closeEvent(None)

#     @pyqtSlot(str)
#     def append_text(self, text):
#         self.log.moveCursor(QTextCursor.End)
#         self.log.insertPlainText(text)

#     def right_click_handler(self, position):
#         selected_item = self.treeWidget.selectedItems()[0]
#         if selected_item.childCount() != 0:  # PP: Skip for folders
#             return

#         options = QtWidgets.QMenu(self.treeWidget)
#         action_options = options.addAction('Info')
#         action2 = options.exec_(self.treeWidget.mapToGlobal(position))
#         if action2 is not None:
#             if action2 == action_options:
#                 items = self.treeWidget.selectedItems()
#                 self.open_html(items[0].text(0))

#     def open_html(self, test_name: str):
#         test_path = find_tests([test_name])[0]
#         from os import path
#         html_path = path.join(path.dirname(path.abspath(test_path)), 'html', 'help.html')
#         if path.isfile(html_path):
#             import webbrowser  # PP: May be we want to open .html in new gui window
#             webbrowser.open(html_path, new=2)
#         else:
#             print("help.html not found in \'{}\'".format(html_path))

#     def getTestTree(self) -> OrderedDict:
#         tests_tree = OrderedDict()
#         for file in find_tests(self.platform_name):
#             p = tests_tree
#             path_to_file = os.path.relpath(file, os.getcwd()).split('.')[0]
#             for x in path_to_file.split(os.sep):
#                 p = p.setdefault(x, OrderedDict())
#         return tests_tree

#     def initTestTree(self, folders=None, root_parent=None):
#         if not folders:
#             tree_list = self.getTestTree()
#         else:
#             tree_list = folders

#         if not root_parent:
#             root_parent = self.treeWidget

#         for key, value in tree_list.items():
#             if not value:
#                 items_for_insert = [key, "Не запускался"]
#             else:
#                 items_for_insert = [key]
#             parent = QtWidgets.QTreeWidgetItem(root_parent, items_for_insert)
#             if not value:
#                 parent.setBackground(1, Qt.gray)
#             parent.setFlags(parent.flags() | Qt.ItemIsUserCheckable)
#             parent.setCheckState(0, Qt.Unchecked)
#             if value:
#                 self.initTestTree(value, parent)

#     def find_test_item(self, test_name: str):
#         clist = self.treeWidget.findItems(test_name, Qt.MatchFixedString | Qt.MatchRecursive, 0)
#         if clist and clist[0].childCount() == 0:
#             return clist[0]
#         else:
#             raise Exception("Error. Test item '{}' not found".format(test_name))

#     def set_test_status(self, test_name, test_status):
#         item = self.find_test_item(test_name)

#         if test_status == 0:
#             status = "Пройден"
#             color = Qt.green
#         elif test_status == 1:
#             status = "Ошибка"
#             color = Qt.red
#         elif test_status == 2:
#             status = "Не запускался"
#             color = Qt.gray
#         else:
#             status = "В процессе..."
#             color = Qt.yellow

#         item.setText(1, status)
#         item.setBackground(1, color)

#     def addCheckbox(self, item, state):
#         item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
#         item.setCheckState(0, int(state))

#     def updateCheckbox(self, item):
#         for i in range(item.childCount()):
#             child = item.child(i)
#             if child.flags() & Qt.ItemIsUserCheckable:
#                 child.setCheckState(0, child.parent().checkState(0))

#     def clear_log(self):
#         self.log.clear()

#     def save_log_in_file(self):
#         file_name = QFileDialog.getSaveFileName(self, 'Save File')
#         with open(file_name[0], 'w') as file:
#             text = self.log.toPlainText()
#             file.write(text)
#             file.close()

#     def increment_board_num(self):
#         if self.auto_increment.isChecked():
#             if self.check_all_selected_tests_has_status("Пройден"):
#                 self.boardnum.singleStep()

#     def check_all_selected_tests_has_status(self, status):
#         for item in self.treeWidget.findItems("", Qt.MatchContains | Qt.MatchRecursive):
#             if item.childCount() == 0 and item.checkState(0) > 0:
#                 if item.text(1) != status:
#                     return False
#         return True

#     def getSelectedTests(self, status: str = None) -> list:
#         test_list = []
#         for item in self.treeWidget.findItems("", Qt.MatchContains | Qt.MatchRecursive):
#             if item.childCount() == 0 and item.checkState(0) > 0:
#                 if status:
#                     if item.text(1) == status:
#                         test_list.append(item.text(0))
#                 else:
#                     test_list.append(item.text(0))
#         return test_list

#     def ask_user(self, text: str):
#         answer, ok = QInputDialog.getText(self, 'Для продолжения требуется ответ', text)
#         self.user_answer_signal.emit(answer, ok)

#     def ask_user_continue(self, path_to_help: str):
#         self.viewer = htmlViewer(self, path_to_help)
#         self.user_answer_continue_signal.emit(self.viewer.exec_())

#     def close_ask_dialog(self):
#         if hasattr(self, 'viewer') and self.viewer:
#             self.viewer.close()


# class WriteStream(object):
#     """
#     Class-wrapper for stdout with queue
#     """
#     def __init__(self, queue):
#         self.queue = queue

#     def write(self, text):
#         self.queue.put(text)
#         with open("log.txt", "a") as f:
#             f.write(text)

#     def flush(self):
#         pass


# class TextReceiver(QObject):
#     """
#     Class for receiving text from queue and send write_signal to the main thread of GUI
#     """
#     write_signal = pyqtSignal(str)

#     def __init__(self, queue, *args, **kwargs):
#         QObject.__init__(self, *args, **kwargs)
#         self.queue = queue

#     @pyqtSlot()
#     def run(self):
#         while True:
#             text = self.queue.get()
#             self.write_signal.emit(text)
# ???

# ???
_env = None
_chip = None
_tests = None
# ???

# ???
# # Create Queue and redirect sys.stdout to this queue
# queue = Queue()
# sys.stdout = WriteStream(queue)

# ???
# # Create thread that will listen on the other end of the queue, and send the text to the textedit in application
# text_receiver_thread = QThread(parent=window)
# text_receiver = TextReceiver(queue)
# text_receiver.write_signal.connect(window.append_text)
# text_receiver.moveToThread(text_receiver_thread)
# text_receiver_thread.started.connect(text_receiver.run)
# text_receiver_thread.start()
# ???

def start_testing_gui(test_registry, test_context):
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(test_registry, test_context)
    window.show()
    app.exec_()
