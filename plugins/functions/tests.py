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
from .channel import get_content
from .etc import code, get_int, get_lang, get_text, lang, mention_id, thread
from .filters import is_class_e, is_detected_url
from .telegram import send_message

# Enable logging
logger = logging.getLogger(__name__)


def lang_test(client: Client, message: Message) -> bool:
    # Test message's lang
    try:
        origin_text = get_text(message)
        if re.search(f"^{lang('admin')}{lang('colon')}[0-9]", origin_text):
            aid = get_int(origin_text.split("\n\n")[0].split(lang('colon'))[1])
        else:
            aid = message.from_user.id

        text = ""
        message_text = get_text(message, False, False)

        # Detected record
        content = get_content(message)
        detection = glovar.contents.get(content, "")
        if detection:
            text += f"{lang('record_content')}{lang('colon')}{code(detection)}\n"

        # Detected url
        detection = is_detected_url(message)
        if detection:
            text += f"{lang('record_link')}{lang('colon')}{code(detection)}\n"

        # Get language
        if message_text:
            the_lang = get_lang(message_text)
            if the_lang and the_lang in glovar.lang_all:
                text += f"{lang('message_lang')}{lang('colon')}{code(the_lang)}\n"

        # Send the result
        if text:
            white_listed = is_class_e(None, message, True) or message_text in glovar.except_ids["long"]
            text += f"{lang('white_listed')}{lang('colon')}{code(white_listed)}\n"
            text = f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n\n" + text
            thread(send_message, (client, glovar.test_group_id, text, message.message_id))

        return True
    except Exception as e:
        logger.warning(f"Lang test error: {e}", exc_info=True)

    return False
