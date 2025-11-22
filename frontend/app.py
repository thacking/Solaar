#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio

from config import load_config, save_config

# Hardcoded wave list
WAVE_OPTIONS = [
    "HAPPY ALERT",
    "MAD",
    "SHARP COLLISION",
    "FIREWORKS",
    "SOFT THUMP",
]


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Haptics Settings")

        # Load UI
        builder = Gtk.Builder.new_from_file("ui/main.ui")
        root = builder.get_object("root")
        self.set_child(root)

        # Bind widgets
        self.notif_enabled = builder.get_object("notif_enabled")
        self.notif_default_wave = builder.get_object("notif_default_wave")
        self.rules_list = builder.get_object("rules_list")
        self.rule_name = builder.get_object("rule_name")
        self.rule_pattern = builder.get_object("rule_pattern")  # NEW
        self.rule_wave = builder.get_object("rule_wave")
        self.rule_add = builder.get_object("rule_add")
        self.rule_delete = builder.get_object("rule_delete")
        self.cursor_link_wave = builder.get_object("cursor_link_wave")
        self.cursor_edit_wave = builder.get_object("cursor_edit_wave")

        # Load config
        self.config = load_config()

        # Populate dropdowns
        wave_model = Gtk.StringList.new(WAVE_OPTIONS)
        self.notif_default_wave.set_model(wave_model)
        self.rule_wave.set_model(wave_model)
        self.cursor_link_wave.set_model(wave_model)
        self.cursor_edit_wave.set_model(wave_model)

        # Apply config values
        self.notif_enabled.set_active(self.config["notifications"]["enabled"])
        self.notif_default_wave.set_selected(
            WAVE_OPTIONS.index(self.config["notifications"]["default_wave"])
        )
        self.cursor_link_wave.set_selected(
            WAVE_OPTIONS.index(self.config["cursor"]["link_wave"])
        )
        self.cursor_edit_wave.set_selected(
            WAVE_OPTIONS.index(self.config["cursor"]["edit_wave"])
        )

        # Rules ListStore
        self.rules = Gio.ListStore.new(Gtk.StringObject)
        for rule in self.config["notifications"]["custom"]:
            self.rules.append(Gtk.StringObject.new(rule["name"]))

        # SingleSelection model
        self.rules_selection = Gtk.SingleSelection.new(self.rules)
        self.rules_list.set_model(self.rules_selection)

        # Row factory
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self.setup_rule_item)
        factory.connect("bind", self.bind_rule_item)
        self.rules_list.set_factory(factory)

        # Connect signals with handler references
        self.rule_name_handler = self.rule_name.connect("changed", self.on_rule_edit)
        self.rule_pattern_handler = self.rule_pattern.connect("changed", self.on_rule_edit)  # NEW
        self.rule_wave_handler = self.rule_wave.connect("notify::selected", self.on_rule_edit)
        self.selection_handler = self.rules_selection.connect("notify::selected", self.on_rule_select)

        self.rule_add.connect("clicked", self.on_rule_add)
        self.rule_delete.connect("clicked", self.on_rule_delete)

    # ---------- List row creation ----------
    def setup_rule_item(self, factory, list_item):
        list_item.set_child(Gtk.Label(xalign=0))

    def bind_rule_item(self, factory, list_item):
        obj = list_item.get_item()
        list_item.get_child().set_text(obj.get_string())

    # ---------- Select rule ----------
    def on_rule_select(self, selection, _param):
        pos = selection.get_selected()
        if pos < 0:
            self.rule_name.handler_block(self.rule_name_handler)
            self.rule_pattern.handler_block(self.rule_pattern_handler)
            self.rule_wave.handler_block(self.rule_wave_handler)

            self.rule_name.set_text("")
            self.rule_pattern.set_text("")
            self.rule_wave.set_selected(0)

            self.rule_name.handler_unblock(self.rule_name_handler)
            self.rule_pattern.handler_unblock(self.rule_pattern_handler)
            self.rule_wave.handler_unblock(self.rule_wave_handler)
            return

        rule = self.config["notifications"]["custom"][pos]

        # Block edit signals while updating UI
        self.rule_name.handler_block(self.rule_name_handler)
        self.rule_pattern.handler_block(self.rule_pattern_handler)
        self.rule_wave.handler_block(self.rule_wave_handler)

        self.rule_name.set_text(rule["name"])
        self.rule_pattern.set_text(rule.get("pattern", ""))  # NEW
        self.rule_wave.set_selected(WAVE_OPTIONS.index(rule["wave"]))

        self.rule_name.handler_unblock(self.rule_name_handler)
        self.rule_pattern.handler_unblock(self.rule_pattern_handler)
        self.rule_wave.handler_unblock(self.rule_wave_handler)

    # ---------- Add rule ----------
    def on_rule_add(self, *_):
        new_rule = {"name": "New Rule", "pattern": "", "wave": WAVE_OPTIONS[0]}
        self.config["notifications"]["custom"].append(new_rule)
        self.rules.append(Gtk.StringObject.new(new_rule["name"]))

        # Select the newly added rule
        index = len(self.config["notifications"]["custom"]) - 1
        self.rules_selection.set_selected(index)

        save_config(self.config)

    # ---------- Delete rule ----------
    def on_rule_delete(self, *_):
        pos = self.rules_selection.get_selected()
        if pos < 0:
            return

        self.rules.remove(pos)
        self.config["notifications"]["custom"].pop(pos)

        # Clear UI fields
        self.rule_name.handler_block(self.rule_name_handler)
        self.rule_pattern.handler_block(self.rule_pattern_handler)
        self.rule_wave.handler_block(self.rule_wave_handler)

        self.rule_name.set_text("")
        self.rule_pattern.set_text("")
        self.rule_wave.set_selected(0)

        self.rule_name.handler_unblock(self.rule_name_handler)
        self.rule_pattern.handler_unblock(self.rule_pattern_handler)
        self.rule_wave.handler_unblock(self.rule_wave_handler)

        self.rules_selection.unselect_all()

        save_config(self.config)

    # ---------- Edit rule ----------
    def on_rule_edit(self, *_):
        pos = self.rules_selection.get_selected()
        if pos < 0:
            return

        rule = self.config["notifications"]["custom"][pos]

        new_name = self.rule_name.get_text()
        new_pattern = self.rule_pattern.get_text()  # NEW
        new_wave = WAVE_OPTIONS[self.rule_wave.get_selected()]

        # Update config
        rule["name"] = new_name
        rule["pattern"] = new_pattern
        rule["wave"] = new_wave

        # Replace StringObject safely with signal blocking
        self.rules_selection.handler_block(self.selection_handler)
        self.rules.remove(pos)
        self.rules.insert(pos, Gtk.StringObject.new(new_name))
        self.rules_selection.set_selected(pos)
        self.rules_selection.handler_unblock(self.selection_handler)

        save_config(self.config)

    # ---------- Save on close ----------
    def do_close_request(self, *_):
        self.config["notifications"]["enabled"] = self.notif_enabled.get_active()
        self.config["notifications"]["default_wave"] = \
            WAVE_OPTIONS[self.notif_default_wave.get_selected()]

        self.config["cursor"]["link_wave"] = \
            WAVE_OPTIONS[self.cursor_link_wave.get_selected()]
        self.config["cursor"]["edit_wave"] = \
            WAVE_OPTIONS[self.cursor_edit_wave.get_selected()]

        save_config(self.config)
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
