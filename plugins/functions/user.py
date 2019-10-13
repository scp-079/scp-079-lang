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
from typing import Optional, Union

from pyrogram import Client, Message, User

from .. import glovar
from .etc import crypt_str, get_forward_name, get_full_name, get_now, lang, thread
from .channel import ask_for_help, declare_message, forward_evidence, send_debug, share_bad_user
from .channel import share_watch_user, update_score
from .file import save
from .group import delete_message
from .filters import is_class_d, is_declared_message, is_detected_user, is_high_score_user, is_limited_user
from .filters import is_new_user, is_regex_text, is_watch_user

from .ids import init_user_id
from .telegram import get_users, kick_chat_member

# Enable logging
logger = logging.getLogger(__name__)


def add_bad_user(client: Client, uid: int) -> bool:
    # Add a bad user, share it
    try:
        if uid in glovar.bad_ids["users"]:
            return True

        glovar.bad_ids["users"].add(uid)
        save("bad_ids")
        share_bad_user(client, uid)

        return True
    except Exception as e:
        logger.warning(f"Add bad user error: {e}", exc_info=True)

    return False


def add_detected_user(gid: int, uid: int, now: int) -> bool:
    # Add or update a detected user's status
    try:
        if not init_user_id(uid):
            return False

        previous = glovar.user_ids[uid]["detected"].get(gid)
        glovar.user_ids[uid]["detected"][gid] = now

        return bool(previous)
    except Exception as e:
        logger.warning(f"Add detected user error: {e}", exc_info=True)

    return False


def add_watch_user(client: Client, the_type: str, uid: int, now: int) -> bool:
    # Add a watch ban user, share it
    try:
        until = now + glovar.time_ban
        glovar.watch_ids[the_type][uid] = until
        until = str(until)
        until = crypt_str("encrypt", until, glovar.key)
        share_watch_user(client, the_type, uid, until)
        save("watch_ids")

        return True
    except Exception as e:
        logger.warning(f"Add watch user error: {e}", exc_info=True)

    return False


def ban_user(client: Client, gid: int, uid: Union[int, str]) -> bool:
    # Ban a user
    try:
        thread(kick_chat_member, (client, gid, uid))

        return True
    except Exception as e:
        logger.warning(f"Ban user error: {e}", exc_info=True)

    return False


def get_user(client: Client, uid: Union[int, str]) -> Optional[User]:
    # Get a user
    result = None
    try:
        result = get_users(client, [uid])
        if result:
            result = result[0]
    except Exception as e:
        logger.warning(f"Get user error: {e}", exc_info=True)

    return result


