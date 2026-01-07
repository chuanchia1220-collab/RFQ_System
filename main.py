"""
Main entry point for the RFQ System application.
"""

import flet as ft
from config import TRANSLATIONS
import database

def main(page: ft.Page):
    """
    Main function to initialize the application and setup navigation.
    """
    database.init_db()
    page.title = "RFQ System"
    page.theme_mode = ft.ThemeMode.LIGHT

    # Default Language
    current_lang = "zh"
    t = TRANSLATIONS[current_lang]

    # Destination Index
    def on_nav_change(e):
        selected_index = e.control.selected_index
        if selected_index == 0:
            page.go("/supplier")
        elif selected_index == 1:
            page.go("/rfq")
        elif selected_index == 2:
            page.go("/template")

    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=400,
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.PERSON,
                selected_icon=ft.Icons.PERSON_OUTLINE,
                label=t["supplier_management"]
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.ANALYTICS,
                selected_icon=ft.Icons.ANALYTICS_OUTLINED,
                label=t["rfq_analysis"]
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SETTINGS,
                selected_icon=ft.Icons.SETTINGS_OUTLINED,
                label=t["template_settings"]
            ),
        ],
        on_change=on_nav_change,
    )

    def route_change(_):
        page.views.clear()

        # Update rail selection based on route
        if page.route == "/supplier":
            rail.selected_index = 0
            content = ft.Text(t["supplier_management"])
        elif page.route == "/rfq":
            rail.selected_index = 1
            content = ft.Text(t["rfq_analysis"])
        elif page.route == "/template":
            rail.selected_index = 2
            content = ft.Text(t["template_settings"])
        else:
            # Default fallback
            rail.selected_index = 0
            content = ft.Text(t["supplier_management"])

        page.views.append(
            ft.View(
                page.route,
                [
                    ft.Row(
                        [
                            rail,
                            ft.VerticalDivider(width=1),
                            ft.Column([content], expand=True, alignment=ft.MainAxisAlignment.START),
                        ],
                        expand=True,
                    )
                ],
            )
        )
        page.update()

    def view_pop(_):
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    page.go("/supplier")

if __name__ == "__main__":
    ft.app(main)
