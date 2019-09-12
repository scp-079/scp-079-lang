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
import re

from pyrogram import Client, Message

from .. import glovar
from .etc import code, get_int, get_lang, get_text, thread, user_mention
from .filters import is_class_e
from .telegram import send_message

# Enable logging
logger = logging.getLogger(__name__)


def lang_test(client: Client, message: Message) -> bool:
    # Test message's length
    try:
        message_text = get_text(message)
        if message_text:
            if re.search("^管理员：[0-9]", message_text):
                aid = get_int(message_text.split("\n\n")[0].split("：")[1])
            else:
                aid = message.from_user.id

            the_lang = get_lang(message_text, glovar.lang_protect)
            if the_lang and the_lang in glovar.lang_all:
                text = (f"管理员：{user_mention(aid)}\n\n"
                        f"消息语言：{code(the_lang)}\n"
                        f"白名单：{code(is_class_e(None, message, True))}\n")
                thread(send_message, (client, glovar.test_group_id, text, message.message_id))

        return True
    except Exception as e:
        logger.warning(f"Lang test error: {e}", exc_info=True)

    return False
