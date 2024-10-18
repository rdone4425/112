# Note: QtAsyncio is not used in this file
import sys
import os

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import asyncio
from PyQt6 import QtWidgets, QtGui, QtCore
from git.token_tab import TokenTab
from git.repository_tab import RepositoryTab
from git.search_widget import SearchWidget
from git.github_search import GitHubSearchDialog, search_github, create_repo_widget
import aiohttp
from datetime import datetime
from git.log_tab import LogTab

# 临时创建占位类
class PlaceholderTab(QtWidgets.QWidget):
    def __init__(self, name):
        super().__init__()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QWidget())  # 添加一个空的widget作为占位符
        self.setLayout(layout)
        self.setWindowTitle(name)

class HomeTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # 搜索框移到顶部
        search_layout = QtWidgets.QHBoxLayout()
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("搜索仓库...")
        self.search_input.returnPressed.connect(self.perform_search)
        search_layout.addWidget(self.search_input)

        self.search_type = QtWidgets.QComboBox()
        self.search_type.addItems(["GitHub", "本地"])
        search_layout.addWidget(self.search_type)

        self.search_button = QtWidgets.QPushButton("搜索")
        self.search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_button)

        layout.addLayout(search_layout)

        # 搜索结果区域
        self.search_results_scroll = QtWidgets.QScrollArea()
        self.search_results_scroll.setWidgetResizable(True)
        self.search_results_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.search_results_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.search_results_scroll.setFixedHeight(500)  # 设置固定高度
        self.search_results_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f0f0f0;
            }
        """)
        self.search_results_scroll.setVisible(False)  # 初始时隐藏搜索果区域

        self.search_results_widget = QtWidgets.QWidget()
        self.search_results_layout = QtWidgets.QVBoxLayout(self.search_results_widget)
        self.search_results_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.search_results_scroll.setWidget(self.search_results_widget)

        layout.addWidget(self.search_results_scroll)

        # 欢迎标签和卡片部分
        self.welcome_widget = QtWidgets.QWidget()
        welcome_layout = QtWidgets.QVBoxLayout(self.welcome_widget)

        self.welcome_label = QtWidgets.QLabel("欢迎使用 Git 客户端")
        self.welcome_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.welcome_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px 0;")
        welcome_layout.addWidget(self.welcome_label)

        self.cards_layout = QtWidgets.QHBoxLayout()
        self.cards_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        repo_card = self.create_card("仓库管理", "管理您的Git仓库", lambda: self.main_window.tab_widget.setCurrentIndex(1), "#3498db")
        self.cards_layout.addWidget(repo_card)

        token_card = self.create_card("令牌管理", "管理您的访问令牌", lambda: self.main_window.tab_widget.setCurrentIndex(2), "#2ecc71")
        self.cards_layout.addWidget(token_card)

        welcome_layout.addLayout(self.cards_layout)
        layout.addWidget(self.welcome_widget)

    def create_card(self, title, description, on_click, color):
        card = QtWidgets.QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                background-color: {color};
                border-radius: 10px;
                padding: 20px;
                color: white;
            }}
            QWidget:hover {{
                background-color: {self.darken_color(color)};
            }}
        """)
        card_layout = QtWidgets.QVBoxLayout(card)
        
        title_label = QtWidgets.QLabel(title)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        card_layout.addWidget(title_label)
        
        desc_label = QtWidgets.QLabel(description)
        desc_label.setStyleSheet("font-size: 14px;")
        card_layout.addWidget(desc_label)
        
        card.mousePressEvent = lambda event: on_click()
        
        return card

    def darken_color(self, color):
        # 将颜色变暗一些，用于悬停效果
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        factor = 0.8
        return f"#{int(r*factor):02x}{int(g*factor):02x}{int(b*factor):02x}"

    def perform_search(self):
        search_text = self.search_input.text()
        search_type = self.search_type.currentText()
        if search_text:
            self.welcome_widget.setVisible(False)
            self.search_results_scroll.setVisible(True)
            if search_type == "本地":
                self.search_local_repos(search_text)
            else:
                self.search_github_repos(search_text)
        else:
            self.welcome_widget.setVisible(True)
            self.search_results_scroll.setVisible(False)

    def search_local_repos(self, search_text):
        self.clear_search_results()
        local_results = self.main_window.repository_tab.filter_repos(search_text, "全部")
        if local_results is None:
            print("警告：filter_repos 返回了 None")
            local_results = []  # 如果是 None，使用空列表
        for repo in local_results:
            self.add_search_result(repo, is_local=True)

    def search_github_repos(self, search_text):
        self.clear_search_results()
        search_github(search_text, self.display_github_results)

    @QtCore.pyqtSlot(list)
    def display_github_results(self, repos):
        for repo in repos:
            result_widget = create_repo_widget(repo, self.search_input.text())
            self.search_results_layout.addWidget(result_widget)
        self.search_results_scroll.setVisible(True)
        self.welcome_widget.setVisible(False)

    def add_search_result(self, repo, is_local):
        result_widget = self.create_repo_widget(repo, is_local)
        self.search_results_layout.addWidget(result_widget)

    def clear_search_results(self):
        while self.search_results_layout.count():
            item = self.search_results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def create_repo_widget(self, repo, is_local):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)
        
        name_label = QtWidgets.QLabel(f"<b>{repo['full_name']}</b>")
        layout.addWidget(name_label)
        
        description_label = QtWidgets.QLabel(repo['description'] or "No description")
        description_label.setWordWrap(True)
        layout.addWidget(description_label)
        
        stats_label = QtWidgets.QLabel(f"⭐ {repo['stargazers_count']} | 👀 {repo['watchers_count']} | 🕒 {repo['updated_at']}")
        layout.addWidget(stats_label)
        
        url_label = QtWidgets.QLabel(f"<a href='{repo['html_url']}'>{repo['html_url']}</a>")
        url_label.setOpenExternalLinks(True)
        layout.addWidget(url_label)
        
        widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 5px;
                margin-bottom: 5px;
            }
        """)
        
        return widget

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Git客户端")
        # 设置一个更合理的初始窗口大小
        self.setGeometry(100, 100, 1000, 600)
        
        # 设置应用程序的字体
        self.setFont(QtGui.QFont("微雅黑", 10))
        
        # 创建中心部件
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建主布局
        self.main_layout = QtWidgets.QVBoxLayout(self.central_widget)
        
        # 创建选项卡部件
        self.tab_widget = QtWidgets.QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # 添加选项卡
        self.home_tab = HomeTab(self)
        self.repository_tab = RepositoryTab(self)  # 传入 self 作为 main_window 参数
        self.token_tab = TokenTab(self)  # 传入 self 作为 main_window 参数
        self.log_tab = LogTab()
        
        self.tab_widget.addTab(self.home_tab, "主页")
        self.tab_widget.addTab(self.repository_tab, "仓库")
        self.tab_widget.addTab(self.token_tab, "令牌")
        self.tab_widget.addTab(self.log_tab, "日志")
        
        # 创建状态栏
        self.statusBar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")
        
        # 添加登录状态标签到状态栏
        self.login_status_label = QtWidgets.QLabel("未登录")
        self.statusBar.addPermanentWidget(self.login_status_label)
        
        # 设置样式
        self.set_styles()

        # 连接token更新信号、登录状态更新信号和用户名更新信号
        self.token_tab.token_updated.connect(self.on_token_updated)
        self.token_tab.login_status_updated.connect(self.on_login_status_updated)
        self.token_tab.username_updated.connect(self.on_username_updated)

        # 尝试使用最后一个 token 登录
        QtCore.QTimer.singleShot(0, self.token_tab.try_login_with_last_token)

        # 添加这些连接
        self.token_tab.username_updated.connect(self.update_repository_username)

        # 创建 data 目录
        self.data_dir = os.path.join(os.getcwd(), 'data')
        os.makedirs(self.data_dir, exist_ok=True)

    def search_local_repos(self, search_text):
        self.tab_widget.setCurrentIndex(1)  # 换到仓库标签页
        self.repository_tab.filter_repos(search_text, "全")

    def search_github(self, search_text):
        dialog = GitHubSearchDialog(self)
        dialog.search_widget.search_input.setText(search_text)
        dialog.search_widget.perform_search()
        dialog.exec()

    def show_search_results(self, local_results, github_results):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("搜索结果")
        layout = QtWidgets.QVBoxLayout(dialog)

        tabs = QtWidgets.QTabWidget()
        local_tab = QtWidgets.QWidget()
        github_tab = QtWidgets.QWidget()

        local_layout = QtWidgets.QVBoxLayout(local_tab)
        github_layout = QtWidgets.QVBoxLayout(github_tab)

        for repo in local_results:
            local_layout.addWidget(self.create_repo_widget(repo, is_local=True))

        for repo in github_results:
            github_layout.addWidget(self.create_repo_widget(repo, is_local=False))

        tabs.addTab(local_tab, f"本地结果 ({len(local_results)})")
        tabs.addTab(github_tab, f"GitHub结果 ({len(github_results)})")

        layout.addWidget(tabs)

        close_button = QtWidgets.QPushButton("关闭")
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)

        dialog.setLayout(layout)
        dialog.resize(600, 400)
        dialog.exec()

    def create_repo_widget(self, repo, is_local):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        name_label = QtWidgets.QLabel(f"<b>{repo['name']}</b>")
        layout.addWidget(name_label)

        description_label = QtWidgets.QLabel(repo['description'] or "No description")
        layout.addWidget(description_label)

        if is_local:
            url_label = QtWidgets.QLabel(f"<a href='{repo['html_url']}'>{repo['html_url']}</a>")
        else:
            url_label = QtWidgets.QLabel(f"<a href='{repo['html_url']}'>{repo['full_name']}</a>")
        url_label.setOpenExternalLinks(True)
        layout.addWidget(url_label)

        return widget

    def set_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                color: #2c3e50;
                padding: 8px 12px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border: 1px solid #cccccc;
                border-bottom: 1px solid white;
            }
            QStatusBar {
                background-color: #2c3e50;
                color: white;
            }
        """)

    def on_token_updated(self, token):
        print(f"当前选中的token: {token}")

    @QtCore.pyqtSlot(str)
    def on_username_updated(self, username):
        if username:
            self.tab_widget.setTabText(2, f"令牌 ({username})")
            self.login_status_label.setText(f"已登录: {username}")
        else:
            self.tab_widget.setTabText(2, "令牌")
            self.login_status_label.setText("未登录")

    @QtCore.pyqtSlot(str, bool)
    def on_login_status_updated(self, token, success):
        if success:
            self.statusBar.showMessage(f"Token {token[:4]}...{token[-4:]} 验证成功", 5000)  # 显示5秒
        else:
            self.statusBar.showMessage(f"Token {token[:4]}...{token[-4:]} 验证失败", 5000)  # 显示5秒
            self.tab_widget.setTabText(2, "令牌")
            self.login_status_label.setText("未登录")

    def update_repository_username(self, username):
        self.repository_tab.current_username = username
        self.repository_tab.current_token = self.token_tab.current_token  # 添加这行

    def log_message(self, message):
        self.log_tab.add_log(message)

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()

    # 创建一个新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def run_async_loop():
        asyncio.set_event_loop(loop)
        loop.run_forever()

    # 在单独的线程中运行异步事件循环
    import threading
    threading.Thread(target=run_async_loop, daemon=True).start()

    # 运行 Qt 事件循环
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
