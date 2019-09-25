# Copyright 2019 Canonical, Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging

from urwid import (
    connect_signal,
    Divider,
    Filler,
    PopUpLauncher,
    Text,
    )

from subiquitycore.lsb_release import lsb_release
from subiquitycore.ui.buttons import (
    header_btn,
    other_btn,
    )
from subiquitycore.ui.container import (
    Columns,
    Pile,
    WidgetWrap,
    )
from subiquitycore.ui.utils import (
    button_pile,
    ClickableIcon,
    Color,
    )
from subiquitycore.ui.stretchy import (
    Stretchy,
    )
from subiquitycore.ui.width import (
    widget_width,
    )


log = logging.getLogger('subiquity.ui.help')


def close_btn(parent):
    return other_btn(
        _("Close"), on_press=lambda sender: parent.remove_overlay())


ABOUT_INSTALLER = _("""
Welcome to the Ubuntu Server Installer!

The most popular server Linux in the cloud and data centre, you can
rely on Ubuntu Server and its five years of guaranteed free upgrades.

The installer will guide you through installing Ubuntu Server
{release}.

The installer only requires the up and down arrow keys, space (or
return) and the occasional bit of typing.""")


def rewrap(text):
    paras = text.split("\n\n")
    return "\n\n".join([p.replace('\n', ' ') for p in paras]).strip()


class SimpleTextStretchy(Stretchy):

    def __init__(self, parent, title, text):
        widgets = [
            Text(rewrap(text)),
            Text(""),
            button_pile([close_btn(parent)]),
            ]
        super().__init__(title, widgets, 0, 2)


hline = Divider('─')
vline = Text('│')
tlcorner = Text('┌')
trcorner = Text('┐')
blcorner = Text('└')
brcorner = Text('┘')
rtee = Text('┤')
ltee = Text('├')


def menu_item(text, on_press=None):
    icon = ClickableIcon(_(text), 0)
    if on_press is not None:
        connect_signal(icon, 'click', on_press)
    return Color.frame_button(icon)


class HelpMenu(WidgetWrap):

    def __init__(self, parent):
        self.parent = parent
        close = header_btn(_("Help"))
        about = menu_item(_("About the installer"), on_press=self._about)
        local = menu_item(_("Help on this screen"))
        keys = menu_item(_("Help on keyboard shortcuts"))
        entries = [
            about,
            local,
            hline,
            keys,
            ]
        buttons = [
            close,
            about,
            local,
            keys,
            ]
        for button in buttons:
            connect_signal(button.base_widget, 'click', self._close)

        rows = [
            Columns([
                ('fixed', 1, tlcorner),
                hline,
                (widget_width(close), close),
                ('fixed', 1, trcorner),
                ]),
            ]
        for entry in entries:
            if isinstance(entry, Divider):
                left, right = ltee, rtee
            else:
                left = right = vline
            rows.append(Columns([
                ('fixed', 1, left),
                entry,
                ('fixed', 1, right),
                ]))
        rows.append(
            Columns([
                (1, blcorner),
                hline,
                (1, brcorner),
                ]))
        self.width = max([widget_width(b) for b in buttons]) + 2
        self.height = len(entries) + 2
        super().__init__(Color.frame_header(Filler(Pile(rows))))

    def keypress(self, size, key):
        if key == 'esc':
            self.parent.close_pop_up()
        else:
            return super().keypress(size, key)

    def _close(self, sender):
        self.parent.close_pop_up()

    def _show_overlay(self, stretchy):
        app = self.parent.app
        ui = app.ui
        fp = ui.pile.focus_position
        ui.pile.focus_position = 1
        btn_label = self.parent.btn.base_widget._label
        btn_label._selectable = False
        app.showing_help = True

        def restore_focus():
            app.showing_help = False
            ui.pile.focus_position = fp
            btn_label._selectable = True

        connect_signal(stretchy, 'closed', restore_focus)

        ui.body.show_stretchy_overlay(stretchy)

    def _about(self, sender=None):
        self._show_overlay(
            SimpleTextStretchy(
                self.parent.app.ui.body,
                _("About the installer"),
                _(ABOUT_INSTALLER).format(**lsb_release())))


class HelpButton(PopUpLauncher):

    def __init__(self, app):
        self.app = app
        self.btn = header_btn(_("Help"), on_press=self._open)
        super().__init__(self.btn)

    def _open(self, sender):
        log.debug("open help menu")
        self.open_pop_up()

    def create_pop_up(self):
        self._menu = HelpMenu(self)
        return self._menu

    def get_pop_up_parameters(self):
        return {
            'left': widget_width(self.btn) - self._menu.width + 1,
            'top': 0,
            'overlay_width': self._menu.width,
            'overlay_height': self._menu.height,
            }
