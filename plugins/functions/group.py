# SCP-079-LANG - Ban or delete by detecting the language
# Copyright (C) 2019 SCP-079 <https://scp-079.org>
#
# This file is part of SCP-079-LANG.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from typing import Optional

from pyrogram import Chat, Client, Message

from .. import glovar
from .etc import code, lang, t2t, thread
from .file import save
from .telegram import delete_messages, get_chat, get_messages, leave_chat

# Enable logging
logger = logging.getLogger(__name__)


def delete_message(client: Client, gid: int, mid: int) -> bool:
    # Delete a single message
    try:
        if not gid or not mid:
            return True

        mids = [mid]
        thread(delete_messages, (client, gid, mids))

        return True
    except Exception as e:
        logger.warning(f"Delete message error: {e}", exc_info=True)

    return False


def get_config_text(config: dict) -> str:
    # Get config text
    result = ""
    try:
        # Basic
        default_text = (lambda x: lang("default") if x else lang("custom"))(config.get("default"))
        delete_text = (lambda x: lang("enabled") if x else lang("disabled"))(config.get("delete"))
        restrict_text = (lambda x: lang("enabled") if x else lang("disabled"))(config.get("restrict"))
        result += (f"{lang('config')}{lang('colon')}{code(default_text)}\n"
                   f"{lang('delete')}{lang('colon')}{code(delete_text)}\n"
                   f"{lang('restrict')}{lang('colon')}{code(restrict_text)}\n")

        # Languages
        for the_type in ["name", "text", "sticker", "bio"]:
            the_default = (lambda x: lang("yes") if x else lang("no"))(config.get(the_type)
                                                                       and config[the_type].get("default"))
            the_enable = (lambda x: lang("enabled") if x else lang("disabled"))(config.get(the_type)
                                                                                and config[the_type].get("enable"))

            result += (f"{lang(f'{the_type}_default')}{lang('colon')}{code(the_default)}\n"
                       f"{lang(f'{the_type}_enable')}{lang('colon')}{code(the_enable)}\n")

            if config.get(the_type) and config[the_type].get("list"):
                result += f"{lang(f'{the_type}_lang')}{lang('colon')}" + "-" * 16 + "\n\n"
                for the_lang in config[the_type]["list"]:
                    result += "\t" * 4 + code(the_lang) + "\n"

                result += "\n"

        # Special
        for the_type in ["spc", "spe"]:
            the_filter = (lambda x: lang("filter") if x else lang("ignore"))(config.get(the_type))
            result += f"{lang(the_type)}{lang('colon')}{code(the_filter)}\n"
    except Exception as e:
        logger.warning(f"Get config text error: {e}", exc_info=True)

    return result


def get_description(client: Client, gid: int) -> str:
    # Get group's description
    result = ""
    try:
        group = get_group(client, gid)
        if group and group.description:
            result = t2t(group.description, False)
    except Exception as e:
        logger.warning(f"Get description error: {e}", exc_info=True)

    return result


def get_group(client: Client, gid: int, cache: bool = True) -> Optional[Chat]:
    # Get the group
    result = None
    try:
        the_cache = glovar.chats.get(gid)

        if the_cache:
            result = the_cache
        else:
            result = get_chat(client, gid)

        if cache and result:
            glovar.chats[gid] = result
    except Exception as e:
        logger.warning(f"Get group error: {e}", exc_info=True)

    return result


def get_group_sticker(client: Client, gid: int) -> str:
    # Get group sticker set name
    result = ""
    try:
        group = get_group(client, gid)
        if group and group.sticker_set_name:
            result = group.sticker_set_name
    except Exception as e:
        logger.warning(f"Get group sticker error: {e}", exc_info=True)

    return result


def get_message(client: Client, gid: int, mid: int) -> Optional[Message]:
    # Get a single message
    result = None
    try:
        mids = [mid]
        result = get_messages(client, gid, mids)
        if result:
            result = result[0]
    except Exception as e:
        logger.warning(f"Get message error: {e}", exc_info=True)

    return result


def get_pinned(client: Client, gid: int) -> Optional[Message]:
    # Get group's pinned message
    result = None
    try:
        group = get_group(client, gid)
        if group and group.pinned_message:
            result = group.pinned_message
    except Exception as e:
        logger.warning(f"Get pinned error: {e}", exc_info=True)

    return result


def leave_group(client: Client, gid: int) -> bool:
    # Leave a group, clear it's data
    try:
        glovar.left_group_ids.add(gid)
        save("left_group_ids")
        thread(leave_chat, (client, gid))

        glovar.admin_ids.pop(gid, set())
        save("admin_ids")

        glovar.configs.pop(gid, {})
        save("configs")

        return True
    except Exception as e:
        logger.warning(f"Leave group error: {e}", exc_info=True)

    return False
