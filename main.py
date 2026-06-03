from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivymd.uix.button import MDIconButton, MDFillRoundFlatButton, MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
import database 

Window.size = (360, 640)

class MenuScreen(Screen): pass
class IngredientsScreen(Screen):
    def on_enter(self): MDApp.get_running_app().update_screen_data()
class PremixesScreen(Screen):
    def on_enter(self): MDApp.get_running_app().update_screen_data()
class CalculatorScreen(Screen):
    def on_enter(self): MDApp.get_running_app().update_screen_data()
class HistoryScreen(Screen):
    def on_enter(self): MDApp.get_running_app().update_screen_data()

class InventoryApp(MDApp):
    dialog = None
    current_target = None
    current_mode = None
    recipe_inputs = {} 

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Teal"
        return Builder.load_file("inventory.kv")

    def on_start(self):
        database.init_db()
        self.update_screen_data()

    def update_screen_data(self):
        ingredients, pre_mixes, history = database.get_stock_data()
        
        # 1. Экран сырья (ТЕПЕРЬ ТОЖЕ БЕЗ НАДПИСИ «сырье»)
        try:
            container = self.root.get_screen('ingredients').ids.ingredients_container
            container.clear_widgets()
            for name, qty in ingredients:
                qty_kg_l = qty / 1000.0
                
                # Убираем маркер для красивого отображения
                clean_name = name.replace(" (сырье)", "")
                
                row = BoxLayout(orientation='horizontal', size_hint_y=None, height="55dp", padding="5dp")
                row.add_widget(MDLabel(text=f"{clean_name}\nОстаток: {qty_kg_l} кг/л", font_style="Body1"))
                
                btn = MDIconButton(icon="plus-circle", theme_icon_color="Custom", icon_color=(0.0, 0.8, 0.7, 1), icon_size="28dp")
                btn.bind(on_release=lambda x, n=name: self.show_input_dialog(n, 'INCOME'))
                row.add_widget(btn)
                container.add_widget(row)
        except Exception as e:
            print(f"Ошибка ингредиентов: {e}")
            
        # 2. Экран заготовок
        try:
            container_prem = self.root.get_screen('premixes').ids.premixes_container
            container_prem.clear_widgets()
            for name, qty in pre_mixes:
                row = BoxLayout(orientation='horizontal', size_hint_y=None, height="55dp", padding="5dp")
                row.add_widget(MDLabel(text=f"{name}\nГотово: {qty} л.", font_style="Body1"))
                
                btn = MDFillRoundFlatButton(text="Сделать", size_hint=(None, None), size=("90dp", "36dp"))
                btn.bind(on_release=lambda x, n=name: self.show_input_dialog(n, 'COOK'))
                row.add_widget(btn)
                container_prem.add_widget(row)
        except Exception as e:
            print(f"Ошибка заготовок: {e}")

        # 3. Конструктор техкарт (Без надписи «сырье»)
        try:
            calc_container = self.root.get_screen('calculator').ids.recipe_builder_container
            calc_container.clear_widgets()
            self.recipe_inputs.clear()
            for name, _ in ingredients:
                row = BoxLayout(
                    orientation='horizontal', 
                    size_hint_y=None, 
                    height="45dp", 
                    spacing="10dp", 
                    padding=["5dp", "2dp"]
                )
                
                clean_name = name.replace(" (сырье)", "")
                
                lbl = MDLabel(
                    text=f"{clean_name}:", 
                    font_style="Body1", 
                    size_hint_x=0.65, 
                    halign="left", 
                    pos_hint={"center_y": 0.5}
                )
                row.add_widget(lbl)
                
                inp = TextInput(
                    hint_text="0.0",
                    text="", 
                    size_hint_x=0.35,
                    size_hint_y=None,
                    height="32dp",
                    multiline=False,
                    input_filter="float",
                    font_size="15sp",
                    background_color=(0.18, 0.22, 0.25, 1),
                    foreground_color=(1, 1, 1, 1),
                    padding=["8dp", "4dp", "8dp", "4dp"],
                    pos_hint={"center_y": 0.5}
                )
                row.add_widget(inp)
                self.recipe_inputs[name] = inp 
                calc_container.add_widget(row)
        except Exception as e:
            print(f"Ошибка конструктора: {e}")

        # 4. Экран истории (Без надписи «сырье»)
        try:
            hist_text = ""
            for timestamp, action_type, target_name, amount in history:
                clean_target = target_name.replace(" (сырье)", "")
                
                if action_type == 'INCOME':
                    type_ru = "Приход"
                    is_ingredient = any(target_name == ing[0] for ing in ingredients)
                    display_amount = f"{amount / 1000.0} кг/л" if is_ingredient else f"{amount} л."
                else:
                    type_ru = "Приготовлено"
                    display_amount = f"{amount} л."
                    
                hist_text += f"• [{timestamp}] {type_ru}:\n  {clean_target} -> {display_amount}\n\n"
            self.root.get_screen('history').ids.history_text.text = hist_text if hist_text else "История пуста"
        except Exception as e:
            print(f"Ошибка истории: {e}")

    def show_input_dialog(self, target_name, mode):
        self.current_target = target_name
        self.current_mode = mode
        
        ingredients, _, _ = database.get_stock_data()
        is_ingredient = any(target_name == ing[0] for ing in ingredients)
        unit = "кг/л" if (mode == 'INCOME' and is_ingredient) else "л."
        
        clean_target = target_name.replace(" (сырье)", "")
        
        title_text = f"Приход ({unit}): {clean_target}" if mode == 'INCOME' else f"Сделать по техкарте (л.): {clean_target}"
        self.input_field = MDTextField(text="1", input_filter="float")
        
        self.dialog = MDDialog(
            title=title_text,
            type="custom",
            content_cls=self.input_field,
            buttons=[
                MDRaisedButton(text="ОТМЕНА", on_release=lambda x: self.dialog.dismiss()),
                MDRaisedButton(text="ОК", on_release=self.process_dialog_input)
            ],
        )
        self.dialog.open()

    def process_dialog_input(self, instance):
        try: amount = float(self.input_field.text)
        except ValueError: amount = 1.0
        self.dialog.dismiss()
        
        if self.current_mode == 'INCOME':
            database.add_ingredients(self.current_target, amount * 1000.0)
        elif self.current_mode == 'COOK':
            database.cook_pre_mix(self.current_target, amount)
        self.update_screen_data()

    def show_new_ingredient_dialog(self):
        self.new_ing_field = MDTextField(hint_text="Например: Сироп маракуйя")
        self.dialog = MDDialog(
            title="Добавить новый компонент",
            type="custom",
            content_cls=self.new_ing_field,
            buttons=[
                MDRaisedButton(text="ОТМЕНА", on_release=lambda x: self.dialog.dismiss()),
                MDRaisedButton(text="ДОБАВИТЬ", on_release=self.process_new_ingredient)
            ],
        )
        self.dialog.open()

    def process_new_ingredient(self, instance):
        name = self.new_ing_field.text.strip()
        self.dialog.dismiss()
        if name:
            if not name.endswith("(сырье)"):
                name = f"{name} (сырье)"
            database.add_new_ingredient_to_db(name)
            self.update_screen_data()

    def save_new_premix_recipe(self):
        calc_screen = self.root.get_screen('calculator')
        mix_name = calc_screen.ids.new_mix_name.text.strip()
        try: output = float(calc_screen.ids.new_mix_output.text)
        except ValueError: output = 1.0
            
        if not mix_name: return
            
        chosen_ingredients = {}
        for ing_name, inp_field in self.recipe_inputs.items():
            try:
                if inp_field.text.strip():
                    weight_kg_l = float(inp_field.text)
                    if weight_kg_l > 0:
                        chosen_ingredients[ing_name] = weight_kg_l * 1000.0
            except ValueError: continue
                
        if chosen_ingredients:
            success = database.create_pre_mix_with_recipe(mix_name, output, chosen_ingredients)
            if success:
                calc_screen.ids.new_mix_name.text = ""
                calc_screen.ids.new_mix_output.text = "1"
                self.update_screen_data()

    def undo_action(self):
        if database.undo_last_action():
            self.update_screen_data()

if __name__ == "__main__":
    InventoryApp().run()