def terminate_user(client: Client, message: Message, user: User, context: str) -> bool:
    # Delete user's message, or ban the user
    try:
        result = None

        # Check if it is necessary
        if is_class_d(None, message) or is_declared_message(None, message):
            return False

        gid = message.chat.id
        uid = user.id
        mid = message.message_id
        context_list = context.split()
        the_type = context_list[0]
        the_lang = context_list[1]
        if len(context_list) == 3:
            more = context_list[2]
        else:
            more = None

        now = message.date or get_now()

        if the_type == "name":
            result = forward_evidence(
                client=client,
                message=message,
                user=user,
                level=lang("auto_ban"),
                rule=lang("name_examine"),
                the_lang=the_lang,
                more=more
            )
            if result:
                ban_user(client, gid, uid)
                delete_message(client, gid, mid)
                declare_message(client, gid, mid)
                if the_lang in glovar.lang_name:
                    add_bad_user(client, uid)
                    ask_for_help(client, "ban", gid, uid)
                else:
                    ask_for_help(client, "delete", gid, uid)

                send_debug(
                    client=client,
                    chat=message.chat,
                    action=lang("name_ban"),
                    uid=uid,
                    mid=mid,
                    em=result
                )

            return True

        if the_lang in glovar.lang_text or the_lang in {"spc", "spe"}:
            full_name = get_full_name(user, True)
            forward_name = get_forward_name(message, True)
            if ((is_regex_text("wb", full_name) or is_regex_text("wb", forward_name))
                    and (full_name not in glovar.except_ids["long"] and forward_name not in glovar.except_ids["long"])):
                result = forward_evidence(
                    client=client,
                    message=message,
                    user=user,
                    level=lang("auto_ban"),
                    rule=lang("name_examine"),
                    the_lang=the_lang,
                    more=more
                )
                if result:
                    add_bad_user(client, uid)
                    ban_user(client, gid, uid)
                    delete_message(client, gid, mid)
                    declare_message(client, gid, mid)
                    ask_for_help(client, "ban", gid, uid)
                    send_debug(
                        client=client,
                        chat=message.chat,
                        action=lang("name_ban"),
                        uid=uid,
                        mid=mid,
                        em=result
                    )
            elif is_watch_user(message, "ban"):
                result = forward_evidence(
                    client=client,
                    message=message,
                    user=user,
                    level=lang("auto_ban"),
                    rule=lang("watch_user"),
                    the_lang=the_lang,
                    more=more
                )
                if result:
                    add_bad_user(client, uid)
                    ban_user(client, gid, uid)
                    delete_message(client, gid, mid)
                    declare_message(client, gid, mid)
                    ask_for_help(client, "ban", gid, uid)
                    send_debug(
                        client=client,
                        chat=message.chat,
                        action=lang("watch_ban"),
                        uid=uid,
                        mid=mid,
                        em=result
                    )
            elif is_high_score_user(message):
                score = is_high_score_user(message)
                result = forward_evidence(
                    client=client,
                    message=message,
                    user=user,
                    level=lang("auto_ban"),
                    rule=lang("score_user"),
                    the_lang=the_lang,
                    score=score,
                    more=more
                )
                if result:
                    add_bad_user(client, uid)
                    ban_user(client, gid, uid)
                    delete_message(client, gid, mid)
                    declare_message(client, gid, mid)
                    ask_for_help(client, "ban", gid, uid)
                    send_debug(
                        client=client,
                        chat=message.chat,
                        action=lang("score_ban"),
                        uid=uid,
                        mid=mid,
                        em=result
                    )
            elif is_watch_user(message, "delete"):
                result = forward_evidence(
                    client=client,
                    message=message,
                    user=user,
                    level=lang("auto_delete"),
                    rule=lang("watch_user"),
                    the_lang=the_lang,
                    more=more
                )
                if result:
                    add_watch_user(client, "ban", uid, now)
                    delete_message(client, gid, mid)
                    declare_message(client, gid, mid)
                    ask_for_help(client, "delete", gid, uid, "global")
                    previous = add_detected_user(gid, uid, now)
                    not previous and update_score(client, uid)
                    send_debug(
                        client=client,
                        chat=message.chat,
                        action=lang("watch_delete"),
                        uid=uid,
                        mid=mid,
                        em=result
                    )
            elif not more and (is_new_user(message.from_user, now, gid) and the_lang in glovar.lang_name
                               or is_limited_user(gid, message.from_user, now) and the_lang in glovar.lang_name):
                result = forward_evidence(
                    client=client,
                    message=message,
                    user=user,
                    level=lang("auto_delete"),
                    rule=lang("watch_user"),
                    the_lang=the_lang,
                    more=lang("op_upgrade")
                )
                if result:
                    add_watch_user(client, "ban", uid, now)
                    delete_message(client, gid, mid)
                    declare_message(client, gid, mid)
                    ask_for_help(client, "delete", gid, uid, "global")
                    previous = add_detected_user(gid, uid, now)
                    not previous and update_score(client, uid)
                    send_debug(
                        client=client,
                        chat=message.chat,
                        action=lang("watch_delete"),
                        uid=uid,
                        mid=mid,
                        em=result
                    )
            elif is_detected_user(message) or uid in glovar.recorded_ids[gid] or the_type == "true":
                delete_message(client, gid, mid)
                add_detected_user(gid, uid, now)
                declare_message(client, gid, mid)
            else:
                result = forward_evidence(
                    client=client,
                    message=message,
                    user=user,
                    level=lang("auto_delete"),
                    rule=lang("rule_custom"),
                    the_lang=the_lang,
                    more=more
                )
                if result:
                    glovar.recorded_ids[gid].add(uid)
                    delete_message(client, gid, mid)
                    declare_message(client, gid, mid)
                    previous = add_detected_user(gid, uid, now)
                    not previous and update_score(client, uid)
                    send_debug(
                        client=client,
                        chat=message.chat,
                        action=lang("auto_delete"),
                        uid=uid,
                        mid=mid,
                        em=result
                    )
        else:
            if uid in glovar.recorded_ids[gid]:
                delete_message(client, gid, mid)
                declare_message(client, gid, mid)
            else:
                result = forward_evidence(
                    client=client,
                    message=message,
                    user=user,
                    level=lang("auto_delete"),
                    rule=lang("rule_custom"),
                    the_lang=the_lang,
                    more=more
                )
                if result:
                    glovar.recorded_ids[gid].add(uid)
                    delete_message(client, gid, mid)
                    declare_message(client, gid, mid)
                    send_debug(
                        client=client,
                        chat=message.chat,
                        action=lang("auto_delete"),
                        uid=uid,
                        mid=mid,
                        em=result
                    )

        return bool(result)
    except Exception as e:
        logger.warning(f"Terminate user error: {e}", exc_info=True)

    return False
