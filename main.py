import flet as ft
from config import TRANSLATIONS
import database

def main(page: ft.Page):
    database.init_db()
    page.title = "RFQ System"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1200
    page.window_height = 800

    # 語言與翻譯
    current_lang = "zh"
    t = TRANSLATIONS[current_lang]

    # 右側主內容區域容器
    content_area = ft.Column([ft.Text(t["supplier_management"], size=30)], expand=True)

    # 切換頁面邏輯 (最高 CP 值：不切換路由，只換內容)
    def on_nav_change(e):
        index = e.control.selected_index
        if index == 0:
            content_area.controls = [ft.Text(t["supplier_management"], size=30)]
        elif index == 1:
            content_area.controls = [ft.Text(t["rfq_analysis"], size=30)]
        elif index == 2:
            content_area.controls = [ft.Text(t["template_settings"], size=30)]
        page.update()

    # 側邊導覽欄
    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.PERSON_OUTLINE,
                selected_icon=ft.Icons.PERSON,
                label=t["supplier_management"]
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.ANALYTICS_OUTLINED,
                selected_icon=ft.Icons.ANALYTICS,
                label=t["rfq_analysis"]
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SETTINGS_OUTLINED,
                selected_icon=ft.Icons.SETTINGS,
                label=t["template_settings"]
            ),
        ],
        on_change=on_nav_change,
    )

    # 核心佈局結構
    layout = ft.Row(
        [
            rail,
            ft.VerticalDivider(width=1),
            ft.Container(content=content_area, expand=True, padding=20),
        ],
        expand=True,
    )

    page.add(layout)

if __name__ == "__main__":
    # 使用 WEB_BROWSER 模式可以先排除是否為在地視窗渲染問題
    # 若成功看到畫面，再改回 ft.AppView.FLET_APP
    ft.app(target=main)
