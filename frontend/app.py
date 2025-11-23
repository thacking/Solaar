#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, Gdk

from config import load_config, save_config

WAVE_OPTIONS = [
    "SHARP STATE CHANGE", "DAMP STATE CHANGE", "SHARP COLLISION",
    "DAMP COLLISION", "SUBTLE COLLISION", "HAPPY ALERT", "ANGRY ALERT",
    "COMPLETED", "SQUARE", "WAVE", "FIREWORK", "MAD", "KNOCK", "JINGLE", "RINGING",
]

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Haptics Settings")

        builder = Gtk.Builder.new_from_file("ui/main.ui")
        root = builder.get_object("root")
        self.set_child(root)

        # CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path("style.css")
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Widgets
        self.notif_enabled = builder.get_object("notif_enabled")
        self.notif_default_wave = builder.get_object("notif_default_wave")
        self.rules_list = builder.get_object("rules_list")
        self.rule_name = builder.get_object("rule_name")
        self.rule_pattern_app = builder.get_object("rule_pattern_app")
        self.rule_pattern_summary = builder.get_object("rule_pattern_summary")
        self.rule_pattern_body = builder.get_object("rule_pattern_body")
        self.rule_wave = builder.get_object("rule_wave")
        self.rule_add = builder.get_object("rule_add")
        self.rule_delete = builder.get_object("rule_delete")
        self.cursor_link_wave = builder.get_object("cursor_link_wave")
        self.save_button = builder.get_object("save_button")

        # Load config
        self.config = load_config()

        # Populate dropdowns
        wave_model = Gtk.StringList.new(WAVE_OPTIONS)
        self.notif_default_wave.set_model(wave_model)
        self.rule_wave.set_model(wave_model)
        self.cursor_link_wave.set_model(wave_model)

        # Apply config
        self.notif_enabled.set_active(self.config["notifications"]["enabled"])
        self.notif_default_wave.set_selected(
            WAVE_OPTIONS.index(self.config["notifications"]["default_wave"])
        )
        self.cursor_link_wave.set_selected(
            WAVE_OPTIONS.index(self.config["cursor"]["link_wave"])
        )

        # Rules ListStore
        self.rules = Gio.ListStore.new(Gtk.StringObject)
        for rule in self.config["notifications"]["custom"]:
            self.rules.append(Gtk.StringObject.new(rule["name"]))

        # SingleSelection
        self.rules_selection = Gtk.SingleSelection.new(self.rules)
        self.rules_list.set_model(self.rules_selection)

        # Factory for rows
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self.setup_rule_item)
        factory.connect("bind", self.bind_rule_item)
        self.rules_list.set_factory(factory)

        # Signal handlers
        self.rule_name_handler = self.rule_name.connect("changed", self.on_rule_edit)
        self.rule_pattern_app_handler = self.rule_pattern_app.connect("changed", self.on_rule_edit)
        self.rule_pattern_summary_handler = self.rule_pattern_summary.connect("changed", self.on_rule_edit)
        self.rule_pattern_body_handler = self.rule_pattern_body.connect("changed", self.on_rule_edit)
        self.rule_wave_handler = self.rule_wave.connect("notify::selected", self.on_rule_edit)
        self.selection_handler = self.rules_selection.connect("notify::selected", self.on_rule_select)

        self.rule_add.connect("clicked", self.on_rule_add)
        self.rule_delete.connect("clicked", self.on_rule_delete)
        self.save_button.connect("clicked", self.on_save_button)

        # Select the first rule on startup if exists
        if len(self.config["notifications"]["custom"]) > 0:
            self.rules_selection.set_selected(0)
            # Manually trigger the select handler to populate editor fields
            self.on_rule_select(self.rules_selection, None)

    # List row creation
    def setup_rule_item(self, factory, list_item):
        list_item.set_child(Gtk.Label(xalign=0))

    def bind_rule_item(self, factory, list_item):
        obj = list_item.get_item()
        list_item.get_child().set_text(obj.get_string())

    # Select rule
    def on_rule_select(self, selection, _param):
        pos = selection.get_selected()
        if pos < 0 or pos >= len(self.config["notifications"]["custom"]):
            self.clear_rule_editor()
            return

        rule = self.config["notifications"]["custom"][pos]

        # Block signals
        self.rule_name.handler_block(self.rule_name_handler)
        self.rule_pattern_app.handler_block(self.rule_pattern_app_handler)
        self.rule_pattern_summary.handler_block(self.rule_pattern_summary_handler)
        self.rule_pattern_body.handler_block(self.rule_pattern_body_handler)
        self.rule_wave.handler_block(self.rule_wave_handler)

        self.rule_name.set_text(rule["name"])
        self.rule_pattern_app.set_text(rule.get("pattern_app", ""))
        self.rule_pattern_summary.set_text(rule.get("pattern_summary", ""))
        self.rule_pattern_body.set_text(rule.get("pattern_body", ""))
        self.rule_wave.set_selected(WAVE_OPTIONS.index(rule["wave"]))

        # Unblock signals
        self.rule_name.handler_unblock(self.rule_name_handler)
        self.rule_pattern_app.handler_unblock(self.rule_pattern_app_handler)
        self.rule_pattern_summary.handler_unblock(self.rule_pattern_summary_handler)
        self.rule_pattern_body.handler_unblock(self.rule_pattern_body_handler)
        self.rule_wave.handler_unblock(self.rule_wave_handler)

    # Clear editor
    def clear_rule_editor(self):
        self.rule_name.handler_block(self.rule_name_handler)
        self.rule_pattern_app.handler_block(self.rule_pattern_app_handler)
        self.rule_pattern_summary.handler_block(self.rule_pattern_summary_handler)
        self.rule_pattern_body.handler_block(self.rule_pattern_body_handler)
        self.rule_wave.handler_block(self.rule_wave_handler)

        self.rule_name.set_text("")
        self.rule_pattern_app.set_text("")
        self.rule_pattern_summary.set_text("")
        self.rule_pattern_body.set_text("")
        self.rule_wave.set_selected(0)

        self.rule_name.handler_unblock(self.rule_name_handler)
        self.rule_pattern_app.handler_unblock(self.rule_pattern_app_handler)
        self.rule_pattern_summary.handler_unblock(self.rule_pattern_summary_handler)
        self.rule_pattern_body.handler_unblock(self.rule_pattern_body_handler)
        self.rule_wave.handler_unblock(self.rule_wave_handler)

    # Add rule
    def on_rule_add(self, *_):
        new_rule = {
            "name": "New Rule",
            "pattern_app": "",
            "pattern_summary": "",
            "pattern_body": "",
            "wave": WAVE_OPTIONS[0]
        }
        self.config["notifications"]["custom"].append(new_rule)
        self.rules.append(Gtk.StringObject.new(new_rule["name"]))
        self.rules_selection.set_selected(len(self.config["notifications"]["custom"]) - 1)

    # Delete rule
    def on_rule_delete(self, *_):
        pos = self.rules_selection.get_selected()
        if pos < 0 or pos >= len(self.config["notifications"]["custom"]):
            return
        self.rules.remove(pos)
        self.config["notifications"]["custom"].pop(pos)
        
        # Select the previous item if it exists, otherwise select the first item
        if len(self.config["notifications"]["custom"]) > 0:
            new_pos = max(0, pos - 1)
            self.rules_selection.set_selected(new_pos)
            # Manually trigger the select handler to populate editor fields
            self.on_rule_select(self.rules_selection, None)
        else:
            self.clear_rule_editor()
            self.rules_selection.unselect_all()

    # Edit rule
    def on_rule_edit(self, *_):
        pos = self.rules_selection.get_selected()
        if pos < 0 or pos >= len(self.config["notifications"]["custom"]):
            return

        rule = self.config["notifications"]["custom"][pos]
        rule["name"] = self.rule_name.get_text()
        rule["pattern_app"] = self.rule_pattern_app.get_text()
        rule["pattern_summary"] = self.rule_pattern_summary.get_text()
        rule["pattern_body"] = self.rule_pattern_body.get_text()
        rule["wave"] = WAVE_OPTIONS[self.rule_wave.get_selected()]

        # Update ListStore only if name changed
        current_label = self.rules.get_item(pos).get_string()
        if current_label != rule["name"]:
            self.rules_selection.handler_block(self.selection_handler)
            self.rules.remove(pos)
            self.rules.insert(pos, Gtk.StringObject.new(rule["name"]))
            self.rules_selection.set_selected(pos)
            self.rules_selection.handler_unblock(self.selection_handler)

    # Save button
    def on_save_button(self, *_):
        self.config["notifications"]["enabled"] = self.notif_enabled.get_active()
        self.config["notifications"]["default_wave"] = WAVE_OPTIONS[self.notif_default_wave.get_selected()]
        self.config["cursor"]["link_wave"] = WAVE_OPTIONS[self.cursor_link_wave.get_selected()]

        pos = self.rules_selection.get_selected()
        if 0 <= pos < len(self.config["notifications"]["custom"]):
            rule = self.config["notifications"]["custom"][pos]
            rule["name"] = self.rule_name.get_text()
            rule["pattern_app"] = self.rule_pattern_app.get_text()
            rule["pattern_summary"] = self.rule_pattern_summary.get_text()
            rule["pattern_body"] = self.rule_pattern_body.get_text()
            rule["wave"] = WAVE_OPTIONS[self.rule_wave.get_selected()]

        save_config(self.config)

    # Save on close
    def do_close_request(self, *_):
        self.on_save_button()
        return False


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.haptics.Editor")

    def do_activate(self):
        win = MainWindow(self)
        win.present()


if __name__ == "__main__":
    app = App()
    app.run()
